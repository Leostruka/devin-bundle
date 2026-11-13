# WiCi One + inferssd - eval note

Source reel: subtil DfYM2PORDDg (reels batch-5 survey,
`.devin/research/2026-11-07-reels-batch5-survey.md`). Evaluated
2026-11-07.

## What it is

WiCi One (wici.ai/wici-one): "first wireless GPU" - RTX 5060 Ti 16GB
($2,599; early access $1,999) or RTX 5090 32GB, Wi-Fi 7 4x4 MIMO +
proprietary WiCi Protocol/AirLink. Correction to reel: apps run on the
client device; a driver exposes WiCi One as a local GPU, plus SDK +
OpenAI-compatible API. Pre-order, ships ~Q4 2026. Vendor: systems
research lab (Zili Meng HKUST, Yibin Shen), Shokz-backed, NVIDIA
Inception. Coverage: Gizmodo/PCMag/WIRED/IEEE Spectrum (Oct 5-6 2026).

Caveats: Wi-Fi 7 ~11.5Gbps vs Thunderbolt 4 32Gbps; performance claims
are company demos, not independent benchmarks.

OSS component: `github.com/wici-ai/inferssd` (~350 stars, Apache-2.0) -
llama.cpp-based engine streaming MoE experts from SSD; powers "WiCi
Infer" desktop app.

## Bundle fit

`inferssd` is the only directly reusable piece: SSD-offloaded MoE
inference could extend the local-inference lane (`skills/ai-tools`,
laya extensions, `extensions/` local model surfaces). Hardware itself is
out of scope - no bundle surface consumes a wireless GPU.

## Recommendation

**Track hardware; evaluate inferssd only if a local-inference need
materializes.** No action now; revisit if local MoE offload becomes a
requirement. Do not add as a dependency speculatively.
