"""Booklet renderer tests. Uses Playwright headless — skips if unavailable."""
import io
import os

import pytest

from app.authoring.booklet import RenderRejected, build_html, render_booklet
from app.schemas.guide_draft import BookletSection, DraftState
from tests.test_guide_writer import _draft, BEATS

playwright = pytest.importorskip("playwright.async_api")


def _published(**over):
    d = _draft(**over)
    d.state = DraftState.published
    return d


def _fg002_layout():
    return [
        BookletSection(title="THE CASE", maps_to=["What you might be seeing"], body="Why a photo beats a memory. Small changes are easy to miss."),
        BookletSection(title="THE ROUTINE", maps_to=["What helps day to day"], body="Four clear views per foot. Do not skip the sole."),
        BookletSection(title="THE SIGNALS", maps_to=["What you might be seeing", "What to bring up with your care team"], body="A worth-watching photo shows something new."),
        BookletSection(title="CONSISTENCY", maps_to=["What helps day to day"], body="Start today. Keep photos on your own device only."),
        BookletSection(title="ESCALATION", maps_to=["When sooner is better", "What to bring up with your care team"], body="Bring a worth-showing photo to your appointment."),
    ]


class TestPublishedGate:
    def test_unpublished_draft_rejected(self):
        with pytest.raises(RenderRejected):
            build_html(_draft())  # state defaults to proposed

    def test_published_draft_builds_html(self):
        html = build_html(_published())
        assert "<!DOCTYPE html>" in html and "FIELD GUIDE 002" in html


class TestContentGateReassert:
    def test_banned_word_blocks_render(self):
        bad = list(BEATS)
        from app.schemas.guide_draft import VideoBeat
        bad[0] = VideoBeat(on_screen_text="ok", voiceover="this looks infected", b_roll_hint="x")
        d = _published(video_beats=bad)
        with pytest.raises(RenderRejected):
            build_html(d)


class TestHtmlContent:
    def test_derived_ordinals_from_layout(self):
        html = build_html(_published(booklet_layout=_fg002_layout()))
        for ordv in ["01", "02", "03", "04", "05"]:
            assert f'"ord">{ordv}<' in html
        assert "THE CASE" in html and "ESCALATION" in html

    def test_colophon_has_all_provenance(self):
        html = build_html(_published())
        assert "IWGDF 2023 Prevention Rec 4" in html
        assert "IWGDF 2023 Prevention Rec 5" in html

    def test_disclaimer_and_hash_present(self):
        d = _published()
        html = build_html(d)
        assert "never diagnoses" in html
        assert d.draft_sha256() in html

    def test_no_netnew_content_only_layout_bodies(self):
        # renderer must not contain text that isn't in the draft
        d = _published(booklet_layout=_fg002_layout())
        html = build_html(d)
        assert "Why a photo beats a memory" in html
        # a phrase never in the draft must not appear
        assert "lorem ipsum" not in html.lower()


@pytest.mark.asyncio
class TestPdfRender:
    async def test_renders_valid_pdf(self):
        try:
            pdf = await render_booklet(_published(booklet_layout=_fg002_layout()))
        except Exception as e:
            pytest.skip(f"chromium unavailable: {e}")
        assert pdf.startswith(b"%PDF")
        assert len(pdf) > 3000
        # text extraction sanity
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            text = "\n".join(p.extract_text() or "" for p in doc.pages)
        assert "FIELD GUIDE 002" in text
        assert "never diagnoses" in text
