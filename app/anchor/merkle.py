"""Minimal sha256 Merkle tree. Leaves are hex digests of report hashes."""
from __future__ import annotations

import hashlib


def _h(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(left + right).digest()


def merkle_root(leaf_hex: list[str]) -> str:
    if not leaf_hex:
        raise ValueError("empty leaf set")
    level = [bytes.fromhex(x) for x in leaf_hex]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [_h(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    return level[0].hex()


def merkle_proof(leaf_hex: list[str], index: int) -> list[tuple[str, str]]:
    """Return [(side, sibling_hex), ...] path for leaf at index."""
    level = [bytes.fromhex(x) for x in leaf_hex]
    proof: list[tuple[str, str]] = []
    idx = index
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        sib = idx + 1 if idx % 2 == 0 else idx - 1
        proof.append(("right" if idx % 2 == 0 else "left", level[sib].hex()))
        level = [_h(level[i], level[i + 1]) for i in range(0, len(level), 2)]
        idx //= 2
    return proof
