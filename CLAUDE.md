# CLAUDE.md — footcheck-node

You are working on **footcheck-node**, the OpenDiabetic Foot Check pipeline.
Part of the Swarm & Bee family. Owner: smash. Mission: **free, valid,
educational foot monitoring for diabetics.** Educational monitoring — not a
medical device. It NEVER diagnoses.

## Architecture (do not deviate without explicit approval)

```
iPhone/web capture (4-view protocol: dorsal_left/right, plantar_left/right)
  → QC gate (app/qc/gate.py — thresholds from shared/qc_constants.json ONLY)
  → MedGemma 1.5 4B via vLLM (single-shot, temp 0, guided_json, per-view)
  → server-derived tier (app/schemas/foot_check.py::derive_tier — model has NO vote)
  → Bee FTS5 → Field Guides (app/bee/)
  → FootCheckReport v2 + X-Report-SHA256
  → daily Merkle batch → Hedera HCS + RFC 3161 countersign (app/anchor/)
  → optional: POST /v1/care-package (in-RAM reportlab PDF, user sends it themselves)
Edge mesh roles: SENSE (Watch) → CAPTURE (iPhone) → GATEWAY → INFER → VAULT
```

## INVARIANTS — violating any of these is a build failure

1. **Zero retention (cloud lane).** Images live as `bytes` in-process only.
   No disk writes, no image bytes in logs, containers `read_only` + tmpfs.
   `tests/retention_audit.sh` must pass. vLLM runs `--disable-log-requests`.
2. **Closed vocabulary.** No diagnosis words anywhere — schemas, prompts,
   nudge copy, UI strings. `ObservationTag` is the entire visual vocabulary.
   Tier language is only "worth watching / worth showing your care team."
3. **The model never decides tier.** `derive_tier()` is deterministic server
   code. Any PR that lets model output influence tier directly is rejected.
4. **Prompt pinning.** `prompts/foot_check_v2.txt` is pinned; its sha256 rides
   in every report and anchor. NEVER edit the prompt without running the
   golden set (Phase G below) and bumping the filename version.
5. **Single-source QC.** Thresholds live in `shared/qc_constants.json` only.
   Swift side is GENERATED (`tools/codegen_qc.py` → `dist/ios/QCConstants.swift`).
   Never hand-edit generated files. CI: regenerate + `git diff --exit-code`.
6. **MedGemma is single-shot.** Not evaluated for multi-turn. One image, one
   call, validate → one repair retry → hard fail. Never chat with it.
7. **Server renders, user sends.** No SMTP, no relay, no push of PHI-adjacent
   artifacts. Care packages stream back to the requester only.
8. **SENSE data is sovereign-lane only.** ContextSignals have no cloud
   endpoint. Do not add one.
9. **Audit is allowlisted.** `app/audit/log.py` raises on non-allowlisted
   fields. Extend the allowlist only for hash/enum/latency fields, never PII.
10. **Anchor the hash, never the content.** HCS + RFC 3161 receive Merkle
    roots of report hashes. Nothing else, ever.

## Standing Rules (Swarm & Bee doctrine)

- **No claiming completion without read-back verification.** Run the tests,
  paste the output. "Should work" is not a state.
- File discovered work to `OPEN_ITEMS.md` — never silently drop a loose end.
- Propose full architecture before writing multi-file changes.
- Minimal dependencies. Current allowlist: fastapi, uvicorn, pydantic,
  pydantic-settings, httpx, pillow, numpy, python-multipart, cryptography,
  reportlab (+ dev: pytest, pdfplumber). Justify any addition in one line.
- Async patterns, modern type hints, clean modules. No over-engineering.

## Session Start Checklist

1. `PYTHONPATH=. python3 -m pytest tests/ -q` → expect **31 passed** (or more,
   never fewer).
2. Read `OPEN_ITEMS.md` and `FOOTCHECK_BUILD.md` for current phase.
3. Confirm which lane you're building for (cloud node / edge SKU / iOS seam).

## Test Commands

```bash
PYTHONPATH=. python3 -m pytest tests/ -q          # contract suite (no GPU)
python3 tools/codegen_qc.py && git diff --exit-code dist/ios/  # QC parity
API=https://localhost/v1/check ./tests/retention_audit.sh      # live stack
```

## Deployment targets

- **Cloud node:** RTX 5090 rig (MedGemma solo, `--gpu-memory-utilization 0.85`).
  PRO 6000 rig = Bee tier + LoRA training + canary (:8092).
- **Edge SKUs:** ZimaCube 2 Creator Pack (RTX Pro 2000 — full INFER+VAULT+GATEWAY),
  ZimaCube Standard/Pro (VAULT+GATEWAY), ZimaBoard 2 (GATEWAY), Mac mini
  (llama.cpp/MLX INFER+VAULT), DGX Spark (everything), Jetson Orin Nano (INFER Q4).
- Same containers everywhere — "the cloud we run is the container you can run."

## Compliance framing (bake into every user-facing string)

Educational monitoring — not a medical device — never diagnoses — red tier
means exactly one thing: "worth showing your care team."
