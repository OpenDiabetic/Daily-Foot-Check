---
name: wellness-language
description: Use when writing ANY user-facing or model-facing text in OpenDiabetic — prompts, schemas, nudge copy, UI strings, PDF text, marketing pages, App Store copy, error messages. Enforces educational-not-diagnostic framing and the closed observation vocabulary. Also use when reviewing how model output is surfaced.
---

# Wellness Language Law

Positioning: educational monitoring — not a medical device — it NEVER
diagnoses. This is a compliance boundary (general-wellness posture), not a
style preference.

## The three registers
1. **Observation (model + schema):** only ObservationTag words — redness,
   swelling, skin break, discoloration, nail change, callus, dryness/fissure,
   deformity note, asymmetry, none noted. Plain visual description. NEVER
   disease names, never causes.
2. **Tier (UI/PDF):** green "nothing stood out" / yellow "worth watching" /
   red "worth showing your care team." Red means exactly that sentence —
   never "urgent," never "risk of X."
3. **Nudge (wearables):** "…a good day for a foot check." Signals framed as
   pattern shifts, never symptoms.

## Enforcement pattern (copy, don't invent)
Every module that emits copy owns its strings in ONE place; a test greps
every reachable output against banned-vocab.txt (see
test_copy_never_uses_symptom_language). UI layers render strings verbatim —
no rephrasing.

## When the model violates
Closed-schema validation rejects off-vocab tags. Never post-process a
diagnosis word into a softer one — reject and repair-retry.
