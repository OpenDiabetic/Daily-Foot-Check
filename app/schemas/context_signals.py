"""ContextSignals — passive wearable data (Watch/iPhone SENSE role).

Doctrine:
- Parallel artifact to FootCheckReport. NEVER merged into it. VAULT joins by date.
- Sovereign-lane only: these never transit the cloud lane. Structurally enforced
  by the cloud API simply having no endpoint for them.
- extra='forbid' — unknown fields are a contract violation, not a warning.
- All signals Optional: a Watch-less user is a valid user.
- Wellness framing only. No field name or value may imply a symptom or condition.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

CONTEXT_SCHEMA_VERSION = "footcheck.ctx.v1"


class SignalWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: datetime
    end: datetime


class ContextSignals(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = CONTEXT_SCHEMA_VERSION
    signal_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    window: SignalWindow

    # Apple mobility metrics (HealthKit) — gait offloading shows up here early
    gait_asymmetry_pct: float | None = Field(default=None, ge=0, le=100)
    walking_speed_mps: float | None = Field(default=None, ge=0, le=5)
    walking_speed_delta_pct: float | None = Field(default=None, ge=-100, le=100)
    step_length_m: float | None = Field(default=None, ge=0, le=3)

    # wrist temperature nightly deviation (Series 8+), °C from personal baseline
    wrist_temp_deviation_c: float | None = Field(default=None, ge=-5, le=5)

    # activity context
    steps_7d_avg: int | None = Field(default=None, ge=0)
    stand_hours_7d_avg: float | None = Field(default=None, ge=0, le=24)

    # provenance
    source_device: str = "unknown"          # e.g. "watch-s10", "iphone-16"

    def canonical_bytes(self) -> bytes:
        return self.model_dump_json().encode()

    def signal_sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def nudge_worthy(sig: ContextSignals) -> tuple[bool, str]:
    """Deterministic NUDGE trigger. Wellness copy ONLY — the returned string is
    the exact user-facing line; no UI layer may rephrase it into symptom talk."""
    if sig.gait_asymmetry_pct is not None and sig.gait_asymmetry_pct >= 8.0:
        return True, "Your walking pattern shifted this week — a good day for a foot check."
    if sig.wrist_temp_deviation_c is not None and abs(sig.wrist_temp_deviation_c) >= 0.5:
        return True, "Your nightly baseline drifted a little — a good day for a foot check."
    if sig.walking_speed_delta_pct is not None and sig.walking_speed_delta_pct <= -12.0:
        return True, "You've been moving slower than usual — a good day for a foot check."
    return False, ""
