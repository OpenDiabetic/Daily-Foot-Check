"""Stream B — content harvest. VAULT/sovereign lane ONLY.

The cloud API has no import path to this module. A HarvestPair is assembled
only when: (1) active donation consent exists, (2) the image is EXIF-stripped,
(3) the pair is RJP-scored. Revocation purges before the next training run.
"""
from __future__ import annotations

import hashlib
import io

from PIL import Image

from app.anchor.merkle import merkle_root
from app.harvest.schemas import (
    DonationConsent, DonationRejected, HarvestPair, HoneyCard, RJPTier,
    score_to_tier,
)


def strip_exif(image_bytes: bytes) -> bytes:
    """Re-encode without EXIF (kills GPS + device metadata). PHI firewall.
    Saving without the exif= param drops all EXIF; we also drop the info dict."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.info.pop("exif", None)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=92)
    return out.getvalue()


def assemble_pair(
    *,
    image_bytes: bytes | None,
    report_sha256: str,
    consent: DonationConsent,
    rjp_score: float,
    kind: str = "image_findings",
    tags: list[str] | None = None,
) -> tuple[HarvestPair, bytes | None]:
    """Consent-gated pair assembly. Returns (pair, clean_image_bytes|None).

    Raises DonationRejected if consent is inactive — no pair, no image kept.
    """
    if not consent.active:
        raise DonationRejected("donation consent is not active (missing or revoked)")

    clean_image: bytes | None = None
    image_hash: str | None = None
    if image_bytes is not None:
        clean_image = strip_exif(image_bytes)
        image_hash = hashlib.sha256(clean_image).hexdigest()

    pair = HarvestPair(
        kind=kind,
        image_sha256=image_hash,
        report_sha256=report_sha256,
        consent_sha256=consent.consent_sha256(),
        rjp_score=rjp_score,
        rjp_tier=score_to_tier(rjp_score),
        tags=tags or [],
    )
    return pair, clean_image


def build_honey_card(dataset_name: str, pairs: list[HarvestPair], notes: str = "") -> HoneyCard:
    """Audit BEFORE training (CreditSniper discipline): document tier
    distribution and quarantine non-trainable pairs in the card, not silently."""
    dist: dict[str, int] = {t.value: 0 for t in RJPTier}
    for p in pairs:
        dist[p.rjp_tier.value] += 1
    trainable = [p for p in pairs if p.trainable]
    root = merkle_root([p.report_sha256 for p in pairs]) if pairs else "0" * 64
    return HoneyCard(
        dataset_name=dataset_name,
        pair_count=len(pairs),
        trainable_count=len(trainable),
        tier_distribution=dist,
        merkle_root=root,
        notes=notes,
    )


def purge_revoked(pairs: list[HarvestPair], revoked_consent_hashes: set[str]) -> list[HarvestPair]:
    """Called before every training run. Any pair whose consent was revoked is
    dropped — donation is revocable and revocation is honored pre-train."""
    return [p for p in pairs if p.consent_sha256 not in revoked_consent_hashes]


def training_set(pairs: list[HarvestPair], revoked: set[str]) -> list[HarvestPair]:
    """The final gate: purge revoked, then keep only jelly+honey."""
    live = purge_revoked(pairs, revoked)
    return [p for p in live if p.trainable]
