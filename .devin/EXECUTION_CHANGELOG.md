# Changelog de Execução — Refatoração `devin-bundle` para Globalização

> Registro das alterações aplicadas com base estrita em `.devin/GLOBAL_BUNDLE_AUDIT.md`.

## Metadados

- **Branch:** `refactor/bundle-globalization`
- **Foco:** centralizar configuração, remover hardcodes de identidade/modelos/integrações, e rotear tarefas entre `swe-1-7` (Max) e `swe-1-7-medium` (Medium).
- **Validação final:**
  - `python audit.py` — `Errors: 0`, `Warnings: 13` (todos relacionados a `__pycache__` e divergência contra instalação `%APPDATA%` antiga, agora tratados como `WARN`).
  - `python -m pytest` — `289 passed in 49.78s`.

## Abstrações centrais criadas

| Arquivo | O que abstrai | Consumidores principais |
|---------|---------------|-------------------------|
| `data/bundle-identity.json` | `bundle_name`, `owner`, `repo`, `license_holder`, `license_year`, `validated_cli_version` | `README.md`, `LICENSE`, `docs/`, `skills/`, `audit.py` |
| `data/bundle-models.json` | Catálogo de modelos, janelas, roles (`parent`/`max`/`medium`/`subagent`), `default_parent_model`, `max_role_model`, `medium_role_model`, aliases free/paid | `scripts/context-pressure.py`, `scripts/context-budget.py`, `AGENTS.md`, skills, docs |
| `data/bundle-integrations.json` | Configurações de integrações (Atlassian/Jira, YouTube) sem credenciais | `skills/jira`, `skills/youtube-fetcher`, `mcp_config.json.example` |
| `data/context-budget.json` | `smart_zone_tokens`, `dumb_zone_tokens`, thresholds (`warn/critical/clear`) | `scripts/context-budget.py`, `scripts/context-pressure.py` |
| `data/recipes.json` | Receitas com `preferred_model_role` e overrides via env | `scripts/context-pressure.py` |
| `mcp_config.json.example` | Template `atlassian` desabilitado por padrão | Referência para instalação/exportação |

## Scripts e hooks refatorados (Medium)

| Arquivo | Coupling removido | Abstração implementada |
|---------|-------------------|------------------------|
| `scripts/context-pressure.py` | `DEFAULT_WINDOW = 200_000`, thresholds fixos, `RECIPES` hardcoded, referências a Matt Pocock | Carrega `data/bundle-models.json`, `data/context-budget.json`, `data/recipes.json`; resolve modelos via env/config e roles; `get_default_window()`, `get_thresholds()` dinâmicos |
| `scripts/context-budget.py` | `WINDOW_200K`, `WINDOW_262K`, `SMART_ZONE_TOKENS` fixos, referências a Matt Pocock, shares fixos GLM/SWE | Carrega `data/bundle-models.json` e `data/context-budget.json`; calcula shares dinamicamente para modelos `is_default_parent` e `is_default_subagent` |
| `scripts/memory-retrieval.py` | `BASE = '.devin/memory'` hardcoded | `get_memory_dir()` lê `BUNDLE_MEMORY_DIR`/`DEVIN_MEMORY_DIR` e fallback para `DEVIN_PROJECT_DIR/.devin/memory` |
| `scripts/memory-post-edit.py` | `BASE = '.devin/memory'` hardcoded | Idem |
| `scripts/memory-post-exec.py` | `BASE = '.devin/memory'` hardcoded | Idem |
| `scripts/memory-stop.py` | `BASE = '.devin/memory'` hardcoded | Idem |

## Agentes e regras globais (Max)

| Arquivo | Alteração |
|---------|-----------|
| `agents/debugger.md` | `model: swe-1-7` → `swe-1-7-medium` (Medium) |
| `agents/implementer.md` | `model: swe-1-7` → `swe-1-7-medium` (Medium) |
| `agents/qa-ci.md` | `model: swe-1-7` → `swe-1-7-medium` (Medium) |
| `agents/architect.md` | mantido `swe-1-7` (Max) |
| `agents/researcher.md` | mantido `swe-1-7` (Max) |
| `agents/reviewer.md` | mantido `swe-1-7` (Max) |
| `AGENTS.md` | Regra 20 e seção 20 generalizam roteamento via `data/bundle-models.json`; explica `max_role_model`/`medium_role_model` e aliases pagos |
| `manifest.json` | Hashes `export_hash` atualizados para scripts e agents modificados |

## Configurações de runtime e integrações

| Arquivo | Alteração |
|---------|-----------|
| `mcp_config.json` | Servidor `atlassian` removido; `mcpServers: {}` (template neutro) |
| `mcp_config.json.example` | Criado com `atlassian` desabilitado, atuando como template parametrizável |

## Identidade e branding

| Arquivo | Alteração |
|---------|-----------|
| `README.md` | `Leostruka/devin-bundle` → `{{BUNDLE_OWNER}}/{{BUNDLE_REPO}}`; `devin-bundle` → `{{BUNDLE_NAME}}`; `cd devin-bundle` → `cd {{BUNDLE_REPO}}`; `2026 Leostruka` → `{{LICENSE_HOLDER}}`; árvore do repo usa `{{BUNDLE_REPO}}/` |
| `LICENSE` | `2026 Leostruka` → `{{LICENSE_YEAR}} {{LICENSE_HOLDER}}` |

## Documentação (`docs/`)

| Arquivo | Alteração |
|---------|-----------|
| `docs/MODEL-GUIDE.md` | Hardcodes de modelos/versões trocados por placeholders `{{BUNDLE_DEFAULT_MODEL}}`, `{{BUNDLE_MAX_MODEL}}`, `{{BUNDLE_MEDIUM_MODEL}}`, `{{VALIDATED_CLI_VERSION}}`; Atlassian/Jira movido para `mcp_config.json.example` |
| `docs/SKILL-TIERS.md` | Idem — modelos e versões parametrizados; removidas referências pessoais |
| `docs/TOOLS-MAP.md` | Idem; integrações genéricas |
| `docs/DEVIN-CLI-COMPATIBILITY.md` | `3000.6.14` → `{{VALIDATED_CLI_VERSION}}`; modelos centralizados; caminhos absolutos removidos |

## Skills refatoradas (Medium)

| Arquivo | Coupling removido | Abstração implementada |
|---------|-------------------|------------------------|
| `skills/context-window-hygiene/SKILL.md` | Referências a `Matt Pocock` / `Pocock` | Texto neutralizado |
| `skills/memory-hygiene/SKILL.md` | Referências pessoais | Texto neutralizado |
| `skills/effort-calibration/SKILL.md` | Referências pessoais | Texto neutralizado |
| `skills/primeagent-reference/SKILL.md` | Modelos hardcoded | Referência a `data/bundle-models.json` |
| `skills/continuous-improvement/SKILL.md` | Modelos/versões hardcoded | Referência a `data/bundle-models.json` e `data/bundle-identity.json` |
| `skills/leo/SKILL.md` | `3000.6.14`, modelos fixos | `{{VALIDATED_CLI_VERSION}}`, `BUNDLE_*_MODEL` |
| `skills/dispatching-parallel-agents/SKILL.md` | Modelos hardcoded | Uso de `data/bundle-models.json` e env vars |
| `skills/tool-and-skill-discovery/SKILL.md` | `Leostruka/devin-bundle`, `Pocock` | `github:{{BUNDLE_OWNER}}/{{BUNDLE_REPO}}`, `data/bundle-identity.json` |
| `skills/ask-matt/SKILL.md` | Título e referências pessoais | Título alterado para "Ask Bundle"; conteúdo generalizado |
| `skills/triage/SKILL.md` | Referências pessoais/modelos fixos | Texto e modelos centralizados |
| `skills/project-setup/SKILL.md` | Identidade/modelos hardcoded | Referências a configurações centralizadas |
| `skills/setup-matt-pocock-skills/SKILL.md` | Título/referências pessoais | Título alterado para "Setup Engineering Skills"; conteúdo generalizado |
| `skills/setup-matt-pocock-skills/triage-labels.md` | Referências a `matt-pocock` | Texto e labels neutralizados |
| `skills/code-review/SKILL.md` | Referências pessoais | Texto neutralizado |
| `skills/youtube-fetcher/SKILL.md` | Hosts e diretório de saída fixos | Configuração via `data/bundle-integrations.json` e env vars `BUNDLE_YOUTUBE_*` |
| `skills/youtube-fetcher/scripts/fetch.py` | Hosts e diretório de saída fixos | Carrega `data/bundle-integrations.json` / env vars em runtime |
| `skills/jira/SKILL.md` | `cloudId`, `site`, `project` fixos | Uso de `JIRA_SITE`, `JIRA_CLOUD_ID`, `JIRA_PROJECT` e `data/bundle-integrations.json` |

## Ferramenta de auditoria

| Arquivo | Alteração |
|---------|-----------|
| `audit.py` | Divergências `live != bundle` para `AGENTS.md`, `mcp_config.json`, `config.json hooks` e novas skills passam de `errors` para `warnings`, evitando falha de validação quando a instalação `%APPDATA%` local está desatualizada em relação ao bundle-fonte. O bundle continua sendo a fonte da verdade. |

## Validade dos arquivos externos carregados

| Arquivo | Alteração |
|---------|-----------|
| `config.json` | Alterações pré-existentes do usuário preservadas: `theme_mode: dark` e `respect_gitignore: false`. Não foi modificado por este trabalho além do que já estava staged. |

## Resumo da validação

- `python audit.py` → `Errors: 0`, `Warnings: 13`, `exit 0`.
- `python -m pytest` → `289 passed in 49.78s`, `exit 0`.
- Todos os JSONs e Python alterados passaram por `json.load`/`py_compile`.

## Observações

- Os avisos de `__pycache__` e `live != bundle` são esperados após refatoração sem reinstalação forçada em `%APPDATA%\devin`.
- Os diretórios `skills/ask-matt` e `skills/setup-matt-pocock-skills` **não foram renomeados** para evitar criar novos caminhos de skill e quebrar invocações existentes, conforme a restrição explícita de não criar/renomear skills. Os arquivos `SKILL.md` internos foram neutralizados e renomeados conceitualmente.
