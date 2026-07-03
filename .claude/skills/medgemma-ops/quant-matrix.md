# MedGemma 1.5 4B — per-SKU serving matrix
| SKU | Backend | Precision | VRAM | Expected /view | Notes |
|---|---|---|---|---|---|
| RTX 5090 rig (cloud) | vLLM | BF16 | ~10GB w/ KV | 1–3s | prod :8090, util 0.85 |
| RTX PRO 6000 (canary/Bee) | vLLM | BF16 | split 0.45/0.45 | 1–3s | :8091 Bee, :8092 canary |
| DGX Spark | vLLM | BF16 | util 0.5 | 1–2s | LoRA headroom on same box |
| ZimaCube 2 Creator (RTX Pro 2000 16GB) | vLLM | BF16 | util 0.90 | 2–4s | full sovereign appliance |
| Mac mini M4/M4 Pro | llama.cpp server | Q8_0 GGUF | ~5GB unified | 3–6s | OpenAI-compat :8000 |
| Jetson Orin Nano 8GB | Ollama | Q4_K_M | ~3GB | 8–15s | kiosk tier |
| ZimaCube Std/Pro (no GPU) | llama.cpp CPU | Q4 | — | 30s+ | functional fallback only; role=VAULT preferred |
Numbers are planning estimates — replace with measured p50/p95 before publishing.
