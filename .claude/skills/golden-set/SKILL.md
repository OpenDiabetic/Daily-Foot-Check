---
name: golden-set
description: Use when changing ANY prompt, model checkpoint, QC threshold, or observation schema in the foot check pipeline, and when building or extending the adversarial evaluation set or regression harness.
---

# Golden Set & Prompt Regression

No prompt/model/threshold change ships without this harness passing. Ever.

## Set composition (target ≥50, grow forever)
- QC-hard: blur, dark, washed-out, tiny, extreme aspect
- Not-a-foot: shoe, sock, hand, cat, floor, prosthetic
- Framing: partial foot, two feet in frame, wrong view label
- Content: each ObservationTag represented ≥3x across plantar+dorsal,
  including subtle cases; healthy feet across skin tones (bias check —
  REQUIRED: tier distribution must be stable across skin-tone strata)
- Each item: manifest entry {file, view, expected_qc, expected_tags_superset,
  expected_tier}

## Harness rules
- CPU tier (CI, every commit): QC gate assertions only.
- LIVE tier (FOOTCHECK_LIVE=1, canary :8092): full inference; tier agreement,
  zero off-vocab, plantar skin_break recall pinned (no regressions allowed).
- Prompt changes: run old vs new side-by-side, diff per-item; any tier
  downgrade on a skin_break item = automatic fail.
- Results logged with prompt_sha256 + model_id; keep history — trends matter.
