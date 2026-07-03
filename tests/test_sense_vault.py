"""SENSE + VAULT contract tests — no GPU, no HealthKit, CI-fast."""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.context_signals import ContextSignals, SignalWindow, nudge_worthy
from app.schemas.foot_check import (
    CaptureView, FootCheckReport, Observation, ObservationTag, QCResult, ViewQC,
)
from app.vault.store import Vault

NOW = datetime.now(timezone.utc)
WIN = SignalWindow(start=NOW - timedelta(days=1), end=NOW)


def sig(**kw) -> ContextSignals:
    return ContextSignals(window=WIN, **kw)


class TestContextSignalsContract:
    def test_all_none_is_valid(self):
        s = sig()
        assert s.gait_asymmetry_pct is None and s.signal_sha256()

    def test_unknown_field_rejected(self):
        with pytest.raises(ValidationError):
            ContextSignals(window=WIN, ulcer_risk=0.9)  # symptom vocab -> die

    def test_bounds_enforced(self):
        with pytest.raises(ValidationError):
            sig(gait_asymmetry_pct=140.0)
        with pytest.raises(ValidationError):
            sig(wrist_temp_deviation_c=9.0)

    def test_hash_deterministic(self):
        s = sig(steps_7d_avg=4200)
        assert s.signal_sha256() == s.signal_sha256()


class TestNudgeIsDeterministicWellnessOnly:
    def test_gait_shift_triggers(self):
        fire, copy = nudge_worthy(sig(gait_asymmetry_pct=9.5))
        assert fire and "foot check" in copy

    def test_quiet_signals_do_not_fire(self):
        fire, _ = nudge_worthy(sig(gait_asymmetry_pct=3.0, steps_7d_avg=6000))
        assert not fire

    def test_copy_never_uses_symptom_language(self):
        banned = {"ulcer", "wound", "infection", "inflammation", "symptom",
                  "diagnos", "disease", "neuropath"}
        for s in [sig(gait_asymmetry_pct=20.0),
                  sig(wrist_temp_deviation_c=1.2),
                  sig(walking_speed_delta_pct=-30.0)]:
            _, copy = nudge_worthy(s)
            assert not any(b in copy.lower() for b in banned)


class TestQCSingleSource:
    def test_config_matches_shared_json(self):
        shared = json.loads(
            (Path(__file__).parent.parent / "shared" / "qc_constants.json").read_text()
        )
        s = get_settings()
        assert s.qc_min_side_px == shared["min_side_px"]
        assert s.qc_min_sharpness == shared["min_sharpness"]
        assert s.max_image_bytes == shared["max_image_bytes"]

    def test_swift_codegen_matches_shared_json(self, tmp_path):
        import subprocess, sys
        root = Path(__file__).parent.parent
        subprocess.run([sys.executable, "tools/codegen_qc.py"], cwd=root, check=True)
        swift = (root / "dist" / "ios" / "QCConstants.swift").read_text()
        shared = json.loads((root / "shared" / "qc_constants.json").read_text())
        assert f"minSidePx: Int = {shared['min_side_px']}" in swift
        assert f"maxImageBytes: Int = {shared['max_image_bytes']}" in swift


class TestVault:
    def _vault(self, tmp_path) -> Vault:
        return Vault(tmp_path / "vault.db", tmp_path / "vault.key")

    def _report(self) -> FootCheckReport:
        qc = QCResult(passed=True, sharpness=99, brightness=120, width=1000, height=800)
        return FootCheckReport(
            model_id="m", prompt_sha256="p" * 64,
            views=[ViewQC(view=CaptureView.plantar_left, image_sha256="i" * 64, qc=qc)],
            coverage_complete=False,
            observations=[Observation(tag=ObservationTag.none_noted)],
            attention_tier="green", tier_reason="ok",
        )

    def test_roundtrip_join_by_day(self, tmp_path):
        v = self._vault(tmp_path)
        v.put_report(self._report())
        v.put_signals(sig(gait_asymmetry_pct=4.0))
        bundle = v.day_bundle(date.today())
        assert len(bundle["report"]) == 1 and len(bundle["signals"]) == 1
        assert bundle["signals"][0]["gait_asymmetry_pct"] == 4.0

    def test_comparison_feed_orders_newest_first(self, tmp_path):
        v = self._vault(tmp_path)
        v.put_report(self._report())
        feed = v.comparison_feed(date.today(), lookback=5)
        assert feed and feed[0]["day"] == date.today().isoformat()

    def test_unreadable_without_key(self, tmp_path):
        v = self._vault(tmp_path)
        v.put_report(self._report())
        # attacker with the db but the WRONG key
        intruder = Vault(tmp_path / "vault.db", tmp_path / "other.key")
        assert intruder.verify_readable() is False
        # raw blob is not plaintext JSON
        import sqlite3
        blob = sqlite3.connect(tmp_path / "vault.db").execute(
            "SELECT body FROM vault LIMIT 1").fetchone()[0]
        assert b"observations" not in blob
