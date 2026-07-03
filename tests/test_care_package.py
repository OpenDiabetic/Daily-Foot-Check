"""Care package contract tests — tamper gate + render integrity, no GPU."""
import hashlib
import io

import pdfplumber
import pytest

from app.care.render import render_pdf
from app.schemas.care_package import (
    PDF_DISCLAIMER, CarePackageRequest, TamperError, verify_report,
)
from app.schemas.foot_check import (
    AttentionTier, CaptureView, FootCheckReport, Observation, ObservationTag,
    Prominence, QCResult, ViewQC,
)


def _report() -> FootCheckReport:
    qc = QCResult(passed=True, sharpness=120, brightness=130, width=1200, height=900)
    return FootCheckReport(
        model_id="google/medgemma-1.5-4b-it",
        prompt_sha256="a" * 64,
        views=[
            ViewQC(view=CaptureView.plantar_left, image_sha256="1" * 64, qc=qc),
            ViewQC(view=CaptureView.plantar_right, image_sha256="2" * 64, qc=qc),
        ],
        coverage_complete=False,
        observations=[
            Observation(tag=ObservationTag.callus, prominence=Prominence.moderate,
                        note="callus under ball of foot"),
        ],
        attention_tier=AttentionTier.yellow,
        tier_reason="Worth watching: callus.",
    )


def _request(report: FootCheckReport, **kw) -> CarePackageRequest:
    return CarePackageRequest(report=report,
                              report_sha256=report.report_sha256(), **kw)


class TestTamperGate:
    def test_clean_report_passes(self):
        verify_report(_request(_report()))

    def test_hash_roundtrips_through_json(self):
        """The gate depends on serialize→parse→serialize hash stability."""
        r = _report()
        req = _request(r)
        reparsed = CarePackageRequest.model_validate_json(req.model_dump_json())
        verify_report(reparsed)  # must not raise

    def test_doctored_tier_rejected(self):
        r = _report()
        original_hash = r.report_sha256()
        r.attention_tier = AttentionTier.green   # the doctoring
        req = CarePackageRequest(report=r, report_sha256=original_hash)
        with pytest.raises(TamperError):
            verify_report(req)

    def test_doctored_observation_rejected(self):
        r = _report()
        original_hash = r.report_sha256()
        r.observations[0].note = "totally fine, nothing to see"
        with pytest.raises(TamperError):
            verify_report(CarePackageRequest(report=r, report_sha256=original_hash))


class TestRender:
    def _text(self, pdf_bytes: bytes) -> str:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)

    def test_photoless_render_has_disclaimer_hash_and_tier(self):
        req = _request(_report(), recipient_note="Seeing you Tuesday — flagging this.")
        pdf = render_pdf(req)
        assert pdf.startswith(b"%PDF")
        text = self._text(pdf)
        assert "Patient-generated educational report" in text
        assert req.report_sha256 in text.replace("\n", "")
        assert "YELLOW" in text
        assert "callus" in text
        assert "Seeing you Tuesday" in text
        assert "transparency" in text

    def test_render_never_touches_disk(self, tmp_path, monkeypatch):
        import os
        before = set(os.listdir("/tmp"))
        render_pdf(_request(_report()))
        after = set(os.listdir("/tmp"))
        assert before == after

    def test_photo_embeds_when_hash_matches(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (600, 600), (140, 100, 70)).save(buf, format="JPEG")
        blob = buf.getvalue()
        h = hashlib.sha256(blob).hexdigest()
        r = _report()
        r.views[0].image_sha256 = h
        req = _request(r, include_photos=True)
        pdf = render_pdf(req, photos={h: blob})
        assert len(pdf) > 5000  # image payload present
        assert "plantar left" in self._text(pdf)
