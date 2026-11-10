# Tools Map - mapeamento completo do runtime

Mapeia TODAS as ferramentas, subagentes, hooks, e configs do Devin CLI
runtime vs o que o bundle cobre. Fonte: docs.devin.ai + runtime observado
(versão validada: `3000.11.234` em `data/bundle-identity.json`).

## Ferramentas do runtime (26 ativas + 2 modo-dependentes)

| Ferramenta | Categoria | Hook matcher | Validator | Descrição |
|---|---|---|---|---|
| `read` | File | ✓ | ✓ abs path | Lê arquivo (path absoluto) |
| `write` | File | ✓ | ✓ abs path + parent dir | Escreve/cria arquivo |
| `edit` | File | ✓ | ✓ abs path + old≠new | Edita string exata |
| `apply_patch` | File | — | — (args vary) | Aplica patch (modo-dependente) |
| `notebook_read` | File | ✓ | ✓ abs path | Lê Jupyter notebook |
| `notebook_edit` | File | ✓ | ✓ abs path | Edita célula Jupyter |
| `grep` | Search | ✓ | ✓ regex válida | Busca ripgrep |
| `glob` | Search | ✓ | ✓ pattern | Glob pattern matching |
| `find_file_by_name` | Search | ✓ | ✓ pattern | Busca por nome de arquivo |
| `exec` | Shell | ✓ | ✓ non-empty + no null | Executa comando shell |
| `get_output` | Shell | — | — (trivial: shell_id) | Lê output de shell background |
| `write_to_process` | Shell | — | — (trivial: shell_id) | Escreve em processo interativo |
| `kill_shell` | Shell | — | — (trivial: shell_id) | Mata shell background |
| `web_search` | Web | ✓ | ✓ query não-vazia | Busca web |
| `webfetch` | Web | ✓ | ✓ http(s) URL | Fetch URL |
| `run_subagent` | Subagents | ✓ | ✓ task + profile válido | Spawna subagent |
| `read_subagent` | Subagents | — | — (trivial: agent_id) | Lê output de subagent |
| `skill` | Skills | ✓ | ✓ invoke/list/search | Invoca/descobre skill |
| `todo_write` | Planning | ✓ | ✓ todos + status válido | Gerencia todo list |
| `ask_user_question` | UI | ✓ | ✓ questions + options | Pergunta ao usuário |
| `browser_preview` | Browser | ✓ | ✓ url + name | Abre preview do browser |
| `close_browser_preview` | Browser | — | — (trivial: preview_id) | Fecha preview |
| `request_scope` | Permissions | ✓ | ✓ scope + path | Pede acesso a diretório |
| `mcp_call_tool` | MCP | ✓ | ✓ server + tool | Chama tool MCP |
| `mcp_list_tools` | MCP | — | — (no required args) | Lista tools MCP |
| `mcp_list_servers` | MCP | — | — (no required args) | Lista servers MCP |
| `mcp_read_resource` | MCP | ✓ | ✓ server + uri | Lê resource MCP |
| `exit_plan_mode` | Planning | — | — (no required args) | Sai do Plan mode (modo-dependente) |

**Cobertura: 19/28 ferramentas com validator + hook matcher. 9 excluídas
(trivial/no-op: get_output, write_to_process, kill_shell, read_subagent,
close_browser_preview, mcp_list_tools, mcp_list_servers, apply_patch,
exit_plan_mode) - o tool falha claramente sem validação do hook.**

## Subagentes (17 perfis)

| Perfil | Tipo | Modelo | Tools | Bundle agent file |
|---|---|---|---|---|
| `subagent_explore` | Built-in | Default router (veja `data/bundle-models.json` aliases) | Read-only + web_search | — (built-in) |
| `subagent_general` | Built-in | Herda parent (`BUNDLE_DEFAULT_MODEL` (`swe-2-high`)) | Full (fg) / pre-approved (bg) | — (built-in) |
| `architect` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, grep, glob, web_search, webfetch, mcp_* | `agents/architect.md` |
| `debugger` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write | `agents/debugger.md` |
| `implementer` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, write, edit, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write, notebook_*, mcp_* | `agents/implementer.md` |
| `researcher` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, grep, glob, web_search, webfetch, mcp_* | `agents/researcher.md` |
| `reviewer` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, grep, glob, exec, get_output | `agents/reviewer.md` |
| `qa-ci` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read-only + exec (verify only) | `agents/qa-ci.md` |
| `red-team-lead` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | red-team skills + offsec wrappers | `agents/red-team-lead.md` |
| `product-manager` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, write, edit, grep, glob, exec, web_* | `agents/product-manager.md` |
| `tech-lead` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, write, edit, grep, glob, exec, web_search | `agents/tech-lead.md` |
| `art-director` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, write, edit, grep, glob, exec | `agents/art-director.md` |
| `security-auditor` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, write, edit, grep, glob, exec | `agents/security-auditor.md` |
| `scrum-master` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read, write, edit, grep, glob, exec | `agents/scrum-master.md` |
| `copywriter` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, write, edit, grep, glob, exec | `agents/copywriter.md` |
| `thermo-nuclear-review-subagent` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read-only + exec (verify only) | `agents/thermo-nuclear-review-subagent.md` |
| `thermo-nuclear-code-quality-review-subagent` | Custom | Max (`BUNDLE_MAX_MODEL` (`swe-2-max`)) | read-only + exec (verify only) | `agents/thermo-nuclear-code-quality-review-subagent.md` |
| `chief-of-staff` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, write, exec, grep, glob, find_file_by_name | `agents/chief-of-staff.md` |
| `sentinel` | Custom | Medium (`BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) | read, exec, grep, glob, find_file_by_name | `agents/sentinel.md` |

**Estratégia de modelo:**
- `subagent_explore` (built-in): default router do CLI — verifique `data/bundle-models.json` aliases; evite em modo free.
- Custom agents: pin `BUNDLE_MAX_MODEL` (`swe-2-max`) (Max) ou `BUNDLE_MEDIUM_MODEL` (`swe-2-medium`) (Medium), conforme `data/bundle-models.json` e as variáveis `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL`. NÃO usar aliases pagos não verificados (veja `data/bundle-models.json`).
  - Sem pin, custom agents usam o default router do CLI (possivelmente pago).
- Para trabalho que precisa do parent: usar `subagent_general` (herda parent) ou pin `model: swe-2-high` no agent.

**Contrato do registro (`data/bundle-models.json`):** todo `model:` pin em
`agents/*.md` deve resolver para um `model_uid` declarado no registro; pins
com `cost_tier: paid` exigem justificativa documentada. Overrides por
instalação vivem nas env vars `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL` /
`BUNDLE_DEFAULT_MODEL`. Hoje o contrato é convenção (AGENTS.md rule 20 +
MODEL-GUIDE.md); enforcement via `audit.py` e validação de overrides no
render está planejado.

**VALID_PROFILES no validate-tool-args.py:**
architect, art-director, chief-of-staff, copywriter, debugger,
domain, implementer,
issue-tracker, product-manager, qa-ci, red-team-lead, researcher,
reviewer, scrum-master, security-auditor, subagent_explore,
subagent_general, tech-lead, thermo-nuclear-code-quality-review-subagent,
thermo-nuclear-review-subagent, sentinel, triage-labels. 22 perfis
validados (parity com `agents/*.md` garantida por
`tests/validation/test_profile_parity.py`).

## Hooks (8 eventos, 12 entry points, 52 scripts)

Duas camadas: `hooks.v1.json` liga 11 entry points consolidados; cada
entry point agregador executa seus scripts internos num único processo
via `scripts/_hookrun.py` (merge rules em `.devin/docs/HOOKS-PIPELINE.md`,
fluxo em `.devin/docs/diagrams/hook-event-flow.md`). Scripts internos
NUNCA são ligados diretamente em `hooks.v1.json` (ver
`.devin/adr/006-hook-consolidation.md`); a fonte única é `hooks.v1.json`,
renderizada para `config.json.hooks` no install (ver
`.devin/adr/005-hooks-single-source.md`).

| Evento | Matcher | Entry point | Scripts internos (ordem) | fail_closed |
|---|---|---|---|---|
| PreToolUse | `^exec$` | `pre-exec-guard.py` (300s) | destructive-gate, architecture-gate, check-ai-signature, check-push-green, validate-tool-args, no-em-dash, laya-guard | sim |
| PreToolUse | `^(write\|edit\|notebook_edit)$` | `pre-write-guard.py` (90s) | always: architecture-gate, validate-tool-args, no-em-dash; + check-ai-signature, validate-mermaid apenas em `write`/`edit` | sim |
| PostToolUse | `^(exec\|mcp_call_tool)$` | `post-exec.py` (30s) | silent-error-review, context-pressure, compact-gate, memory-post-exec, gh-pr-assignee, stuck-detect | não |
| PostToolUse | `^exec$` | `dep-audit-gate.py` (35s) | dep-audit install pre-filter + scanner check; [DEP-AUDIT] additionalContext em findings; fail-open | não |
| PostToolUse | `^(write\|edit)$` | `memory-post-edit.py` (10s) + `compact-gate.py` (15s) + `file-size-guard.py` (warn) | entry points diretos (sem agregador) | não |
| PostCompaction | (nenhum) | `constraint-pinning.py` (5s) | direto; evento canônico de pinning | não |
| UserPromptSubmit | (nenhum) | `user-prompt.py` (20s) | constraint-pinning, behavioral-nudge, memory-retrieval, skill-picker, compact-gate | não |
| SessionStart | (nenhum) | `session-start.py` (10s) | constraint-pinning, context-budget | não |
| Stop | (nenhum) | `stop-guard.py` (25s) | check-ai-signature, refine-review-prompt, memory-stop, no-em-dash | não |
| SessionEnd | (nenhum) | `memory-stop.py` (5s) | direto | não |
| PermissionRequest | (nenhum) | (array vazio) | nenhum hook ligado | não |

Merge semantics (`_hookrun.run`): qualquer `decision: block` vence (a
razão do primeiro blocker é preservada; exit 2 propaga);
`additionalContext` concatena na ordem; `updatedInput` faz shallow-merge;
stdout não-JSON vai para stderr; um script interno que falha é fail-open
(log em stderr, não bloqueia). `fail_closed: true` na entrada do
hooks.v1.json cobre apenas falha do próprio entry point.

**Eventos disponíveis no runtime mas não utilizados pelo bundle:**
- `PermissionRequest`: dispara quando o agente precisa de decisão de permissão. Matcher em `tool_name`. Ligado com array vazio (documenta intenção de não interceptar).
- `PreCompact` (3000.11.92): dispara antes da compactação; matcher `manual`/`auto`; falhas não bloqueiam. Não ligado: nenhum script do bundle precisa agir antes da compactação; `compact-gate.py` já decide o trigger antes.
- `PostCompact` (3000.11.92): contrato novo, coexiste com `PostCompaction` (legacy, ainda suportado). `PostCompaction` é o evento canônico do pinning hoje; `PostCompact` fica deliberadamente desligado para não disparar `constraint-pinning.py` duas vezes por compactação. Se o CLI deprecar `PostCompaction`, migrar o matcher para `PostCompact` com um marker por `session_id` para idempotência.

**Campos de hook novos (3000.11.205 / 3000.11.234):**
- `fail_closed: true` na entrada do hook: falha do próprio hook bloqueia a ação guardada. Adotado nos dois matchers `PreToolUse` (verificado empiricamente); demais hooks seguem fail-open.
- `stop: "<reason>"` no output: encerra o turn a partir de qualquer evento (Claude-format `continue: false`/`stopReason` também lido).
- `hookSpecificOutput.updatedInput` (PreToolUse): mescla argumentos reescritos antes da execução da tool.
- `hookSpecificOutput.updatedToolOutput` (PostToolUse): reescreve o resultado da tool antes do modelo ler (redaction).
- `session_id` e `prompt_id` no stdin de todos os eventos (`prompt_id` rotaciona a cada prompt do usuário e fica ausente antes do primeiro prompt, ex.: `SessionStart`).

**Campos/superfícies de hook novos (3000.12.17):**
- `ContextInput`: hooks podem observar texto repassado ao contexto (ex.: relatórios de subagentes). Changelog-only até agora; sem consumer no bundle.
- `PostToolUse`: quando o resultado é truncado, o payload passa a incluir o path do output completo; candidato para `post-exec.py`/`silent-error-review` lerem o arquivo em vez do texto inline.
- `UserPromptSubmit` agora dispara também em transferência de task via `/handoff`; `constraint-pinning.py` cobre o canal cloud.

**Scripts manuais (não-hooks):**
- validate-refinement-evidence.py — verifica refinements.log.jsonl
- validate-skill-format.py — valida formato de skills
- spec-consistency.py - checa drift plano/ADR/ledger vs repo (gate manual, stdlib-only)

## Configs do runtime

| Config | Local (bundle) | Local (Devin home) | Função |
|---|---|---|---|
| AGENTS.md | `./AGENTS.md` | `~/.config/devin/AGENTS.md` | Regras globais (20 regras) |
| config.json | `./config.json` | `~/.config/devin/config.json` | Modelo, hooks, theme |
| mcp_config.json | `./mcp_config.json` | `~/.config/devin/mcp_config.json` | MCP servers |
| hooks.v1.json | `./hooks.v1.json` | — (renderizado em `config.json.hooks` no install) | Fonte única de hooks (`.devin/adr/005-hooks-single-source.md`); também template `.devin/` |
| credentials.toml | `./credentials.toml` | — | Credenciais (MASKED) |
| agents/ | `./agents/` | `~/.config/devin/agents/` | 21 perfis user-level |
| .devin/agents/ | `./.devin/agents/` | — | 4 perfis project-local + README (ver `.devin/agents/README.md`) |
| skills/ | `./skills/` | `~/.config/devin/skills/` | 182 skills |
| extensions/ | `./extensions/` | `~/.config/devin/extensions/` | Utilitários locais (`computer-use` — GUI automation; `system-control` — OS autorizado; `scrape-tools` — fetch/parse web via Scrapling, ver `extensions/scrape-tools/USAGE.md`; `asr` — whisper.cpp local; `gcal` — Google Calendar free/busy + roteiro + escrita `add`/`apply` (gated por `--confirm`); `code-graph` — índice estrutural FTS5; `harness-tree` — árvore c1..c8 diff/validate/snapshot; `design-intelligence` — BM25 + corpus design 34 domínios) |
| scripts/ | `./scripts/` | `~/.config/devin/scripts/` | 52 scripts Python + 1 JS |
| docs/ (dissolvida) | `./.devin/{docs,plans,templates}/` | `~/.config/devin/docs/` | Documentação do bundle |
| MODEL-GUIDE.md | `./.devin/docs/MODEL-GUIDE.md` | `~/.config/devin/docs/MODEL-GUIDE.md` | Guia de modelos (veja `data/bundle-models.json`) |
| SKILL-TIERS.md | `./.devin/docs/SKILL-TIERS.md` | `~/.config/devin/docs/SKILL-TIERS.md` | Discovery por domínio + custos |
| TOOLS-MAP.md | `./.devin/docs/TOOLS-MAP.md` | `~/.config/devin/docs/TOOLS-MAP.md` | Este arquivo |
| manifest.json | `./manifest.json` | — | Manifesto de export |
| .mcp.json | — (deny rule) | `~/.config/devin/.mcp.json` | MCP config alternativo |

**Ferramentas externas verificadas (não vendored - evals #423-#426):**
- `agent-desktop` (vercel-labs, Apache-2.0, v1.2.0): `npx agent-desktop`
  - percepção UIA/AX-tree p/ desktop apps, refs estáveis, JSON envelopes;
  spike de backend p/ computer-use em #427.
- `stageshow` (benjitaylor/skills, sem licença): `npx skills add
  benjitaylor/skills --skill stageshow` - faux-UI p/ marketing; padrão
  rehearsal-gate documentado em #428.
- `pr-agent` (The-PR-Agent, Apache-2.0/MIT): `pip install pr-agent` -
  reviewer externo via litellm; TRACK até existir provider key (#426).
- `dropstone` (dropstone.io): agente CLI em open weights com lineup
  rotativo; TRACK - lições aplicadas em MODEL-GUIDE.md (#425).

**Configs do runtime NÃO no bundle (não bundleable):**
- System prompt (Devin CLI runtime, injetado pelo CLI)
- Sandbox config (runtime, não persistente)
- Model picker state (runtime UI)
- Editor integration state (Windsurf, VS Code — runtime)
- Session state (conversa, não config)

## MCP Servers

O bundle carrega servidores MCP a partir de `mcp_config.json` no Devin home do usuário. O arquivo `mcp_config.json.example` contém um exemplo de integração de issue tracker; parâmetros de integração (site, cloud ID, enablement) estão em `data/bundle-integrations.json`. Autentique antes de habilitar; credenciais e notas específicas de integração local devem ficar no troubleshooting local, não no bundle global.

**Auditoria MCP (arXiv:2606.30317):**
- Tool count por server < 10-15 para >90% accuracy (Claude Haiku)
- 20-30 tools para Sonnet 4
- Verifique tool count com `mcp_list_tools` quando o servidor MCP estiver logado
- Se >15 tools, considerar `mcp-governance` skill

## Modos do Devin CLI

| Modo | Comando | Comportamento |
|---|---|---|
| Normal | `/normal` | Pede aprovação para tools com side effects |
| Accept Edits | `/accept-edits` | Auto-aprova edits no workspace |
| Smart | `/smart` | Auto-aprova ações que modelo rápido julga seguras |
| Plan | `/plan` | Read-only planning (sem changes) |
| Bypass | `/bypass` | Auto-aprova tudo |
| Autonomous | — | Só em sandbox sessions |

**Nota:** O modo é controlado pelo usuário na UI, não pelo agente. O agente
não escolhe o modo. Em `normal` (default), o runtime pede aprovação para
tools com side effects - não é o agente pedindo, é o runtime.

## Comandos do CLI (3000.11.x)

| Comando | Tipo | Função |
|---|---|---|
| `devin --cloud` / `devin cloud` / `/cloud` | Cloud | Roda sessão Devin Cloud a partir do CLI |
| `devin cloud drs` | Cloud | Gerencia Declarative Repo Setup (blueprints de ambiente, sandbox sessions, builds) |
| `devin connect <CODE>` | Cloud | Conecta esta máquina a uma sessão cloud para local tool use (hidden; ver imagens, copiar arquivos) |
| `/handoff`, `/pickup` | Cloud | Traz branch de PR de sessão cloud para sessão local |
| `devin ssh` / `/ssh` | Cloud | Conecta a uma VM Devin Cloud |
| `devin forward` | Cloud | Port-forward de box cloud → localhost |
| `/goal <objective>` | REPL | Continua trabalhando no objetivo entre turns até completar/bloquear (pausa aos 50 turns; `resume`/`clear`) |
| `/rename [title]` | REPL | Renomeia a sessão; sem argumento gera título a partir do contexto (3000.11.205) |
| `/confetti` | REPL | Animação de celebração (3000.11.205) |
| `/hooks` | REPL | Lista hooks carregados e o arquivo de origem de cada um |
| `devin models` | CLI | Lista os modelos disponíveis na conta |
| `devin desktop [ARGS]...` | CLI | Abre o Devin Desktop correspondente ao canal do CLI |
| `--verbosity <0..3>` (`DEVIN_VERBOSITY`) | CLI flag | Sobrescreve `agent.verbosity` apenas na execução atual (`0` quiet .. `3` verbose) |
| `/billing on\|off` | REPL | Liga/desliga provider billing (modelos com `*` no picker cobram via plano do provider) |
| `Alt+Enter` no `/model` picker | REPL | Troca modelo só na sessão atual (`model_picker.confirm_for_session` rebinda) |
| `/vim` | REPL | Edição Vim no prompt (Esc = Normal mode) (3000.12.17) |
| `Alt+P` / `Alt+N` no `/model` picker | REPL | Pina modelos; pins aparecem primeiro e `Alt+N` cicla sem reabrir o picker (3000.12.17) |
| `permission_mode` em `/config` | REPL | Modo de permissão inicial de novas sessões locais; `--permission-mode` sobrescreve por launch (3000.12.17) |
| `devin mcp list --json` | CLI | Inventário machine-readable de MCP servers (estado, transport, tools desabilitadas) (3000.12.17) |
| `Alt+V` (Windows) / `Ctrl+V`,`Alt+V` (WSL) | REPL | Cola imagens do clipboard (3000.12.17) |
| `/resume` com projeto+idade; `Alt+G` | REPL | Busca por projeto; alterna dir atual vs todos os projetos (3000.12.17) |
| `1`/`2`/`3`/`4` no approval prompt | REPL | Once/Session/Project/Always sem setas (3000.12.17) |
| `devin rules`, `devin skills`, `devin plugins`, `devin doctor` | Config | Gerência nativa de rules/skills/plugins e diagnóstico |

**Nota 3000.11.1:** bloco `otel` no `config.json` ou `OTEL_EXPORTER_OTLP_*`
exportam eventos/métricas para um collector OpenTelemetry; não adotado
(sem collector configurado; `devin doctor` já valida o ambiente).

**Notas 3000.11.205/228/234:**
- `/loop` e `agent.model_mixture` removidos; usar `/goal`. A skill
  `scheduled-turns` usa `devin -p`, não afetada.
- `read_config_from.cloud` (novo): `false` mantém MCPs do Devin Cloud e
  plugins pessoais fora do CLI. Adotado como `false` no bundle.
- `DEVIN_SESSION_STORE=files` (experimental): sessões como arquivos p/
  homes em NFS/SMB. Não adotado (env var).
- `agent.verbosity`: detalhe do transcript (`0..3`). Adotado como `3` em `config.json` (restaura cards completos); `--verbosity` / `DEVIN_VERBOSITY` sobrescreve por sessão (3000.11.234).
- `keymap`: modificadores separados por `-` (`ctrl-4`); validação no startup alerta conflitos/chaves inválidas e reverte para o default.
- Permission prompt mostra a regra exata (`Exec(docker build)`), com
  Allow/Bypass/Deny + duração do grant (`Once`/`Session`/`Project`/`Always`)
  e `e` para editar o comando.
- Steering agora interrompe imediatamente preservando comandos longos.

**Notas 3000.12.17:**
- `/config` salva mudanças sem restart (valem em `/clear`, `/resume`, `/cloud`).
- `UserPromptSubmit` cobre `/handoff`; `PostToolUse` recebe path do output
  completo quando truncado; `ContextInput` observa texto repassado
  (subagent reports); changelog-only até os docs de hooks listarem.
- Fixes relevantes: approvals de plan mostram resumo+path; Accept Edits/Smart
  reconhecem edits em network shares Windows/WSL; `devin -p` continua após
  tool call negada; imagens indecodificáveis não derrubam o turn.

## Modelos disponíveis (Devin CLI `3000.12.17`)

| model_uid | Label | Effort | Context | Custo | Recomendado |
|---|---|---|---|---|---|
| `BUNDLE_DEFAULT_MODEL` (`swe-2-high`) | SWE-2 High (parent) | high | 262K | **Free** | ✓ (config.json) |
| `BUNDLE_MEDIUM_MODEL` (`swe-2-medium`) | SWE-2 Medium | medium | 262K | **Free** | Tarefas simples, ajustes pontuais, scripts isolados |
| `BUNDLE_MAX_MODEL` (`swe-2-max`) | SWE-2 Max | max | 262K | **Free** | Tarefas abertas, refactors globais, long-horizon |
| `swe-2-flash-{medium,high,max}` | SWE-2 Flash | medium/high/max | 262K | **Free** (janela) | Fast lane ~200 tok/s; ver `data/bundle-models.json` + MODEL-GUIDE |
| `paid_model_alias` | Paid alias | — | see registry | see registry | NUNCA usar sem confirmar `data/bundle-models.json` |
| `adaptive` | Paid router | see registry | — | see registry | Não usar em modo free |
| `opus` | Paid model | Anthropic | — | see registry | Não usar em modo free |
| `sonnet` | Paid model | Anthropic | — | see registry | Não usar em modo free |
| `gpt` | Paid model | OpenAI | — | see registry | Não usar em modo free |
| `codex` | Paid model | OpenAI | — | see registry | Não usar em modo free |
| `gemini` | Paid model | Google | — | see registry | Não usar em modo free |

**⚠️ Política CONDICIONAL:** quando o parent está em modelo FREE (lido de `data/bundle-models.json` com `cost_tier: free`), NUNCA usar modelos pagos para subagents. Short names/aliases (`opus`, `sonnet`, `codex`, `gemini` etc.) podem resolver para entradas pagas - verifique `data/bundle-models.json` antes de usar. Use o parent (`BUNDLE_DEFAULT_MODEL` (`swe-2-high`)) e os subagent models (`BUNDLE_MAX_MODEL` (`swe-2-max`) / `BUNDLE_MEDIUM_MODEL` (`swe-2-medium`)) do registro. Quando o parent é pago, subagents podem usar pagos.

## Context budget (parent model)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável)
AGENTS.md                    ~5605 tok (2.80%)
SKILL-TIERS.md (se lido)     ~1782 tok (0.89%)
MODEL-GUIDE.md (se lido)     ~3711 tok (1.86%)
TOOLS-MAP.md (se lido)       ~2478 tok (1.24%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (configured)   ~???? tok (medir com mcp-governance)
─────────────────────────────────────────────
Total fixo (sem docs opt)    ~5605 tok (2.80%)
Total c/ docs opt            ~13576 tok (6.79%)
Disponível para trabalho     consulte `context_window` em `data/bundle-models.json`
```

**Nota:** MODEL-GUIDE.md, TOOLS-MAP.md e SKILL-TIERS.md são leituras
opcionais (não carregam automaticamente). AGENTS.md é fixo.
