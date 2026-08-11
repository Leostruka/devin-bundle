# devin-bundle

Export + instalador do Devin CLI para sincronizar skills e regras consolidadas entre máquinas.
Empacota **só as skills que o Devin usa de fato** + as **regras consolidadas** que você definiu,
e restaura tudo no destino correto via um único comando.

## O que tem dentro

```
devin-bundle/
├── AGENTS.md          # regras consolidadas (7 seções, Devin-focused)
├── manifest.json      # 43 skills + origem + propósito
├── export.ps1         # exportador Windows (PowerShell)
├── export.sh          # exportador Linux/WSL/macOS (bash)
├── install.ps1        # instalador Windows (PowerShell)
├── install.sh         # instalador Linux/WSL/macOS (bash)
├── README.md          # este arquivo
└── skills/            # 43 skills
    │
    │  === Meta / discovery ===
    ├── tool-and-skill-discovery/   # achar skill certa pra qualquer tarefa
    ├── find-skills/                # descobrir e instalar skills novas
    ├── self-extend/                # auto-evoluir: criar tools, hooks, skills
    ├── using-skills/          # invocar skills antes de qualquer resposta
    ├── writing-skills/             # como escrever skills (TDD: RED-GREEN-REFACTOR)
    │
    │  === Git / GitHub ===
    ├── git-helper/                 # workflow git, branches, commits
    ├── gh/                         # padrões pro GitHub CLI
    ├── resolving-merge-conflicts/  # resolver merge conflicts
    ├── using-git-worktrees/        # workspaces isolados com git worktrees
    │
    │  === Design / planning ===
    ├── grilling/                   # UNIFICADO: brainstorming + grilling
    ├── writing-plans/              # plano a partir de spec
    ├── to-spec/                    # conversa -> spec -> issue tracker
    ├── to-tickets/                 # plan/spec -> tracer-bullet tickets
    ├── wayfinder/                  # planejar trabalho enorme como decision tickets
    ├── domain-modeling/            # domain model com CONTEXT.md + ADRs
    ├── codebase-design/            # vocabulário de design de codebase
    ├── grill-with-docs/            # grilling + domain model building
    │
    │  === Implementation ===
    ├── tdd/                        # UNIFICADO: iron-law + seams-first TDD
    ├── implement/                  # build from spec/tickets com TDD + code-review
    ├── prototype/                  # protótipo descartável (HTML) p/ design question
    ├── code-review/                # UNIFICADO: subagent dispatch + two-axis review
    ├── receiving-code-review/      # como receber feedback: verificar antes de implementar
    ├── subagent-driven-development/ # fresh subagent per task + task review + final review
    ├── executing-plans/            # fallback: executar plan sem subagents (checkpoints)
    ├── dispatching-parallel-agents/ # um subagent por problema independente (paralelo)
    ├── finishing-a-development-branch/ # step final: verify tests, merge/PR/keep
    ├── verification-before-completion/ # iron law: no completion claims without evidence
    │
    │  === Debugging / research ===
    ├── systematic-debugging/       # reproduzir, rastrear, isolar root cause
    ├── diagnosing-bugs/            # loop de diagnóstico: red -> minimise -> fix
    ├── research/                   # investigar com fontes primárias citadas
    │
    │  === Architecture ===
    ├── improve-codebase-architecture/  # scan codebase + relatório HTML
    │
    │  === Knowledge / docs ===
    ├── graphify/                   # knowledge graph de qualquer input
    ├── memory-bridge/              # comparar wiki knowledge entre AI tools
    ├── context7/                   # docs atualizadas de libs/frameworks
    ├── writing-for-agents/         # escrever docs para agents (skills, AGENTS.md)
    ├── obsidian-project-docs/      # documentar projetos em Obsidian (SRS, Bases, Canvas, C4/diagramas, logbook)
    │
    │  === Workflow / UX ===
    ├── handoff/                    # compactar conversa para outro agent
    ├── teach/                      # ensinar skill/conceito multi-sessão
    ├── wait-what/                  # re-explicar mensagem que não fez sentido
    ├── to-questionnaire/           # decisão -> questionnaire markdown
    ├── wizard/                     # gerar bash wizard p/ procedimentos manuais
    │
    │  === Testing / CI ===
    ├── mutation-testing/           # ADAPTADO: mutation testing p/ encontrar gaps de teste
    └── debug-ci-failures/          # ADAPTADO: debug de falhas de CI (CI-agnostic)
```

## Regras consolidadas (AGENTS.md)

1. **Customer-first planning** — começar pela experiência do cliente e trabalhar de trás pra frente até a tecnologia (Steve Jobs, WWDC 1997). Obrigatório em qualquer planejamento, criação ou melhoria.
2. **No AI signatures** — nunca citar/assinar Devin em commits, PRs, releases, docs, código.
3. **Skill self-maintenance** — skills são vivas: atualizar, criar, podar. É assim que o Devin vira especialista em qualquer coisa.
4. **Skill/tool discovery** — descobrir e invocar skills no início de tarefas não-triviais.
5. **Functional programming and clean code** — FCIS, pure functions, immutability, pipeline composition, condense and reduce.
6. **Inner-loop validation** — validar (lint, typecheck, test) antes de commitar, enquanto o contexto está quente. Mirror CI localmente. No push without green.
7. **graphify trigger** — `/graphify` ativa o skill graphify antes de tudo.

## Skills unificadas (3)

Três pares de skills que sobrepunham entre conjuntos anteriores de skills foram unificadas em uma só, com lógica de decisão para quando usar qual abordagem:

| Skill unificada | Fonte A | Fonte B | Lógica de decisão |
|---|---|---|---|
| `tdd` | test-driven-development (iron law, red-green-refactor, rationalizations) | tdd (seams, vertical slices, anti-patterns) | Seams-first para decidir ONDE testar; iron law para COMO testar. Ambos na implementação real. |
| `code-review` | requesting-code-review (subagent dispatch, template, when to request) | code-review (two-axis Standards vs Spec, code smells baseline, parallel sub-agents) | Subagent dispatch para preservar contexto; two-axis para metodologia. Ambos no review real. |
| `grilling` | brainstorming (one question at a time, visual companion, design doc, writing-plans) | grilling (design tree, frontier rounds, numbered questions, sub-agents for facts) | Brainstorm para explorar ideia fuzzy; grill para stress-testar design. Ambos em sequência: brainstorm -> grill -> spec. |

## Skills adaptadas (2)

Duas skills do CircleCI `chunk-cli` foram adaptadas para serem CI-agnostic (funcionam sem CircleCLI):

| Skill adaptada | Fonte original | O que mudou |
|---|---|---|
| `mutation-testing` | `chunk-testing-gaps` (CircleCI) | Stage 2 (validation) agora é local-first com CI opcional. Stage 3 (production cross-reference) já era opcional. Renomeado de `chunk-testing-gaps` para `mutation-testing` (nome mais descritivo). |
| `debug-ci-failures` | `debug-ci-failures` (CircleCI) | Generalizado de CircleCI MCP-only para CI-agnostic: GitHub Actions via `gh` CLI, CircleCI via MCP, GitLab via `glab`, Jenkins via CLI, ou logs manuais. Tabela de decisão no topo para qual ferramenta usar. |

**Não absorvidas:** `chunk-sidecar` e `chunk-review` — dependem de infra CircleCI provisionada (chunk CLI + token + sidecar cloud).

## Instalar

### Windows (PowerShell)
```powershell
cd devin-bundle
.\install.ps1              # instala (pula se já igual)
.\install.ps1 -DryRun      # só mostra o que faria
.\install.ps1 -Force       # sobrescreve diferenças sem perguntar
```
Destino: `%APPDATA%\devin\` → `skills\`, `AGENTS.md`

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x install.sh
./install.sh               # instala
./install.sh --dry-run     # só mostra
./install.sh --force       # sobrescreve
```
Destino: `${XDG_CONFIG_HOME:-~/.config}/devin/` → `skills/`, `AGENTS.md`

## O que o instalador faz

1. Cria o diretório `devin/` no local correto da plataforma (se faltar).
2. Copia `AGENTS.md` consolidado sobre o existente (com `-Force` se diferente).
3. Copia cada skill em `skills/<nome>/` para o destino.
   - Se a skill já existe e é idêntica (hash) → pula.
   - Se existe e difere → só sobrescreve com `-Force`/`--force`.
   - Se não existe → instala.
4. Imprime resumo: quantas instaladas, atualizadas, inalteradas.

## Versionar / sincronizar máquinas

Este repo é um repo Git normal:
```powershell
cd devin-bundle
git init
git add -A
git commit -m "initial devin bundle"
git remote add origin <seu-repo>
git push -u origin main
```

Na outra máquina:
```bash
git clone <seu-repo> devin-bundle
cd devin-bundle
./install.sh --force   # ou install.ps1 -Force no Windows
```

## Exportar (regenerar o bundle da máquina fonte)

Depois de mudar skills/regras no dia a dia, regenere o bundle para que ele reflita o estado atual:

### Windows (PowerShell)
```powershell
cd devin-bundle
.\export.ps1                    # copia skills + regras para o bundle
.\export.ps1 -DryRun            # só mostra o que faria
.\export.ps1 -Commit -Push      # exporta + commita + pusha em um passo
```

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x export.sh
./export.sh                     # copia skills + regras para o bundle
./export.sh --dry-run           # só mostra
./export.sh --commit --push     # exporta + commita + pusha
```

O que o exportador faz:
1. Lê `manifest.json` para saber quais skills exportar e onde encontrá-las.
2. Resolve `%APPDATA%`, `%USERPROFILE%`, `~` nos `original_path`.
3. Copia cada skill do local original para `skills/<nome>/` (sobrescreve se mudou).
4. Copia o `AGENTS.md` live (ou `rules.md` fallback) para `bundle/AGENTS.md`.
5. Compara hashes: só copia se o conteúdo mudou (idempotente).
6. Com `-Commit`/`--commit`: faz `git add -A && git commit` com mensagem datada.
7. Com `-Push`/`--push`: faz `git push` depois do commit.

## Atualizar o bundle

Para regenerar a partir da máquina fonte depois de mudar skills/regras:
1. Rode `.\export.ps1` (ou `./export.sh`) para sincronizar o bundle com a máquina atual.
2. Edite `manifest.json` se adicionou/removeu skills (adicione a entrada com `name` + `original_path`).
3. `.\export.ps1 -Commit -Push` para commitar e pushar em um passo.

O instalador é idempotente — rodar de novo só atualiza o que mudou (com `-Force`).
