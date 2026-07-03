# FOOTCHECK_BUILD.md — Claude Code build plan

Read CLAUDE.md first. Its invariants override anything below.
Work phase by phase, in order. After each phase: run the test suite, paste
output, update OPEN_ITEMS.md, commit with `phase-X:` prefix.

---

## STATE: VERIFIED DONE (do not rebuild — extend)

All of the following exists in this repo, tested green (31/31), and smoke-run
against a mocked vLLM end to end:

- **v2 contract** `app/schemas/foot_check.py` — CaptureView 4-photo protocol,
  ViewQC, closed ObservationTag vocab, deterministic `derive_tier` (plantar
  skin_break → red, proven).
- **API** `app/main.py` — `POST /v1/check` (4-view session, per-view QC retake
  reasons, concurrent per-view MedGemma calls, side/region backfill from view
  labels), `POST /v1/care-package` (tamper gate 409, foreign-photo 409, in-RAM
  reportlab PDF), `/healthz`, `/transparency`.
- **QC** `app/qc/gate.py` + `shared/qc_constants.json` + `tools/codegen_qc.py`
  → `dist/ios/QCConstants.swift` (generated, parity-tested).
- **Inference** `app/inference/medgemma.py` — single-shot, guided_json,
  validate → repair-once → fail. View label via `{view_label}` token replace.
- **Bee** `app/bee/` — in-memory FTS5 over `guides_seed.json` (10 seed guides;
  real Field Guide Collection content is Phase F).
- **Anchor** `app/anchor/` — Merkle (+proofs), daily batcher, HCS submit
  (SDK-optional, dry-run safe), RFC 3161 via openssl+httpx (LIVE-verified
  against freetsa.org: Status Granted).
- **SENSE/VAULT** `app/schemas/context_signals.py` (extra=forbid, wellness-only
  nudge copy enforced by test) + `app/vault/store.py` (Fernet-encrypted SQLite,
  day-join, `comparison_feed()` for MedGemma multi-timepoint).
- **Ops** `docker-compose.yml` (5090 node: vLLM+api+caddy, read_only/tmpfs),
  `caddy/Caddyfile` (body-free logs), `tests/retention_audit.sh`,
  `prompts/foot_check_v2.txt` (pinned).
- **Web** `web/index.html` — dual TOP/BOTTOM SCAN SVG hero, plantar ulcer
  zones, pure CSS animation, Atkinson Hyperlegible, zero JS.

Baseline check before any work: `PYTHONPATH=. python3 -m pytest tests/ -q` → 31 passed.

---

## PHASE A — Edge compose profiles

**What:** `compose.zimacube-creator.yml` (vLLM on RTX Pro 2000, util 0.90,
VAULT volume on HDD pool at `/DATA/footlab-vault`, gateway services),
`compose.zimaboard.yml` (gateway-only: api WITHOUT inference route enabled —
add `FOOTCHECK_ROLE=gateway` env that 503s `/v1/check` locally and forwards to
a discovered INFER peer once Phase C lands; until then 503 with clear message),
`compose.mac.yml` (llama.cpp server container `ghcr.io/ggml-org/llama.cpp:server`
with MedGemma GGUF Q8, OpenAI-compat on :8000), `compose.jetson.yml` (Ollama
arm64, Q4), `compose.dgx.yml` (identical to root compose, util 0.5, leaves
headroom for LoRA).
**Where:** repo root, plus `app/config.py` gains `role: str = "all"` and
`backend: str = "vllm"`.
**Why:** one repo, six SKUs; the sovereignty pitch is literal.
**Test:** `docker compose -f compose.X.yml config` validates for all; role=
gateway returns 503 with actionable message; contract tests still 31 passed.

## PHASE B — Backend adapter

**What:** `app/inference/backend.py` — thin capability layer over the
OpenAI-compatible endpoints (vllm | llamacpp | ollama | mlx). Differences:
guided_json only on vLLM (others rely on prompt + validate/repair), timeouts
per class (vllm 60s, llamacpp 120s, ollama/jetson 180s). `analyze()` moves
behind it; medgemma.py keeps the parse/repair logic.
**Where:** `app/inference/backend.py`, small edits to `medgemma.py`, env
`FOOTCHECK_BACKEND`.
**Why:** Mac/Jetson SKUs can't run vLLM; contract must not fork.
**Test:** parametrized unit tests mock each backend shape; golden JSON
produces identical FootCheckReport structure across backends.

## PHASE C — Mesh (mDNS)

**What:** `app/mesh/beacon.py` (advertise `_footlab._tcp` with TXT: role,
backend, model, prompt_sha256, version) + `app/mesh/discover.py` (peer table,
health poll `/healthz`, strongest-INFER selection: dgx > vllm-gpu > llamacpp >
ollama). Gateway role forwards `/v1/check` multipart to selected peer via
httpx streaming; adds `served_by` passthrough header.
**Where:** `app/mesh/`, dep add: `zeroconf` (justify: only mDNS lib needed).
**Why:** iPhone finds the lab zero-config; ZimaBoard gateway becomes useful.
**Test:** two uvicorn instances on localhost with fake TXT records; kill INFER
peer → gateway reroutes < 5s; forwarded session returns identical report hash
structure.

## PHASE D — served_by provenance

**What:** `FootCheckReport.served_by: ServedBy {device_class, backend,
model_id}` — schema v2 stays (additive field with default), populated by the
node from env `FOOTCHECK_DEVICE_CLASS`.
**Where:** `app/schemas/foot_check.py`, `app/main.py`, compose profiles set env.
**Why:** never lie about where compute happened — cloud vs cube vs mac is
visible in every report.
**Test:** contract test per device class; hash determinism preserved.

## PHASE E — ZimaOS app manifest

**What:** `dist/zimaos/` — ZimaOS/CasaOS-style app manifest (docker-compose +
metadata: name "OpenDiabetic Foot Lab", icon, tips) wrapping the
zimacube-creator profile with sane defaults; VAULT path pre-mapped to /DATA.
**Where:** `dist/zimaos/`.
**Why:** distribution: one-click install for the Zima installed base.
**Test:** manifest lints against their published schema; cold VM → install →
first check < 10 min (manual gate, document result in OPEN_ITEMS.md).

## PHASE F — Bee content: Field Guide Collection

**What:** replace `guides_seed.json` bodies with the real 22-guide Field Guide
Collection (3 seasons) — owner will supply content; build the loader to accept
`FOOTCHECK_GUIDES_PATH` override so content ships as data, not code.
**Where:** `app/bee/`.
**Why:** routing quality is only as good as the corpus.
**Test:** every ObservationTag routes to ≥1 guide; FG-003 (Foot Photos)
reachable from none_noted.

## PHASE G — Golden set + prompt regression harness

**What:** `tests/golden/` — 50 adversarial images (blur, dark, washed,
not-a-foot, shoe, cat, partial foot) + expected QC/tier outcomes in a manifest;
`tests/test_golden.py` runs QC gate on all (no GPU) and, with
`FOOTCHECK_LIVE=1`, runs full inference against the canary (:8092).
**Where:** `tests/golden/`.
**Why:** Invariant 4 — no prompt change without this passing.
**Test:** the harness itself; CI job wiring.

## PHASE H — Launch hardening

**What:** Caddy rate limit (10 checks/min/IP), request body size cap at edge
(52MB for 4 images), `/transparency` gains live mirror-node fetch of the
latest anchor, pin freetsa CA chain for automated `openssl ts -verify` in CI,
dedicated HCS topic env documented (owner mints topic).
**Where:** `caddy/Caddyfile`, `app/main.py`, `tests/`.
**Why:** public launch checklist.
**Test:** rate limit returns 429 on burst; retention audit still clean; CI
verifies a stored .tsr against pinned chain.

## PHASE I — iOS seam (docs only in this repo)

**What:** `dist/ios/SEAM.md` — exact multipart shapes for `/v1/check` and
`/v1/care-package`, QCConstants usage, Bonjour service string, share-sheet
flow (UIActivityViewController with returned PDF), SENSE→VAULT posting shape
(sovereign lane only).
**Where:** `dist/ios/`.
**Why:** the iOS repo builds against this seam; keep it authoritative here.
**Test:** doc review — every endpoint example is copy-paste-runnable curl.

---

## Definition of done (whole build)

- All phases committed, suite ≥ 31 passed + new phase tests green
- `tests/retention_audit.sh` clean on the 5090 stack
- One end-to-end demo: 4 photos → report → care package PDF → anchor flush
  with real HCS tx id + verified .tsr
- OPEN_ITEMS.md empty or every remaining line owner-acknowledged
