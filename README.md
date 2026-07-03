# footcheck-node v0.1

OpenDiabetic Foot Check — image in, educational report out, **nothing retained**.
One container stack that runs identically on the swarmrails 5090 rig (cloud lane)
or a user's own GPU box (sovereign lane).

```
iPhone / web capture
  → QC gate (blur/light/resolution — rejects before GPU spend)
  → MedGemma 1.5 4B via vLLM (single-shot, temperature 0, guided_json)
  → server-derived attention tier (model has NO vote on tier)
  → Bee: FTS5 → Field Guide routing
  → FootCheckReport JSON  +  X-Report-SHA256 header
  → daily Merkle batch → Hedera HCS  +  RFC 3161 countersign (dual anchor)
```

## Quickstart (5090 rig)

```bash
cp .env.example .env            # add HF_TOKEN (accept HAI-DEF terms on HF first)
docker compose up -d --build    # first boot pulls ~8GB of weights
curl -k https://localhost/healthz
curl -k -F "image=@foot.jpg" https://localhost/v1/check
```

## Zero-retention, enforced not promised

| Layer | Mechanism |
|---|---|
| Process | image handled as `bytes`, never written |
| Container | `read_only: true`, `tmpfs: /tmp`, `cap_drop: ALL` |
| vLLM | `--disable-log-requests` (image tokens never hit logs) |
| Edge | Caddy logs strip headers + query strings; no bodies |
| Audit | allowlisted hash-only JSONL to stdout — PII fields raise `ValueError` |
| Proof | `tests/retention_audit.sh` → `docker diff` must be clean (CI gate) |

## Evidence rail

- Per-check: report hash returned to user (`X-Report-SHA256`)
- Daily: Merkle root of all hashes → HCS topic (consumer receipt, mirror-node
  verifiable by URL) **and** RFC 3161 token on the same root (court-native).
- Prompt is pinned (`prompts/foot_check_v2.txt`); its sha256 rides in every
  report and every anchor. Changing the prompt without a golden-set pass is a
  Standing Rules violation.

Verify HCS: `GET https://mainnet.mirrornode.hedera.com/api/v1/topics/{topic}/messages`
Verify TSR: `openssl ts -verify -digest <root> -sha256 -in <root>.tsr -CAfile tsa-chain.pem`

## Test

```bash
PYTHONPATH=. pytest tests/ -q          # contract tests (no GPU)
API=https://localhost/v1/check ./tests/retention_audit.sh   # live stack
```

## Layout

```
app/schemas/foot_check.py   # THE contract: closed vocab, derive_tier()
app/qc/gate.py              # PIL+numpy quality gate
app/inference/medgemma.py   # single-shot vLLM client, validate-retry-fail
app/bee/retrieve.py         # in-memory FTS5 over Field Guides
app/anchor/                 # merkle / hedera / rfc3161 / daily batcher
app/audit/log.py            # hash-only allowlisted audit
app/main.py                 # POST /v1/check, /transparency, /healthz
prompts/foot_check_v2.txt   # pinned; sha256 anchored
web/index.html              # how-it-works page w/ 3D foot
caddy/Caddyfile             # TLS edge, body-free logs
tests/                      # contract tests + retention audit
```

## Open items → OPEN_ITEMS.md

- [ ] Create dedicated HCS topic for footcheck (separate from RJP topic)
- [ ] Golden set: 50 adversarial images (blur / not-a-foot / shoe / cat) for
      prompt regression before any prompt bump
- [ ] Canary MedGemma on PRO 6000 rig GPU1 (:8092) + Caddy failover upstream
- [ ] iOS app: point capture flow at POST /v1/check; render report card
- [ ] Publish `opendiabetic/footlab-node` image (the sovereign-lane one-liner)
- [ ] `/transparency` page: add live mirror-node fetch of latest anchor
- [ ] Fetch + pin freetsa CA chain for automated `openssl ts -verify` in CI
- [ ] Rate limiting at Caddy (e.g. 10 checks/min/IP) before public launch

## SENSE + VAULT (added this session)

- `app/schemas/context_signals.py` — wearable contract: gait asymmetry, walking
  speed delta, wrist temp deviation, activity. `extra='forbid'`, all Optional,
  hash-anchored. `nudge_worthy()` owns the ONLY user-facing nudge copy —
  wellness language enforced by test (`test_copy_never_uses_symptom_language`).
- `shared/qc_constants.json` — SINGLE SOURCE for QC thresholds. Python config
  reads it; `tools/codegen_qc.py` emits `dist/ios/QCConstants.swift`. CI rule:
  regenerate + `git diff --exit-code`.
- `app/vault/store.py` — sovereign-lane encrypted history (Fernet, device
  keyfile 0600). Joins reports+signals by day; `comparison_feed()` is the
  MedGemma 1.5 multi-timepoint / Phase 3 ComparisonEngine input. Cloud lane has
  no code path to it.

## Care Package (send-to-care-team)

- `POST /v1/care-package` — server RENDERS (reportlab, in-RAM), only the USER
  sends via their device share sheet. We never relay PHI.
- Tamper gate: client echoes report JSON + hash; server re-hashes and 409s any
  doctored report (`app/schemas/care_package.py`).
- Photos opt-in and sha256-matched to report views — foreign images 409.
- PDF footer prints report/prompt hashes + transparency verify pointer, so the
  receiving clinician can confirm the document is unaltered.
