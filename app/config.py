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


@lru_cache
def get_settings() -> Settings:
    return Settings()
