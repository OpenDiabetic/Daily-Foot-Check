"""footcheck-node API.

One job: image in -> FootCheckReport out -> nothing retained.

The image lives as `bytes` in this process for the duration of the request
and is never written to any filesystem, cache, or log. The container runs
read-only with tmpfs /tmp as belt-and-suspenders.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.anchor.daily import AnchorBatcher
from app.audit.log import audit
from app.bee.retrieve import Bee
from app.config import get_settings
from app.inference.medgemma import InferenceError, analyze
from app.care.render import render_pdf
from app.qc.gate import run_qc
from app.schemas.care_package import CarePackageRequest, TamperError, verify_report
from app.schemas.foot_check import (
    REQUIRED_VIEWS, VIEW_LABELS, CaptureView, FootCheckReport, FootRegion,
    FootSide, Observation, ObservationTag, ViewQC, derive_tier,
)
import hashlib

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("footcheck")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    app.state.bee = Bee()
    app.state.http = httpx.AsyncClient()
    app.state.batcher = AnchorBatcher()
    app.state.batcher.start()
    log.info(
        "footcheck-node up model=%s prompt_sha256=%s anchor=%s",
        s.model_id, s.prompt_sha256[:16], s.anchor_enabled,
    )
    yield
    await app.state.batcher.stop()
    await app.state.http.aclose()


app = FastAPI(
    title="OpenDiabetic Foot Check API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://opendiabetic.com", "https://www.opendiabetic.com"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}


@app.get("/transparency")
async def transparency() -> dict:
    s = get_settings()
    return {
        "design": [
            "Your image is processed entirely in memory and never written to disk.",
            "Containers run read-only; there is nowhere to write it.",
            "Logs contain hashes only — never image bytes, report bodies, or emails.",
            "Daily Merkle roots of report hashes are anchored to Hedera HCS and "
            "countersigned by an RFC 3161 timestamp authority.",
        ],
        "model_id": s.model_id,
        "prompt_sha256": s.prompt_sha256,
        "hedera_topic_id": s.hedera_topic_id or "pending",
        "hedera_mirror": (
            f"https://mainnet.mirrornode.hedera.com/api/v1/topics/"
            f"{s.hedera_topic_id or '{topic}'}/messages"
        ),
        "tsa": s.tsa_url,
        "disclaimer": "Educational monitoring — not a medical device. It never diagnoses.",
    }


@app.post("/v1/booklet")
async def booklet(package: str = Form(...)) -> Response:
    """Render a PUBLISHED GuideDraft to a print-ready booklet PDF, in RAM.
    Enforces published-only + wellness content gate before rendering."""
    from app.authoring.booklet import RenderRejected, render_booklet
    from app.schemas.guide_draft import GuideDraft

    try:
        draft = GuideDraft.model_validate_json(package)
    except Exception as exc:
        raise HTTPException(400, f"Invalid guide draft: {exc}") from exc

    try:
        pdf_bytes = await render_booklet(draft)
    except RenderRejected as exc:
        raise HTTPException(409, str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{draft.guide_id}-booklet.pdf"',
            "X-Draft-SHA256": draft.draft_sha256(),
        },
    )


@app.post("/v1/care-package")
async def care_package(
    request: Request,
    package: str = Form(...),          # CarePackageRequest JSON
    images: list[UploadFile] | None = File(default=None),
) -> Response:
    """Render the send-to-care-team PDF, entirely in RAM, streamed back.
    The SERVER renders; only the USER sends (device share sheet). Photos are
    accepted only if their sha256 matches a view in the verified report."""
    s = get_settings()
    t0 = time.monotonic()

    try:
        req = CarePackageRequest.model_validate_json(package)
        verify_report(req)
    except TamperError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, f"Invalid care package request: {exc}") from exc

    photos: dict[str, bytes] = {}
    if req.include_photos and images:
        valid_hashes = {v.image_sha256 for v in req.report.views}
        for img in images:
            b = await img.read()
            if len(b) > s.max_image_bytes:
                raise HTTPException(413, "An image exceeds 12 MB.")
            h = hashlib.sha256(b).hexdigest()
            if h not in valid_hashes:
                raise HTTPException(
                    409, "A supplied photo does not match any view in this "
                         "report and cannot be included in a verified package."
                )
            photos[h] = b

    pdf_bytes = render_pdf(req, photos)

    audit(
        request_id=req.report.request_id,
        report_sha256=req.report_sha256,
        prompt_sha256=req.report.prompt_sha256,
        model_id=req.report.model_id,
        attention_tier=req.report.attention_tier.value,
        outcome="care_package_ok",
        latency_ms=int((time.monotonic() - t0) * 1000),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="foot-check-care-package.pdf"',
            "X-Report-SHA256": req.report_sha256,
        },
    )


@app.post("/v1/check")
async def check(
    request: Request,
    images: list[UploadFile] = File(...),
    views: str = Form(...),   # comma list, e.g. "dorsal_left,dorsal_right,plantar_left,plantar_right"
) -> JSONResponse:
    """The 4-photo protocol: top + bottom of each foot, one request, all in
    RAM. Plantar views (where ulcers form) are required for a complete check;
    partial sessions are accepted but flagged `coverage_complete: false`."""
    s = get_settings()
    t0 = time.monotonic()
    import asyncio

    try:
        view_list = [CaptureView(v.strip()) for v in views.split(",") if v.strip()]
    except ValueError as exc:
        raise HTTPException(400, f"Unknown view label: {exc}") from exc
    if not view_list or len(view_list) != len(images):
        raise HTTPException(400, "Provide one view label per image (1-4 of: "
                                 + ", ".join(v.value for v in REQUIRED_VIEWS))
    if len(set(view_list)) != len(view_list):
        raise HTTPException(400, "Duplicate view labels in one session.")

    # read everything into RAM up front
    blobs: list[bytes] = []
    for img in images:
        b = await img.read()
        if len(b) > s.max_image_bytes:
            raise HTTPException(413, "An image exceeds 12 MB. Use standard photos.")
        if not b:
            raise HTTPException(400, "Empty image in session.")
        blobs.append(b)

    # 1. QC every view — reject the whole session with per-view retake reasons
    view_qcs: list[ViewQC] = []
    failed: dict[str, list[str]] = {}
    for view, b in zip(view_list, blobs):
        qc, _ = run_qc(b)
        view_qcs.append(ViewQC(view=view, image_sha256=hashlib.sha256(b).hexdigest(), qc=qc))
        if not qc.passed:
            failed[view.value] = qc.reasons
    if failed:
        for vq in view_qcs:
            audit(image_sha256=vq.image_sha256, qc_passed=vq.qc.passed,
                  outcome="qc_rejected" if not vq.qc.passed else "qc_ok_in_failed_session",
                  latency_ms=int((time.monotonic() - t0) * 1000))
        return JSONResponse(status_code=422, content={
            "detail": "Some photos need a retake.",
            "retake": failed,
            "views": [vq.model_dump(mode="json") for vq in view_qcs],
        })

    # 2. MedGemma — one single-shot call per view, concurrently
    try:
        findings_list = await asyncio.gather(*[
            analyze(b, request.app.state.http, VIEW_LABELS[v])
            for v, b in zip(view_list, blobs)
        ])
    except InferenceError as exc:
        for vq in view_qcs:
            audit(image_sha256=vq.image_sha256, qc_passed=True,
                  outcome="inference_failed",
                  latency_ms=int((time.monotonic() - t0) * 1000))
        raise HTTPException(502, f"Analysis unavailable: {exc}") from exc

    # 3. Merge observations; backfill side/region from the view label when the
    #    model returned unknown — the user's label is ground truth for framing
    observations: list[Observation] = []
    for view, findings in zip(view_list, findings_list):
        side = FootSide.left if "left" in view.value else FootSide.right
        default_region = FootRegion.plantar if "plantar" in view.value else FootRegion.dorsal
        for obs in findings.observations:
            if obs.side == FootSide.unknown:
                obs.side = side
            if obs.region == FootRegion.unknown:
                obs.region = default_region
            observations.append(obs)
    # collapse to a single none_noted if that's all there is
    real = [o for o in observations if o.tag != ObservationTag.none_noted]
    observations = real or [observations[0]]

    # 4. Tier — deterministic, server-side
    tier, tier_reason = derive_tier(observations)

    # 5. Bee — route to Field Guides
    guides = request.app.state.bee.guides_for(observations)

    report = FootCheckReport(
        model_id=s.model_id,
        prompt_sha256=s.prompt_sha256,
        views=view_qcs,
        coverage_complete=set(view_list) == set(REQUIRED_VIEWS),
        observations=observations,
        attention_tier=tier,
        tier_reason=tier_reason,
        guides=guides,
    )
    report_hash = report.report_sha256()

    await request.app.state.batcher.add(report_hash)
    for vq in view_qcs:
        audit(request_id=report.request_id, image_sha256=vq.image_sha256,
              report_sha256=report_hash, prompt_sha256=s.prompt_sha256,
              model_id=s.model_id, attention_tier=tier.value, qc_passed=True,
              outcome="ok", latency_ms=int((time.monotonic() - t0) * 1000))

    return JSONResponse(
        content=report.model_dump(mode="json"),
        headers={"X-Report-SHA256": report_hash},
    )
