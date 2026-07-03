---
name: care-package
description: Use when working on the send-to-care-team feature — PDF rendering, tamper verification, share flows, /v1/care-package endpoint, or any feature that exports a report outside the app.
---

# Care Package — Server Renders, User Sends

We NEVER transmit PHI: no SMTP, no relay, no push. The server renders a PDF
in RAM and streams it back; the USER sends it via their device share sheet.
This keeps the platform out of transmitter posture and keeps zero-retention
literally true.

## Tamper gate (non-negotiable order of operations)
1. Client echoes report JSON + the X-Report-SHA256 it received.
2. Server re-parses, re-hashes, compares. Mismatch → 409, no render.
   (Depends on serialize→parse→serialize hash stability — test it.)
3. Photos opt-in AND sha256-matched to report views. Foreign image → 409.
   Nobody borrows the verification footer for a doctored document.

## PDF content law
- Header disclaimer verbatim: "Patient-generated educational report. Not a
  clinical record. This tool never diagnoses."
- Tier chip + tier_reason, observations table (closed vocab), session
  coverage line, optional patient note (≤280 chars).
- Footer on EVERY page: report sha256, prompt sha256, model_id, transparency
  verify pointer. The clinician-side superpower: verifiable-unaltered.

## Render law
reportlab canvas → BytesIO → bytes. Zero disk writes (test: /tmp listing
identical before/after). Multi-page safe. Photos only when hash-verified.
Stream with Content-Disposition attachment + X-Report-SHA256 header.
