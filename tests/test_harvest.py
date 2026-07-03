"""Harvest tests — consent, PHI firewall, RJP quarantine, revocation. No GPU."""
import io
from datetime import datetime, timedelta, timezone

import pytest
from PIL import Image

from app.harvest.collector import (
    assemble_pair, build_honey_card, strip_exif, training_set,
)
from app.harvest.schemas import (
    AggregateSignal, DonationConsent, DonationRejected, RJPTier, score_to_tier,
)
from app.harvest.signal import aggregate


def _consent(revoked=False) -> DonationConsent:
    c = DonationConsent(subject_ref="a" * 32)
    if revoked:
        c.revoked = True
        c.revoked_at = datetime.now(timezone.utc)
    return c


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (400, 400), (120, 90, 70)).save(buf, format="JPEG")
    return buf.getvalue()


class TestConsentGate:
    def test_active_consent_assembles_pair(self):
        pair, img = assemble_pair(image_bytes=_jpeg(), report_sha256="r" * 64,
                                  consent=_consent(), rjp_score=8.5)
        assert pair.trainable and img is not None
        assert pair.consent_sha256 and pair.image_sha256

    def test_revoked_consent_rejected(self):
        with pytest.raises(DonationRejected):
            assemble_pair(image_bytes=_jpeg(), report_sha256="r" * 64,
                          consent=_consent(revoked=True), rjp_score=9.0)


class TestPHIFirewall:
    def test_pair_holds_no_user_id(self):
        pair, _ = assemble_pair(image_bytes=_jpeg(), report_sha256="r" * 64,
                                consent=_consent(), rjp_score=9.0)
        blob = pair.model_dump_json()
        # only hashes link things — no subject_ref, no email
        assert "subject_ref" not in blob and "@" not in blob

    def test_exif_stripped(self):
        # build a jpeg WITH exif, confirm output has none
        img = Image.new("RGB", (300, 300), (10, 20, 30))
        buf = io.BytesIO()
        exif = img.getexif()
        exif[271] = "SecretCameraMake"  # Make tag
        img.save(buf, format="JPEG", exif=exif)
        cleaned = strip_exif(buf.getvalue())
        assert b"SecretCameraMake" not in cleaned
        assert Image.open(io.BytesIO(cleaned)).getexif().get(271) is None


class TestRJPQuarantine:
    def test_tier_boundaries(self):
        assert score_to_tier(9.5) == RJPTier.jelly
        assert score_to_tier(8.0) == RJPTier.honey
        assert score_to_tier(5.0) == RJPTier.pollen
        assert score_to_tier(2.0) == RJPTier.propolis

    def test_only_jelly_honey_train(self):
        pairs = [
            assemble_pair(image_bytes=None, report_sha256=f"{i}" * 64,
                          consent=_consent(), rjp_score=s)[0]
            for i, s in enumerate([9.5, 8.0, 5.0, 2.0])
        ]
        keep = training_set(pairs, revoked=set())
        assert len(keep) == 2
        assert all(p.trainable for p in keep)

    def test_honey_card_audits_distribution(self):
        pairs = [
            assemble_pair(image_bytes=None, report_sha256=f"{i}" * 64,
                          consent=_consent(), rjp_score=s)[0]
            for i, s in enumerate([9.5, 8.0, 5.0])
        ]
        card = build_honey_card("foot-lora-v1", pairs)
        assert card.pair_count == 3 and card.trainable_count == 2
        assert card.tier_distribution["jelly"] == 1
        assert card.tier_distribution["pollen"] == 1
        assert len(card.merkle_root) == 64


class TestRevocationPurge:
    def test_revoked_pair_purged_before_training(self):
        c1, c2 = _consent(), _consent()
        p1, _ = assemble_pair(image_bytes=None, report_sha256="1" * 64,
                              consent=c1, rjp_score=9.0)
        p2, _ = assemble_pair(image_bytes=None, report_sha256="2" * 64,
                              consent=c2, rjp_score=9.0)
        # c2 later revokes → its pair must drop even though tier is jelly
        keep = training_set([p1, p2], revoked={c2.consent_sha256()})
        assert len(keep) == 1 and keep[0].report_sha256 == "1" * 64


class TestStreamASignalIsContentFree:
    def test_aggregate_holds_no_content(self):
        now = datetime.now(timezone.utc)
        records = [
            {"outcome": "ok", "attention_tier": "green", "coverage_complete": True},
            {"outcome": "ok", "attention_tier": "red", "coverage_complete": True},
            {"outcome": "qc_rejected", "qc_reasons": ["Photo looks blurry."]},
        ]
        sig = aggregate(records, now - timedelta(days=1), now)
        assert sig.checks_total == 3
        assert round(sig.qc_bounce_rate, 2) == 0.33
        assert sig.tier_counts == {"green": 1, "red": 1}
        assert sig.view_coverage_rate == 1.0
        assert sig.qc_reason_counts["Photo looks blurry."] == 1
        # the signal object is serializable and contains no image/report bodies
        blob = sig.model_dump_json()
        assert "image" not in blob and "sha256" not in blob
