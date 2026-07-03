# OPEN_ITEMS.md — footcheck-node

Filed per Standing Rules. Claude Code: update this file every session.

- [ ] PHASE A–I per FOOTCHECK_BUILD.md (in order)
- [ ] Owner: mint dedicated HCS topic for footcheck (separate from RJP 0.0.10291838)
- [ ] Owner: HF token + accept HAI-DEF terms on google/medgemma-1.5-4b-it
- [ ] Owner: supply real Field Guide Collection content (22 guides) for Phase F
- [ ] Owner: bench hardware — ZimaCube 2 Creator Pack + ZimaBoard 2 (5–7 day ship)
- [ ] Owner: DNS check.opendiabetic.com → 5090 rig edge
- [ ] Reply to gavigtl5678@gmail.com once cloud lane is public

## Found + fixed (landing session, 2026-07-03)
- [x] `tools/codegen_qc.py` embedded a wall-clock timestamp in the generated Swift, so invariant #5's gate (`regenerate + git diff --exit-code`) always false-failed. Removed the `// Generated:` stamp → codegen is now deterministic (proven: two regenerations byte-identical).
