---
name: medgemma-ops
description: Use when serving, calling, configuring, benchmarking, or debugging MedGemma 1.5 4B anywhere in the fleet — vLLM on rigs, llama.cpp on Mac, Ollama on Jetson, ZimaCube GPU. Also use when choosing quantization, GPU memory splits, ports, or writing inference client code.
---

# MedGemma 1.5 Ops

Model: google/medgemma-1.5-4b-it (HAI-DEF license — accept terms on HF; not a
medical device; owner validates before clinical adjacency). 4B multimodal,
SigLIP encoder trained incl. dermatology. BF16 ≈ 8GB.

## Laws
1. **Single-shot only.** Not evaluated for multi-turn — never chat. One
   image + pinned prompt → JSON → validate → one repair retry → fail.
2. **temperature 0, closed schema.** On vLLM use guided_json (decoder cannot
   leave schema). Other backends: prompt + Pydantic validate/repair.
3. **Prompt sensitivity is real** (more than base Gemma 3). Prompt file is
   pinned + hashed; changes go through golden-set skill.
4. Image travels as base64 data-URL in request body: RAM → socket → GPU.
   Never a path.

## Serving matrix → quant-matrix.md
Quick rules: 5090/PRO 6000/DGX = vLLM BF16; Mac = llama.cpp Q8 GGUF (server
mode, OpenAI-compat); Jetson Orin Nano = Ollama Q4. Ports: prod 8090 (5090),
Bee 8091, canary 8092 (PRO 6000 GPU1). vLLM flags that matter:
`--disable-log-requests` (zero-retention law), `--max-model-len 8192`,
gpu-memory-utilization: 0.85 solo / 0.45+0.45 co-located / 0.90 ZimaCube
Creator (RTX Pro 2000 16GB) / 0.5 DGX (leave LoRA headroom).

## Client pattern
httpx.AsyncClient, per-backend timeouts (vllm 60s, llamacpp 120s, ollama
180s), asyncio.gather for multi-view sessions. Health: poll /health (vLLM)
before routing; mesh picks strongest INFER peer.

## Bench before claiming
`vllm bench serve` with real foot-photo payloads → publish p50/p95 only from
measurement. Co-location stress: hammer both engines, watch for OOM, tune
splits down 0.05 at a time.
