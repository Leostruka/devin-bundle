# devin-bundle

Export + instalador do Devin CLI para sincronizar **todo o setup** entre máquinas.
Empacota skills, regras consolidadas, config, hooks, scripts, MCP e credentials —
e restaura tudo no destino correto via um único comando.

## O que tem dentro

```
devin-bundle/
├── AGENTS.md            # regras consolidadas (13 regras, negative-constraint framed)
├── agents/              # 5 perfis de subagent (architect, debugger, implementer, researcher, reviewer)
├── skills/              # 54 skills (auto-discover, não limitado ao manifest)
├── config.json          # model, theme, attribution (org_id MASKED por padrão)
├── hooks.v1.json        # PreToolUse + PostCompaction + Stop hooks
├── scripts/             # hook Python scripts (check-ai-signature, check-push-green, post-compaction-reminder)
├── mcp_config.json      # MCP server config (tokens MASKED por padrão)
├── credentials.toml     # API keys (ALL values MASKED por padrão)
├── manifest.json        # metadata das skills (name, source, purpose)
├── export.ps1           # exportador Windows (PowerShell)
├── export.sh            # exportador Linux/WSL/macOS (bash)
├── install.ps1          # instalador Windows (PowerShell)
├── install.sh           # instalador Linux/WSL/macOS (bash)
├── .gitattributes       # LF para .sh, CRLF para .ps1
├── .gitignore           # ignora __pycache__, .devin/brainstorm/
└── README.md            # este arquivo
```

## Componentes exportados (8)

| Componente | Origem | Destino | Masking |
|---|---|---|---|
| AGENTS.md | `%APPDATA%\devin\AGENTS.md` | `bundle/AGENTS.md` | não precisa |
| agents/ | `%APPDATA%\devin\agents\*.md` | `bundle/agents/` | não precisa |
| skills/ | `%APPDATA%\devin\skills\*` | `bundle/skills/` | não precisa |
| config.json | `%APPDATA%\devin\config.json` | `bundle/config.json` | org_id → MASKED |
| hooks.v1.json | `%APPDATA%\devin\hooks.v1.json` | `bundle/hooks.v1.json` | não precisa |
| scripts/ | `%APPDATA%\devin\scripts\*` | `bundle/scripts/` | não precisa |
| mcp_config.json | `%APPDATA%\devin\mcp_config.json` | `bundle/mcp_config.json` | env values → MASKED |
| credentials.toml | `%APPDATA%\devin\credentials.toml` | `bundle/credentials.toml` | ALL values → MASKED |

## Regras consolidadas (AGENTS.md)

13 regras, todas framed como negative constraints (evidence-based: arXiv:2604.11088 — positive directives prejudicam, só negatives ajudam individualmente):

1. **Don't start with technology** — start with customer experience, then choose tech.
2. **No AI signatures in deliverables** — never sign commits, files, PRs, releases, or docs with an AI tool.
3. **Don't use outdated or missing skills** — update wrong skills before use; create skills for recurring patterns; prune dead ones.
4. **Don't start non-trivial tasks without skill discovery** — invoke matching skills before touching code.
5. **No push without green** — run local checks before committing; fix failures in the inner loop.
6. **graphify trigger** — `/graphify` runs first.
7. **Execute-first, opinion-silent** — don't reframe, suggest alternatives, or critique clear tasks. Push back only on false premises, irreversible actions, or deliverable-changing ambiguity.
8. **Telegraphic output** — no filler, no preamble, no unsolicited opinions. Short sentences, structured formats. Verbose only for debugging, architecture, or unfamiliar domains.
9. **Don't add observability infrastructure without `observability-quality` skill** — context-dependent, not universal.
10. **Don't execute without planning, don't declare without verifying** — todo list for 3+ step tasks; verify before claiming done; parallelize independent work; read before writing.
11. **Never fail from failures** — resolve them or deliver a working solution. If unsure or not 100% confident, search certified sources until the answer is coherent, rational, and well-founded.
12. **Maximum precision, zero tolerance for partial verification** — every claim verified against primary source by reading it directly. Subagent returns are leads, not answers.
13. **Devin CLI is not a security sandbox** — agent runs with user's permissions. Run untrusted code in external sandbox. Review skills/MCP servers before installing. Guard against reward hacking in self-improvement loops.

## Hooks (3 eventos)

| Evento | Script | Função |
|---|---|---|
| PreToolUse (exec/write/edit) | `check-ai-signature.py` | Bloqueia AI signatures em commits (-m e -F), writes, edits |
| PreToolUse (exec) | `check-push-green.py` | Bloqueia push sem checks verdes |
| PostCompaction | `post-compaction-reminder.py` | Re-prima regras críticas após compaction (counter 5.6%/step compliance decay) |
| Stop | `check-ai-signature.py` | Escaneia staged changes por AI signatures antes de parar |

Evidence: symbolic guardrails = 74% de policies enforceable (arXiv:2604.15579).

## Instalar

### Windows (PowerShell)
```powershell
cd devin-bundle
.\install.ps1                    # instala tudo (skip existing, merge config)
.\install.ps1 -DryRun            # só mostra o que faria
.\install.ps1 -Force             # sobrescreve diferenças
.\install.ps1 -Force -Backup     # sobrescreve salvando backup antes
.\install.ps1 -RestoreSecrets    # também instala credentials.toml (se unmasked)
```
Destino: `%APPDATA%\devin\`

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x install.sh
./install.sh                     # instala
./install.sh --dry-run           # só mostra
./install.sh --force             # sobrescreve
./install.sh --restore-secrets   # instala credentials.toml
```
Destino: `${XDG_CONFIG_HOME:-~/.config}/devin/`

### O que o instalador faz

1. Cria `%APPDATA%\devin\` (ou `~/.config/devin/`) se faltar.
2. **AGENTS.md** — instala se não existe; skip se idêntico; `-Force` para sobrescrever.
3. **agents/** — instala cada perfil `.md`.
4. **skills/** — instala cada skill; skip se idêntica; `-Force` para atualizar.
5. **config.json** — **MERGE** por padrão (preserva `org_id` local, aplica model/theme/etc. do bundle). `-Force` para sobrescrever completamente.
6. **hooks.v1.json** — instala.
7. **scripts/** — instala hook Python scripts.
8. **mcp_config.json** — skip se valores MASKED (tokens não restauráveis). `-Force` para instalar estrutura mascarada.
9. **credentials.toml** — só com `-RestoreSecrets`. Skip se MASKED.
10. Imprime resumo: installed, overwritten, merged, skipped, backups.

## Exportar (regenerar o bundle da máquina fonte)

### Windows (PowerShell)
```powershell
cd devin-bundle
.\export.ps1                    # exporta com secrets MASKED
.\export.ps1 -DryRun            # só mostra o que faria
.\export.ps1 -Commit -Push      # exporta + valida + commita + pusha
.\export.ps1 -NoMask -Commit    # exporta com secrets reais + commita (NÃO pushar para repo público)
```

### Linux / WSL / macOS (bash)
```bash
cd devin-bundle
chmod +x export.sh
./export.sh                     # exporta com secrets MASKED
./export.sh --dry-run           # só mostra
./export.sh --commit --push     # exporta + valida + commita + pusha
./export.sh --no-mask --commit  # exporta com secrets reais + commita
```

### O que o exportador faz

1. **AGENTS.md** — copia do live para o bundle (LF line endings).
2. **agents/** — copia todos os perfis `.md`.
3. **skills/** — **auto-descobre** TODAS as skills no diretório live (não limita ao manifest). Compara hashes, só copia se mudou.
4. **config.json** — copia com `org_id` MASKED (ou real com `-NoMask`).
5. **hooks.v1.json** — copia.
6. **scripts/** — copia hook Python scripts.
7. **mcp_config.json** — copia com env values MASKED (ou reais com `-NoMask`).
8. **credentials.toml** — copia com ALL values MASKED (ou reais com `-NoMask`).
9. **Pre-push validation** (com `-Push`): valida JSON syntax + Python syntax antes de pushar. Aborta se falhar.
10. **Commit** (com `-Commit`): `git add -A && git commit` com mensagem detalhada (skill count + componentes).
11. **Push** (com `-Push`): `git push` após validação passar.

### Secrets masking

| Arquivo | Default | Com -NoMask |
|---|---|---|
| config.json | org_id → MASKED | org_id real |
| mcp_config.json | env values → MASKED | tokens reais |
| credentials.toml | ALL values → MASKED | API keys reais |

**AVISO:** `-NoMask` exporta secrets reais. NUNCA pushar para repo público com `-NoMask`.
Use `-NoMask` apenas para backup local ou transferência direta entre máquinas confiáveis.

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
./install.sh --force          # ou install.ps1 -Force no Windows
```

Para restaurar credentials.toml na outra máquina:
1. Na máquina fonte: `.\export.ps1 -NoMask` (NÃO pushar)
2. Transfira o `credentials.toml` manualmente (USB, scp, etc.)
3. Na máquina destino: `.\install.ps1 -RestoreSecrets`

## Atualizar o bundle

Depois de mudar skills/regras/config no dia a dia:
1. Rode `.\export.ps1` para sincronizar o bundle com a máquina atual.
2. `.\export.ps1 -Commit -Push` para commitar e pushar em um passo (com validação).

O instalador é idempotente — rodar de novo só atualiza o que mudou (com `-Force`).

## Skills (54)

O bundle auto-descobre todas as skills em `%APPDATA%\devin\skills\`. O `manifest.json` contém metadata (name, source, purpose) para referência, mas a lista de skills exportadas é determinada pelo diretório live, não pelo manifest.

### Skills unificadas (3)

| Skill unificada | Fonte A | Fonte B | Lógica de decisão |
|---|---|---|---|
| `tdd` | test-driven-development (iron law) | tdd (seams, vertical slices) | Seams-first para ONDE; iron law para COMO. |
| `code-review` | requesting-code-review (subagent dispatch) | code-review (two-axis Standards vs Spec) | Subagent dispatch para contexto; two-axis para metodologia. |
| `grilling` | brainstorming (one question at a time) | grilling (design tree, frontier rounds) | Brainstorm para explorar; grill para stress-testar. |

### Skills adaptadas (2)

| Skill adaptada | Fonte original | O que mudou |
|---|---|---|
| `mutation-testing` | `chunk-testing-gaps` (CircleCI) | Local-first com CI opcional. |
| `debug-ci-failures` | `debug-ci-failures` (CircleCI) | CI-agnostic: GitHub Actions, CircleCI, GitLab, Jenkins. |

### Skills adaptadas do PrimeAgent/RLM (7)

Adaptadas de pesquisa verificada contra fontes primárias (arXiv:2512.24601, arXiv:2605.09998, arXiv:2603.02615, PrimeAgent blog/GitHub, ARC Prize leaderboard). Ver `primeagent-reference` skill para o mapa completo de verificação.

| Skill | Fonte PrimeAgent/RLM | Adapção para Devin CLI |
|---|---|---|
| `context-folding` | RLM (arXiv:2512.24601) — prompt-as-variable, REPL, recursive sub-queries | Offload para arquivo + grep/partition + subagent_explore (depth=1 only). Depth=2+ causa overthinking (arXiv:2603.02615: 3.6s→344.5s). |
| `refine` | Continual Harness (arXiv:2605.09998) — `/refine` CRUD edits no harness | Trajectory review → small evidence-backed edits em skills/rules/agents/hooks. Base prompt imutável. Reward hacking guard (Factorio lesson). Auto-trigger via Stop hook + `.refine-pending` marker. Outcome tracking via `refinements.log.jsonl`. |
| `autonomous-gates` | PrimeAgent `--autonomous-gate` (PrimeAgent blog) | Gates definidos no planning, executados após cada step, final gate antes de declarar done. Bounded output, idempotent, no-change skip. |
| `primeagent-reference` | Todas as fontes verificadas | Reference card: 9/9 features adaptadas (3 direct, 3 emulated, 1 partial, 2 guardrails), key numbers, erros do vídeo corrigidos. |
| `a2a-mailbox` | PrimeAgent A2A messaging (PrimeAgent blog) | Filesystem as message broker. Mailboxes per agent. Sequential A2A via file routing. Emula `agent_message.send()`. Limitação: não real-time, não persistent handles. |
| `session-checkpoint` | PrimeAgent daemon-backed reattach (PrimeAgent blog) | Structured checkpoint file (todos, decisions, files, verification, next actions). New session reads e resumes. Emula `prime-agent attach`. Limitação: não real-time reattach. |
| `heartbeat` | PrimeAgent `/heartbeat` + `schedule` (PrimeAgent blog) | OS scheduler (Task Scheduler/cron) + heartbeat script launches new Devin CLI session. In-session nudges via PostToolUse hook. Limitação: não re-enters existing session. |

### Status de adaptação: 9/9 features

- **3 direct adaptations** (context-folding, autonomous-gates, Rule 13): feature maps cleanly to Devin CLI runtime
- **3 emulated adaptations** (a2a-mailbox, session-checkpoint, heartbeat): pattern preserved via file-based workarounds, each documents limitations vs PrimeAgent
- **1 partial** (skills as Python packages): already supported by Devin CLI's `scripts/` directory
- **2 guardrails** (refine + reward hacking guard): adapted with safety mechanisms
