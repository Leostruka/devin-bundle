# Skill Tiers - discovery rápido por domínio

Skills por domínio de uso + custo (tok = bytes÷4 do SKILL.md, medido 2026-10-31).
Só custam quando invocadas. Use isto (~3800 tok) em vez de `skill list` (~1600 tok).
Subconjunto curado de alto uso - o índice completo das 185 é `manifest.json`
(`skills[].name`). Skills consolidadas são routers: o SKILL.md é caro de entrada;
detalhe vive em `modes/`/`reference/` e só é lido sob demanda (`+defer`).

**Project-local** (`.devin/skills/`, não distribuídas): `verify-atlas` (dogfood do
GitHub Pages: build, launch, doctor, navegação, evidência - invocação manual),
`rts-3d-procedural-art`, `rts-hud-audio-design` (helpers de arte do projeto).

## Modelos alvo (SWE-2 + Flash, roteamento por nível de esforço)

| model_uid | Effort | Contexto | Uso | Notas |
|---|---|---|---|---|
| `BUNDLE_MEDIUM_MODEL` (default `swe-2-medium`) | Medium | 262K | Tarefas simples, ajustes pontuais, scripts isolados | **gratuito até 2026-11-30** |
| `BUNDLE_DEFAULT_MODEL` (default `swe-2-max`) | Max | 262K | Primário (parent); julgamento, multi-arquivo | **gratuito até 2026-11-30**, default geral |
| `BUNDLE_MAX_MODEL` (default `swe-2-max`) | Max | 262K | Subagent Max (`model:` pin); julgamento, exploração profunda | **gratuito até 2026-11-30** |
| `BUNDLE_FAST_MODEL` (default `swe-2-flash-high`) | High (fast lane) | 262K | Subagent execução bounded (`model:` pin); ~200 tok/s | **gratuito até 2026-12-04 18:00 UTC** |
| `swe-2-flash-medium` | Medium (fast lane) | 262K | Subagent volume mecânico/triagem (`model:` pin) | **gratuito permanente** (`free_tier_permanent`) |

Subagents customizados usam `model: swe-2-max` (julgamento/auditoria), `model: swe-2-flash-high` (execução bounded) ou `model: swe-2-flash-medium` (volume mecânico), conforme `data/bundle-models.json` e as variáveis `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL` / `BUNDLE_FAST_MODEL`. **NÃO usar aliases pagos não verificados** - eles podem apontar para um modelo pago.
Sem pin, os custom agents usam o default router do CLI (possivelmente pago). `subagent_general` herda o parent (`BUNDLE_DEFAULT_MODEL`) quando esse for gratuito. **Evitar `subagent_explore`** - pode resolver para um modelo pago; usar o custom `researcher` (gratuito, veja `data/bundle-models.json`).

## Núcleo (raciocínio lógico, qualquer trabalho)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `skill-discovery` | Encontra skill certa + instala/avalia externas + guia de uso | 861 | Início de tarefa, antes de ação não-trivial |
| `planning` | Spec → plano + tickets + questionnaire + wayfinder (4 modos, +9.8k defer) | 765 | Antes de implementar complexo |
| `execution` | Executa c/ checkpoints, implementa de spec, loop AFK, cadence | 1153 | Implementação estruturada |
| `context-hygiene` | Doc grande em 200k, clear vs compact, custo, esforço | 1191 | Contexto apertando, doc/log > 50k tok |
| `mcp-governance` | Custos de tool defs + quais MCPs manter ativos (+5.8k defer) | 908 | Antes de adicionar MCP |
| `dispatching-parallel-agents` | Subagents têm 262k próprio + plan execution | 10590 | 2+ tarefas independentes |
| `gates` | Prova de conclusão, unlazy ledger, gates autônomos | 1127 | Antes de "terminei" |
| `testing` | Test-first, gaps de teste, mutation (+7.5k defer) | 478 | Feature/bugfix |
| `adaptive-agenda-calendar-routine-engine` | Calendário -> agenda HH:MM estrita, 4 perfis de rotina, fluxo 5 estágios (>=32 ciclos) | ~1.1k | Trabalho em horas/dias/semanas/sprints |

Raramente >3 por tarefa (~5000 tok).

## Documentação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `writing-skills` | Criar skills c/ TDD + docs que agentes consomem (+27k defer) | 706 | Escrever/criar skill, regra, doc |
| `knowledge-modeling` | Glossário, ADRs, bounded contexts, extração e ontologia (+19.8k defer) | 699 | Modelar domínio, estruturar conhecimento |
| `planning` | Spec + Tickets + Questionnaire (modos) | 765 | Conversa → spec/tickets/quest |
| `technical-writing` | Prosa técnica: clareza, estrutura, voz (docs/READMEs) | 2224 | Escrever doc para humanos |

## Programação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `execution` | Implementa de spec/tickets | 1153 | Spec existe |
| `code-review` | Review 2-eixos, PR via `gh`, receber feedback (3 modos, +7.8k defer) | 599 | Antes de merge, revisar/receber PR |
| `blast-radius` | Mapa de impacto do diff: dependentes, contratos, testes afetados | 952 | Antes de merge, mudança em código compartilhado |
| `architecture` | Módulos profundos, seams, deepening, strangler-fig (+3k defer) | 935 | Designar/refatorar arquitetura, legado |
| `prototype` | Código descartável p/ design question | 780 | Dúvida de design |
| `big-file-refactor` | Modularização 3-fases de arquivos >1k linhas | 665 | Arquivo gigante/contexto estourando |
| `cli-adapter` | Controlar tool sem API/MCP via CLI construído (padrão wrapper) | 602 | Tool externa sem integração oficial |
| `criador-de-devin-app` | Intent recorrente -> app nomeado (APP.md + cadence + done-when) | ~1.1k | Criar automação/agente nomeado para devin-cli |
| `roteiro` | Dia real -> roteiro em slots livres (gcal) | ~1.5k | Planejar o dia contra free/busy real |
| `correct` | Correção mínima e direcionada de bug (fix-loop discipline) | 642 | Bugfix pontual sem refatorar |

## Debug

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `debugging` | Pipeline 6-fases unificado + diagnóstico cross builds/jobs/envs (+8.8k defer) | 615 | "Debug this", bug não óbvio, CI failing |

## Git/GitHub

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `git-workflows` | Branches, commits, worktree isolado, conflitos | 813 | Git workflow, isolar feature, merge conflict |
| `gh` | GitHub CLI c/ JSON | 2294 | Issues, PRs, Actions |
| `finishing-a-development-branch` | Testes + opções de integração | 1870 | Branch completa |

## Issue tracker

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `jira` | Issue tracker via MCP configurado (exemplo em `mcp_config.json.example` e `data/bundle-integrations.json`) | 1713 | Interagir c/ issue tracker (requer MCP) |
| `intake` | Triagem + sizing + intenção em tickets (+4.2k defer) | 997 | Triar issues/PRs, estimar PR, validar intenção |

## Obsidian e organização de arquivos

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `obsidian-workflow` | Build + Reorganize + Audit + Cross-session (4 modos, +73k defer) | 17485 | Qualquer operação Obsidian |

Custo alto. Invoque só quando for operação Obsidian real.

## Planejamento/decisão

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `planning` | Mapa de decision tickets (wayfinder mode) | 765 | Trabalho > 1 sessão |
| `grilling` | Stress-test de ideia (3 modos: default, stateless, with-docs, +21.8k defer) | 3508 | Design/plan ser desafiado |
| `playbook` | Playbook reutilizável c/ Procedure/Specs/Advice (replica cloud) | 1516 | Tarefa repetida, "make this reusable" |
| `execution` | Decide onde colocar checkpoints de review/planning (cadence) | 1153 | Tarefa pequena pode pular grilling? |
| `arena` | Torneio: N soluções paralelas, juízes ranqueiam, campeão mergeia | 933 | Decisão aberta com várias opções reais |

## Pesquisa

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `research` | Subagent investiga c/ citações + multi-pass deep search | 651 | Investigação c/ fontes, "deep search" |
| `scan` | Codebase-wide investigation por objetivo (equiv. `/scan` do Devin Cloud): Plan→Shard→Map→Reduce c/ subagents → relatório priorizado em `.devin/scans/` | — | "ache dead code", gaps de teste, auditoria de migração/estilo |
| `context7` | Docs atualizadas de libs | 339 | Pergunta sobre lib |
| `youtube-fetcher` | YouTube URL + caption JSON → transcript raw + metadata em `.devin/notes/youtube/` | 1334 | Ingerir transcript de vídeo fornecido pelo usuário |
| `ai-coding-dictionary` | Definições canônicas para jargão de AI coding | 346 | Alinhar termos como harness engineering |

## Data

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `data-analyst` | SQL-first exploration via MCP, schema-aware, charts (replica DANA cloud) | 1519 | Query DB, análise de dados, charts |

## Meta (gestão de sessão)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `ask-bundle` | Orquestrador universal — classifica objetivo, roteia skills/flows (+8.3k defer) | 1642 | Início de sessão, objetivo vago, orquestração |
| `memory-management` | Memória cross-session: quando/como usar + higiene (+7k defer) | 1092 | Nota a persistir, memory cross-session |
| `devin-config` | Audita `.devin/` (scan/explain/diff/doctor/plan) + adiciona skill/hook/MCP/regra (+15k defer) | 993 | Auditoria `.devin/`, evoluir Devin CLI |
| `handoff` | Compacta p/ outro agente | 262 | Passar trabalho |
| `wait-what` | Re-explica mensagem | 121 | Reexplicar |
| `gates` | Gates p/ modo autônomo | 1127 | "Run unattended" |
| `create-verification-skill` | Gera verify-* skill: invariants + probes + evidence dir | 1620 | Operação repetida precisa de verificação |
| `maintain-verification-skill` | Atualiza verify-* quando o sistema muda | 1206 | Probe quebrou após refactor |
| `afk-loop` | Loop autônomo sobre issues Markdown em DAG (frontier, worktree, TDD) | 975 | Trabalhar issues sem supervisão |
| `autonomous-gates` | Quality gates p/ tarefas long-horizon com acceptance criteria | 1558 | "Autonomous mode", rodada longa |
| `agent-cost-guard` | Custo de tokens por loop, token-maxing, limite de fan-out | 595 | Monitorar custo, paralelismo excessivo |
| `context-folding` | RLM-style folding p/ contexto grande / docs longos | 1552 | Contexto enchendo, compact perde info |
| `context-window-hygiene` | Lost-in-middle, clear-vs-compact, MCP bloat, effort match | 1413 | Agente esquece instruções, contexto apertado |
| `executing-plans` | Executa plano escrito por fases com checkpoints | 993 | Plano aprovado para executar |

## Setup (one-time)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `project-bootstrap` | Onboarding `.devin/` + repo p/ skills eng + pre-commit (+8.6k defer) | 473 | Setup inicial, primeira configuração |
| `devin-config` | Adiciona skill/hook/MCP/regra | 993 | Evoluir Devin CLI |

## Artefatos de pesquisa (não uso diário - PrimeAgent/RLM)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `self-improvement` | PrimeAgent reference (4 modos) + 10-step improvement loop c/ held-out (+15k defer) | 668 | Pesquisar PrimeAgent/RLM, melhoria do bundle |

## Design / Frontend

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `impeccable` | Vocabulário de design para interfaces frontend: evita estéticas genéricas, define contexto antes de construir, aplica comandos de design (polish, audit, distill, etc.) | 1593 | Projetar, refatorar, auditar ou polir UI/UX |
| `brag` | Gera launch video 15-25s do projeto via Hyperframes: inspect → storyboard → compose → render (+refs defer; assets mp3/ogg bundled; needs Node+ffmpeg) | ~2200 | "/brag", launch video, compartilhar o que construiu |
| `camera-blocking` | Direção de câmera para repaint de vídeo: blockout+rig+playblast em Blender headless -> prompt segundo-a-segundo -> hero scroll-bound | ~1800 | Hero de site com câmera, video-to-hero via Seedance-class |

## Infra / Quality / Release

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `deploy` | Deploy, release, rollback e smoke tests | 344 | Publicar ou promover versão |
| `security` | SAST, dependências, segredos + checklist `.env`/endpoints/destruição (+1.2k defer) | 693 | Auditar segurança, antes de commit/deploy |
| `performance` | Profile, benchmark e otimização | 290 | Lentidão ou gargalo |
| `a11y-audit` | WCAG, keyboard, screen-reader, contraste | 303 | Verificar acessibilidade |
| `api-spec` | REST/OpenAPI/contract + specs como contexto para IA | 509 | Design ou review de API |
| `database` | Schema, migrations, queries, índices | 294 | Modelagem ou otimização DB |
| `e2e-testing` | Playwright/Selenium/Cypress journeys | 294 | Testes de jornada crítica |
| `docker` | Build, run, compose, scan de imagens | 398 | Containers e stacks |
| `i18n` | Traduções, plural, LTR/RTL, formatos | 277 | Multi-idioma |
| `benchmark-checklist` | Checklist de perfil/benchmark reproduzível (pstack port) | 1239 | Medir antes/depois com rigor |
| `web-perf-checklist` | Fix-list de ~30 itens de performance web por camada | 1174 | App web lento, audit de perf |
| `security-audit-cf` | Auditoria de segurança completa (STRIDE-ish, workflow por fases) | 5545 | Audit/pen-test pedido explicitamente |
| `shorts-factory` | Pipeline vídeo curto: roteiro, TTS, stock, legenda, ffmpeg | 1553 | Shorts/Reels/TikTok end-to-end |
| `agentic-rag` | RAG agentivo: retrieve -> decision-gate -> answer/escalate | 2015 | Implementar Q&A com evidência |

## Extensões locais (tools, não-skills)

Utilitários executáveis instalados em `~/.config/devin/extensions/` (Windows: `%APPDATA%\devin\extensions\`). Documentação completa vive no `USAGE.md` de cada extensão. Uma extensão pode ter um skill wrapper em `skills/<nome>/` só para auto-descoberta (o SKILL.md aponta de volta para o `USAGE.md`).

| Extensão | Faz | Quando | Docs completas |
|---|---|---|---|
| `computer-use` | Screenshot da tela, clique/movimento de mouse em (X,Y), digitação de texto e atalhos — replica Computer Use do Devin Cloud no CLI. Skill wrapper: `skills/computer-use/` | Automatizar GUI desktop, validar app visualmente, interagir com app sem API | `extensions/computer-use/USAGE.md` |
| `ai-tools` | Ferramentas ML locais offline-first (`abliterator.py`, `prompt_compiler.py`) + playbook de Post-Training, Reasoning Distillation (`s1K`/R1) e RLVR/GRPO — JSON stdout, `--self-test`, sem download. Skill wrapper: `skills/ai-tools/` | Experimentos de interpretabilidade, pós-treinamento, destilação ou RLVR de modelos | `extensions/ai-tools/USAGE.md` |
| `system-control` | Controle autorizado do OS: inventário de processos/serviços, exec one-shot limitada, sessões persistentes, event streams, cópia de arquivo verificada por hash. Deny-wins + confirmações one-shot; sem daemon privilegiado por default. Skill wrapper: `skills/system-control/` | APIs de sistema em vez de GUI computer-use | `extensions/system-control/USAGE.md` |

## Disciplinas de código e shell (novo, portado)

| Skill | Faz | Quando |
|---|---|---|
| `powershell-safe` | Traps do PS 5.1: redirect UTF-16/BOM, read-write mesmo pipe, `$null` apaga, `-LiteralPath` | File I/O via PowerShell, .ps1 |
| `shell-safe` | Análogo bash: same-file redirect, `rm -rf $VAR` vazio, pipefail, glob, tarbomb | Comandos shell, .sh |
| `edge-cases` | Enumerar inputs/estados/falhas antes de codar + self-review adversarial | Feature/bugfix, antes de "pronto" |
| `dead-wire` | Auditoria de feature morta: botão sem destino, evento sem ouvinte, flag sem write path | Auditoria de completude |
| `github-actions` | Segurança CI: SHA pinning, `pull_request_target`, script injection, OIDC | Editar/revisar workflows |
| `webhooks` | Assinatura HMAC, idempotência por event_id, fast-ack + fila | Endpoint de callback de terceiro |
| `typescript-node` | Strict TS, async footguns, ESM/CJS, npm hygiene | Código TS/Node |
| `binary-triage` | Evidência de binário fechado sem Ghidra: strings, exports, getters, ctypes | Comparar builds/engines de libs |
| `ghidra` | RE headless de firmware raw (Thumb/TMode, seeds Capstone) | Firmware `.bin` sem símbolos |
| `dma` | Pentest/recon orquestrado com scope contract + tools stdlib (`/dma`) | Pentest em alvo autorizado |
| `lean-code` | Menor solução que funciona, minimal-diff, YAGNI, anti-bloat | Escrever/revisar código, escolher dependência |
| `no-comments` | Caça comment smells e stale suppressions no diff | Limpar comentários antes de PR |
| `de-slop` | Quality pass completa no diff: simplificar, remover slop | Antes de abrir PR |
| `edge-coverage` | Edge Inventory obrigatório p/ testes: boundary/equivalence | Montar/auditar suíte de testes |
| `tdd` | Red-green-refactor com evidência | Feature/bugfix com teste primeiro |

## Outros

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `teach` | Aprendizado guiado multi-sessão | 2471 | Aprender conceito |
| `wizard` | Scripts p/ procedimentos manuais | 1033 | Provisioning one-off |
| `observability-quality` | Infra de observabilidade c/ evidência | 2370 | Adicionar logging/metrics/tracing |
| `cu-realtime` | Padrões medidos de baixa latência p/ computer-use (espera, batch, reflexo) | 850 | Reação rápida em CU/terminal |

## Linha lógica para parent + subagent

```
Tarefa → AGENTS.md (~4900 tok, fixo, cache-stable) → leia SKILL-TIERS.md (~1700 tok)
  → identifique domínio → invoque 1-3 skills (~500-3500 tok router; modes/ sob demanda)
  → trabalho (50k-150k tok no parent `BUNDLE_DEFAULT_MODEL`; por subagent `BUNDLE_MAX_MODEL`)
  >60% usado? → context-hygiene | dispatching-parallel-agents (paralelo) | clear (tarefa mudou)
  → gates antes de pronto
```

O parent (`BUNDLE_DEFAULT_MODEL`) tem thinking mode (raciocina antes de output) e tool-use during inference
(decide quando usar ferramentas nativamente). O subagent (`BUNDLE_MAX_MODEL`) tem self-compaction treinada
(resume + continua do summary) e alto TPS (fan-out barato em wall-clock). Veja `data/bundle-models.json` para janelas e custos.

## Anti-patterns

| Evitar | Alternativa |
|---|---|
| `skill list` sem necessidade | Leia SKILL-TIERS.md |
| `self-improvement` sem motivo de pesquisa | Não invocar — é referência |
| MCPs sem usar | Só ativar quando preciso |
| Compact quando precisa do detalhe | `context-hygiene` |
| `obsidian-workflow` para edição pontual (~17485 tok) | Só para operações Obsidian reais |
| Subagent general para pesquisa | Use researcher (`BUNDLE_MAX_MODEL`, gratuito, veja `data/bundle-models.json`) |
| Pin `model: pago` em agents read-only | Pin `model: swe-2-max` → subagent Max gratuito (veja `data/bundle-models.json`) |
