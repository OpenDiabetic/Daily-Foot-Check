#!/usr/bin/env python3
"""Generate FootLabKit/QCConstants.swift from shared/qc_constants.json.

Usage:  python3 tools/codegen_qc.py            # writes dist/ios/QCConstants.swift
CI:     regenerate and `git diff --exit-code`  # drift between JSON and Swift = fail
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "shared" / "qc_constants.json"
OUT = ROOT / "dist" / "ios" / "QCConstants.swift"

TEMPLATE = """// GENERATED FILE — do not edit.
// Source of truth: shared/qc_constants.json (version {version})
// Regenerate: python3 tools/codegen_qc.py
// Generated: {stamp}
//
// Parity rule: SentinelCapture's on-device gate MUST pass/fail identically to
// app/qc/gate.py on the golden image set. Same constants, same verdicts.

import Foundation

public enum QCConstants {{
    public static let version = "{version}"
    public static let minSidePx: Int = {min_side_px}
    public static let minSharpness: Double = {min_sharpness}
    public static let minBrightness: Double = {min_brightness}
    public static let maxBrightness: Double = {max_brightness}
    public static let maxImageBytes: Int = {max_image_bytes}
    public static let lumaDownscaleMaxSide: Int = {luma_downscale_max_side}
}}
"""


def main() -> None:
    c = json.loads(SRC.read_text())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        TEMPLATE.format(stamp=datetime.now(timezone.utc).isoformat(), **{
            k: v for k, v in c.items() if not k.startswith("_")
        })
    )
    print(f"wrote {OUT.relative_to(ROOT)} (source {c['version']})")


if __name__ == "__main__":
    main()
