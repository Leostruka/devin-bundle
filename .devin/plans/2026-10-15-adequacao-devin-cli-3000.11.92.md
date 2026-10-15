# Plano: adequar o bundle ao Devin CLI v3000.11.92

**Objetivo:** alinhar declaração de versão, tabela de capacidades e docs de runtime ao CLI instalado `3000.11.92` (delta desde o último alinhamento: `3000.11.1` validado; intermediária `3000.11.3` coberta).

**Arquitetura:** uma mudança de config é proposta. `agent.subagent_model` é o mecanismo nativo para o `default_subagent_model` que `data/bundle-models.json` já declarava. O resto é documentação de decisões e bump do pin.

**Stack:** docs Markdown, `data/bundle-identity.json`, `config.json`, verificação via `devin doctor`, `audit.py`, `pytest`.

## Estado observado (2026-10-15)

- `devin --version`: `3000.11.92 (7f4e64980e22)`.
- Pin atual: `"validated_cli_version": "3000.11.1"` em `data/bundle-identity.json`; README.md linha 41 hardcoded.
- `devin doctor`: 2/2 pass (profiles + otel env).
- `devin rules list`: limpo. `.devin/rules/` tem só `.gitkeep`; 4 regras always-on + 1 glob-scoped (template project-bootstrap).
- `devin models list`: trio SWE-2 free inalterado (`swe-2-high/medium/max`, 262K, Free); famílias pagas novas (lightning, Fable 5.1, Opus 5.5) não tocam `data/bundle-models.json`.
- `devin cloud --help`: subcomando `drs` presente. `devin connect --help`: comando hidden presente (local tool use para sessões cloud).

## Verificação empírica de `agent.subagent_model`

- Teste: `devin --config <cfg com agent.subagent_model=swe-2-max> -p "dispatch subagent_explore ..."` → tool result de `run_subagent` reporta `subagent/model: "SWE-2 Max"`.
- Controle: mesmo prompt com `config.json` sem a chave → `subagent/model: "SWE-2 High"` (herda o parent; o "default router" do CLI resolve para o parent nesta versão).
- Conclusão: a chave é honrada e muda o modelo do `subagent_explore`. Adotada com `swe-2-max` (= `default_subagent_model` do registry).
- Nota: chaves desconhecidas em `agent` são ignoradas silenciosamente (controle com `bogus_key_xyz` também inicia). A evidência do pin vem do `subagent/model` no tool result, não do parse.

## Delta 3000.11.1 → 3000.11.92 que toca o bundle

| Item | Superfície do bundle | Ação |
|---|---|---|
| `agent.subagent_model` (config) | `config.json`, política de modelos | **adotar**: pin `swe-2-max` |
| `PreCompact`/`PostCompact` hooks (matchers `manual`/`auto`) | seção Lifecycle hooks do compat doc | documentar; `PostCompaction` segue suportado |
| `/goal`, steering mid-turn, `/billing`, `Alt+Enter` model pick | TOOLS-MAP comandos | documentar |
| `typewriter`, `local_tools_bypass_permissions`, `disable_osc`, `proxy.gzip`, `DEVIN_SESSIONS_DIR` | config template | decisão: não adotar (cosmético / bypass amplo / sem proxy / env var) |
| Plugins: `platforms`, `PLUGIN_ROOT`/`PLUGIN_DATA`, repos skills-only, non-semver | seção Plugins | documentar |
| MCP: protocol 2026-07-28, `Source:` line, User-Agent, cloud remote MCP (Private Preview), OAuth eviction | seção MCP do TOOLS-MAP | documentar |
| `sandbox.excluded.allow`, `Write(...)` allow auto-aprova em autonomous | seção Sandbox | documentar |
| Fixes: `read_config_from` project-level + skills de provider off bloqueadas; `.devin/rules/` e `global_rules.md` sob `windsurf:false`; hooks foreign-event; `devin connect` aprovação nomeia regra | seções Rules/read_config_from | adotado (passivo) |
| `devin cloud` bare = sessão cloud; `cloud drs` | TOOLS-MAP | documentar |
| `devin --cloud` falha rápido; proxy cobre WS/plugin downloads; session DB em NFS; `--model` cold-start | runtime | adotado (passivo) |

## Fontes primárias

- https://docs.devin.ai/cli/changelog/stable (v3000.11.92, 2026-10-14; v3000.11.3, 2026-09-22)
- https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks (ainda sem `PreCompact`/`PostCompact`; changelog é a fonte)
- `devin --help`, `devin doctor`, `devin rules list`, `devin models list`, `devin cloud --help`, `devin connect --help`, sessions.db (`subagent/model` no tool result)

## Global Constraints

- Decisões seguem o formato (Capability | Decision | Rationale).
- `config.json` ganha apenas `agent.subagent_model`, chave com evidência empírica.
- Sem placeholders `{{...}}` novos além dos existentes.
- Docs do repo em PT-BR nos planos; compat doc em EN (convenção existente).

## Aceitação

- [x] `bundle-identity.json`, README e `devin --version` em paridade (`3000.11.92`).
- [x] Tabela cobre todo o delta com decisão explícita por item.
- [x] `agent.subagent_model` verificado com evidência reproduzível (sessions.db `subagent/model`), incluindo controle sem a chave.
- [x] `python audit.py` 0 erros; `python -m pytest` 1682 passed, 4 skipped; 2 falhas ambientais pre-existentes (`test_ppisp_prep` ×2: `import torch` quebrado no host, `torch_python.dll` WinError 126); `devin doctor` 2/2; install em APPDATA temporário 160 arquivos + doctor pass.
- [x] Nenhum `tmp_*` sobrevive no commit final.
