// GENERATED FILE — do not edit.
// Source of truth: shared/qc_constants.json (version qc.v1)
// Regenerate: python3 tools/codegen_qc.py
//
// Parity rule: SentinelCapture's on-device gate MUST pass/fail identically to
// app/qc/gate.py on the golden image set. Same constants, same verdicts.

import Foundation

public enum QCConstants {
    public static let version = "qc.v1"
    public static let minSidePx: Int = 512
    public static let minSharpness: Double = 40.0
    public static let minBrightness: Double = 40.0
    public static let maxBrightness: Double = 235.0
    public static let maxImageBytes: Int = 12582912
    public static let lumaDownscaleMaxSide: Int = 1024
}
