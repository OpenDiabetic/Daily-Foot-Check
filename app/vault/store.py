"""VAULT — sovereign-lane encrypted history store.

Runs ONLY on edge devices (ZimaCube, Mac mini, DGX). The cloud lane has no
import path to this module and no endpoint that accepts its data.

Design:
- SQLite file on the device pool; every record body Fernet-encrypted before
  insert. Metadata columns (day, kind, sha256) stay plaintext for joins —
  they are hashes and dates, never content.
- Key lives in a device keyfile (0600, generated on first boot). Lose the
  key = lose history, by design. We cannot recover it and say so up front.
- The ComparisonEngine feed: pairs of (report, signals) for the same day and
  prior baselines — exactly what MedGemma 1.5 multi-timepoint calls want.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.schemas.context_signals import ContextSignals
from app.schemas.foot_check import FootCheckReport

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vault (
    id INTEGER PRIMARY KEY,
    day TEXT NOT NULL,                -- ISO date, join key
    kind TEXT NOT NULL CHECK (kind IN ('report','signals')),
    sha256 TEXT NOT NULL UNIQUE,      -- anchored hash (public anyway)
    body BLOB NOT NULL,               -- Fernet-encrypted JSON
    stored_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vault_day ON vault(day, kind);
"""


class Vault:
    def __init__(self, db_path: Path, key_path: Path) -> None:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        if not key_path.exists():
            key_path.write_bytes(Fernet.generate_key())
            key_path.chmod(0o600)
        self._fernet = Fernet(key_path.read_bytes())
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.executescript(_SCHEMA)

    # ---- writes -----------------------------------------------------------
    def put_report(self, report: FootCheckReport) -> None:
        self._put(report.created_at.date(), "report",
                  report.report_sha256(), report.model_dump_json())

    def put_signals(self, sig: ContextSignals) -> None:
        self._put(sig.created_at.date(), "signals",
                  sig.signal_sha256(), sig.model_dump_json())

    def _put(self, day: date, kind: str, sha: str, body_json: str) -> None:
        self._db.execute(
            "INSERT OR IGNORE INTO vault (day, kind, sha256, body, stored_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (day.isoformat(), kind, sha,
             self._fernet.encrypt(body_json.encode()),
             datetime.now(timezone.utc).isoformat()),
        )
        self._db.commit()

    # ---- reads ------------------------------------------------------------
    def day_bundle(self, day: date) -> dict:
        """All decrypted artifacts for one day: {'report': [...], 'signals': [...]}"""
        rows = self._db.execute(
            "SELECT kind, body FROM vault WHERE day = ? ORDER BY id",
            (day.isoformat(),),
        ).fetchall()
        out: dict[str, list[dict]] = {"report": [], "signals": []}
        for kind, blob in rows:
            out[kind].append(json.loads(self._fernet.decrypt(blob)))
        return out

    def comparison_feed(self, day: date, lookback: int = 5) -> list[dict]:
        """Most recent `lookback` day-bundles up to and including `day`,
        newest first — the ComparisonEngine / multi-timepoint input."""
        days = self._db.execute(
            "SELECT DISTINCT day FROM vault WHERE day <= ? "
            "ORDER BY day DESC LIMIT ?",
            (day.isoformat(), lookback),
        ).fetchall()
        return [
            {"day": d, **self.day_bundle(date.fromisoformat(d))} for (d,) in days
        ]

    def verify_readable(self) -> bool:
        """Health probe: can we decrypt the newest record with our key?"""
        row = self._db.execute(
            "SELECT body FROM vault ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return True
        try:
            self._fernet.decrypt(row[0])
            return True
        except InvalidToken:
            return False
