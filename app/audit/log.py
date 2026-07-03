"""Hash-only audit log.

One JSON line per check to stdout (journald / docker logs). This is the ONLY
trace a check leaves on the node:
  - request_id, timestamps, latency
  - sha256(image), sha256(report), prompt hash, model id, tier
NEVER: image bytes, report body, email, IP, user agent.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_audit = logging.getLogger("footcheck.audit")
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(message)s"))
_audit.addHandler(_handler)
_audit.setLevel(logging.INFO)
_audit.propagate = False

_ALLOWED = {
    "request_id", "image_sha256", "report_sha256", "prompt_sha256",
    "model_id", "attention_tier", "qc_passed", "latency_ms", "outcome",
}


def audit(**fields) -> None:
    bad = set(fields) - _ALLOWED
    if bad:
        raise ValueError(f"audit log rejects non-allowlisted fields: {bad}")
    fields["at"] = datetime.now(timezone.utc).isoformat()
    _audit.info(json.dumps(fields, separators=(",", ":")))
