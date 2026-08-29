# Skill Tiers — discovery rápido por domínio

Skills por domínio de uso + custo (tok = bytes÷4 do SKILL.md, medido 2026-08-22).
Só custam quando invocadas. Use isto (~1700 tok) em vez de `skill list` (~1600 tok).

## Modelos alvo

| Modelo | Contexto | Uso | Notas |
|---|---|---|---|
| GLM-5.2 High | 200K | Primário (parent) | Thinking mode, tool-use during inference, cache $0.26/M read |
| SWE-1.7 | 262K | Subagent (`model: swe-1-7` pin) | Self-compaction trained, 1000 TPS, **gratuito** |
| SWE-1.6 | 200K | Default subagent router | Sem pin, Devin CLI resolve para SWE-1.6 (docs.devin.ai/cli/subagents) |

Subagents customizados têm `model: swe-1-7` pin → SWE-1.7 Max (262K, **gratuito**, rápido). **NÃO usar `swe` (alias para swe-1.7-lightning, PAGO).
Sem pin, usariam SWE-1.6 (default router, 200K, **pago** $0.5/$2.5 MTok). `subagent_general` herda GLM-5.2 High do parent (**gratuito**). **Evitar `subagent_explore`** (resolve para SWE-1.6 pago) — usar custom `researcher` (gratuito, 262K).

## Núcleo (raciocínio lógico, qualquer trabalho)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `tool-and-skill-discovery` | Encontra skill certa + instala/avalia externas | 1009 | Início de tarefa |
| `using-skills` | Guia de uso de skills antes de qualquer ação | 742 | Antes de ação não-trivial |
| `writing-plans` | Spec → plano task-by-task | 1785 | Antes de implementar complexo |
| `executing-plans` | Executa c/ checkpoints | 535 | Implementação estruturada |
| `context-folding` | Doc grande em 200k (offload+grep) | 1353 | Doc/log > 50k tok |
| `context-window-hygiene` | clear vs compact | 1125 | Contexto apertando |
| `mcp-context-audit` | Custos de tool defs dos MCPs | 884 | Antes de adicionar MCP |
| `mcp-lazy-enablement` | Decide quais MCPs manter ativos | 1163 | Depois de `mcp-context-audit` ou com muitos MCPs |
| `dispatching-parallel-agents` | Subagents têm 262k próprio + plan execution | 10065 | 2+ tarefas independentes |
| `verification-before-completion` | Não declarar pronto sem verificar | 1305 | Antes de "terminei" |
| `unlazy` | Força prova de conclusão, evita "done" vazio | 1048 | Antes de declarar pronto |
| `effort-calibration` | Escolhe nível de raciocínio por dificuldade da tarefa | 2435 | Tarefa parece simples demais ou difícil demais |
| `tdd` | Test-first | 2186 | Feature/bugfix |

Raramente >3 por tarefa (~5000 tok).

## Documentação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `writing-for-agents` | Docs que agentes consomem | 2757 | Escrever skill/regra/doc |
| `domain-modeling` | Glossário, ADRs, bounded contexts | 846 | Modelar domínio |
| `planning-pipeline` | Spec + Tickets + Questionnaire (3 modos) | 2945 | Conversa → spec/tickets/quest |
| `writing-skills` | Criar skills c/ TDD | 6717 | Criar skill (pesada) |

## Programação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `implement` | Implementa de spec/tickets | 109 | Spec existe |
| `code-review` | Review 2-eixos | 2558 | Antes de merge |
| `pr-review` | Review no GitHub via `gh` c/ comentários/sugestões | 1576 | Revisar PR no GitHub |
| `receiving-code-review` | Avalia feedback sem acordo performático | 1564 | Recebeu review |
| `codebase-design` | Módulos profundos, seams | 1579 | Designar arquitetura |
| `improve-codebase-architecture` | Deepening p/ AI-nav | 1489 | Refatorar navegabilidade |
| `prototype` | Código descartável p/ design question | 713 | Dúvida de design |
| `mutation-testing` | Gaps de teste | 1546 | Testes passam, suspeita gaps |

## Debug

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `diagnosing-bugs` | Pipeline 6-fases unificado (classifica + root-cause) | 3678 | "Debug this", bug não óbvio |
| `debug-ci-failures` | Diagnóstico跨 builds/jobs/envs | 1373 | CI failing |

## Git/GitHub

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `git-helper` | Branches, commits, workflow | 303 | Perguntas git simples |
| `gh` | GitHub CLI c/ JSON | 2270 | Issues, PRs, Actions |
| `finishing-a-development-branch` | Testes + opções de integração | 1801 | Branch completa |
| `using-git-worktrees` | Worktree isolado | 1715 | Isolar feature |
| `resolving-merge-conflicts` | Resolve conflito traçando intent | 230 | Merge/rebase conflict |

## Jira

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `jira` | Jira via MCP atlassian | 1639 | Interagir c/ Jira (requer MCP) |
| `triage` | State machine de triagem | 1672 | Triar issues/PRs |

## Obsidian e organização de arquivos

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `obsidian-workflow` | Build + Reorganize + Audit + Cross-session (4 modos) | 17435 | Qualquer operação Obsidian |

Custo alto. Invoque só quando for operação Obsidian real.

## Planejamento/decisão

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `wayfinder` | Mapa de decision tickets | 2938 | Trabalho > 1 sessão |
| `grilling` | Stress-test de ideia (3 modos: default, stateless, with-docs) | 2656 | Design/plan ser desafiado |
| `playbook` | Playbook reutilizável c/ Procedure/Specs/Advice (replica cloud) | 1496 | Tarefa repetida, "make this reusable" |
| `review-cadence` | Decide onde colocar checkpoints de review/planning (shift left/right) | 1217 | Decidir se tarefa pequena pode pular grilling |

## Pesquisa

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `research` | Subagent investiga c/ citações | 171 | Investigação c/ fontes |
| `context7` | Docs atualizadas de libs | 737 | Pergunta sobre lib |
| `deep-mode` | Multi-pass agentic search c/ citações (replica Deep Mode cloud) | 1800 | "Deep search", exploração exaustiva |
| `structured-knowledge-extraction` | Extrai entidades, relações, evidências e proveniência de Markdown/texto para JSON/Markdown versionado sem dependências | ~1124 | Quando estruturar conhecimento de documentos |
| `ai-coding-dictionary` | Definições canônicas para jargão de AI coding | 315 | Alinhar termos como harness engineering, context engineering |

## Data

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `data-analyst` | SQL-first exploration via MCP, schema-aware, charts (replica DANA cloud) | 2100 | Query DB, análise de dados, charts |

## Meta (gestão de sessão)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `ask-matt` | Router idea-to-ship | 3037 | Não sabe qual skill |
| `project-memory` | Captura memória do projeto entre sessões | 1042 | Nota importante que deve persistir |
| `devin-manager` | Audita `.devin/` com scan/explain/diff/doctor/plan | ~974 | Quando `.devin/` precisa de auditoria determinística |
| `memory-hygiene` | Quando e como usar memória cross-session | 1736 | Cross-session memory, context window |
| `handoff` | Compacta p/ outro agente | 219 | Passar trabalho |
| `wait-what` | Re-explica mensagem | 81 | Reexplicar |
| `autonomous-gates` | Gates p/ modo autônomo | 1462 | "Run unattended" |

## Setup (one-time)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `setup-matt-pocock-skills` | Configura repo p/ skills eng | 1754 | Setup inicial |
| `project-setup` | Onboarding geral do projeto Devin | 2622 | Primeira configuração `.devin/` |
| `setup-pre-commit` | Husky + lint-staged | 585 | Pre-commit hooks |
| `self-extend` | Adiciona skill/hook/MCP/regra | 1755 | Evoluir Devin CLI |

## Artefatos de pesquisa (não uso diário — PrimeAgent/RLM)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `primeagent-reference` | Reference card + A2A + Refine + Subagent Router (4 modos) | 10091 | Pesquisar PrimeAgent/RLM |
| `continuous-improvement` | FASE 0 + 10-step self-improvement loop c/ held-out | ~3500 | Melhoria contínua do bundle |

## Design / Frontend

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `impeccable` | Vocabulário de design para interfaces frontend: evita estéticas genéricas, define contexto antes de construir, aplica comandos de design (polish, audit, distill, etc.) | ~1031 | Projetar, refatorar, auditar ou polir UI/UX |

## Infra / Quality / Release

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `deploy` | Deploy, release, rollback e smoke tests | ~400 | Publicar ou promover versão |
| `security-audit` | SAST, dependências, vazamento de segredos | ~450 | Auditar segurança |
| `performance` | Profile, benchmark e otimização | ~400 | Lentidão ou gargalo |
| `a11y-audit` | WCAG, keyboard, screen-reader, contraste | ~450 | Verificar acessibilidade |
| `api-design` | REST/OpenAPI/contract tests | ~500 | Design ou review de API |
| `database` | Schema, migrations, queries, índices | ~450 | Modelagem ou otimização DB |
| `e2e-testing` | Playwright/Selenium/Cypress journeys | ~500 | Testes de jornada crítica |
| `cost-optimization` | Tokens, cache, model routing, MCPs | ~450 | Reduzir custo de inferência |
| `docker` | Build, run, compose, scan de imagens | ~400 | Containers e stacks |
| `i18n` | Traduções, plural, LTR/RTL, formatos | ~450 | Multi-idioma |
| `legacy-refactor` | Strangler-fig, seams, modernization | ~500 | Modernizar código legado |

## Outros

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `teach` | Aprendizado guiado multi-sessão | 2409 | Aprender conceito |
| `wizard` | Scripts p/ procedimentos manuais | 992 | Provisioning one-off |
| `observability-quality` | Infra de observabilidade c/ evidência | 2338 | Adicionar logging/metrics/tracing |

## Linha lógica para GLM-5.2 (200K) + SWE-1.7 (262K)

```
Tarefa → AGENTS.md (~4900 tok, fixo, cache-stable) → leia SKILL-TIERS.md (~1700 tok)
  → identifique domínio → invoque 1-3 skills (~1000-9700 tok)
  → trabalho (50k-150k tok no parent GLM-5.2; 262k por subagent SWE-1.7)
  >60% usado? → context-folding (doc) | dispatching-parallel-agents (paralelo) | clear (tarefa mudou)
  → verification-before-completion antes de pronto
```

GLM-5.2 tem thinking mode (raciocina antes de output) e tool-use during inference
(decide quando usar ferramentas nativamente). SWE-1.7 tem self-compaction treinada
(resume + continua do summary) e 1000 TPS (fan-out barato em wall-clock).

## Anti-patterns

| Evitar | Alternativa |
|---|---|
| `skill list` sem necessidade | Leia SKILL-TIERS.md |
| `primeagent-reference` sem motivo de pesquisa | Não invocar — é referência |
| MCPs sem usar | Só ativar quando preciso |
| Compact quando precisa do detalhe | `context-folding` |
| `obsidian-workflow` para edição pontual (~17435 tok) | Só para operações Obsidian reais |
| Subagent general para pesquisa | Use researcher (SWE-1.7, 262K, gratuito) |
| Pin `model: sonnet` em agents read-only | Pin `model: swe-1-7` → SWE-1.7 Max (262K, gratuito) |
