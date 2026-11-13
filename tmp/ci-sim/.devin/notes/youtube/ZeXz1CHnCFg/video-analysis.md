# Analise: ZeXz1CHnCFg -- 4 open-source tools (OrcDev)

## Ferramentas e vereditos

| # | Tool | O que e | Veredito |
|---|------|---------|----------|
| 1 | interior.dev (ddoemonn) | React micro-interactions (copy button, floating label, password strength, skeleton swap); shadcn-registry style | **Rejeitado** -- fora do dominio do bundle (nao somos frontend) |
| 2 | Social SDK (opencoredev) | `social.post.publish` para X/YouTube/IG/Threads/TikTok/LinkedIn; agent consome "integration checklist" | **Rejeitado** -- posting exige credenciais; contradiz `agent-reach` whitelist (credential-free only) |
| 3 | Ponytail (DietrichGebert) | Ruleset/plugin "least code that works"; comandos review/audit/debt/gain; checklist minimal-diff | **Absorvido parcialmente** -- checklist de 4 perguntas incorporado ao zoom-out do Goldfish (abaixo) |
| 4 | Ghostex (maddada) | Workspace nativo Rust (ghostty) p/ multi-agentes; chat-rendered terminals, multi-conta c/ failover, handoff claude<->codex, delayed actions, worktrees, visibilidade de subagentes | **Rejeitado** -- app externo; features sao do runtime/host, nao de codigo do bundle. `scheduled-turns` ja cobre delayed turns |

## Absorcao Ponytail (implementado)

Checklist minimal-diff integrado ao `zoom-out` do Goldfish Review em:

- `agents/reviewer.md`
- `.devin/agents/repo-reviewer.md`
- `.devin/sdd/goldfish-review.md` (protocolo canonico)

Perguntas: precisa existir? stdlib cobre? dep instalada cobre?
feature nativa cobre? Abstracao nova que falha nas 4 = finding
Important. Comandos ponytail (audit/debt/gain) nao adotados --
cobertos por code-review skill + ledgers existentes.

## Rejeicoes registradas

- Social SDK: escopo credential-free da politica de scraping.
- Ghostex: executavel de terceiro; sem surface de integracao.
- interior.dev: sem projeto frontend neste repo.
