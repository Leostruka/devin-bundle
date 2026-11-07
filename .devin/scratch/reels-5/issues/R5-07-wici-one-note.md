# research note: WiCi One wireless GPU + inferssd

status: ready-for-agent
priority: P3
source: reels batch-5 survey, subtil DfYM2PORDDg

## Evidence

Transcript (`.devin/scratch/reels-5/transcripts/DfYM2PORDDg.txt`, PT): "Wici.ai criou um jeito de rodar placa de video pelo wifi": a device with just a GPU streaming its OS for gaming/local AI over WiFi.

Verified (research 2026-11-07): WiCi One (wici.ai/wici-one), "first wireless GPU": RTX 5060 Ti 16GB ($2,599; early access $1,999) or RTX 5090 32GB, Wi-Fi 7 4x4 MIMO + proprietary WiCi Protocol/AirLink. Correction to reel: apps run on the client device; a driver exposes WiCi One as a local GPU (plus SDK + OpenAI-compatible API). Pre-order, ships ~Q4 2026. Company: systems research lab (Zili Meng HKUST, Yibin Shen), Shokz-backed, NVIDIA Inception. Coverage: Gizmodo/PCMag/WIRED/IEEE Spectrum (Oct 5-6 2026). Caveats: Wi-Fi 7 ~11.5Gbps vs Thunderbolt 4 32Gbps; performance claims are company demos.

OSS component: `github.com/wici-ai/inferssd` (~350 stars, Apache-2.0): a llama.cpp-based engine streaming MoE experts from SSD; powers "WiCi Infer" desktop app. Only directly reusable piece for the bundle (local-inference lane: `skills/ai-tools`, laya extensions).

## Task

Write `.devin/research/wici-one-eval.md`: product facts vs reel claims, inferssd assessment (does SSD-offloaded MoE inference fit the bundle's local-ML surfaces, ai-tools/laya-tools?), recommendation (track hardware; evaluate inferssd only if a local-inference need materializes). Update `.devin/research/INDEX.md` if it catalogs evals.

## Acceptance

- [ ] Eval note with dated facts and explicit recommendation
- [ ] inferssd fit analysis against actual bundle inference surfaces (cite skill/extension names)
