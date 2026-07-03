"""Single-shot MedGemma 1.5 call via vLLM's OpenAI-compatible endpoint.

Doctrine:
- One shot. MedGemma is not evaluated for multi-turn — we never chat with it.
- temperature 0, closed schema, vLLM guided_json constrains decoding.
- Validate with Pydantic. One repair retry (with the validation error fed
  back), then hard-fail. No silent degradation.
- Image travels as a base64 data URL in the request body: RAM -> socket ->
  GPU. It is never written anywhere.
"""
from __future__ import annotations

import base64
import json

import httpx

from app.config import get_settings
from app.schemas.foot_check import ModelFindings


class InferenceError(RuntimeError):
    pass


def _payload(prompt: str, image_b64: str, repair_hint: str | None) -> dict:
    s = get_settings()
    user_content: list[dict] = [
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
        },
        {"type": "text", "text": prompt},
    ]
    if repair_hint:
        user_content.append(
            {
                "type": "text",
                "text": (
                    "Your previous output failed validation with this error:\n"
                    f"{repair_hint}\nReturn ONLY the corrected JSON object."
                ),
            }
        )
    return {
        "model": s.model_id,
        "temperature": 0.0,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": user_content}],
        # vLLM structured output — decoder literally cannot leave the schema
        "extra_body": {"guided_json": ModelFindings.model_json_schema()},
    }


def _parse(raw: str) -> ModelFindings:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return ModelFindings.model_validate(json.loads(text))


async def analyze(image_bytes: bytes, client: httpx.AsyncClient, view_label: str) -> ModelFindings:
    s = get_settings()
    image_b64 = base64.b64encode(image_bytes).decode()
    prompt = s.prompt_text.replace("{view_label}", view_label)

    repair_hint: str | None = None
    last_err = ""
    for _attempt in range(2):
        body = _payload(prompt, image_b64, repair_hint)
        extra = body.pop("extra_body")
        resp = await client.post(
            f"{s.vllm_base_url}/chat/completions",
            json={**body, **extra},
            timeout=s.inference_timeout_s,
        )
        if resp.status_code != 200:
            raise InferenceError(f"vLLM returned {resp.status_code}: {resp.text[:300]}")

        raw = resp.json()["choices"][0]["message"]["content"]
        try:
            return _parse(raw)
        except Exception as exc:  # validation or JSON error -> one repair pass
            last_err = str(exc)[:400]
            repair_hint = last_err

    raise InferenceError(f"Model output failed validation twice: {last_err}")
