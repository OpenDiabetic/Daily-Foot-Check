from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

_SHARED = Path(__file__).parent.parent / "shared" / "qc_constants.json"
_QC = json.loads(_SHARED.read_text())


class Settings(BaseSettings):
    # inference
    vllm_base_url: str = "http://medgemma:8000/v1"
    model_id: str = "google/medgemma-1.5-4b-it"
    inference_timeout_s: float = 60.0
    max_image_bytes: int = _QC["max_image_bytes"]

    # prompt (pinned + hashed; hash is anchored with every report)
    prompt_path: Path = Path(__file__).parent.parent / "prompts" / "foot_check_v2.txt"

    # QC gate thresholds — SINGLE SOURCE: shared/qc_constants.json (Swift codegen
    # reads the same file). Env overrides exist for lab tuning only; production
    # runs stock so phone and node gates agree.
    qc_min_side_px: int = _QC["min_side_px"]
    qc_min_sharpness: float = _QC["min_sharpness"]
    qc_min_brightness: float = _QC["min_brightness"]
    qc_max_brightness: float = _QC["max_brightness"]
    qc_luma_downscale_max_side: int = _QC["luma_downscale_max_side"]

    # guide writer — Qwen3.6-35B-A3B (apache-2.0, MoE 35B/3B-active, multimodal,
    # 262K ctx) + foot-guide LoRA on PRO 6000, :8093.
    # Card-official Instruct/non-thinking sampling: temp 0.7, top_p 0.80,
    # top_k 20, min_p 0, presence 1.5, repetition 1.0. We nudge temp to 0.6 for
    # authoring determinism; guided_json owns structure so presence 1.5 is safe.
    writer_base_url: str = "http://guidewriter:8000/v1"
    writer_model_id: str = "Qwen/Qwen3.6-35B-A3B"    # + LoRA adapter once trained
    writer_lora_name: str = ""
    writer_temperature: float = 0.6
    writer_top_p: float = 0.80
    writer_top_k: int = 20
    writer_min_p: float = 0.0
    writer_presence_penalty: float = 1.5
    writer_repetition_penalty: float = 1.0
    writer_timeout_s: float = 180.0
    writer_prompt_path: Path = Path(__file__).parent.parent / "prompts" / "guide_writer_v1.txt"

    # anchoring
    anchor_enabled: bool = False           # flip on in prod
    anchor_flush_seconds: int = 86_400     # daily batch
    hedera_topic_id: str = ""              # e.g. "0.0.XXXXXXX"
    hedera_operator_id: str = ""
    hedera_operator_key: str = ""          # ED25519 private key (env only)
    tsa_url: str = "https://freetsa.org/tsr"
    anchor_out_dir: Path = Path("/tmp/anchors")  # tmpfs — receipts are re-derivable

    model_config = {"env_prefix": "FOOTCHECK_", "env_file": ".env"}

    @property
    def prompt_text(self) -> str:
        return self.prompt_path.read_text()

    @property
    def prompt_sha256(self) -> str:
        return hashlib.sha256(self.prompt_text.encode()).hexdigest()

    @property
    def writer_prompt_text(self) -> str:
        return self.writer_prompt_path.read_text()

    @property
    def writer_prompt_sha256(self) -> str:
        return hashlib.sha256(self.writer_prompt_text.encode()).hexdigest()


@lru_cache
def get_settings() -> Settings:
    return Settings()
