"""Contract tests — no GPU required. Run in CI on every commit."""
import pytest
from pydantic import ValidationError

from app.anchor.merkle import merkle_proof, merkle_root
from app.audit.log import audit
from app.schemas.foot_check import (
    AttentionTier, ModelFindings, Observation, ObservationTag, Prominence,
    derive_tier,
)


def obs(tag, prom=Prominence.subtle):
    return Observation(tag=tag, prominence=prom)


class TestTierIsDeterministicAndServerOwned:
    def test_skin_break_is_always_red(self):
        tier, _ = derive_tier([obs(ObservationTag.skin_break)])
        assert tier == AttentionTier.red

    def test_prominent_redness_plus_swelling_is_red(self):
        tier, _ = derive_tier([
            obs(ObservationTag.redness, Prominence.prominent),
            obs(ObservationTag.swelling, Prominence.prominent),
        ])
        assert tier == AttentionTier.red

    def test_subtle_redness_is_yellow(self):
        tier, _ = derive_tier([obs(ObservationTag.redness)])
        assert tier == AttentionTier.yellow

    def test_callus_alone_is_green(self):
        tier, _ = derive_tier([obs(ObservationTag.callus)])
        assert tier == AttentionTier.green

    def test_none_noted_is_green(self):
        tier, _ = derive_tier([obs(ObservationTag.none_noted)])
        assert tier == AttentionTier.green


class TestClosedVocabulary:
    def test_off_vocab_tag_rejected(self):
        with pytest.raises(ValidationError):
            ModelFindings.model_validate(
                {"observations": [{"tag": "cellulitis"}]}  # diagnosis vocab -> die
            )

    def test_empty_observations_rejected(self):
        with pytest.raises(ValidationError):
            ModelFindings.model_validate({"observations": []})

    def test_note_length_capped(self):
        with pytest.raises(ValidationError):
            Observation(tag=ObservationTag.redness, note="x" * 500)


class TestMerkle:
    def test_single_leaf_root_is_leaf(self):
        leaf = "aa" * 32
        assert merkle_root([leaf]) == leaf

    def test_proof_roundtrip(self):
        import hashlib
        leaves = [hashlib.sha256(bytes([i])).hexdigest() for i in range(5)]
        root = merkle_root(leaves)
        path = merkle_proof(leaves, 2)
        node = bytes.fromhex(leaves[2])
        for side, sib in path:
            sib_b = bytes.fromhex(sib)
            node = (
                hashlib.sha256(node + sib_b).digest()
                if side == "right"
                else hashlib.sha256(sib_b + node).digest()
            )
        assert node.hex() == root


class TestAuditAllowlist:
    def test_pii_fields_rejected(self):
        with pytest.raises(ValueError):
            audit(email="leak@example.com")

    def test_image_bytes_rejected(self):
        with pytest.raises(ValueError):
            audit(image_body=b"...")
