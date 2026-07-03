"""FootCheckReport contract — the single schema every component speaks.

Doctrine:
- MedGemma proposes OBSERVATIONS ONLY, locked to a closed vocabulary.
- The attention tier is derived SERVER-SIDE from observations (never trusted
  from the model).
- No diagnosis vocabulary exists anywhere in this file. Ever.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "footcheck.v2"

DISCLAIMER = (
    "Educational monitoring — not a medical device. This report never "
    "diagnoses. If anything here concerns you, show it to your care team."
)


class CaptureView(str, Enum):
    """The 4-photo protocol. Plantar views are where ulcers form —
    they are required for a complete check, never optional extras."""
    dorsal_left = "dorsal_left"
    dorsal_right = "dorsal_right"
    plantar_left = "plantar_left"
    plantar_right = "plantar_right"


REQUIRED_VIEWS = [
    CaptureView.dorsal_left, CaptureView.dorsal_right,
    CaptureView.plantar_left, CaptureView.plantar_right,
]

VIEW_LABELS = {
    CaptureView.dorsal_left: "top of the left foot",
    CaptureView.dorsal_right: "top of the right foot",
    CaptureView.plantar_left: "bottom (sole) of the left foot",
    CaptureView.plantar_right: "bottom (sole) of the right foot",
}


class ObservationTag(str, Enum):
    redness = "redness"
    swelling = "swelling"
    skin_break = "skin_break"
    discoloration = "discoloration"
    nail_change = "nail_change"
    callus = "callus"
    dryness_fissure = "dryness_fissure"
    deformity_note = "deformity_note"
    asymmetry = "asymmetry"
    none_noted = "none_noted"


class FootSide(str, Enum):
    left = "left"
    right = "right"
    unknown = "unknown"


class FootRegion(str, Enum):
    plantar = "plantar"
    dorsal = "dorsal"
    heel = "heel"
    arch = "arch"
    toes = "toes"
    ankle = "ankle"
    unknown = "unknown"


class Prominence(str, Enum):
    subtle = "subtle"
    moderate = "moderate"
    prominent = "prominent"


class AttentionTier(str, Enum):
    green = "green"    # nothing worth flagging today
    yellow = "yellow"  # worth watching / mention at next visit
    red = "red"        # worth showing your care team soon


class Observation(BaseModel):
    tag: ObservationTag
    side: FootSide = FootSide.unknown
    region: FootRegion = FootRegion.unknown
    prominence: Prominence = Prominence.subtle
    note: str = Field(default="", max_length=240)

    @field_validator("note")
    @classmethod
    def strip_note(cls, v: str) -> str:
        return v.strip()


class ModelFindings(BaseModel):
    """Exact shape MedGemma must return. Nothing else is accepted."""
    observations: list[Observation] = Field(min_length=1, max_length=12)


class QCResult(BaseModel):
    passed: bool
    sharpness: float          # variance-of-Laplacian proxy
    brightness: float         # 0..255 mean luma
    width: int
    height: int
    reasons: list[str] = Field(default_factory=list)


class ViewQC(BaseModel):
    view: CaptureView
    image_sha256: str
    qc: QCResult


class GuideRef(BaseModel):
    guide_id: str             # e.g. "FG-003"
    title: str
    reason: str               # which observation tag routed here


class FootCheckReport(BaseModel):
    schema_version: str = SCHEMA_VERSION
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    model_id: str
    prompt_sha256: str
    views: list[ViewQC]       # per-view QC + hash of each image we NEVER stored
    coverage_complete: bool   # all 4 views present (both plantar + both dorsal)
    observations: list[Observation]
    attention_tier: AttentionTier
    tier_reason: str
    guides: list[GuideRef] = Field(default_factory=list)
    disclaimer: str = DISCLAIMER

    def canonical_bytes(self) -> bytes:
        return self.model_dump_json(exclude={"disclaimer"}).encode()

    def report_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def derive_tier(observations: list[Observation]) -> tuple[AttentionTier, str]:
    """Deterministic tier logic. The model has zero say in this."""
    tags = {o.tag for o in observations}
    prominent = {
        o.tag for o in observations if o.prominence == Prominence.prominent
    }

    if ObservationTag.skin_break in tags:
        return AttentionTier.red, "A possible skin break was noted."
    if {ObservationTag.redness, ObservationTag.swelling} <= prominent:
        return AttentionTier.red, "Prominent redness and swelling were noted together."
    if ObservationTag.discoloration in prominent:
        return AttentionTier.red, "Prominent discoloration was noted."

    watch = tags & {
        ObservationTag.redness,
        ObservationTag.swelling,
        ObservationTag.discoloration,
        ObservationTag.nail_change,
        ObservationTag.dryness_fissure,
        ObservationTag.asymmetry,
    }
    if watch:
        pretty = ", ".join(sorted(t.value.replace("_", " ") for t in watch))
        return AttentionTier.yellow, f"Worth watching: {pretty}."

    return AttentionTier.green, "Nothing stood out in this check."
