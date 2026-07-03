"""Guide authoring contract — the SOURCE ARTIFACT of the content supply chain.

One GuideDraft fans out to: Claude-Design booklet, short-form video script,
knowledge-graph nodes, Bee FTS5 corpus, and the published library. So the
schema carries not just prose but the structured hooks each renderer needs:
per-section pull-quotes, a shot list for video, graph claim edges, and Bee
routing terms.

Doctrine:
- extra='forbid' — the model cannot invent fields.
- Closed vocabulary (ObservationTag) governs which observations a guide serves.
- Every clinical claim is provenance-bound; no unsourced claims survive the gate.
- Writer emits state='proposed'. Only a human reviewer promotes to 'published'.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.foot_check import ObservationTag

GUIDE_SCHEMA_VERSION = "guide.v1"

DISCLAIMER = (
    "Educational monitoring — not a medical device. It never diagnoses. "
    "If anything here concerns you, show it to your care team."
)


class DraftState(str, Enum):
    proposed = "proposed"     # writer output — enters review queue
    in_review = "in_review"
    published = "published"   # human-promoted only
    rejected = "rejected"


class ClaimStrength(str, Enum):
    strong = "strong"
    conditional = "conditional"
    consensus = "consensus"       # expert opinion / best-practice
    contextual = "contextual"     # general educational framing


class ClaimSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim: str = Field(max_length=300)
    source: str = Field(max_length=200)        # e.g. "IWGDF 2023 Prevention Rec 4"
    source_year: int = Field(ge=1990, le=2100)
    strength: ClaimStrength


class GuideBrief(BaseModel):
    """Input to the writer — assembled by field-guide-writer R&D stage."""
    model_config = ConfigDict(extra="forbid")

    guide_id: str = Field(pattern=r"^FG-\d{3}$")
    title: str = Field(max_length=90)
    tags: list[ObservationTag] = Field(min_length=1)
    season: int = Field(ge=1, le=4)
    iwgdf_risk_context: str = Field(default="", max_length=400)
    provenance: list[ClaimSource] = Field(min_length=1)


class GuideSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    heading: str = Field(max_length=80)
    body: str = Field(max_length=2400)
    pull_quote: str = Field(default="", max_length=160)  # booklet/social hook


CANONICAL_HEADINGS = [
    "What you might be seeing",
    "What helps day to day",
    "What to bring up with your care team",
    "When sooner is better",
]


class BookletSection(BaseModel):
    """Long-form RENDER HINT — editorial structure for booklet/library pages.

    Not a content source: every booklet section must map back to one or more
    canonical sections (the clinical spine). The renderer reorganizes canonical
    bodies into editorial flow; it never introduces net-new clinical claims.
    Ordinal is DERIVED at render (list position), never stored here — so the
    "01 · 02 · 03" numbering can never lie.
    """
    model_config = ConfigDict(extra="forbid")
    title: str = Field(max_length=80)           # e.g. "THE CASE", "THE ROUTINE"
    maps_to: list[str] = Field(min_length=1)    # canonical heading(s) this draws from
    body: str = Field(max_length=2400)


class VideoBeat(BaseModel):
    """One beat of the short-form script — feeds the video renderer."""
    model_config = ConfigDict(extra="forbid")
    on_screen_text: str = Field(max_length=90)
    voiceover: str = Field(max_length=240)
    b_roll_hint: str = Field(max_length=120)   # e.g. "plantar close-up, soft light"


class GraphClaim(BaseModel):
    """A knowledge-graph edge: this guide asserts claim → backed by source."""
    model_config = ConfigDict(extra="forbid")
    subject_tag: ObservationTag
    predicate: str = Field(max_length=60)      # e.g. "is_helped_by", "worth_watching_when"
    object_text: str = Field(max_length=200)
    provenance_index: int                      # points into GuideDraft.provenance


class GuideDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = GUIDE_SCHEMA_VERSION
    draft_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: DraftState = DraftState.proposed

    # identity / routing
    guide_id: str = Field(pattern=r"^FG-\d{3}$")
    title: str = Field(max_length=90)
    tags: list[ObservationTag] = Field(min_length=1)
    season: int = Field(ge=1, le=4)

    # prose — the four canonical sections (field-guide-author template)
    sections: list[GuideSection] = Field(min_length=4, max_length=4)

    # downstream-render hooks (populated by the writer in one shot)
    bee_body: str = Field(max_length=1200)          # FTS5 retrieval text (routing terms)
    video_beats: list[VideoBeat] = Field(min_length=3, max_length=8)
    graph_claims: list[GraphClaim] = Field(default_factory=list)
    # optional long-form editorial structure for booklet/library renderers.
    # None => renderer falls back to the canonical four sections directly.
    booklet_layout: list[BookletSection] | None = Field(default=None)

    # evidence
    provenance: list[ClaimSource] = Field(min_length=1)

    # generation provenance
    writer_model_id: str
    prompt_sha256: str
    disclaimer: str = DISCLAIMER

    @field_validator("sections")
    @classmethod
    def canonical_headings(cls, v: list[GuideSection]) -> list[GuideSection]:
        got = [s.heading.strip() for s in v]
        if got != CANONICAL_HEADINGS:
            raise ValueError(f"sections must be exactly {CANONICAL_HEADINGS}, got {got}")
        return v

    @model_validator(mode="after")
    def booklet_layout_maps_to_canonical(self) -> "GuideDraft":
        """Every booklet section must map to real canonical headings — the
        render hint can reorganize but never escape the clinical spine."""
        if self.booklet_layout is None:
            return self
        valid = set(CANONICAL_HEADINGS)
        for i, bs in enumerate(self.booklet_layout):
            bad = [h for h in bs.maps_to if h not in valid]
            if bad:
                raise ValueError(
                    f"booklet_layout[{i}] maps_to unknown canonical heading(s): {bad}"
                )
        covered = {h for bs in self.booklet_layout for h in bs.maps_to}
        missing = valid - covered
        if missing:
            raise ValueError(
                f"booklet_layout must cover all canonical sections; missing: {sorted(missing)}"
            )
        return self

    def booklet_render(self) -> list[dict]:
        """Ordinals DERIVED here (never stored) — numbering cannot drift."""
        layout = self.booklet_layout or [
            BookletSection(title=s.heading, maps_to=[s.heading], body=s.body)
            for s in self.sections
        ]
        return [
            {"ordinal": f"{i+1:02d}", "title": bs.title, "body": bs.body,
             "maps_to": bs.maps_to}
            for i, bs in enumerate(layout)
        ]

    def full_text(self) -> str:
        parts = [self.title]
        for s in self.sections:
            parts += [s.heading, s.body]
        parts.append(self.disclaimer)
        return "\n\n".join(parts)

    def canonical_bytes(self) -> bytes:
        return self.model_dump_json(exclude={"disclaimer", "draft_id", "created_at"}).encode()

    def draft_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
