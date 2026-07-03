---
name: medgemma-finetune
description: Use when building the foot-specific MedGemma LoRA — dataset curation, training config, eval gates, deployment of fine-tuned checkpoints. Also use when designing the opt-in data-donation flow or tagging training pairs.
---

# MedGemma Foot-LoRA Pipeline

Goal: foot-domain LoRA on MedGemma 1.5 4B, trained on PRO 6000 rig GPU1 /
DGX, deployed behind the same single-shot contract.

## Dataset doctrine (Royal Jelly discipline)
- Pairs: (image_ref, FootCheckReport-shaped findings). NEVER store images
  without explicit opt-in donation consent — separate flow, separate consent
  screen, revocable. Until donation flow exists, train on public/licensed
  dermatology-adjacent sets + synthetic QC-hard negatives.
- Tier every pair jelly/honey/pollen/propolis (9–10 / 7–8.9 / 4–6.9 / <4).
  Train on jelly+honey only. Quarantine think-tag or off-vocab contamination
  (CreditSniper lesson: 1,172 pairs quarantined — audit BEFORE training).
- Content-address shards (SHA256), Merkle root anchored to HCS. Honey Card
  documents every dataset.

## Training config — Gold Standard
LoRA r=64, alpha=32, all projections. Early stopping on eval loss (SwarmCurator
lesson: 27B best at step 400). Watch generalization gap; Signal-9B v3 hit
zero gap with early stop at 800 — that's the bar.

## Eval gates (ALL must pass before a checkpoint serves)
1. Golden set (see golden-set skill): tier agreement ≥ baseline prompt.
2. Vocab discipline: 0 off-schema tags across the full eval sweep.
3. Plantar sensitivity: skin_break recall on plantar views must not regress
   even 1 case vs baseline — this is the mission metric.
4. Canary soak on :8092 for 48h before prod flip.
Deploy = new model_id string; reports carry it; never hot-swap silently.
