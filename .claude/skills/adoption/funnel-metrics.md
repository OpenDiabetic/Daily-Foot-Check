# Adoption funnel — metric definitions (all PHI-free)
| Stage | Metric | Definition | Privacy note |
|---|---|---|---|
| Request | reply_latency | request_ts → first_reply_ts | count/latency only |
| First check | activation_rate | first_checks / requests | hashed cohort id |
| First check | qc_bounce_rate | sessions with any 422 / sessions | drives capture UX |
| Habit | adherence_7d / _30d | rolling distinct check-days / window | per hashed user, local |
| Habit | nudge_to_check | checks within 24h of a nudge / nudges | cadence tuning |
| Care loop | red_to_sent | care_packages_sent / red_tier_reports | trust flywheel |
| Advocacy | referral_installs | new users w/ referral source | source hashed |
| SKU | lane_mix | cloud vs sovereign share | no device fingerprint |
Rules: aggregate at write time; no per-event image/email/report bodies ever;
telemetry rides the same audit allowlist discipline as the pipeline.
North star: 30-day self-exam adherence (the ulcer-prevention behavior).
