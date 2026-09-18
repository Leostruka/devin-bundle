# Tools Map — mapeamento completo do runtime

Mapeia TODAS as ferramentas, subagentes, hooks, e configs do Devin CLI
runtime vs o que o bundle cobre. Fonte: docs.devin.ai + runtime observado
(versão validada: `{{VALIDATED_CLI_VERSION}}` em `data/bundle-identity.json`).

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
exit_plan_mode) — o tool falha claramente sem validação do hook.**

## Subagentes (7 perfis)

| Perfil | Tipo | Modelo | Tools | Bundle agent file |
|---|---|---|---|---|
| `subagent_explore` | Built-in | Default router (veja `data/bundle-models.json` aliases) | Read-only + web_search | — (built-in) |
| `subagent_general` | Built-in | Herda parent (`{{BUNDLE_DEFAULT_MODEL}}`) | Full (fg) / pre-approved (bg) | — (built-in) |
| `architect` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, web_search, webfetch, mcp_* | `agents/architect.md` |
| `debugger` | Custom | Medium (`{{BUNDLE_MEDIUM_MODEL}}`) | read, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write | `agents/debugger.md` |
| `implementer` | Custom | Medium (`{{BUNDLE_MEDIUM_MODEL}}`) | read, write, edit, grep, glob, exec, get_output, write_to_process, kill_shell, todo_write, notebook_*, mcp_* | `agents/implementer.md` |
| `researcher` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, web_search, webfetch, mcp_* | `agents/researcher.md` |
| `reviewer` | Custom | Max (`{{BUNDLE_MAX_MODEL}}`) | read, grep, glob, exec, get_output | `agents/reviewer.md` |

**Estratégia de modelo:**
- `subagent_explore` (built-in): default router do CLI — verifique `data/bundle-models.json` aliases; evite em modo free.
- Custom agents: pin `{{BUNDLE_MAX_MODEL}}` (Max) ou `{{BUNDLE_MEDIUM_MODEL}}` (Medium), conforme `data/bundle-models.json` e as variáveis `BUNDLE_MAX_MODEL` / `BUNDLE_MEDIUM_MODEL`. NÃO usar aliases pagos não verificados (veja `data/bundle-models.json`).
  - Sem pin, custom agents usam o default router do CLI (possivelmente pago).
- Para trabalho que precisa do parent: usar `subagent_general` (herda parent) ou pin `model: {{BUNDLE_DEFAULT_MODEL}}` no agent.

**VALID_PROFILES no validate-tool-args.py:**
architect, debugger, implementer, researcher, reviewer, subagent_explore,
subagent_general — todos os 7 perfis validados.

## Hooks (8 eventos, 18 scripts)

| Evento | Matcher | Script(s) | Função |
|---|---|---|---|
| PreToolUse | `^exec$` | destructive-gate.py | Bloqueia ops destrutivas |
| PreToolUse | `^exec$` | architecture-gate.py | Bloqueia mutações sem manifesto |
| PreToolUse | `^(write\|edit\|notebook_edit)$` | architecture-gate.py | Bloqueia edits sem ARCHITECTURE_MANIFEST |
| PreToolUse | `^exec$` | check-ai-signature.py | Bloqueia assinaturas AI |
| PreToolUse | `^exec$` | check-push-green.py | Bloqueia push sem green |
| PreToolUse | `^(write\|edit)$` | check-ai-signature.py | Bloqueia assinaturas AI em writes |
| PreToolUse | `^(write\|edit)$` | validate-mermaid.py | Valida Mermaid em writes |
| PreToolUse | 19 tool names | validate-tool-args.py | Valida argumentos (ALTK SPARC) |
| PostToolUse | `^(exec\|mcp_call_tool)$` | silent-error-review.py | Revisa erros silenciosos (ALTK scope) |
| PostToolUse | `^(exec\|mcp_call_tool)$` | context-pressure.py | Reporta context pressure e padrões de tools caras (Rule 18) |
| PostToolUse | `^exec$` | memory-post-exec.py | Injeta memórias por symbol/keyword após exec |
| PostToolUse | `^(write\|edit)$` | memory-post-edit.py | Injeta memórias por path após write/edit |
| PostCompaction | — | constraint-pinning.py | Detecta constraints dropadas |
| UserPromptSubmit | — | constraint-pinning.py | Re-injeta constraints |
| UserPromptSubmit | — | behavioral-nudge.py | Nudge behavioral self-check (Rules 7,8,4,17) |
| UserPromptSubmit | — | memory-retrieval.py | Recupera memórias de `.devin/memory/` por cues |
| SessionStart | — | constraint-pinning.py | Limpa markers stale |
| SessionStart | — | context-budget.py | Reporta token cost |
| SessionEnd | — | memory-stop.py | Log do estado de `.devin/memory/` no fim de sessão |
| Stop | — | check-ai-signature.py | Verifica assinaturas no fim |
| Stop | — | refine-review-prompt.py | Prompt de refine review |
| Stop | — | memory-stop.py | Log do estado de `.devin/memory/` |

**Evento disponível no runtime mas não utilizado pelo bundle:**
- `PermissionRequest` — dispara quando o agente precisa de decisão de permissão. Matcher em `tool_name`.

**Scripts manuais (não-hooks):**
- validate-refinement-evidence.py — verifica refinements.log.jsonl
- validate-skill-format.py — valida formato de skills

## Configs do runtime

| Config | Local (bundle) | Local (Devin home) | Função |
|---|---|---|---|
| AGENTS.md | `./AGENTS.md` | `~/.config/devin/AGENTS.md` | Regras globais (20 regras) |
| config.json | `./config.json` | `~/.config/devin/config.json` | Modelo, hooks, theme |
| mcp_config.json | `./mcp_config.json` | `~/.config/devin/mcp_config.json` | MCP servers |
| hooks.v1.json | `./hooks.v1.json` | `~/.config/devin/hooks.v1.json` | Hooks legacy (backup) |
| credentials.toml | `./credentials.toml` | — | Credenciais (MASKED) |
| agents/ | `./agents/` | `~/.config/devin/agents/` | 5 perfis customizados |
| skills/ | `./skills/` | `~/.config/devin/skills/` | 83 skills |
| extensions/ | `./extensions/` | `~/.config/devin/extensions/` | Utilitários locais (ex: `computer-use` — GUI automation) |
| scripts/ | `./scripts/` | `~/.config/devin/scripts/` | 18 scripts Python + 1 JS |
| MODEL-GUIDE.md | `./MODEL-GUIDE.md` | — | Guia de modelos (veja `data/bundle-models.json`) |
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

O bundle carrega servidores MCP a partir de `mcp_config.json` no Devin home do usuário. O arquivo `mcp_config.json.example` contém um exemplo de integração de issue tracker; parâmetros de integração (site, cloud ID, enablement) estão em `data/bundle-integrations.json`. Autentique antes de habilitar; credenciais e notas específicas de integração local devem ficar no troubleshooting local, não no bundle global.

**Auditoria MCP (arXiv:2606.30317):**
- Tool count por server < 10-15 para >90% accuracy (Claude Haiku)
- 20-30 tools para Sonnet 4
- Verifique tool count com `mcp_list_tools` quando o servidor MCP estiver logado
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

## Modelos disponíveis (Devin CLI `{{VALIDATED_CLI_VERSION}}`)

| model_uid | Label | Effort | Context | Custo | Recomendado |
|---|---|---|---|---|---|
| `{{BUNDLE_DEFAULT_MODEL}}` | SWE-2 High (parent) | high | 262K | **Free** | ✓ (config.json) |
| `{{BUNDLE_MEDIUM_MODEL}}` | SWE-2 Medium | medium | 262K | **Free** | Tarefas simples, ajustes pontuais, scripts isolados |
| `{{BUNDLE_MAX_MODEL}}` | SWE-2 Max | max | 262K | **Free** | Tarefas abertas, refactors globais, long-horizon |
| `paid_model_alias` | Paid alias | — | see registry | see registry | NUNCA usar sem confirmar `data/bundle-models.json` |
| `adaptive` | Paid router | see registry | — | see registry | Não usar em modo free |
| `opus` | Paid model | Anthropic | — | see registry | Não usar em modo free |
| `sonnet` | Paid model | Anthropic | — | see registry | Não usar em modo free |
| `gpt` | Paid model | OpenAI | — | see registry | Não usar em modo free |
| `codex` | Paid model | OpenAI | — | see registry | Não usar em modo free |
| `gemini` | Paid model | Google | — | see registry | Não usar em modo free |

**⚠️ Política CONDICIONAL:** quando o parent está em modelo FREE (lido de `data/bundle-models.json` com `cost_tier: free`), NUNCA usar modelos pagos para subagents. Short names/aliases (`opus`, `sonnet`, `codex`, `gemini` etc.) podem resolver para entradas pagas — verifique `data/bundle-models.json` antes de usar. Use o parent (`{{BUNDLE_DEFAULT_MODEL}}`) e os subagent models (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`) do registro. Quando o parent é pago, subagents podem usar pagos.

## Context budget (parent model)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável)
AGENTS.md                    ~5605 tok (2.80%)
SKILL-TIERS.md (se lido)     ~1782 tok (0.89%)
MODEL-GUIDE.md (se lido)     ~3711 tok (1.86%)
TOOLS-MAP.md (se lido)       ~2478 tok (1.24%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (configured)   ~???? tok (medir com mcp-context-audit)
─────────────────────────────────────────────
Total fixo (sem docs opt)    ~5605 tok (2.80%)
Total c/ docs opt            ~13576 tok (6.79%)
Disponível para trabalho     consulte `context_window` em `data/bundle-models.json`
```

**Nota:** MODEL-GUIDE.md, TOOLS-MAP.md e SKILL-TIERS.md são leituras
opcionais (não carregam automaticamente). AGENTS.md é fixo.
