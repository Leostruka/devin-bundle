# Reels batch-8 + web links survey (2026-11-12)

Transcripts: .devin/scratch/reels-8/transcripts/ (12/12 ok, cp1252 mojibake leve - issue filed).
Pipeline: extensions/asr/transcribe.py --lang pt.

| # | Link | Tema | Veredicto |
|---|------|------|-----------|
| R1 | huwprosser DfXwuL0izsO | Busy Bar hardware/dev | COVERED - extensions/busybar shipped (#505) |
| R2 | odyssey.systems | world models (Odyssey-3, Agora-2 multi-agent sim, PROWL-2 agent+world co-curriculum RL) | NOTE - conceitual: evals/sim-training p/ agentes; guardado como referencia de arquitetura de eval |
| R3 | akita rinha final | docker compose + postgres + Gatling + EXPLAIN ANALYZE + pool sizing | ADOPT - issue #567 (load-test playbook) |
| R4 | bobbby.rn DfkUISAMnPb | OpenWorker (Andrew Ng) - co-worker AI, 40+ connectors | NOTE - produto, overlap conceitual c/ gcal+agenda |
| R5 | the.mindloop DfSn_x9gMsx | Vercel Agent Desktop - a11y tree vs screenshots, -84% tokens | ADAPT - issue #568 (computer-use a11y eval) |
| R6 | baptisteodonovan DdEea0wiU1_ | 5 repos: OpenCloud, Invideous, OpenMAPIC, research-academic, Minimite | NOTE - Minimite (treina mini modelo <$0.50) vira pointer p/ ai-tools; resto fora de escopo |
| R7 | ufd_tech DfngW6OjLaN | TaskMon GPU (open-source GPU task manager, NVIDIA/AMD/Intel/Apple) | NOTE - observabilidade GPU p/ local inference |
| R8 | hackedbyilan DfoYtUxsErn | AI hacking learning path (labs/challenges/prompt repo) | NOTE - recursos p/ offsec-tools |
| R9 | devvveloper DfncrVjh-0u | Alto Ontology (NVIDIA) - text-to-SQL business glossary + query history + human cert | ADOPT - issue #569 (data-analyst ontology layer) |
| R10 | asharasjad DfoU9n2Bx0e | Seacore Q3.5 - 4B 3D world model via Ollama/browser | NOTE - pointer p/ ai3d-gen/comfyui |
| R11 | linuxparahackers Dfmwvxattcl | White Rabbit Neo/Deep Hat - uncensored sec AI | NOTE - ja temos offsec-tools+red-team-lead |
| R12 | louis_rlee DfnKmAPIoAW | Roon - native UI toolkit; agent renders PNG + drives clicks | ADAPT - issue #570 (agent-rendered UI eval loop) |
| R13 | gustagoat.ai Dfby7sPgMPU | perf optimization checklist (skeleton, webp/avif, dedup, debounce, pagination, CDN, N+1, brotli, cache, lazy) | ADOPT - issue #571 (perf-checklist skill) |
| R14 | lucasaicreator DfkiN83xND0 | thousand-brains + hybrid small model (Qwen 4B+35B, frozen core + neural adapters, 71tok/s @4GB) | ADAPT - issue #572 (ai-tools adapter eval) |

Achado infra no recon: transcribe.py nao pinna stdout UTF-8 no Windows ->
JSON saiu cp1252 (mojibake em transcricoes PT). Issue #573.

## Outcomes (fechamento 14:35)

- Resolvidos: #567 (PR #575), #569 (PR #575), #573 (PR #574 + #577 audit[42]), #570 (spike validado)
- Covered: #571 (web-perf-checklist), #568 (cu_agent_desktop)
- Backlog: #572 (GPU eval; torch local cpu-only)
- NOTEs viraram pointers duraveis: ai3d-gen/Seacore, red-team/WRNeo, ai-tools/Minimite+TaskMon, devin-integrate/OpenWorker (PR #576)
- Achado infra: transcribe stdout pin -> [42] novo check + 39 arquivos pinados total
- PRs: #574, #575, #576, #577 merged
