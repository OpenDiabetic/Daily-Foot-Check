---
name: harvest
description: Use when building or reviewing anything that turns pipeline output into training data — donation consent, image/report pair assembly, RJP tiering, Honey Card datasets, Merkle-anchored shards, aggregate signal for golden-set selection, or the MedGemma/GuideWriter LoRA training feeds. The training-data flywheel skill.
---

# Harvest — the Training-Data Flywheel

Every check, care package, and reviewer verdict is training signal. Harvest
sweeps it into the next foot-LoRA and GuideWriter-LoRA — free service becomes
proprietary model advantage. This runs UNDER zero-retention, not against it.

## Two streams, strictly separated
- **Stream A — AggregateSignal (cloud-legal, always on):** hashes, tiers, QC
  stats, reviewer reject rate. NO content, so NO consent needed. Tells us what
  to train and feeds golden-set adversarial selection. `app/harvest/signal.py`.
- **Stream B — HarvestPair (VAULT/sovereign only, opt-in):** (image, report)
  pairs. Requires explicit revocable donation consent. The cloud API has no
  import path to the collector. `app/harvest/collector.py`.

## Consent law (Stream B — non-negotiable)
1. No pair without an ACTIVE DonationConsent — `assemble_pair` raises
   DonationRejected otherwise.
2. Consent is on-device, explicit, revocable. The consent record is
   Merkle-anchorable ("user said yes on date X" is provable).
3. Revocation is honored BEFORE training: `training_set()` calls
   `purge_revoked()` first, then keeps only trainable tiers. A revoked jelly
   pair still drops.

## PHI firewall
- A HarvestPair links to consent by HASH only — never a user id or email
  (test: `test_pair_holds_no_user_id`).
- Donated images are EXIF-stripped before acceptance (`strip_exif` — kills GPS
  + device metadata). subject_ref is a per-device salt hash, never a user id.

## RJP tiering (audit BEFORE training — CreditSniper discipline)
Every pair scored jelly/honey/pollen/propolis (9–10 / 7–8.9 / 4–6.9 / <4).
Only jelly+honey train. Quarantine is documented in the Honey Card, never
silent. A Honey Card accompanies every shard set: pair_count, trainable_count,
tier_distribution, consent_basis, merkle_root, hcs_anchor.

## Anchoring
Content-addressed shards (SHA256), Merkle root, HCS anchor — same rail as
reports. The dataset's provenance is as verifiable as a foot-check receipt.

## What harvest feeds
| Source | Pair kind | Trains |
|---|---|---|
| report + donated image | image_findings | MedGemma foot-LoRA |
| ComparisonEngine deltas | multitimepoint | MedGemma longitudinal LoRA |
| reviewer-approved GuideDraft | guide_draft | GuideWriter-LoRA |
| QC bounces / retakes (Stream A) | — | golden-set adversarial |

## Build recipe
1. Stream A ships now (no consent friction) — aggregate hash-only audit rows.
2. Stream B gates behind the iOS donation flow (separate consent screen,
   settings-revocable). Until that ships, collector is dormant but tested.
3. Before any LoRA run: `training_set(pairs, revoked)` → Honey Card → anchor.
   Never train on un-audited pairs. File gaps to OPEN_ITEMS.md.
