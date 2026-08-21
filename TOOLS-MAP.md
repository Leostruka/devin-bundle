# Tools Map — mapeamento completo do runtime

Mapeia TODAS as ferramentas, subagentes, hooks, e configs do Devin CLI
runtime vs o que o bundle cobre. Fonte: docs.devin.ai + runtime observado
(2026-08-20, Devin CLI v3000.4.25).

## Ferramentas do runtime (25 ativas + 2 modo-dependentes)

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

**Cobertura: 19/27 ferramentas com validator + hook matcher. 8 excluídas
(trivial/no-op: get_output, write_to_process, kill_shell, read_subagent,
close_browser_preview, mcp_list_tools, mcp_list_servers, apply_patch,
exit_plan_mode) — o tool falha claramente sem validação do hook.**

## Subagentes (7 perfis)

| Perfil | Tipo | Modelo | Tools | Bundle agent file |
|---|---|---|---|---|
| `subagent_explore` | Built-in | SWE-1.6 (default router) | Read-only + web_search | — (built-in) |
| `subagent_general` | Built-in | GLM-5.2 (parent) | Full (fg) / pre-approved (bg) | — (built-in) |
| `architect` | Custom | SWE-1.7 (`model: swe-1-7`, gratuito) | read, grep, glob, web_search, webfetch, mcp_* | `agents/architect.md` |
| `debugger` | Custom | SWE-1.7 (`model: swe-1-7`, gratuito) | read, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write | `agents/debugger.md` |
| `implementer` | Custom | SWE-1.7 (`model: swe-1-7`, gratuito) | read, write, edit, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write, notebook_*, mcp_* | `agents/implementer.md` |
| `researcher` | Custom | SWE-1.7 (`model: swe-1-7`, gratuito) | read, grep, glob, web_search, webfetch, mcp_* | `agents/researcher.md` |
| `reviewer` | Custom | SWE-1.7 (`model: swe-1-7`, gratuito) | read, grep, glob, exec, get_output | `agents/reviewer.md` |

**Estratégia de modelo:**
- `subagent_explore` (built-in): SWE-1.6 via default router (Devin CLI docs)
- Custom agents: `model: swe-1-7` pin → SWE-1.7 Max (262K, 1000 TPS, **gratuito**). NÃO usar `swe` (alias pago)
  - Sem pin, custom agents usariam SWE-1.6 (default router), não SWE-1.7
- Para trabalho que precisa GLM-5.2: usar `subagent_general` (herda parent) ou
  pin `model: glm-5-2` no agent

**VALID_PROFILES no validate-tool-args.py:**
architect, debugger, implementer, researcher, reviewer, subagent_explore,
subagent_general — todos os 7 perfis validados.

## Hooks (6 eventos, 11 scripts)

| Evento | Matcher | Script(s) | Função |
|---|---|---|---|
| PreToolUse | `^exec$` | destructive-gate.py | Bloqueia ops destrutivas |
| PreToolUse | `^exec$` | check-ai-signature.py | Bloqueia assinaturas AI |
| PreToolUse | `^exec$` | check-push-green.py | Bloqueia push sem green |
| PreToolUse | `^(write\|edit)$` | check-ai-signature.py | Bloqueia assinaturas AI em writes |
| PreToolUse | `^(write\|edit)$` | validate-mermaid.py | Valida Mermaid em writes |
| PreToolUse | 19 tool names | validate-tool-args.py | Valida argumentos (ALTK SPARC) |
| PostToolUse | `^(exec\|mcp_call_tool)$` | silent-error-review.py | Revisa erros silenciosos (ALTK scope) |
| PostCompaction | — | constraint-pinning.py | Detecta constraints dropadas |
| UserPromptSubmit | — | constraint-pinning.py | Re-injeta constraints |
| SessionStart | — | constraint-pinning.py | Limpa markers stale |
| SessionStart | — | context-budget.py | Reporta token cost |
| Stop | — | check-ai-signature.py | Verifica assinaturas no fim |
| Stop | — | refine-review-prompt.py | Prompt de refine review |

**Scripts manuais (não-hooks):**
- validate-refinement-evidence.py — verifica refinements.log.jsonl
- validate-skill-format.py — valida formato de skills

## Configs do runtime

| Config | Local (bundle) | Local (live WSL) | Função |
|---|---|---|---|
| AGENTS.md | `./AGENTS.md` | `~/.config/devin/AGENTS.md` | Regras globais (19 regras) |
| config.json | `./config.json` | `~/.config/devin/config.json` | Modelo, hooks, theme |
| mcp_config.json | `./mcp_config.json` | `~/.config/devin/mcp_config.json` | MCP servers |
| hooks.v1.json | `./hooks.v1.json` | `~/.config/devin/hooks.v1.json` | Hooks legacy (backup) |
| credentials.toml | `./credentials.toml` | — | Credenciais (MASKED) |
| agents/ | `./agents/` | `~/.config/devin/agents/` | 5 perfis customizados |
| skills/ | `./skills/` | `~/.config/devin/skills/` | 46 skills |
| scripts/ | `./scripts/` | `~/.config/devin/scripts/` | 11 scripts Python + 1 JS |
| MODEL-GUIDE.md | `./MODEL-GUIDE.md` | — | Guia GLM-5.2 + SWE-1.7 |
| SKILL-TIERS.md | `./SKILL-TIERS.md` | — | Discovery por domínio + custos |
| TOOLS-MAP.md | `./TOOLS-MAP.md` | — | Este arquivo |
| manifest.json | `./manifest.json` | — | Manifesto de export |
| .mcp.json | — (deny rule) | `~/.config/devin/.mcp.json` | MCP config alternativo |

**Configs do runtime NÃO no bundle (não bundleable):**
- System prompt (Devin CLI runtime, injetado pelo CLI)
- Sandbox config (runtime, não persistente)
- Model picker state (runtime UI)
- Editor integration state (Windsurf, VS Code — runtime)
- Session state (conversa, não config)

## MCP Servers

| Server | Bundle mcp_config.json | Tools | Notas |
|---|---|---|---|
| atlassian | ✓ | Rovo MCP (Jira/Confluence) | Requer login — não funciona no WSL sem credenciais Windows |

**Auditoria MCP (arXiv:2606.30317):**
- Tool count por server < 10-15 para >90% accuracy (Claude Haiku)
- 20-30 tools para Sonnet 4
- Atlassian: verificar tool count com `mcp_list_tools` quando logado
- Se >15 tools, considerar `mcp-context-audit` skill

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
tools com side effects — não é o agente pedindo, é o runtime.

## Modelos disponíveis (Devin CLI v3000.4.25)

| model_uid | Label | Provider | Context | Credit mult | Recomendado |
|---|---|---|---|---|---|
| `glm-5-2` | GLM-5.2 High | ZAI | 200K | 1.5 | ✓ (config.json) |
| `glm-5-2-max` | GLM-5.2 Max | ZAI | 200K | 3 | |
| `glm-5-2-max-1m` | GLM-5.2 Max 1M | ZAI | 1M | 6 | |
| `glm-5-2-none` | GLM-5.2 No Thinking | ZAI | 200K | 1 | |
| `glm-5-2-none-1m` | GLM-5.2 No Thinking 1M | ZAI | 1M | — | |
| `swe-1-7` | SWE-1.7 Max | Cognition | 262K | **Free** | Subagent default (gratuito) |
| `swe` | SWE-1.7 Lightning | Cognition | 202K | $2.5/$12.5 | **PAGO** — alias, não usar |
| `adaptive` | Adaptive router | Cognition | — | — | Model router |
| `opus` | Claude Opus (latest) | Anthropic | — | — | |
| `sonnet` | Claude Sonnet (latest) | Anthropic | — | — | |
| `gpt` | GPT (latest) | OpenAI | — | — | |
| `codex` | Codex (latest) | OpenAI | — | — | |
| `gemini` | Gemini (latest) | Google | — | — | |

Short names (`opus`, `sonnet`, `swe`, `codex`, `gemini`) sempre resolvem
para a latest version na família.

## Context budget (200K GLM-5.2)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável)
AGENTS.md                    ~5463 tok (2.73%)
SKILL-TIERS.md (se lido)     ~1782 tok (0.89%)
MODEL-GUIDE.md (se lido)     ~3711 tok (1.86%)
TOOLS-MAP.md (se lido)       ~2478 tok (1.24%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (atlassian)    ~???? tok (medir com mcp-context-audit)
─────────────────────────────────────────────
Total fixo (sem docs opt)    ~5463 tok (2.73%)
Total c/ docs opt            ~13434 tok (6.72%)
Disponível para trabalho     ~186551-194537 tok (93.28-97.27%)
```

**Nota:** MODEL-GUIDE.md, TOOLS-MAP.md e SKILL-TIERS.md são leituras
opcionais (não carregam automaticamente). AGENTS.md é fixo.
