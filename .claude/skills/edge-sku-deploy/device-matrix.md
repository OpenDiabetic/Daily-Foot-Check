# Foot Lab SKU / role matrix
| SKU | Hardware | Roles | Backend | Notes |
|---|---|---|---|---|
| Foot Lab One | ZimaCube 2 Creator (i5/64GB/RTX Pro 2000) | INFER+VAULT+GATEWAY | vLLM BF16 util 0.90 | flagship appliance; VAULT on HDD pool /DATA |
| Foot Lab Home | ZimaCube 2 Std/Pro | VAULT+GATEWAY (+INFER w/ PCIe GPU) | llama.cpp CPU fallback | upgrade ramp to One |
| Foot Lab Gateway | ZimaBoard 2 | GATEWAY | none | dual 2.5GbE; LAN-only enforcement point |
| Foot Lab Studio | Mac mini M4/Pro | INFER+VAULT | llama.cpp Q8 / MLX | volume seller |
| Foot Lab Max | DGX Spark | ALL + LoRA training | vLLM BF16 util 0.5 | prosumer/clinic |
| Foot Lab Embedded | Jetson Orin Nano 8GB | INFER | Ollama Q4 | kiosk/waiting room |
| Cloud node | RTX 5090 rig | INFER+GATEWAY | vLLM BF16 util 0.85 | check.opendiabetic.com |
| Canary/Bee | RTX PRO 6000 rig | canary :8092, Bee :8091 | vLLM | prompt regression + failover |
