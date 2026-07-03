"""Hedera HCS anchor. SDK import is optional so dev machines without the
Hedera SDK still run the full pipeline in DRY_RUN.

Message format (JSON, < 1024 bytes):
  {"v":"footcheck.v1","root":"<merkle-root-hex>","n":<leaf-count>,"prompt":"<prompt-sha256>"}

Verification path for anyone, no wallet needed:
  GET https://mainnet.mirrornode.hedera.com/api/v1/topics/{topic}/messages
"""
from __future__ import annotations

import json
import logging

from app.config import get_settings

log = logging.getLogger("footcheck.anchor")


async def submit_root(root_hex: str, leaf_count: int, prompt_sha256: str) -> str | None:
    """Submit merkle root to HCS. Returns consensus tx id or None in dry-run."""
    s = get_settings()
    message = json.dumps(
        {"v": "footcheck.v1", "root": root_hex, "n": leaf_count, "prompt": prompt_sha256},
        separators=(",", ":"),
    )

    if not (s.anchor_enabled and s.hedera_topic_id and s.hedera_operator_id):
        log.info("hcs.dry_run root=%s n=%d", root_hex, leaf_count)
        return None

    try:
        from hedera import (  # type: ignore
            AccountId, Client, PrivateKey, TopicId, TopicMessageSubmitTransaction,
        )
    except ImportError:
        log.error("hedera SDK not installed but anchoring enabled — root NOT submitted")
        return None

    client = Client.forMainnet()
    client.setOperator(
        AccountId.fromString(s.hedera_operator_id),
        PrivateKey.fromString(s.hedera_operator_key),
    )
    receipt = (
        TopicMessageSubmitTransaction()
        .setTopicId(TopicId.fromString(s.hedera_topic_id))
        .setMessage(message)
        .execute(client)
        .getReceipt(client)
    )
    tx_id = str(receipt.transactionId) if hasattr(receipt, "transactionId") else "submitted"
    log.info("hcs.anchored root=%s tx=%s", root_hex, tx_id)
    return tx_id
