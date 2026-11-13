# Reels batch-6 survey (2026-11-08)

4 Instagram links, all new (no overlap with batches 2-5). Transcripts:
`.devin/scratch/reels-6/transcripts/` (whisper.cpp base, EN; PT retry not
needed - content is EN-narrated or PT-ASR-garbled but legible).

| # | Reel | Conteudo real | Veredito |
|---|---|---|---|
| 1 | ox8erlin DfeIuzRMHn5 | "Roon": framework UI em Rust (time do OpenCode), renderer GPU proprio, headless -> agentes renderizam UI tree->PNG, inspecionam elementos, injetam mouse/teclado p/ testar UIs desktop sem tela | EVAL -> computer-use/cu-realtime: headless UI verification path (P3) |
| 2 | odaviandrei DfcYqoux0CH | Teardown privacidade Samsung TV: ACR capturando tela a cada 0.5s, mic ambiente via devices pareados, compartilhamento com advertisers; Samsung respondeu parcialmente | NOTE - consumer privacy, nao e material de bundle |
| 3 | drclaudiomessias DfcSO5Cj3Su | "MiroFish": simula milhares de personas sinteticas em rede social falsa p/ testar ideias; #1 GitHub, investido pela Shanda (¥30M); "termometro, nao milagre" - LLMs interpretam, nao sao clientes reais | EVAL -> ux-researcher/data-analyst (M2_15): synthetic-user idea validation (P3) |
| 4 | ronaldlsb DfA1mcmPRnB | Root na LG TV webOS: removeu ACR/telemetria, abriu SSH, detalha sandbox por-app; videos de exploits ja publicados | NOTE - consumer privacy/hardening, nao e material de bundle |

## Decisoes

- R6-01 roon-eval (P3): headless Rust UI renderer e o unico caminho viavel
  p/ agentes verificarem UIs sem display real (CI, VMs, remote). Bundle ja
  tem rust-core (PyO3) e computer-use (precisa de tela). Eval: viabilidade,
  licenca, se substitui/complementa CU, ou se e so mais um renderer.
- R6-02 mirofish-eval (P3): validacao de ideias com personas LLM e adjacente
  aos perfis ux-researcher/data-analyst criados em M2_15; risco conhecido =
  respostas sinteticas nao sao clientes reais (proprio reel admite).
  Eval: o que daria p/ medir sem cair em falsa confianca.

Sem issues para reels 2 e 4 (privacidade de consumo - registrar-only).

## Evidencia

- Transcripts: `.devin/scratch/reels-6/transcripts/*.txt|json`.
- Pesquisa pendente nos evals: github do Roon (time OpenCode), repo
  MiroFish, terms dos devices Samsung/LG TV citados.
