"""Harvest schemas — the training-data flywheel.

Two streams, strictly separated:
  A. AggregateSignal  — cloud-legal, always on. Hashes/tiers/QC only, no content.
  B. HarvestPair      — VAULT-only, opt-in donation. (image, report) pairs,
                        RJP-tiered, consent-gated, Merkle-anchored.

PHI firewall: a HarvestPair links to its consent by HASH only. No user id,
no email. EXIF is stripped before a donated image is ever accepted.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

HARVEST_SCHEMA_VERSION = "harvest.v1"


# ---- Royal Jelly tiering -------------------------------------------------
class RJPTier(str, Enum):
    jelly = "jelly"        # 9.0–10.0 — train
    honey = "honey"        # 7.0–8.9  — train
    pollen = "pollen"      # 4.0–6.9  — quarantine
    propolis = "propolis"  # <4.0     — quarantine


TRAINABLE = {RJPTier.jelly, RJPTier.honey}


def score_to_tier(score: float) -> RJPTier:
    if score >= 9.0:
        return RJPTier.jelly
    if score >= 7.0:
        return RJPTier.honey
    if score >= 4.0:
        return RJPTier.pollen
    return RJPTier.propolis


# ---- Stream B: consent + content pairs -----------------------------------
class DonationConsent(BaseModel):
    """Explicit, revocable, on-device consent. The record is itself anchored
    so 'user said yes on date X' is provable; revocation purges before the
    next training run."""
    model_config = ConfigDict(extra="forbid")

    consent_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scope: str = "footcheck-image-donation"
    revoked: bool = False
    revoked_at: datetime | None = None
    # device-local subject ref: a per-device random salt hash — NEVER a user id
    subject_ref: str = Field(min_length=16, max_length=64)

    def consent_sha256(self) -> str:
        payload = f"{self.consent_id}|{self.scope}|{self.subject_ref}|{self.granted_at.isoformat()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    @property
    def active(self) -> bool:
        return not self.revoked


class DonationRejected(ValueError):
    pass


class HarvestPair(BaseModel):
    """One training example. Linked to consent by hash only."""
    model_config = ConfigDict(extra="forbid")

    pair_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    kind: str = Field(pattern=r"^(image_findings|guide_draft|multitimepoint)$")

    image_sha256: str | None = None       # for image_findings/multitimepoint
    report_sha256: str                    # the paired report/draft hash
    consent_sha256: str                   # PHI firewall: link to consent by hash

    rjp_score: float = Field(ge=0.0, le=10.0)
    rjp_tier: RJPTier
    tags: list[str] = Field(default_factory=list)  # e.g. ["has_anomaly","plantar","skin_break"]

    @property
    def trainable(self) -> bool:
        return self.rjp_tier in TRAINABLE


class HoneyCard(BaseModel):
    """Dataset provenance doc — accompanies every training shard set."""
    model_config = ConfigDict(extra="forbid")

    card_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = HARVEST_SCHEMA_VERSION
    dataset_name: str
    pair_count: int = Field(ge=0)
    trainable_count: int = Field(ge=0)
    tier_distribution: dict[str, int] = Field(default_factory=dict)
    consent_basis: str = "explicit opt-in donation (revocable, on-device)"
    merkle_root: str
    hcs_anchor: str | None = None         # tx id once anchored
    notes: str = ""


# ---- Stream A: cloud-legal aggregate signal ------------------------------
class AggregateSignal(BaseModel):
    """No content. Ever. Counts, tiers, QC stats — the 'what to train' signal
    that needs no consent because it holds nothing personal."""
    model_config = ConfigDict(extra="forbid")

    window_start: datetime
    window_end: datetime
    checks_total: int = Field(ge=0)
    qc_bounce_rate: float = Field(ge=0.0, le=1.0)
    tier_counts: dict[str, int] = Field(default_factory=dict)     # green/yellow/red
    view_coverage_rate: float = Field(ge=0.0, le=1.0)             # 4/4 sessions share
    reviewer_reject_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    # capture-difficulty signal: which QC reasons fire most (drives golden-set)
    qc_reason_counts: dict[str, int] = Field(default_factory=dict)
