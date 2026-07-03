"""RFC 3161 countersignature of the daily Merkle root.

Uses the openssl binary to build the TimeStampReq (zero extra Python deps),
httpx to POST it to the TSA, and writes the .tsr token to tmpfs. The token is
re-derivable evidence — losing it only loses convenience, never truth, because
the same root is on HCS.

Verify anytime:
  openssl ts -verify -digest <root_hex> -sha256 -in batch.tsr -CAfile tsa-chain.pem
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx

from app.config import get_settings

log = logging.getLogger("footcheck.anchor")


async def timestamp_root(root_hex: str, out_dir: Path) -> Path | None:
    s = get_settings()
    out_dir.mkdir(parents=True, exist_ok=True)
    tsq = out_dir / f"{root_hex[:16]}.tsq"
    tsr = out_dir / f"{root_hex[:16]}.tsr"

    proc = await asyncio.create_subprocess_exec(
        "openssl", "ts", "-query",
        "-digest", root_hex, "-sha256", "-cert",
        "-out", str(tsq),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, err = await proc.communicate()
    if proc.returncode != 0:
        log.error("tsq.build_failed: %s", err.decode()[:200])
        return None

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                s.tsa_url,
                content=tsq.read_bytes(),
                headers={"Content-Type": "application/timestamp-query"},
            )
        if resp.status_code != 200:
            log.error("tsa.http_%d", resp.status_code)
            return None
        tsr.write_bytes(resp.content)
        log.info("rfc3161.countersigned root=%s tsr=%s", root_hex, tsr.name)
        return tsr
    except httpx.HTTPError as exc:
        log.error("tsa.unreachable: %s", exc)
        return None
