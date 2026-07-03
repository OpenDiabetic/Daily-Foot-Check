---
name: zero-retention
description: Use when building or reviewing ANY endpoint, service, container, or log that touches user images, health data, or PHI-adjacent content across the Swarm & Bee ecosystem (OpenDiabetic, SwarmMed, LegalSniper client docs). Encodes never-persist patterns and the retention-audit CI gate.
---

# Zero Retention

The claim is "we CANNOT keep your data," enforced in layers — not "we won't."

## The layer stack (all required)
1. **Process:** content handled as `bytes` in-request only. No tempfiles, no
   caches, no passing paths — pass bytes.
2. **Container:** `read_only: true`, `tmpfs: [/tmp]`, `cap_drop: [ALL]`,
   no volumes on any container that touches content. Model-weight caches OK
   (weights aren't PHI) — isolate in named volumes.
3. **Inference server:** vLLM `--disable-log-requests` (prompts embed image
   tokens). llama.cpp: `--log-disable`. Ollama: debug logging off.
4. **Edge:** proxy logs strip bodies, query strings, and headers.
5. **Audit:** allowlisted fields only, enforced in code (raise on violation).
   Hashes, enums, latency — never bytes, emails, IPs, notes.

## The proof (ship it, don't just claim it)
- `tests/retention_audit.sh`: N live requests → `docker diff` on every
  content-touching container must be empty outside tmpfs. CI-gate releases.
- Render-in-RAM check: directory listings identical before/after render.
- Public `/transparency` endpoint describing the design + verify pointers.

## Review → checklist.md
Reject on sight: `open(`/`write(` near request bytes, UploadFile `.file`
passed to libs that spool to disk, logging `request.body`, ORM models with
content columns, "temporary" S3/R2 writes of user content.
