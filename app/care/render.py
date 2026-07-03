"""Care package PDF render — reportlab canvas, entirely in RAM.

BytesIO in, bytes out. No temp files, no disk, ever. Styled to Hive Calm:
propolis header band, amber accents, tier chip, verify footer.
"""
from __future__ import annotations

import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

from app.config import get_settings
from app.schemas.care_package import PDF_DISCLAIMER, CarePackageRequest

PROPOLIS = HexColor("#201711")
WAX = HexColor("#F5EEDF")
HONEY = HexColor("#B5771D")
INK = HexColor("#2A2119")
INK_SOFT = HexColor("#5C5245")
TIER = {"green": HexColor("#4E7A64"), "yellow": HexColor("#C9922A"), "red": HexColor("#A84A32")}

W, H = letter
M = 0.8 * inch


def render_pdf(req: CarePackageRequest, photos: dict[str, bytes] | None = None) -> bytes:
    """photos: {image_sha256: jpeg_bytes} — already hash-verified by caller."""
    s = get_settings()
    r = req.report
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    c.setTitle("OpenDiabetic Foot Check — Care Package")

    # ---- header band ----
    c.setFillColor(PROPOLIS)
    c.rect(0, H - 1.25 * inch, W, 1.25 * inch, fill=1, stroke=0)
    c.setFillColor(WAX)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(M, H - 0.62 * inch, "Foot Check — Care Package")
    c.setFillColor(HexColor("#E9A63C"))
    c.setFont("Helvetica", 9)
    c.drawString(M, H - 0.85 * inch, PDF_DISCLAIMER)
    c.setFillColor(HexColor("#B8A98E"))
    c.drawRightString(W - M, H - 0.62 * inch, f"Checked: {r.created_at:%Y-%m-%d %H:%M UTC}")
    c.drawRightString(W - M, H - 0.85 * inch, f"Request: {r.request_id[:12]}")

    y = H - 1.7 * inch

    # ---- tier chip ----
    tier_col = TIER[r.attention_tier.value]
    c.setFillColor(tier_col)
    c.roundRect(M, y - 0.12 * inch, 1.5 * inch, 0.34 * inch, 6, fill=1, stroke=0)
    c.setFillColor(WAX)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(M + 0.75 * inch, y - 0.02 * inch, r.attention_tier.value.upper())
    c.setFillColor(INK)
    c.setFont("Helvetica", 11)
    c.drawString(M + 1.7 * inch, y - 0.02 * inch, r.tier_reason)
    y -= 0.55 * inch

    # ---- session coverage ----
    c.setFillColor(INK_SOFT)
    c.setFont("Helvetica", 9)
    views = ", ".join(v.view.value.replace("_", " ") for v in r.views)
    cov = "complete (4/4 views)" if r.coverage_complete else f"partial ({len(r.views)}/4 views)"
    c.drawString(M, y, f"Session: {cov} — {views}")
    y -= 0.35 * inch

    # ---- observations table ----
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(M, y, "Observations (visual only — closed vocabulary)")
    y -= 0.28 * inch
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HONEY)
    for x, head in [(M, "What"), (M + 1.6 * inch, "Side"), (M + 2.5 * inch, "Region"),
                    (M + 3.5 * inch, "Prominence"), (M + 4.6 * inch, "Note")]:
        c.drawString(x, y, head)
    y -= 0.06 * inch
    c.setStrokeColor(HONEY)
    c.line(M, y, W - M, y)
    y -= 0.2 * inch
    c.setFont("Helvetica", 9)
    c.setFillColor(INK)
    for o in r.observations:
        c.drawString(M, y, o.tag.value.replace("_", " "))
        c.drawString(M + 1.6 * inch, y, o.side.value)
        c.drawString(M + 2.5 * inch, y, o.region.value)
        c.drawString(M + 3.5 * inch, y, o.prominence.value)
        note = o.note if len(o.note) <= 42 else o.note[:39] + "..."
        c.drawString(M + 4.6 * inch, y, note)
        y -= 0.22 * inch
        if y < 2.2 * inch:
            _footer(c, r, s)
            c.showPage()
            y = H - M

    # ---- recipient note ----
    if req.recipient_note:
        y -= 0.15 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(M, y, "Note from the patient:")
        y -= 0.2 * inch
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(INK_SOFT)
        c.drawString(M, y, req.recipient_note[:110])
        y -= 0.35 * inch

    # ---- photos (opt-in, hash-verified) ----
    if req.include_photos and photos:
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(M, y, "Photos (as analyzed — quality-gated)")
        y -= 0.15 * inch
        x = M
        img_w, img_h = 2.25 * inch, 2.25 * inch
        for vq in r.views:
            blob = photos.get(vq.image_sha256)
            if blob is None:
                continue
            if x + img_w > W - M:
                x = M
                y -= img_h + 0.45 * inch
            if y - img_h < 1.6 * inch:
                _footer(c, r, s)
                c.showPage()
                y = H - M - 0.2 * inch
                x = M
            from reportlab.lib.utils import ImageReader
            c.drawImage(ImageReader(io.BytesIO(blob)), x, y - img_h,
                        width=img_w, height=img_h, preserveAspectRatio=True, anchor="nw")
            c.setFont("Helvetica", 8)
            c.setFillColor(INK_SOFT)
            c.drawString(x, y - img_h - 0.16 * inch, vq.view.value.replace("_", " "))
            x += img_w + 0.3 * inch

    _footer(c, r, s)
    c.showPage()
    c.save()
    return buf.getvalue()


def _footer(c: rl_canvas.Canvas, r, s) -> None:
    c.setFillColor(PROPOLIS)
    c.rect(0, 0, W, 1.1 * inch, fill=1, stroke=0)
    c.setFillColor(HexColor("#E9A63C"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(M, 0.82 * inch, "Verify this report has not been altered:")
    c.setFillColor(HexColor("#E8DCC4"))
    c.setFont("Courier", 7)
    c.drawString(M, 0.64 * inch, f"report sha256  {r.report_sha256()}")
    c.drawString(M, 0.50 * inch, f"prompt sha256  {r.prompt_sha256}")
    c.drawString(M, 0.36 * inch, f"model          {r.model_id}")
    c.setFillColor(HexColor("#B8A98E"))
    c.setFont("Helvetica", 7)
    c.drawString(M, 0.18 * inch,
                 "Daily-batch anchored to Hedera HCS + RFC 3161 countersigned — "
                 "verify at opendiabetic.com/transparency")
