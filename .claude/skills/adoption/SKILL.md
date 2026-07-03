---
name: adoption
description: Use when working on user growth, activation, onboarding, retention, adherence, the foot-check-request funnel, referral loops, care-team distribution, edge/SKU adoption, or any feature/metric that moves someone from "requested a foot check" to "checks daily and stays." The growth-engineering skill for OpenDiabetic.
---

# Adoption Engineering

Mission constraint: this is a FREE service for diabetics who need it. Adoption
success = sustained daily self-exam adherence (the guideline-backed behavior
that actually prevents ulcers), NOT vanity signups. Every growth mechanic is
measured against adherence, never against engagement-for-its-own-sake, and
never at the cost of zero-retention or wellness-language.

## The funnel (instrument every stage)
1. **Request** — inbound foot-check request (e.g. build@opendiabetic.com
   email). Stage metric: time-to-first-reply.
2. **First check** — completed 4-view session. Metric: request→first-check
   conversion; blockers are QC failures and capture friction (see
   sentinel-capture). Reduce here first.
3. **Habit** — the mission stage. IWGDF: daily self-exam + once-daily temp
   self-monitoring (risk 2–3). Metric: 7-day and 30-day check adherence.
   Lever: Watch NUDGE (wellness copy law) + VAULT streaks/trends.
4. **Care-team loop** — a red/yellow tier produces a care-package the user
   sends. Metric: tier-red → care-package-sent rate. This is the clinical
   payoff AND the highest-trust growth surface.
5. **Advocacy** — clinicians who receive verifiable care-packages become a
   referral channel; households add members; sovereign users buy a SKU.

## Adoption ladder (privacy dictates the arc)
Cloud lane (zero setup, amnesiac) → habit forms → user wants HISTORY →
sovereign SKU (VAULT trends). The moat feature (longitudinal) is the natural
upsell that is ALSO the deepest privacy posture. Never invert this: don't
push hardware before the habit exists.

## Distribution channels (ranked, production-sound)
1. **Care-team PDF** — every care-package is verifiable-unaltered; clinicians
   trust it → highest-quality channel. Build referral affordances here first.
2. **ZimaOS app store** — one-click install to the self-hosting installed
   base (see edge-sku-deploy). Colonize hardware users already own.
3. **Clinic kiosk** — Jetson SKU in waiting rooms; assisted first-check for
   users who can't see their own soles.
4. **Community/word-of-mouth** — the amputation-survivor mission story is
   real and earned; let it carry, never manufacture urgency.

## Hard lines (adoption NEVER buys growth with these)
- No dark patterns, no manufactured urgency, no engagement loops that inflate
  check frequency beyond clinical value (daily is the target — more is not
  "better" and implying so violates wellness-language).
- No PHI in any growth analytics. Funnel metrics are counts and hashed cohort
  ids — never image bytes, emails-in-analytics, or report bodies (audit
  allowlist law extends to growth telemetry).
- No over-reliance framing: the product's job is to route people TO their
  care team, not to substitute for it. Retention that isolates a user from
  clinical care is a failure, not a win.

## Build recipe (what to instrument)
1. Funnel table: stage counts, hashed cohort id, tier distribution, SKU/lane.
   Storage obeys zero-retention — aggregate, not per-user PHI.
2. Adherence job: rolling 7/30-day check rate per (hashed) user; feeds NUDGE
   cadence, never sold or exported.
3. Care-loop metric: red-tier→sent conversion; the trust flywheel's health.
4. A/B only on capture friction and copy clarity — never on urgency or fear.
File growth gaps to OPEN_ITEMS.md.
