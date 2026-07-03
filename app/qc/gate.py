"""Image quality gate. Rejects junk before a single GPU cycle is spent.

Pure PIL + numpy — no OpenCV dependency. Sharpness uses a
variance-of-Laplacian proxy computed with a 3x3 kernel convolution.
"""
from __future__ import annotations

import io

import numpy as np
from PIL import Image, UnidentifiedImageError

from app.config import get_settings
from app.schemas.foot_check import QCResult

_LAPLACIAN = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float64)


def _to_luma(img: Image.Image, max_side: int = 1024) -> np.ndarray:
    img = img.convert("L")
    if max(img.size) > max_side:
        scale = max_side / max(img.size)
        img = img.resize(
            (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
        )
    return np.asarray(img, dtype=np.float64)


def _laplacian_variance(luma: np.ndarray) -> float:
    # valid-mode 2D convolution via shifted sums (fast enough at 1024px)
    p = np.pad(luma, 1, mode="edge")
    lap = (
        p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:] - 4.0 * luma
    )
    return float(lap.var())


def run_qc(image_bytes: bytes) -> tuple[QCResult, Image.Image | None]:
    s = get_settings()
    reasons: list[str] = []

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()
    except (UnidentifiedImageError, OSError):
        return (
            QCResult(
                passed=False, sharpness=0.0, brightness=0.0,
                width=0, height=0,
                reasons=["File is not a readable image. Use JPEG, PNG, or HEIC-exported JPEG."],
            ),
            None,
        )

    w, h = img.size
    if min(w, h) < s.qc_min_side_px:
        reasons.append(
            f"Image is too small ({w}x{h}). Move closer or use a higher-resolution setting."
        )

    luma = _to_luma(img, max_side=s.qc_luma_downscale_max_side)
    brightness = float(luma.mean())
    sharpness = _laplacian_variance(luma)

    if brightness < s.qc_min_brightness:
        reasons.append("Photo is too dark. Add light or move near a window.")
    elif brightness > s.qc_max_brightness:
        reasons.append("Photo is washed out. Reduce direct light or flash.")

    if sharpness < s.qc_min_sharpness:
        reasons.append("Photo looks blurry. Hold steady and tap to focus on the foot.")

    return (
        QCResult(
            passed=not reasons,
            sharpness=round(sharpness, 2),
            brightness=round(brightness, 2),
            width=w,
            height=h,
            reasons=reasons,
        ),
        img,
    )
