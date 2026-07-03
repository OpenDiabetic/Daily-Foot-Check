"""GuideWriter — Qwen3.5-32B (+ Gold Standard foot-guide LoRA) on the PRO 6000.

Separate lane from MedGemma: different model, different port (8093), different
process. The writer produces a GuideDraft in one shot; two gates run before it
may enter the review queue:
  1. schema (guided_json + Pydantic) — structural
  2. content gate (banned-vocab + provenance integrity) — semantic
A failing draft gets one repair pass, then is flagged for a human, never
silently published.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.config import get_settings
from app.schemas.guide_draft import GuideBrief, GuideDraft

_BANNED = Path(__file__).parent.parent.parent / "shared" / "banned_vocab.txt"


class WriterError(RuntimeError):
    pass


class ContentGateError(WriterError):
    pass


def _load_banned() -> set[str]:
    if _BANNED.exists():
        return {w.strip().lower() for w in _BANNED.read_text().splitlines() if w.strip()}
    # fallback mirrors the pinned prompt's ban list
    return {
        "diagnose", "diagnosis", "disease", "ulcer", "wound", "infection",
        "inflammation", "neuropathy", "ischemia", "gangrene", "cellulitis",
        "necrosis", "prognosis", "risk of", "prescribe", "treatment",
        "urgent", "emergency", "symptom",
    }


def content_gate(draft: GuideDraft, brief: GuideBrief) -> None:
    """Semantic safety net — runs BEFORE the review queue."""
    import re

    banned = _load_banned()
    # roots that inflect — match as prefixes so ulcerated/infected/diagnosed
    # are all caught, not just the base form.
    stems = {"ulcer", "infect", "inflam", "diagnos", "neuropath", "gangren",
             "necros", "prescrib", "amputat", "gangren"}
    # reader-facing surfaces EXCLUDING the fixed disclaimer (which legitimately
    # contains "diagnoses" — the whole point of the product).
    surfaces = [draft.title, draft.bee_body]
    for s in draft.sections:
        surfaces += [s.heading, s.body, s.pull_quote]
    for b in draft.video_beats:
        surfaces += [b.on_screen_text, b.voiceover]
    blob = "\n".join(surfaces).lower()
    hits = sorted(
        w for w in banned
        if re.search(rf"(?<![a-z]){re.escape(w)}(?![a-z])", blob)
    )
    stem_hits = sorted(st for st in stems if re.search(rf"(?<![a-z]){st}", blob))
    all_hits = sorted(set(hits) | set(stem_hits))
    if all_hits:
        raise ContentGateError(f"banned vocabulary in draft: {all_hits}")

    # provenance integrity: graph claims must index real sources
    for gc in draft.graph_claims:
        if not (0 <= gc.provenance_index < len(draft.provenance)):
            raise ContentGateError(
                f"graph_claim provenance_index {gc.provenance_index} out of range"
            )
    # writer must not drop the brief's sources
    if len(draft.provenance) < len(brief.provenance):
        raise ContentGateError("draft dropped provenance entries from the brief")


def _messages(system: str, brief: GuideBrief, repair: str | None) -> list[dict]:
    user = (
        "Write the Field Guide for this brief. Return only the GuideDraft JSON.\n\n"
        + brief.model_dump_json(indent=2)
    )
    if repair:
        user += f"\n\nYour previous output failed a gate:\n{repair}\nReturn corrected JSON only."
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


async def write_guide(brief: GuideBrief, client: httpx.AsyncClient) -> GuideDraft:
    s = get_settings()
    system = s.writer_prompt_text

    repair: str | None = None
    last = ""
    for _ in range(2):
        # Qwen3-32B is a hybrid thinking model — force NON-THINKING for
        # constrained JSON authoring. Belt (chat_template_kwargs) + suspenders
        # (/no_think already in the pinned system prompt).
        body = {
            "model": s.writer_lora_name or s.writer_model_id,
            "temperature": s.writer_temperature,
            "top_p": s.writer_top_p,
            "top_k": s.writer_top_k,
            "min_p": s.writer_min_p,
            "presence_penalty": s.writer_presence_penalty,
            "repetition_penalty": s.writer_repetition_penalty,
            "max_tokens": 4096,
            "messages": _messages(system, brief, repair),
            "guided_json": GuideDraft.model_json_schema(),
            # Qwen3.6 has NO /think soft switch — enable_thinking=False is the
            # only non-thinking mechanism. Do not rely on prompt-side toggles.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        resp = await client.post(
            f"{s.writer_base_url}/chat/completions",
            json=body, timeout=s.writer_timeout_s,
        )
        if resp.status_code != 200:
            raise WriterError(f"writer vLLM {resp.status_code}: {resp.text[:300]}")

        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # defensive: strip any stray <think> block if thinking leaked through
        if "</think>" in raw:
            raw = raw.rsplit("</think>", 1)[1].strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[4:] if raw.startswith("json") else raw
        try:
            draft = GuideDraft.model_validate(json.loads(raw))
            # stamp generation provenance the model shouldn't own
            draft.writer_model_id = s.writer_model_id
            draft.prompt_sha256 = s.writer_prompt_sha256
            content_gate(draft, brief)
            return draft
        except Exception as exc:
            last = str(exc)[:400]
            repair = last

    raise WriterError(f"guide draft failed gates twice: {last}")
