# Card: DgLtA_qSr5D - squid5090 + inference-optimisation skill

URL: https://www.instagram.com/maestrosdaiahub/reel/DgLtA_qSr5D/ | channel: maestrosdaiahub | date: 20261125

VISUAL: `frames/DgLtA_qSr5D_01.jpg`/`_02.jpg` show a tensorfish post: point Gemini 4 Neon at the RTX 5090, leave it alone, return to a zero-dependency Zig + sm_120a CUDA inference engine; squid5090 branding; >275 tokens/s and 370-440 tok/s claims; 1M context in 22.7 GiB VRAM; a GitHub screenshot for `tensorfish/squid5090`; a separate skill card for agent hill-climbing of decode/speculative decoding/prefill/KV/startup/TTFT on any hardware/quantization.

CITED: `tensorfish/squid5090`; `sybil-solutions/inference-optimisation-skill`; Gemini 4 Neon; RTX 5090; llama.cpp. External verification: `external/squid5090_README.md`, `external/inference_skill.md`, `external/inference_levers.md`, `github_repo_snapshot.json`. squid5090 exists (257 stars, license NOASSERTION); the skill exists (MIT, 2,750 stars). Search also found no independent runtime replication; benchmark numbers remain author-reported.

CLAIMS: squid5090 is single-binary/zero-Python Zig+CUDA for Inkling-2-Mini on RTX 5090 (README observed). Author benchmark table reports 312-545 tok/s depending mode/task and quality metrics; reel's "4x llama.cpp" and "1M context without spill" are self-reported, not independently verified. The optimisation skill's method is directly observed: theoretical ceiling first, one change at a time, interleaved controls, ledger, stability/quality gates, clean pinned publication.

PAIN-VOCAB: "testar uma mudança de cada vez, medir e só manter o que ficou mais rápido"; "qualquer placa e qualquer modelo local" (`transcript_digest.md` lines 49-63).

BUNDLE-RELEVANCE: Highest-value process import. `performance` is generic; `continuous-improvement` has evidence discipline but not hardware ceilings, thermal/noise controls, GPU serialization, memory-cap watchdogs, long-context stability gates, or lossless-output equivalence checks. This is directly relevant to local-model operation, `ai-tools`, `laya`, and cost/performance governance.

EVIDENCE-QUALITY: observed=10 self-reported=7 unverified=2
