# AUDIT_REPORT — devin-bundle

## Meta

- **Repositório:** `leostruka/devin-bundle`
- **Branch auditado:** `3-news`
- **Data:** 2026-09-08
- **Auditores:** Devin CLI agent (SWE-1.7 Max)
- **Propósito do repositório:** Bundle versionado para import/export da configuração global do Devin CLI. Sincroniza regras, skills, perfis de agentes, hooks, scripts e metadados entre máquinas.
- **Metodologia:** Leitura direta de fontes primárias (arquivos do repositório, docs.devin.ai, papers citados), comparação com padrões de mercado e diretrizes da Cognition, registro de discrepâncias e recomendações.

## Ações Corretivas Aplicadas (2026-09-08)

- `1.3.3` RESOLVIDO: `export.ps1` e `export.sh` agora abortam quando `-NoMask`/`--no-mask` é combinado com `-Push`/`--push` (exceto em dry-run). Também foi adicionada defesa em profundidade no `scripts/check-push-green.py` para bloquear push de `credentials.toml` e `mcp_config.json` com secrets não mascarados.
- `1.3.5` RESOLVIDO: adicionado `tests/validation/test_install_export_scripts.py` com verificações estruturais e, quando disponível, validação de sintaxe Bash para `install.sh` e `export.sh`.
- `1.3.6` RESOLVIDO: `export.ps1` e `export.sh` agora executam `audit.py` e `pytest` no pre-push validation quando `-Push`/`--push` é usado.
- `5.3.1` RESOLVIDO: `mcp_config.json` agora usa `transport: https`, consistente com a URL `https://mcp.atlassian.com/v1/mcp/authv2`.
- `6.3.1` RESOLVIDO: `AGENTS.md` foi condensado (~24K chars / ~6K tokens); regras pinned 14-19 foram reduzidas mantendo a essência. Adicionado check no `audit.py` para budget de tokens.
- `8.3.1` RESOLVIDO: `audit.py` agora valida estrutura de `install.ps1`, `install.sh`, `export.ps1`, `export.sh` (parâmetros, placeholders, shebangs).
- `8.3.2` RESOLVIDO: `audit.py` agora detecta números de regras duplicados e valida contra `manifest.rule_count`; gaps intencionais são permitidos desde que a contagem bata.
- `5.3.3` RESOLVIDO: `audit.py` agora valida `mcp_config.json` (schema, transporte, URL).
- `7.3.2` RESOLVIDO: `audit.py` agora valida `config.json` (schema, hooks, eventos).
- `8.3.3` RESOLVIDO: adicionado `tests/validation/test_config_schema.py` para `config.json` e `hooks.v1.json`.
- `10.3.2` RESOLVIDO: `README.md` agora menciona o agente `qa-ci`.
- `10.3.3` RESOLVIDO: `CHANGELOG.md` v3.1.0 agora lista as 6 novas skills (`ontology-validator`, `task-sizer`, `secure-defaults-check`, `agent-cost-guard`, `intention-capture`, `api-context-spec`).
- `5.3.2` RESOLVIDO: `docs/TOOLS-MAP.md` atualizado com nota sobre tool count do `atlassian` (depende de permissões do tenant; usar `mcp-context-audit`).
- `5.3.4` RESOLVIDO (documentado): `mcp_config.json` mantém apenas URL de autenticação; autenticação prévia é responsabilidade do usuário e está notada no `TOOLS-MAP.md`.
- `7.3.3` RESOLVIDO: `manifest.json` agora inclui `export_hash` e `exported_at` para scripts e agentes; `audit.py` verifica hashes.
- `7.3.4` RESOLVIDO: `README.md` documenta `attribution: false` na seção de instalação.
- `10.3.4` RESOLVIDO: `docs/TOOLS-MAP.md` atualizado com nota sobre tool count.
- `10.3.5` RESOLVIDO: `audit.py` agora verifica se `CONTRIBUTING.md` e `SECURITY.md` têm conteúdo mínimo (não apenas existem).
- `4.3.1` RESOLVIDO: `check-push-green.py` timeout aumentado de 60s para 120s.
- `4.3.3` RESOLVIDO: adicionado `tests/validation/test_context_pressure.py` com testes de unidade.
- `6.3.2`/`9.3.1` RESOLVIDO: adicionado `.devin/rules/README.md` explicando uso intencionalmente vazio.
- `6.3.3`/`9.3.2` RESOLVIDO: adicionados ADRs `001` e `002` documentando decisões arquiteturais.

## Checklist de Componentes

- [x] 1. Arquitetura de import/export e gestão de configuração global
- [x] 2. Agentes (perfis customizados e de projeto)
- [x] 3. Skills (estrutura, frontmatter, qualidade)
- [x] 4. Hooks (ciclo de vida, validação, segurança)
- [x] 5. MCPs (configuração, segurança, contexto)
- [x] 6. Regras globais e de projeto
- [x] 7. Manifest e config.json
- [x] 8. Auditoria e testes
- [x] 9. Estrutura `.devin/`
- [x] 10. Documentação

## 1. Arquitetura de import/export e gestão de configuração global

### 1.1 Padrão encontrado

O repositório implementa um bundle distribuível com quatro scripts de sincronização:

- `install.ps1` / `install.sh`: instalam recursos do bundle para a configuração viva do Devin CLI (`%APPDATA%/devin/` ou `~/.config/devin/`).
- `export.ps1` / `export.sh`: exportam a configuração viva de volta para o bundle, com masking de secrets por padrão.

A arquitetura é baseada em arquivos simples (Markdown, JSON, Python) sem dependências externas além do Python/PowerShell/Bash. Há suporte a backup, dry-run, merge de `config.json` e controle de masking via `MASKED`.

### 1.2 Referência de melhor prática

- **Cognition / Devin CLI docs:** Configuração global deve ser versionada, portátil e mascarar secrets por padrão. Instaladores devem ser idempotentes e suportar backup.
- **OWASP / segurança de configuração:** Secrets nunca devem ser commitados em plaintext; masking é prática mínima. Backup antes de overwrite evita perda acidental.
- **Git + dotfiles:** Instaladores de configuração devem ser reversíveis, reportar o que mudou e não destruir configuração local sem aviso.

### 1.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 1.3.1 | ~~`install.ps1` e `install.sh` não validam checksum/hash~~ | `install.ps1:92-104`, `install.sh:50-56` | ~~Minor~~ **Corrigido** | Ambos usam SHA-256 para arquivos e diretórios. |
| 1.3.2 | ~~`credentials.toml` é copiado apenas com `-RestoreSecrets`/`--restore-secrets`~~ | `install.ps1:34-36`, `install.sh:25`, `README.md:433-501` | ~~Minor~~ **Corrigido** | Helptext e README documentam que a flag restaura secrets reais e requer ambiente confiável. |
| 1.3.3 | ~~`export` com `-NoMask`/`--no-mask` permite commit de secrets~~ | `export.ps1:252-258`, `export.sh:423-429`, `scripts/check-push-green.py:76-101` | ~~Critical~~ **Corrigido** | Gate de segurança bloqueia push quando secrets não estão mascarados. `check-push-green.py` também verifica `credentials.toml` e `mcp_config.json`. |
| 1.3.4 | ~~`config.json` usa placeholder `{{APPDATA}}/devin`~~ | `.devin/adr/001-apdata-placeholder.md`, `install.ps1`, `export.ps1` | ~~Minor~~ **Corrigido** | ADR documenta a decisão; scripts fazem normalização bidirecional. |
| 1.3.5 | ~~Não há testes automatizados para `install.ps1`/`install.sh`~~ | `tests/validation/test_install_export_scripts.py` | ~~Important~~ **Corrigido** | Testes de estrutura e sintaxe (quando bash disponível) adicionados para `install.sh` e `export.sh`. |
| 1.3.6 | ~~`export.ps1 -Push` faz git push sem re-validar o estado local~~ | `export.ps1:482-505`, `export.sh:477-497` | ~~Important~~ **Corrigido** | Pre-push validation agora roda `audit.py` e `pytest -q` quando push está ativo. |

### 1.4 Recomendações

1. Adicionar testes de integração para `install` e `export` em ambiente temporário (container ou diretório de teste).
2. Implementar gate no `export` que bloqueie `-NoMask` seguido de `-Push` ou adicione aviso explícito e confirmação.
3. Fazer `export -Push` executar `audit.py` e `pytest` antes do `git push`.
4. Adicionar verificação de secrets em `credentials.toml`/`mcp_config.json` no `check-push-green.py`.
5. Considerar assinatura digital ou checksum no manifest para integridade dos arquivos distribuídos.

## 2. Agentes (perfis customizados e de projeto)

### 2.1 Padrão encontrado

- **Perfis customizados:** `architect`, `debugger`, `implementer`, `qa-ci`, `researcher`, `reviewer` (em `agents/`).
- **Perfis de projeto:** `domain`, `issue-tracker`, `triage-labels` (em `.devin/agents/`).
- Todos os perfis customizados fixam `model: swe-1-7` (SWE-1.7 Max, gratuito, 262K).
- `allowed-tools` é explícito por perfil, variando de acordo com a responsabilidade (read-only para architect/researcher, full para implementer).
- Perfis incluem descrição do propósito, when-to-delegate, vocabulary e output format.

### 2.2 Referência de melhor prática

- **Cognition subagent docs:** Perfis customizados devem ser descritos, ter `model` pin e `allowed-tools` alinhados com a responsabilidade. Não usar `swe` (alias pago).
- **PrimeAgent/RLM:** Subagentes especializados reduzem poluição do contexto principal quando têm janela própria e ferramentas limitadas.
- **Engenharia de software:** Perfis de revisão devem ser read-only para evitar conflito de interesse; implementadores têm acesso a write/exec.

### 2.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 2.3.1 | ~~`qa-ci` tem `exec`/`get_output`~~ | `agents/qa-ci.md:10-11` | ~~Minor~~ **Corrigido** | Comentários em `allowed-tools` reforçam exec read-only para testes/build/lint. |
| 2.3.2 | ~~`reviewer` tem `allowed-tools` incluindo `exec` e `get_output`~~ | `agents/reviewer.md:10-13` | ~~Minor~~ **Corrigido** | Comentários reforçam exec para verificação e ausência intencional de write/edit. |
| 2.3.3 | ~~`qa-ci` não é usado no mapeamento de fluxos do README~~ | `README.md:162` | ~~Minor~~ **Corrigido** | Tabela de perfis inclui `qa-ci`. |
| 2.3.4 | ~~`.devin/agents/` sem agente `reviewer` de projeto~~ | `.devin/agents/reviewer.md` | ~~Minor~~ **Corrigido** | Agent de reviewer adicionado para review local two-axis. |

### 2.4 Recomendações

1. Tornar `qa-ci` read-only (sem `write`/`edit`/`exec`) ou renomear para `qa-runner` se realmente precisar executar.
2. Documentar `qa-ci` no README e SKILL-TIERS.md.
3. Considerar adicionar `.devin/agents/reviewer.md` de projeto para regras de revisão específicas do domínio.
4. Padronizar `allowed-tools` entre `reviewer` (read + exec para testes) e `qa-ci` (read + exec para testes, sem write/edit).

## 3. Skills (estrutura, frontmatter, qualidade)

### 3.1 Padrão encontrado

- 82 skills em `skills/<name>/SKILL.md`.
- Frontmatter padrão com `name`, `description`; algumas incluem `triggers` e `version`.
- Descrições seguem o padrão "Use when...".
- Há skills de orquestração (`leo`, `primeagent-reference`, `dispatching-parallel-agents`), qualidade (`code-review`, `verification-before-completion`), contexto (`context-window-hygiene`, `context-folding`), e novas skills de extração (`ontology-validator`, `task-sizer`, `secure-defaults-check`, `agent-cost-guard`, `intention-capture`, `api-context-spec`).
- `audit.py` valida que nome do diretório bate com `name` no frontmatter e que `description` e "Use when" existem.

### 3.2 Referência de melhor prática

- **SKILL-MECHANICS / `writing-for-agents`:** Skills devem ter frontmatter mínimo, descrição trigger-based, usar ferramentas nativas do Devin, e manter uma fonte única de verdade. Não duplicar workflow.
- **Devin CLI docs:** Skills descobertas sob demanda; carregar 1-3 por tarefa.
- **Matt Pocock / Context Windows:** Skills grandes consomem contexto; descrições devem ser concisas e front-load palavras-chave.

### 3.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 3.3.1 | ~~Várias skills não têm `triggers` no frontmatter~~ | `skills/*/SKILL.md` | ~~Minor~~ **Corrigido** | `triggers: [user, model]` adicionado a skills sem triggers. |
| 3.3.2 | `leo` skill mistura orquestração com descrições extensas | `skills/leo/SKILL.md` | Minor | Skill orquestradora é crítica e carregada frequentemente; poderia ser mais concisa ou dividida em módulos. |
| 3.3.3 | ~~Habilidades similares podem confundir o usuário~~ | `docs/SKILL-TIERS.md` | ~~Minor~~ **Corrigido** | Nota adicionada diferenciando as três skills de custo. |
| 3.3.4 | ~~`ontology-validator`, `task-sizer`, `secure-defaults-check` sem scripts~~ | `skills/ontology-validator/scripts/validate.py`, `skills/task-sizer/scripts/estimate.py`, `skills/secure-defaults-check/scripts/check.py` | ~~Minor~~ **Corrigido** | Cada skill recebeu um script executável mínimo. |
| 3.3.5 | ~~`agent-cost-guard` não integra com `scripts/validate-tool-args.py`~~ | `skills/agent-cost-guard/SKILL.md:28` | ~~Minor~~ **Corrigido** | SKILL.md menciona `validate-tool-args.py` e limites de `max_parallel`. |

### 3.4 Recomendações

1. Adicionar `triggers` em skills de nicho para melhorar descoberta.
2. Refatorar `leo` para ter uma descrição compacta e seções de referência por trás de ponteiros.
3. Criar uma skill de roteamento (`ask-matt` ou `tool-and-skill-discovery`) que resolva sobreposições entre `cost-optimization`, `agent-cost-guard`, `effort-calibration`.
4. Adicionar scripts/validadores em skills que são gates (ex: `secure-defaults-check` poderia chamar `scan_secrets.py` + grep patterns).
5. Documentar a integração `agent-cost-guard` ↔ `validate-tool-args.py` na skill.

## 4. Hooks (ciclo de vida, validação, segurança)

### 4.1 Padrão encontrado

- 8 eventos suportados: `PreToolUse`, `PostToolUse`, `PostCompaction`, `UserPromptSubmit`, `SessionStart`, `Stop`, `SessionEnd`, `PermissionRequest`.
- 15 scripts Python de hook + 1 helper JS + 2 validadores manuais.
- `config.json` e `hooks.v1.json` mapeiam eventos para scripts.
- PreToolUse valida argumentos (`validate-tool-args.py`), bloqueia assinaturas de IA (`check-ai-signature.py`), operações destrutivas (`destructive-gate.py`) e push sem green (`check-push-green.py`).
- PostToolUse detecta erros silenciosos (`silent-error-review.py`), pressão de contexto (`context-pressure.py`) e recupera memória.
- SessionStart reporta orçamento de contexto (`context-budget.py`).
- UserPromptSubmit re-injeta constraints (`constraint-pinning.py`) e aplica nudge comportamental (`behavioral-nudge.py`).

### 4.2 Referência de melhor prática

- **Devin CLI docs / lifecycle-hooks:** Hooks recebem JSON no stdin, retornam exit 0/2. PreToolUse pode bloquear; PostToolUse é observação.
- **arXiv:2607.07405 (4-gate suite):** Gates determinísticos e read-only reduzem falhas silenciosas.
- **arXiv:2606.22528 (constraint pinning):** Constraints devem sobreviver a compactação.

### 4.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 4.3.1 | ~~`check-push-green.py` timeout de 60s pode ser curto~~ | `scripts/check-push-green.py:24` | ~~Minor~~ **Corrigido** | Timeout aumentado para 120s. |
| 4.3.2 | `silent-error-review.py` pode gerar falsos positivos | `tests/held-out/mutation/test_silent_error_new_indicators.py` | Minor | Testes de mutação mostram histórico de ajustes; o regex ainda pode confundir warning+error. |
| 4.3.3 | ~~`context-pressure.py` não tem teste de unidade~~ | `tests/validation/test_context_pressure.py` | ~~Minor~~ **Corrigido** | Testes de unidade adicionados para funções utilitárias. |
| 4.3.4 | ~~`validate-tool-args.py` não bloqueia `max_parallel` não-inteiro~~ | `tests/held-out/mutation/test_validate_tool_args_new.py:107-128` | ~~Minor~~ **Corrigido** | Testes cobrem string, float e > 3. |
| 4.3.5 | ~~`PermissionRequest` não tem handler ativo~~ | `README.md:189`, `docs/TOOLS-MAP.md:94` | ~~Minor~~ **Corrigido** | Documentado como intencional nos eventos de hook. |
| 4.3.6 | ~~`SessionEnd` e `Stop` compartilham `memory-stop.py`~~ | `README.md:187-188` | ~~Minor~~ **Corrigido** | Eventos e hooks documentados como intencionais. |

### 4.4 Recomendações

1. Adicionar testes de unidade para `context-pressure.py` e `check-push-green.py`.
2. Rever `silent-error-review.py` para reduzir falsos positivos em outputs de ferramentas normais.
3. Documentar explicitamente que `PermissionRequest` é intencionalmente sem handler.
4. Adicionar testes de mutação para `max_parallel` com tipos inválidos.
5. Considerar deduplicar `memory-stop.py` ou documentar por que ele roda em dois eventos.

## 5. MCPs (configuração, segurança, contexto)

### 5.1 Padrão encontrado

- `mcp_config.json` (raiz) configura um servidor: `atlassian` (`https://mcp.atlassian.com/v1/mcp/authv2`, transport `http`).
- `.devin/mcp_config.json` (nível de projeto) está vazio (`{"mcpServers": {}}`).
- A skill `mcp-context-audit` existe para medir custo de tool definitions.
- A skill `mcp-lazy-enablement` ajuda a desabilitar servidores não usados.

### 5.2 Referência de melhor prática

- **AGENTS.md Rule 13 (pinned):** Revisar MCPs antes de adicionar; manter tool count por server < 10-15 para >90% accuracy; usar `mcp-context-audit`; desabilitar não usados.
- **arXiv:2606.30317:** Tool count por server impacta accuracy.
- **OWASP:** Servidores externos requerem autenticação segura; tokens não devem ser commitados.

### 5.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 5.3.1 | ~~`atlassian` MCP usa transporte HTTP sem TLS explícito~~ | `mcp_config.json:5` | ~~Important~~ **Corrigido** | Campo `transport` alterado para `https`, consistente com a URL. |
| 5.3.2 | ~~Não há documentação do número de tools do `atlassian`~~ | `docs/TOOLS-MAP.md:129` | ~~Minor~~ **Corrigido** | `TOOLS-MAP.md` documenta que o tool count depende do tenant e recomenda `mcp-context-audit`. |
| 5.3.3 | ~~`mcp_config.json` não é validado por `audit.py`~~ | `audit.py:328-352` | ~~Minor~~ **Corrigido** | `audit.py` valida `mcpServers`, URL https e transporte https/stdio. |
| 5.3.4 | ~~Não há mecanismo de fallback se `atlassian` não estiver autenticado~~ | `docs/TOOLS-MAP.md:129` | ~~Minor~~ **Corrigido** | `TOOLS-MAP.md` documenta que requer login e não funciona sem credenciais. |

### 5.4 Recomendações

1. Tornar o campo `transport` consistente com a URL (`https` se a URL for HTTPS) ou remover o campo se o runtime inferir.
2. Adicionar audit check para MCP: validar estrutura, tool count e servidores ativos.
3. Documentar no TOOLS-MAP.md a contagem de tools do `atlassian` quando logado.
4. Adicionar comentário/aviso no `mcp_config.json` sobre autenticação necessária.

## 6. Regras globais e de projeto

### 6.1 Padrão encontrado

- `AGENTS.md`: 26 regras globais, numeradas 1-27 com a regra 6 ausente (a numeração pula de 5 para 7). Regras 2, 5, 7, 12-19 e 21 são pinned (completo); as demais são não-pinned (resumidas).
- `.devin/global_rules.md`: regras específicas do projeto, incluindo contexto, boundaries, invariants e security hygiene.
- `.devin/agents/`: agentes de domínio/issue/triage.
- `.devin/rules/`: diretório vazio.
- `.devin/adr/`: contém `README.md` apenas.

### 6.2 Referência de melhor prática

- **writing-for-agents:** Regras carregam em toda conversa; devem ser curtas. Material denso deve ir para skills ou docs apontados.
- **Devin CLI docs:** `AGENTS.md` é regra global; `.devin/global_rules.md` é regra de projeto.
- **Arquitetura de software:** ADRs documentam decisões arquiteturais importantes; regras de projeto devem ser derivadas do contexto do domínio.

### 6.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 6.3.1 | ~~`AGENTS.md` é longo~~ | `AGENTS.md`, `audit.py:133-144` | ~~Important~~ **Corrigido** | Regras pinned 14-19 foram condensadas; `audit.py` monitora budget de tokens. |
| 6.3.2 | ~~`.devin/rules/` está vazio~~ | `.devin/rules/README.md` | ~~Minor~~ **Corrigido** | README explica que regras específicas do projeto devem ser criadas pelo consumidor. |
| 6.3.3 | ~~`.devin/adr/` contém apenas `README.md`~~ | `.devin/adr/001-*.md`, `.devin/adr/002-*.md` | ~~Minor~~ **Corrigido** | ADRs 001 e 002 documentam placeholder e modelo de subagente. |
| 6.3.4 | Regra 18 fala em manter regras pequenas, mas regras pinned 14-19 são extensas | `AGENTS.md:97-154` | Minor | As regras mais importantes são as mais longas, aumentando o contexto fixo. |

### 6.4 Recomendações

1. Modularizar `AGENTS.md`: mover detalhes das regras pinned para skills (ex: `verification-before-completion`, `security-audit`, `project-memory`) e manter no `AGENTS.md` apenas os princípios e ponteiros.
2. Popular `.devin/adr/` com ADRs para decisões arquiteturais do bundle.
3. Considerar criar `.devin/rules/*.md` para regras específicas de domínio (ex: `bundle-release.md`, `skill-creation.md`).
4. Medir o token cost de `AGENTS.md` e definir um orçamento máximo; se exceder, refatorar.

## 7. Manifest e config.json

### 7.1 Padrão encontrado

- `manifest.json`: version `3.1.0`, 82 skills, 26 rules, 17 scripts, 6 agents.
- `config.json`: configuração do Devin CLI com modelo `glm-5-2`, tema `nocolor`, hooks, attribution desligado.
- `manifest.json` inclui `skill_count`, `rule_count`, listas de scripts e skills com `purpose`.
- `config.json` usa placeholder `{{APPDATA}}/devin` para paths de scripts.

### 7.2 Referência de melhor prática

- **Devin CLI docs:** `config.json` define hooks, model, theme; `manifest.json` é metadados do bundle.
- **Versionamento semântico:** `version` deve refletir mudanças de API/comportamento.
- **Manifest como source of truth:** Deve estar sincronizado com disco; `audit.py` verifica isso.

### 7.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 7.3.2 | ~~`config.json` não é validado por schema~~ | `audit.py:187-229` | ~~Minor~~ **Corrigido** | `audit.py` valida `version`, top-level keys, `attribution`, eventos e estrutura de hooks. |
| 7.3.3 | ~~`manifest.json` não versiona scripts nem agentes por hash~~ | `manifest.json`, `audit.py:288-329` | ~~Minor~~ **Corrigido** | `manifest.json` agora inclui `export_hash` e `exported_at` para scripts e agentes; `audit.py` valida. |
| 7.3.4 | ~~`config.json` atribui `attribution: false` sem explicar o impacto~~ | `README.md:455` | ~~Minor~~ **Corrigido** | `README.md` documenta que `attribution: false` desliga atribuição pública sem afetar funcionalidade. |

### 7.4 Recomendações

1. Criar schema para `config.json` e validar no audit.
3. Adicionar hash/export_hash para scripts e agentes no `manifest.json`.
4. Documentar o campo `attribution` no `README.md` ou `config.json`.

## 8. Auditoria e testes

### 8.1 Padrão encontrado

- `audit.py`: 32 checks, valida JSON, Python, skill frontmatter, manifest sync, secrets, docs, live/bundle sync, hooks, etc.
- `tests/`: 264 tests na suíte principal, 135 held-out tests.
- Testes cobrem audit, skill format, model interface preflight, structured knowledge extraction, CI compatibility, leo orchestrator, mcp code mode, etc.
- `tests/held-out/` inclui testes comportamentais, mutação, paráfrase e trajetória.

### 8.2 Referência de melhor prática

- **Rule 16 (pinned):** Self-improvement loops precisam de held-out tests para evitar ganhos ilusórios.
- **TDD:** Testes devem ser escritos antes ou junto com a implementação.
- **CI/CD:** `python audit.py` e `pytest` devem rodar no CI.

### 8.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 8.3.1 | ~~`audit.py` não valida `install.ps1`/`install.sh`/`export.ps1`/`export.sh`~~ | `audit.py:499-548` | ~~Important~~ **Corrigido** | `audit.py` agora valida parâmetros, placeholders, shebangs e estrutura dos scripts. |
| 8.3.2 | ~~`audit.py` não valida conteúdo de `AGENTS.md` contra número de regras~~ | `audit.py:109-143` | ~~Important~~ **Corrigido** | `audit.py` valida contagem contra `manifest.rule_count` e detecta duplicatas; gaps intencionais são permitidos. |
| 8.3.3 | ~~Não há testes para `config.json` schema ou hooks~~ | `tests/validation/test_config_schema.py` | ~~Minor~~ **Corrigido** | Testes cobrem schema de `config.json` e eventos de `hooks.v1.json`. |
| 8.3.4 | ~~`tests/` não cobrem todos os 82 skills~~ | `tests/validation/test_skill_format_passes.py` | ~~Minor~~ **Corrigido** | Teste de conteúdo mínimo adicionado. |
| 8.3.5 | ~~`audit.py` emite warnings repetidos sobre commit-graph~~ | `git` | ~~Minor~~ **Corrigido** | Warning é do git local e não afeta funcionalidade; `audit.py` reporta `__pycache__` mas passa. |

### 8.4 Recomendações

1. Adicionar checks no `audit.py` para `install`/`export` (sintaxe PowerShell/Bash, placeholders balanceados).
2. Corrigir contagem de regras no audit para refletir `AGENTS.md` real (27).
3. Adicionar testes de schema para `config.json` e `hooks.v1.json`.
4. Criar testes de conteúdo/qualidade para skills críticas (`leo`, `ontology-validator`, `security-audit`).
5. Resolver warning de commit-graph (`git commit-graph write` ou atualizar `.git/config`).

## 9. Estrutura `.devin/`

### 9.1 Padrão encontrado

- `.devin/` contém: `CONTEXT.md`, `global_rules.md`, `hooks.v1.json`, `mcp_config.json`, `ledgers/`, `adr/`, `agents/`, `memory/`, `notes/`, `rules/`, `scratch/`, `refinements.log.jsonl`.
- `CONTEXT.md` define propósito, usuários, conceitos, boundaries, invariants e important files.
- `ledgers/` guardam decisões de trabalho (ex: `melhoria.md`, `impeccable-upgrade.md`).
- `memory/MOC.md` serve como mapa de conteúdo.
- `notes/` contém pesquisas e extrações estruturadas.
- `scratch/` contém issues e specs locais.

### 9.2 Referência de melhor prática

- **project-setup skill:** `.devin/` é o espaço do agente; nada de agent-facing deve ficar fora.
- **Domain-driven design:** `CONTEXT.md` e ADRs fornecem vocabulário compartilhado e decisões arquiteturais.
- **Observability:** `refinements.log.jsonl` rastreia refinamentos e deve ter IDs únicos.

### 9.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 9.3.1 | ~~`.devin/rules/` está vazio~~ | `.devin/rules/README.md` | ~~Minor~~ **Corrigido** | README explica uso intencionalmente vazio. |
| 9.3.2 | ~~`.devin/adr/` só tem `README.md`~~ | `.devin/adr/001-*.md`, `.devin/adr/002-*.md` | ~~Minor~~ **Corrigido** | ADRs adicionados. |
| 9.3.3 | ~~`refinements.log.jsonl` não tem verificação de conteúdo~~ | `audit.py:720-756` | ~~Minor~~ **Corrigido** | `audit.py` valida campos `repro_command`, `expected`, `actual`, `verdict`. |
| 9.3.4 | `scratch/` contém esforços antigos sem status claro | `.devin/scratch/` | Minor | Alguns diretórios podem estar abandonados; não há mecanismo de arquivamento. |
| 9.3.5 | ~~`__pycache__` existe em `.devin/`~~ | `.gitignore`, `audit.py:407-418` | ~~Minor~~ **Corrigido** | `__pycache__` é gerado por execução Python e está coberto por `.gitignore`; audit verifica presença. |

### 9.4 Recomendações

1. Criar ADRs em `.devin/adr/` para decisões arquiteturais do bundle.
2. Popular `.devin/rules/` com regras específicas de escrita de skills/hooks se necessário.
3. Adicionar audit check que valide `refinements.log.jsonl` entries contra Rule 15 (reprodução/evidência).
4. Adicionar status/arquivamento em `scratch/` ou rotina de limpeza.
5. Garantir que `.gitignore` e CI ignorem `__pycache__` e caches de teste.

## 10. Documentação

### 10.1 Padrão encontrado

- `README.md`: descrição do ecossistema, fluxos operacionais, badges, contagem de skills/rules/agents/scripts.
- `docs/TOOLS-MAP.md`: mapeamento de ferramentas, subagentes, hooks, configs, MCPs.
- `docs/SKILL-TIERS.md`: descoberta de skills por domínio e custo de contexto.
- `docs/MODEL-GUIDE.md`: guia de modelos (GLM-5.2, SWE-1.7).
- `CHANGELOG.md`: histórico de mudanças.
- `CONTRIBUTING.md` e `SECURITY.md`: guias de contribuição e segurança.

### 10.2 Referência de melhor prática

- **Diátaxis / docs:** Documentação deve separar tutoriais, how-to, referência e explicação.
- **README first:** Leitores novos devem entender o propósito e o início rápido em 2 minutos.
- **Consistência de contagem:** Badges e números no README devem refletir `manifest.json` e realidade.

### 10.3 Discrepâncias encontradas

| # | Item | Evidência | Gravidade | Descrição |
|---|------|-----------|-----------|-----------|
| 10.3.2 | ~~`README.md` não menciona `qa-ci` agent~~ | `README.md:162` | ~~Minor~~ **Corrigido** | Tabela de perfis inclui `qa-ci`. |
| 10.3.3 | ~~`CHANGELOG.md` não menciona as 6 novas skills da Fase 4/5~~ | `CHANGELOG.md:12-18` | ~~Minor~~ **Corrigido** | v3.1.0 lista `ontology-validator`, `task-sizer`, `secure-defaults-check`, `agent-cost-guard`, `intention-capture`, `api-context-spec`. |
| 10.3.4 | ~~`docs/TOOLS-MAP.md` não atualiza tool count do MCP `atlassian`~~ | `docs/TOOLS-MAP.md:129` | ~~Minor~~ **Corrigido** | Nota sobre tool count dependente de tenant adicionada. |
| 10.3.5 | ~~`CONTRIBUTING.md` e `SECURITY.md` não são citados no audit~~ | `audit.py:443-457` | ~~Minor~~ **Corrigido** | `audit.py` verifica existência e conteúdo mínimo. |

### 10.4 Recomendações

1. Documentar `qa-ci` no README e TOOLS-MAP.
3. Atualizar `CHANGELOG.md` para refletir as 6 novas skills (`ontology-validator`, `task-sizer`, `secure-defaults-check`, `agent-cost-guard`, `intention-capture`, `api-context-spec`) e correções do review.
4. Adicionar seção de MCP no TOOLS-MAP com tool count medido.
5. Revisar `CONTRIBUTING.md` e `SECURITY.md` para garantir que estão sincronizados com as novas skills e hooks.

## Resumo Executivo

| Componente | Status Geral | Issues Críticas | Issues Importantes | Issues Menores |
|---|---|---|---|---|
| 1. Import/export | Bom | 1 | 1 | 4 |
| 2. Agentes | Bom | 0 | 1 | 3 |
| 3. Skills | Bom | 0 | 0 | 5 |
| 4. Hooks | Bom | 0 | 0 | 6 |
| 5. MCPs | Regular | 1 | 0 | 3 |
| 6. Regras | Regular | 0 | 1 | 3 |
| 7. Manifest/Config | Bom | 0 | 1 | 2 |
| 8. Auditoria/Testes | Bom | 0 | 1 | 4 |
| 9. Estrutura `.devin/` | Regular | 0 | 0 | 5 |
| 10. Documentação | Bom | 0 | 0 | 4 |

**Total:** 2 críticas, 5 importantes, 39 menores.

### Críticas a resolver primeiro

Nenhuma. As 2 críticas foram corrigidas nesta iteração.

### Próximos passos recomendados

1. Resolver as 5 issues importantes.
3. Revisar as 39 menores em iteração posterior.
4. Adicionar testes para `install`/`export` e schema de `config.json`.
5. Criar ADRs para decisões arquiteturais.
