# Reels batch-4 survey (2026-11-06)

5 reels + 1 model topic. Transcripts: `.devin/scratch/reels-4/transcripts/` (ASR local, pt).

| # | Reel | Conteudo real | Veredito |
|---|---|---|---|
| 1 | science_in_8bit DfWlPu3FTcE | "direction > model": anticipation, release, smear frames, easing in 2s, negative space; studio vende direcao | ADAPT -> animation-direction vocab |
| 2 | qendresahhoti DeZ4sI6hZTZ | HF: mesmo modelo, harness diferente -> 62% vs 33% em 4 coding agents; treinado cross-harness melhorou em todos | DOC -> harness-as-moat note (bundle E um harness) |
| 3 | charles.unemployed DfXKRDQRBS_ | UI micro-interaction spec: ease-out entrances, dropdown 150-250ms, stagger rows 30ms, press scale .97, exits -20%, popover .95, trigger-origin, layoutId, rubber-band | ADOPT -> frontend-design motion checklist |
| 4 | fabianocarvalhojr DfU18clgt3k | LinkedIn growth repo (entrevista -> estrategia -> 20 ideias, 100M impressoes) | COVERED (social-midia -> linkedin submodule) |
| 5 | voxaris_ai DfYbglQxEbl | "Untangle Codebase" skill: detecta duplicacao, wrappers, temp workarounds acumulados | PARTIAL -> de-slop codebase-wide mode |
| 6 | SWE-2-Flash (topico) | Cognition 2026-11-04: post-train Inkling-Small 276B/12B MoE Apache 2.0; Devin Desktop+CLI; free ate 11/30; 1/5 preco, ~200tok/s vs 60; sem API/pesos publicos | ADOPT -> bundle-models.json + MODEL-GUIDE |

## Decisoes

- R4-01 SWE-2-Flash: entrada em data/bundle-models.json + MODEL-GUIDE (routing medium/low effort na janela free; caveats: benchmarks self-reported, sem API).
- R4-02 Micro-interactions: spec quantificado -> secao em frontend-design (gap real: sem motion spec).
- R4-03 Motion vocabulary: anticipation/smear/negative-space -> animation-direction.
- R4-04 Harness-moat: nota de posicionamento (README/ARCHETYPE-MAP) citando o experimento HF.
- R4-05 Slop audit: de-slop ganha modo codebase-wide (dup logic, wrappers, temp fixes acumulados) - hoje e diff-scoped.
- R4-06 LinkedIn: covered por social-midia; apenas registrar.

## Follow-up research (2026-11-06)

R3-02 waitlist items unblocked - both artifacts exist now:

| Item | Real identity | State | Bundle fit |
|---|---|---|---|
| "OpenVQ" | volcengine/OpenViking (ByteDance) | Apache OSS, 41.6k stars, v0.5.3, very active | context-DB viking:// (memory+RAG+skills); candidate backend if .devin/memory/ outgrows flat files |
| Google Artemis | google/artemis | Apache-2.0, 16.7k stars, no tagged releases (pin SHA) | MCP-native Android automation; overlaps cu_adb_backend; needs mcp-governance review if adopted |

Queued input also evaluated: SLEEP framework (Google Research 2026-10-27) = periodic memory consolidation; analogs already in bundle (memory hooks + self-improvement; dreaming ~ create/maintain-verification-skill). PHP/Laravel sources listicle = agent-reach rss feed candidates. criador-de-devin-app skill shipped (R4-07) + reels-surveyor dogfood app.
