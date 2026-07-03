---
name: footcheck-pipeline
description: Use when writing, reviewing, or extending ANY code in footcheck-node or the OpenDiabetic Foot Check pipeline — endpoints, schemas, inference, QC, Bee routing, anchoring, tiers. Also use when another repo consumes FootCheckReport. Encodes the 10 platform invariants and the contract map.
---

# Foot Check Pipeline

Pipeline: capture (4-view) → QC gate → MedGemma 1.5 single-shot per view →
server-derived tier → Bee/Field Guides → FootCheckReport v2 → daily Merkle →
HCS + RFC 3161. Optional: /v1/care-package.

## Invariants (any violation = reject the change)
1. Zero retention in cloud lane — see zero-retention skill.
2. Closed vocabulary — see wellness-language skill. ObservationTag is the
   ENTIRE visual vocabulary. Adding a tag requires: schema + prompt bump +
   golden-set pass + Bee routing entry + tier-logic review, in one PR.
3. `derive_tier()` is deterministic server code. Model output NEVER
   influences tier directly. skin_break is ALWAYS red.
4. Prompt is pinned (`prompts/foot_check_vN.txt`); sha256 rides in every
   report + anchor. Changing it = new filename + golden-set regression.
5. QC thresholds live ONLY in `shared/qc_constants.json`; Swift is generated.
6. MedGemma is single-shot. Validate → one repair retry → hard fail.
7. Anchor hashes, never content.

## Contract map
- FootCheckReport v2: views (ViewQC[]), coverage_complete, observations,
  attention_tier, tier_reason, guides, prompt_sha256. Hash =
  sha256(model_dump_json minus disclaimer). Additive fields only; anything
  affecting hash semantics bumps schema_version.
- View labels are ground truth: backfill model-unknown side/region from view.
- Partial sessions allowed, flagged coverage_complete=false. Never block.

## Extension recipe
1. Propose contract change first (schema diff) before code.
2. Add contract tests BEFORE implementation (tier determinism, vocab
   rejection, hash round-trip serialize→parse→serialize).
3. Run `PYTHONPATH=. pytest tests/ -q` and paste output — no completion
   claims without read-back.
4. File leftovers to OPEN_ITEMS.md.
