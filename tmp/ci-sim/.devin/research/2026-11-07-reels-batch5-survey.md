# Reels batch-5 survey (2026-11-07)

11 Instagram links. 3 overlap batch-4 (already surveyed, issues R4-* exist).
8 new. Transcripts: `.devin/scratch/reels-5/transcripts/` (whisper.cpp base;
`--lang pt`/`es` retries for matheusgomes/moxen.studio; airesearches is a
`/p/` carousel: caption + archive used instead of per-clip ASR).

| # | Reel | Conteudo real | Veredito |
|---|---|---|---|
| 1 | charles.unemployed DfXKRDQRBS_ | UI micro-interaction spec (ease-out, 150-250ms dropdowns, stagger 30ms, press .97, exits -20%) | COVERED batch-4 -> R4-02 resolved (frontend-design motion section) |
| 2 | fabianocarvalhojr DfU18clgt3k | LinkedIn growth repo (entrevista -> estrategia -> 20 ideias) | COVERED batch-4 -> R4-06 (social-midia/linkedin) |
| 3 | voxaris_ai DfYbglQxEbl | "Untangle Codebase" skill: duplicacao, wrappers, temp workarounds | COVERED batch-4 -> R4-05 (de-slop codebase mode) |
| 4 | moxen.studio DfYMlgrBQiy | "Parrilla": dashboard onde usuario arrasta widgets, vizinhos abrem com fisica de mola, resize em passos de grid. Serie moxen.cl/recursos/ (vanilla JS, sem deps). Reel so musica | ADAPT -> frontend-design: dashboard-grid/reflow pattern note (P3) |
| 5 | airesearches/p/DfRqGa6DJgh | Carousel semanal "huge week in AI" (~20 clips). Conta 1.43M: newsletter airesearches.tech (beehiiv), arquivo GitHub airesearch-official/AI-Weekly-News, YouTube roundups | ADAPT -> agent-reach/research: fontes de curadoria AI-news (P3) |
| 6 | matheusgomes DcUOPkPzorX | PT: script Python sem LLM que varre dependencias vulneraveis a cada update; pegou lib com submodulos vulneraveis em producao ("seguranca nao se brinca") | ADOPT -> dep-audit script/hook; gap real (security-audit e so checklist) (P2) |
| 7 | talhaxcodes DdMUB4kskYv | Taxonomia de ~22 estilos visuais (claymorphism..wabi-sabi). Match ~1:1 com filtercoffee.dev field guide | ADAPT -> design-intelligence/frontend-design: style-taxonomy reference (P3) |
| 8 | subtil DfYM2PORDDg | Wici One: "primeira GPU wireless" (RTX 5060 Ti/5090, WiFi 7, ~$2.6k, pre-order Q4 2026); apps rodam no client, driver expoe GPU local. Componente OSS: wici-ai/inferssd (Apache-2.0, llama.cpp MoE-via-SSD) | NOTE -> research backlog (hardware nao possuido); inferssd e unico componente reaproveitavel (P3) |
| 9 | kairozmind DfZdE8plZ0A | 5 sinais de upload que parece seguro (adaptado de designmotionhq.com/patterns/file-upload-ux): reacao ao drag-over (3 sinais), progresso honesto % + ETA, retry inline sem re-selecionar, preview como prova, progresso/retry por arquivo | ADOPT -> frontend-design: upload/file-state UX checklist (P2) |
| 10 | noxprojectsx DfXQwlbz13S | "Craft Anything" (storytold/craft-anything, ~20k stars, alpha, MIT/Apache): cola link -> Study/Build/Check clona app/site com claude headless + ~300 inspection tools CLI/MCP. REA (morluto/rea, ~440k stars) ja integrado via rea-ops | EVAL -> research backlog (alpha, overlaps cli-adapter/re-binary domains) (P3) |
| 11 | parthknowsai DfZuDIUOGJZ | Google SLEEP framework: "Language Models Need Sleep" arXiv:2606.03979, fase sleep consolida memoria em pesos (distillation + MoE experts + dreaming RL) | COVERED -> avaliado no follow-up batch-4; registrar ponteiro (P3) |

## Decisoes

- R5-01 dep-audit (P2): matheusgomes, bundle nao tem scanner de CVEs automatizado; security-audit so checklist manual. Issue: script dep-audit (OSV-Scanner/pip-audit/npm audit/cargo audit) + gatilho opcional.
- R5-02 upload-trust (P2): kairozmind, frontend-design nao cobre estados assincronos de upload; checklist concreto com fonte primaria (designmotionhq pattern page).
- R5-03 style-taxonomy (P3): talhaxcodes, ponteiro para field guide de estilos no design-intelligence/frontend-design.
- R5-04 dashboard-reflow (P3): moxen.studio, nota de pattern (spring reflow em grid editavel) em frontend-design.
- R5-05 airesearches-sources (P3): newsletter + GitHub archive como fontes de curadoria; verificar RSS beehiiv `/feed`.
- R5-06 craft-anything-eval (P3): eval note; alpha, domain adjacente a re-binary/cli-adapter.
- R5-07 wici-one-note (P3): hardware eval; inferssd como candidato futuro p/ inferencia local SSD-offload.
- R5-08 sleep-framework-pointer (P3): doc-only, liga reel ao eval batch-4.

## Evidencia

- Transcripts: `.devin/scratch/reels-5/transcripts/*.txt|json` (DcUOPkPzorX.pt.json PT, DdMUB4kskYv.txt, DfZdE8plZ0A.txt, DfXQwlbz13S.txt, DfYM2PORDDg.txt, DfZuDIUOGJZ.txt, DfYMlgrBQiy.es.json = music-only, DfRqGa6DJgh = carousel caption).
- Pesquisas: craft-anything github.com/storytold/craft-anything; REA github.com/morluto/rea; WiCi wici.ai/wici-one + github.com/wici-ai/inferssd; SLEEP arXiv:2606.03979 + research.google blog 2026-10-27; designmotionhq.com/patterns/file-upload-ux; filtercoffee.dev field guide; airesearches.tech + github.com/airesearch-official/AI-Weekly-News; moxen.cl/recursos/.
