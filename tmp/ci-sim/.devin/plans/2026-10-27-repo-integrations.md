# Integracao de repositorios externos (Stackademic top-10)

Data: 2026-10-27. Fonte: https://blog.stackademic.com/10-best-ai-github-repositories-to-supercharge-your-agent-886aad14e5f6
Milestone: v3.12.0. Issues: #224-#229.

## Matriz de analise (10 itens vs bundle)

| # | Repo | Licenca | Veredito | Racional |
|---|------|---------|----------|----------|
| 1 | anthropics/skills `frontend-design` | Apache-2.0 | INTEGRAR (skill, #224) | SKILL.md standalone; direcao estetica; complementa `impeccable` |
| 2 | latent-spaces/brag | MIT | JA COBERTO (#225 fechada) | `skills/brag/` ja portado (references/scripts/assets, chama `npx hyperframes`); #226 adiciona wrapper governado |
| 3 | heygen-com/hyperframes | Apache-2.0 | INTEGRAR (wrapper, #226) | HTML->MP4 headless `npx hyperframes`; alternativa ao Remotion; dep do brag full |
| 4 | Panniantong/Agent-Reach | MIT | INTEGRAR (wrapper, #227) | JSON CLI; github/youtube/bilibili/v2ex/web sem creds; canais-cookie rejeitados por policy |
| 5 | unclecode/crawl4ai | Apache-2.0 | JA COBERTO | `scrape-tools` ja cobre extracao (TLS-impersonation, CSS/XPath, adaptive selectors); badge de atribuicao obrigatoria e custo |
| 6 | mattpocock/skills | MIT | JA COBERTO | `grill-me` = `grilling` (spec-gate identico); `tdd`/`implement`/`triage`/`research` existem; `pr` ja portado |
| 7 | morluto/rea | MIT | JA COBERTO | `extensions/rea-ops` + `skills/re-binary` + probes red-team ja integram `rea-agents` |
| 8 | jamiepine/voicebox | MIT | INTEGRAR (wrapper, #228) | backend FastAPI :17493 headless; TTS local fecha pipeline asr + animation-direction |
| 9 | debpalash/VoiceStudio | AGPL-3.0 | FORA | AGPL + desktop-GUI-centric; voicebox cobre o caso headless |
| 10 | santifer/career-ops | MIT | INTEGRAR (skill parcial, #229) | modos scan/score/tailor/track portaveis; dashboard Go + auto-submit fora |

## Entregas

- skills/frontend-design, skills/career-ops (markdown)
- extensions/hyperframes + skills/hyperframes (wrapper npx)
- extensions/agent-reach + skills/agent-reach (wrapper, canais sem cred)
- extensions/voicebox + skills/tts (wrapper HTTP :17493)
- manifest.json: 5 entries novas, skill_count 83 -> 88
- testes de contrato: test_hyperframes_wrapper, test_agent_reach_wrapper, test_voicebox_wrapper

## Gates

- audit.py 0 erros (skill frontmatter + manifest sync + skill_count)
- pytest wrapper contracts (sem rede)
- validate-skill-format.py
- export.ps1 -DryRun
- qa-ci independente
