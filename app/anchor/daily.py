"""Daily anchor batch: report hashes queue in RAM, flush = Merkle root ->
HCS submit + RFC 3161 countersign of the SAME root.

The queue holds only sha256 hex strings. If the process dies before a flush,
users still hold their reports (with hashes) client-side — the next check
re-enters the evidence stream. No PHI at risk, ever.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from app.anchor.hedera import submit_root
from app.anchor.merkle import merkle_root
from app.anchor.rfc3161 import timestamp_root
from app.config import get_settings

log = logging.getLogger("footcheck.anchor")


class AnchorBatcher:
    def __init__(self) -> None:
        self._queue: list[str] = []
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None

    async def add(self, report_sha256: str) -> None:
        async with self._lock:
            self._queue.append(report_sha256)

    async def flush(self) -> dict | None:
        s = get_settings()
        async with self._lock:
            if not self._queue:
                return None
            leaves, self._queue = self._queue, []

        root = merkle_root(leaves)
        tx_id = await submit_root(root, len(leaves), s.prompt_sha256)
        tsr_path = await timestamp_root(root, s.anchor_out_dir)

        manifest = {
            "flushed_at": datetime.now(timezone.utc).isoformat(),
            "root": root,
            "leaf_count": len(leaves),
            "hcs_tx": tx_id,
            "rfc3161_token": tsr_path.name if tsr_path else None,
            "prompt_sha256": s.prompt_sha256,
        }
        log.info("anchor.flush %s", json.dumps(manifest, separators=(",", ":")))
        return manifest

    async def _loop(self) -> None:
        s = get_settings()
        while True:
            await asyncio.sleep(s.anchor_flush_seconds)
            try:
                await self.flush()
            except Exception:  # never let the batcher die silently
                log.exception("anchor.flush_failed")

    def start(self) -> None:
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        await self.flush()  # final drain on shutdown
