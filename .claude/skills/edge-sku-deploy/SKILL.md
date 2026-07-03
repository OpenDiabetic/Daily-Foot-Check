---
name: edge-sku-deploy
description: Use when deploying, packaging, or debugging Foot Lab on ANY device — ZimaCube 2, ZimaBoard 2, Mac mini, DGX Spark, Jetson Orin Nano, the 5090/PRO-6000 rigs — including compose profiles, mesh roles, mDNS discovery, ZimaOS app packaging, and install scripts.
---

# Edge SKU Deploy — One Repo, Every Device

"The cloud we run is the container you can run" — literal. Same images,
role-tuned compose profiles. Never fork per device.

## Roles
INFER (MedGemma serving) / VAULT (encrypted history) / GATEWAY (mDNS beacon,
QC, Bee, anchor batcher, routing) / SENSE (wearables, device-side).
Role via FOOTCHECK_ROLE; gateway-only nodes 503 local /v1/check with an
actionable message and forward to the strongest discovered INFER peer.

## SKU map → device-matrix.md
Foot Lab One = ZimaCube 2 Creator Pack (RTX Pro 2000): full appliance,
INFER+VAULT+GATEWAY, the flagship. ZimaBoard 2 = $-entry GATEWAY (dual
2.5GbE — can also enforce "footcheck traffic never leaves LAN" at routing
layer). Mac mini = volume INFER+VAULT. DGX Spark = everything + training.
Jetson = kiosk INFER. Provenance: every report carries served_by
{device_class, backend} — never lie about where compute happened.

## Mesh law
Advertise _footlab._tcp with TXT: role, backend, model, prompt_sha256,
version. Discovery health-polls /healthz; INFER preference: dgx > vllm-gpu >
llamacpp > ollama. Failover target: reroute <5s. Prompt-hash mismatch
between peers = refuse to route (split-brain prompts are a silent corruption
vector).

## Packaging
ZimaOS: dist/zimaos manifest, VAULT pre-mapped to /DATA. install.sh detects
hw (nvidia-smi / sysctl / tegra) → picks profile. Every SKU's definition of
done: cold device → first check < 15 min, retention audit clean.
