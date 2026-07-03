# E2E Functionality Review — 2026-07-03 (pre-hardware)

## VERIFIED (executed in review, outputs read back)
| # | Surface | Result |
|---|---------|--------|
| 1 | Contract suite | 31/31 passed |
| 2 | 4-view session: full/partial/dup | 200 red-tier merge ✓ / coverage_complete:false ✓ / 400 ✓ |
| 3 | Plantar skin_break → red | ✓ (the protocol's reason to exist) |
| 4 | Side/region backfill from view labels | ✓ |
| 5 | QC reject w/ per-view retake reasons | 422 ✓ |
| 6 | Care package: PDF stream | 200, 2.36MB, 4 photos embedded ✓ |
| 7 | Tamper gate (doctored tier) | 409 ✓ |
| 8 | Foreign photo injection | 409 ✓ |
| 9 | Hash round-trip (serialize→parse→serialize) | stable ✓ |
| 10 | Merkle root + proofs | ✓ |
| 11 | RFC 3161 vs freetsa.org | LIVE: Status Granted, sha256 match ✓ |
| 12 | Anchor daily flush manifest | ✓ (HCS dry-run — no topic yet) |
| 13 | Vault encrypt/join/comparison_feed | ✓; wrong-key read fails ✓ |
| 14 | ContextSignals contract + nudge copy ban-list | ✓ |
| 15 | QC single-source: python↔json↔swift | AGREE ✓ |
| 16 | compose invariants (read_only/tmpfs/no-vol/disable-log-requests) | ✓ |
| 17 | Dockerfile (paths, non-root, openssl) | ✓ |
| 18 | Audit allowlist raises on PII | ✓ |
| 19 | Page: dual scans, ulcer zones, no-JS, a11y, reduced-motion | 8/8 ✓ |
| 20 | Loose-end grep | clean (1 comment placeholder = owner item) |

## UNVERIFIED — requires hardware/creds (blocks launch, not build)
| # | Surface | Needs | Where it gates |
|---|---------|-------|----------------|
| U1 | Real MedGemma 1.5 inference quality + latency | 5090 rig + HF token | first `docker compose up` |
| U2 | vLLM guided_json behavior w/ real model | same | Phase G golden set |
| U3 | Live HCS submit (real tx id) | minted topic + operator keys | OPEN_ITEMS |
| U4 | retention_audit.sh on live stack | docker on rig | CI gate before public |
| U5 | Caddy TLS + body-free logs in anger | DNS + rig | launch hardening (Phase H) |
| U6 | Throughput/concurrency bench | rig | honest latency claims on page |
| U7 | HEIC-from-iPhone ingestion path | real iPhone photos | iOS seam (Phase I) — Pillow needs pillow-heif if raw HEIC sent; iOS should export JPEG |

## Findings filed
- U7 is the one real code-adjacent gap found by this review → added to OPEN_ITEMS.
