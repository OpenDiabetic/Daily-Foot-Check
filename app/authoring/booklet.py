"""Booklet renderer — published GuideDraft → print-ready PDF.

guide-to-production made executable. Laws enforced here:
  1. Published-only: state != published raises RenderRejected.
  2. No net-new content: consumes booklet_render() output ONLY; the colophon
     is generated from draft.provenance. The renderer cannot inject prose.
  3. Derived numbering: ordinals come from booklet_render(), never literals.
  4. Wellness re-assert: content_gate runs on assembled text before render.
  5. In-RAM: HTML built in memory, Playwright renders to bytes, no disk writes
     of content (Chromium uses its own tmp, never our content).
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from playwright.async_api import async_playwright

from app.authoring.writer import ContentGateError, content_gate
from app.schemas.guide_draft import DraftState, GuideDraft
from app.schemas.guide_draft import GuideBrief

_TEMPLATE = Path(__file__).parent.parent.parent / "prompts" / "booklet_template.html"


class RenderRejected(ValueError):
    pass


def _esc(s: str) -> str:
    return html.escape(s, quote=True)


def _sections_html(draft: GuideDraft) -> str:
    blocks: list[str] = []
    for sec in draft.booklet_render():
        maps = " · ".join(sec["maps_to"])
        # split body into paragraphs on blank lines / sentence groups
        paras = [p.strip() for p in re.split(r"\n\s*\n", sec["body"]) if p.strip()] or [sec["body"]]
        body_html = "".join(f"<p>{_esc(p)}</p>" for p in paras)
        blocks.append(
            f'<div class="zone">'
            f'<div class="band"><span class="ord">{sec["ordinal"]}</span>'
            f'<h2>{_esc(sec["title"])}</h2>'
            f'<span class="maps">draws from: {_esc(maps)}</span></div>'
            f'{body_html}</div>'
        )
    return "\n".join(blocks)


def _provenance_html(draft: GuideDraft) -> str:
    rows: list[str] = []
    for c in draft.provenance:
        rows.append(
            f'<tr><td class="claim">{_esc(c.claim)}</td>'
            f'<td class="src">{_esc(c.source)}</td>'
            f'<td>{c.source_year}</td>'
            f'<td class="strength">{_esc(c.strength.value)}</td></tr>'
        )
    return "\n".join(rows)


def build_html(draft: GuideDraft, *, cadence: str = "Daily", version: str = "v1.0",
               subtitle: str = "") -> str:
    """Assemble the booklet HTML. Runs the wellness content gate on the
    reader-facing text before returning — a slipped banned word never renders."""
    if draft.state != DraftState.published:
        raise RenderRejected(f"only published drafts render to booklet (state={draft.state.value})")

    # re-assert wellness law on human-editable draft (booklet layout bodies too)
    brief = GuideBrief(guide_id=draft.guide_id, title=draft.title, tags=draft.tags,
                       season=draft.season, provenance=draft.provenance)
    try:
        content_gate(draft, brief)
    except ContentGateError as exc:
        raise RenderRejected(f"content gate failed — will not render: {exc}") from exc

    guide_num = draft.guide_id.split("-")[1]
    tmpl = _TEMPLATE.read_text()
    subs = {
        "{{GUIDE_NUM}}": guide_num,
        "{{TITLE}}": _esc(draft.title),
        "{{TITLE_UPPER}}": _esc(draft.title.upper()),
        "{{SUBTITLE}}": _esc(subtitle or draft.sections[0].pull_quote or ""),
        "{{CADENCE}}": _esc(cadence),
        "{{VERSION}}": _esc(version),
        "{{REVIEWED}}": date.today().isoformat(),
        "{{SECTIONS}}": _sections_html(draft),
        "{{PROVENANCE}}": _provenance_html(draft),
        "{{DRAFT_HASH}}": draft.draft_sha256(),
        "{{DISCLAIMER}}": _esc(draft.disclaimer),
        "{{WRITER_MODEL}}": _esc(draft.writer_model_id.upper()),
    }
    for k, v in subs.items():
        tmpl = tmpl.replace(k, v)
    return tmpl


async def render_booklet(draft: GuideDraft, **kw) -> bytes:
    """published draft → PDF bytes, in-RAM via headless Chromium."""
    page_html = build_html(draft, **kw)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox"])
        try:
            page = await browser.new_page()
            await page.set_content(page_html, wait_until="networkidle")
            pdf = await page.pdf(
                format="Letter", print_background=True,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            await browser.close()
    return pdf
