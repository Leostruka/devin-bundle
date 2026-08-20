# Skill Tiers — discovery rápido por domínio

Skills por domínio de uso + custo (tok = bytes÷4). Só custam quando invocadas.
Use isto (~1700 tok) em vez de `skill list` (~1600 tok) — categorizado por domínio.

## Núcleo (raciocínio lógico, qualquer trabalho)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `tool-and-skill-discovery` | Encontra skill certa + instala/avalia externas | 1000 | Início de tarefa |
| `using-skills` | Guia de uso de skills antes de qualquer ação | 800 | Antes de ação não-trivial |
| `writing-plans` | Spec → plano task-by-task | 1500 | Antes de implementar complexo |
| `executing-plans` | Executa c/ checkpoints | 1200 | Implementação estruturada |
| `context-folding` | Doc grande em 200k (offload+grep) | 2500 | Doc/log > 50k tok |
| `context-window-hygiene` | clear vs compact | 1200 | Contexto apertando |
| `mcp-context-audit` | Custos de tool defs dos MCPs | 1500 | Antes de adicionar MCP |
| `mcp-lazy-enablement` | Enable/disable MCP por tarefa | 1400 | MCP ativo mas não usado |
| `dispatching-parallel-agents` | Subagents têm 200k próprio + plan execution | 9700 | 2+ tarefas independentes |
| `verification-before-completion` | Não declarar pronto sem verificar | 800 | Antes de "terminei" |
| `tdd` | Test-first | 2000 | Feature/bugfix |

Raramente >3 por tarefa (~5000 tok).

## Context tools (scripts, não skills — rodam automaticamente)

| Tool | Faz | Quando |
|---|---|---|
| `context-budget.py` | Mede tokens de AGENTS.md (SessionStart) | Automático no início |
| `context-budget.py --full` | Mede AGENTS.md + MCP + skills dir + model-aware thresholds | Manual, auditoria |
| `context-pressure.py` | Estima crescimento cumulativo de contexto (PostToolUse) | Automático pós-tool |
| `context-pressure.py --report` | Relatório de pressão atual | Manual, checar contexto |
| `data/model-context-windows.json` | Tabela de modelos + context windows + thresholds | Referência para scripts |

## Documentação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `writing-for-agents` | Docs que agentes consomem | 2000 | Escrever skill/regra/doc |
| `domain-modeling` | Glossário, ADRs, bounded contexts | 1750 | Modelar domínio |
| `planning-pipeline` | Spec + Tickets + Questionnaire (3 modos) | 3000 | Conversa → spec/tickets/quest |
| `writing-skills` | Criar skills c/ TDD | 6548 | Criar skill (pesada) |

## Programação

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `implement` | Implementa de spec/tickets | 1500 | Spec existe |
| `code-review` | Review 2-eixos | 2509 | Antes de merge |
| `receiving-code-review` | Avalia feedback sem acordo performático | 5000 | Recebeu review |
| `codebase-design` | Módulos profundos, seams | 2750 | Designar arquitetura |
| `improve-codebase-architecture` | Deepening p/ AI-nav | 1750 | Refatorar navegabilidade |
| `prototype` | Código descartável p/ design question | 625 | Dúvida de design |
| `mutation-testing` | Gaps de teste | 2000 | Testes passam, suspeita gaps |

## Debug

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `diagnosing-bugs` | Pipeline 6-fases unificado (classifica + root-cause) | 4500 | "Debug this", bug não óbvio |
| `debug-ci-failures` | Diagnóstico跨 builds/jobs/envs | 2000 | CI failing |

## Git/GitHub

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `git-helper` | Branches, commits, workflow | 1500 | Perguntas git simples |
| `gh` | GitHub CLI c/ JSON | 4000 | Issues, PRs, Actions |
| `finishing-a-development-branch` | Testes + opções de integração | 5000 | Branch completa |
| `using-git-worktrees` | Worktree isolado | 4250 | Isolar feature |
| `resolving-merge-conflicts` | Resolve conflito traçando intent | 325 | Merge/rebase conflict |

## Jira

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `jira` | Jira via MCP atlassian | 1500 | Interagir c/ Jira (requer MCP) |
| `triage` | State machine de triagem | 2750 | Triar issues/PRs |

## Obsidian e organização de arquivos

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `obsidian-workflow` | Build + Reorganize + Audit + Cross-session (4 modos) | 14674 | Qualquer operação Obsidian |

Custo alto. Invoque só quando for operação Obsidian real.

## Planejamento/decisão

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `wayfinder` | Mapa de decision tickets | 2936 | Trabalho > 1 sessão |
| `grilling` | Stress-test de ideia (3 modos: default, stateless, with-docs) | 2400 | Design/plan ser desafiado |

## Pesquisa

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `research` | Subagent investiga c/ citações | 300 | Investigação c/ fontes |
| `context7` | Docs atualizadas de libs | 2000 | Pergunta sobre lib |

## Meta (gestão de sessão)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `ask-matt` | Router idea-to-ship | 2871 | Não sabe qual skill |
| `handoff` | Compacta p/ outro agente | 375 | Passar trabalho |
| `wait-what` | Re-explica mensagem | 125 | Reexplicar |
| `autonomous-gates` | Gates p/ modo autônomo | 4000 | "Run unattended" |
| `memory-hygiene` | Stateless vs managed vs naive memory | 1600 | Decidir auto-memory / MEMORY.md |
| `effort-calibration` | Calibrar effort à dificuldade | 2400 | Over-thinking / escolher effort |

## Setup (one-time)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `setup-matt-pocock-skills` | Configura repo p/ skills eng | 3000 | Setup inicial |
| `setup-pre-commit` | Husky + lint-staged | 1000 | Pre-commit hooks |
| `self-extend` | Adiciona skill/hook/MCP/regra | 4500 | Evoluir Devin CLI |

## Artefatos de pesquisa (não uso diário — PrimeAgent/RLM)

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `primeagent-reference` | Reference card + A2A + Refine + Subagent Router (4 modos) | 7875 | Pesquisar PrimeAgent/RLM |

## Outros

| Skill | Faz | Tok | Quando |
|---|---|---|---|
| `teach` | Aprendizado guiado multi-sessão | 2375 | Aprender conceito |
| `wizard` | Scripts p/ procedimentos manuais | 1000 | Provisioning one-off |
| `observability-quality` | Infra de observabilidade c/ evidência | 2285 | Adicionar logging/metrics/tracing |

## Linha lógica para 200k

```
Tarefa → AGENTS.md (~6300 tok, fixo) → leia SKILL-TIERS.md (~1800 tok)
  → identifique domínio → invoque 1-3 skills (~3000-7500 tok)
  → trabalho (50k-150k tok)
  >60% usado? → context-folding (doc) | dispatching-parallel-agents (paralelo) | clear (tarefa mudou)
  → verification-before-completion antes de pronto
```

## Anti-patterns

| Evitar | Alternativa |
|---|---|
| `skill list` sem necessidade | Leia SKILL-TIERS.md |
| `primeagent-reference` sem motivo de pesquisa | Não invocar — é referência |
| MCPs sem usar | Só ativar quando preciso (`mcp-lazy-enablement`) |
| Compact quando precisa do detalhe | `context-folding` |
| `obsidian-workflow` para edição pontual (~14674 tok) | Só para operações Obsidian reais |
| Ignorar `context-pressure.py` warnings | Clear/compact quando avisar |
