"""Stream A — aggregate signal. Cloud-legal, always on, holds NO content.

Consumes the same hash-only audit records the pipeline already emits and rolls
them into an AggregateSignal: what's hard to capture, tier mix, reviewer
reject rate. This tells us WHAT to train and feeds golden-set adversarial
selection — without ever touching an image or a report body.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from app.harvest.schemas import AggregateSignal


def aggregate(
    audit_records: list[dict],
    window_start: datetime,
    window_end: datetime,
) -> AggregateSignal:
    """audit_records: the hash-only JSONL rows (outcome, attention_tier,
    qc_passed, etc.). No image bytes exist in these by construction."""
    total = len(audit_records)
    if total == 0:
        return AggregateSignal(
            window_start=window_start, window_end=window_end,
            checks_total=0, qc_bounce_rate=0.0, view_coverage_rate=0.0,
        )

    qc_bounced = sum(1 for r in audit_records if r.get("outcome") == "qc_rejected")
    tiers = Counter(r["attention_tier"] for r in audit_records if r.get("attention_tier"))
    reviewer_rejects = sum(1 for r in audit_records if r.get("outcome") == "reviewer_rejected")
    ok_sessions = [r for r in audit_records if r.get("outcome") == "ok"]
    complete = sum(1 for r in ok_sessions if r.get("coverage_complete") is True)

    return AggregateSignal(
        window_start=window_start,
        window_end=window_end,
        checks_total=total,
        qc_bounce_rate=round(qc_bounced / total, 4),
        tier_counts=dict(tiers),
        view_coverage_rate=round(complete / len(ok_sessions), 4) if ok_sessions else 0.0,
        reviewer_reject_rate=round(reviewer_rejects / total, 4),
        qc_reason_counts=dict(Counter(
            reason for r in audit_records for reason in r.get("qc_reasons", [])
        )),
    )
