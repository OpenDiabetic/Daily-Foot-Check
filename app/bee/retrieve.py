"""Bee — maps observation tags to Field Guides via SQLite FTS5.

The index is built in :memory: at startup from guides_seed.json, so the
container stays fully read-only. 22 guides fit in page cache; retrieval is
sub-millisecond.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.schemas.foot_check import GuideRef, Observation, ObservationTag

_SEED = Path(__file__).parent / "guides_seed.json"

# tag -> FTS query terms
_TAG_QUERIES: dict[ObservationTag, str] = {
    ObservationTag.redness: "redness OR irritation OR pressure",
    ObservationTag.swelling: "swelling OR edema",
    ObservationTag.skin_break: '"skin break" OR wound OR blister OR cut',
    ObservationTag.discoloration: "discoloration OR color OR circulation",
    ObservationTag.nail_change: "nail OR toenail",
    ObservationTag.callus: "callus OR corn OR friction",
    ObservationTag.dryness_fissure: "dry OR cracking OR fissure OR moisturize",
    ObservationTag.deformity_note: "shape OR fit OR footwear",
    ObservationTag.asymmetry: "compare OR asymmetry OR baseline",
    ObservationTag.none_noted: "daily OR routine OR photo",
}


class Bee:
    def __init__(self) -> None:
        self._db = sqlite3.connect(":memory:", check_same_thread=False)
        self._db.execute(
            "CREATE VIRTUAL TABLE guides USING fts5(guide_id, title, body)"
        )
        seed = json.loads(_SEED.read_text())
        self._db.executemany(
            "INSERT INTO guides (guide_id, title, body) VALUES (?, ?, ?)",
            [(g["guide_id"], g["title"], g["body"]) for g in seed],
        )
        self._db.commit()

    def guides_for(self, observations: list[Observation], limit_per_tag: int = 1) -> list[GuideRef]:
        seen: set[str] = set()
        out: list[GuideRef] = []
        for obs in observations:
            query = _TAG_QUERIES.get(obs.tag)
            if not query:
                continue
            rows = self._db.execute(
                "SELECT guide_id, title FROM guides WHERE guides MATCH ? "
                "ORDER BY rank LIMIT ?",
                (query, limit_per_tag),
            ).fetchall()
            for guide_id, title in rows:
                if guide_id in seen:
                    continue
                seen.add(guide_id)
                out.append(
                    GuideRef(
                        guide_id=guide_id,
                        title=title,
                        reason=obs.tag.value.replace("_", " "),
                    )
                )
        return out[:5]
