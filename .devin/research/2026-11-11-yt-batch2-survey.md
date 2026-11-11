# YouTube batch-2 survey (2026-11-11)

4 links. Transcripts: `.devin/scratch/yt-batch2/transcripts/` (3 vtt subs +
1 whisper.cpp fallback — KDyPHt4lW60 subs 429'd). Metadata oEmbed-verified.
Deep research: 4 parallel researcher subagents (transcript + web-verify + bundle-fit).

| # | Video | Conteúdo real | Veredito |
|---|---|---|---|
| 1 | DByAR5Su1Yw "make it better" ×100 (Nate Herk) | Forced-iterate experiment: same prompt 100 rounds, "must ship a change every time". Sonnet ~$25/2h plateau@32; Opus $137/8.5h accretion-collapse. Zero web searches in 200 rounds. | **NOTE** — já absorvido (R7-13/#446 → contrato bounded-iteration em impeccable). Residual: eval sem cases |
| 2 | GRlcm3wmOqs LIQUID software factory (IndyDevDan) | TSF demo p/ curso pago: `.tsf/` empty-factory template + skill configure; features reais: budget $/tempo por subagent, summarizer de tool-calls por modelo barato, parity agente↔UI | **EVAL** — gap real: budgets $/tempo por subagent (P3) |
| 3 | vSCYL8ySh9g Dory looped transformer (Witteveen) | NVIDIA Dory1.0-4B nGPT looped (16/40/16, k elástico). Já avaliado: eval #441 dory-loop-sweep → DEFER (CPU −14pts, 20-110× latência) | **NOTE** — eval feito; residual: gotchas do fork p/ ai-tools |
| 4 | KDyPHt4lW60 31 ways Claude 2027 (Nick Saraev) | Catálogo de casos; fact-check externo: só 17/31 reais (8 parciais, 6 astroturfados). Playbooks replicáveis: device-repurpose, saas-replacer. Traço comum dos reais: agente tinha como verificar o próprio trabalho | **EVAL** — 2 playbooks viram skills (P2) |

## Verificações externas

- Self-Refine = arXiv:2303.17651 (vídeo 1 é a variante forced-iterate).
- TSF não é público; proxy: `disler/super-simple-software-factory` (MIT, ~1K★).
- Dory: arXiv:2611.03998; pesos `nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-*` OpenMDW-1.1; vLLM PR #60149; GGUF key `dory.num_loops` ≠ HF `n_recurrent_loops` (silent fallback queimou 1 sweep).
- Anthropic Project Deal real: 69 agentes, 186 deals (anthropic.com/features/project-deal). Levels SaaS purge real (levels.io). Router-8x/DJI-drone/BlackBerry/Airbnb-sweep = **astroturf** (chooseto.ai fact-check) — não codificar.

## Issues

| Issue | Origem | Pri | Escopo |
|---|---|---|---|
| device-repurpose playbook skill | vídeo 4 | P2 | pipeline recon(UART/ADB/web-admin/fw)→strip→UI própria→verify; ancora em devin-integrate + firmware-probe + computer-use cu_adb_backend |
| saas-replacer skill | vídeo 4 | P2 | inventário de assinaturas→ranking de substituibilidade→clone mínimo self-hosted + manutenção agendada |
| per-subagent cost/time budgets | vídeo 2 | P3 | `max_cost_usd`/`max_minutes` em validate-tool-args + agent-cost-guard + ledger |
| eval cases p/ bounded-iteration | vídeo 1 | P3 | `.devin/evals/design-iteration-loop/` tem só README — cases.json + report.json (lint-count ↓ monótono, held-out verde) |

NOTE-only: vídeo 3 (eval DEFER já registrado); agent-negotiation (transporte
api-bridge existe, demanda especulativa); astroturfed cases registrados como
anti-fontes.

## Aplicado direto (sem issue)

- ai-tools SKILL.md: nota sobre gotchas do Dory fork (GGUF vs HF key names).
