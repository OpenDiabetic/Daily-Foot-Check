---
name: sentinel-capture
description: Use when working on photo capture — the iOS Foot Lab app camera flow, web capture, QC gating on any client, view labeling, image format handling (HEIC/JPEG), or the multipart shapes for /v1/check. The SENTINEL protocol skill.
---

# SENTINEL Capture — 4-View Protocol

A check = 4 photos: dorsal_left, dorsal_right, plantar_left, plantar_right.
**Plantar views matter most — ulcers form on the sole.** Partial sessions
allowed (coverage_complete=false) but UI always guides toward 4/4.

## Client QC parity law
On-device gate MUST pass/fail identically to the server gate. Constants come
ONLY from generated QCConstants (source: shared/qc_constants.json). Golden
image set must produce identical verdicts on Swift and Python. If a photo
passes on-phone, it can never bounce at the node.

## Capture UX rules
- Guide plantar shots explicitly (mirror-on-floor or partner-assist prompts;
  many users cannot see their own soles — this is the accessibility core).
- Consistent framing across days: overlay ghost of last baseline (VAULT lane)
  for comparability; MedGemma multi-timepoint rewards consistent angles.
- Retake flow is per-view: server 422 returns per-view reasons — surface the
  exact human-readable reason, retake ONLY the failed views.

## Format law
iOS exports JPEG at capture (never send raw HEIC — server QC uses Pillow
without HEIC decode by design; keeps zero-retention path dependency-minimal).
Max 12MB/image (shared constant). EXIF: strip GPS before upload — location
never leaves the device.

## Multipart shape (/v1/check)
files: images[] (1–4, jpeg) + form: views="dorsal_left,plantar_left,..."
(one label per image, no dups). Response headers carry X-Report-SHA256 —
persist it client-side; it's the user's receipt and the care-package key.
