---
name: vault-longitudinal
description: Use when working on encrypted history, baselines, trends, day-over-day comparison, the ComparisonEngine, multi-timepoint MedGemma calls, or wearable ContextSignals storage. Sovereign-lane only features.
---

# VAULT & Longitudinal (the moat)

History is structurally sovereign-exclusive: the cloud lane is amnesiac by
design, so trends exist ONLY on edge devices. Never add a cloud endpoint for
ContextSignals or stored images — that's the moat AND the compliance line.

## Storage law
- SQLite + Fernet per-record encryption; key = device keyfile 0600, generated
  first boot. Lose key = lose history, by design — say so in UI up front.
- Plaintext columns: day, kind, sha256 only (already-public hashes + dates).
- Image retention is OPT-IN, local-only, revocable, and never synced.

## Comparison feed
`comparison_feed(day, lookback=5)` → newest-first day bundles
(report+signals). This is the input for MedGemma 1.5 multi-timepoint calls
(native capability: longitudinal image analysis). Multi-timepoint calls are
still SINGLE-SHOT: one request containing prior+current images + pinned
comparison prompt (separate pinned file, own hash, own golden set).

## Trend framing (wellness-language applies doubly)
Deltas are described as changes, never trajectories toward conditions:
"the red area near the left big toe looks larger than Tuesday" ✓
"worsening" alone ✗ (attach to observation, not the person). Tier from
comparison uses the same derive_tier — a NEW skin_break vs baseline is red.

## SENSE joins
ContextSignals stored beside reports, joined by day. Nudges computed
on-device from nudge_worthy() — copy strings are law, UI renders verbatim.
