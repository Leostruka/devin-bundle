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
- `5.3.1` RESOLVIDO: `mcp_config.json` agora usa `transport: https`, consistente com a URL `https://mcp.atlassian.com/v1/mcp/authv2`.

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
| 1.3.1 | `install.ps1` e `install.sh` não validam checksum/hash dos arquivos copiados | `install.ps1:58-78`, `install.sh` | Minor | Não há verificação de integridade além de comparação byte-a-byte. Não impede tampering, apenas detecta diferenças. |
| 1.3.2 | `credentials.toml` é copiado apenas com `-RestoreSecrets`/`--restore-secrets` | `install.ps1:22`, `install.sh` | Minor | Boa prática, mas a flag `--restore-secrets` pode ser confundida com "não mascarar"; documentação clara ajuda. |
| 1.3.3 | ~~`export` com `-NoMask`/`--no-mask` permite commit de secrets~~ | `export.ps1:252-258`, `export.sh:423-429`, `scripts/check-push-green.py:76-101` | ~~Critical~~ **Corrigido** | Gate de segurança bloqueia push quando secrets não estão mascarados. `check-push-green.py` também verifica `credentials.toml` e `mcp_config.json`. |
| 1.3.4 | `config.json` usa placeholder `{{APPDATA}}/devin` que é expandido no install e recolapsado no export | `install.sh:76-80`, `export.sh:70-74` | Minor | Mecanismo de placeholder funciona, mas adiciona complexidade e risco de drift se o path contiver caracteres especiais. |
| 1.3.5 | Não há testes automatizados para `install.ps1`/`install.sh` | `tests/` | **Important** | Testes cobrem scripts Python, mas não os instaladores/exporters PowerShell/Bash. Mudanças nesses scripts só são detectadas em uso manual. |
| 1.3.6 | `export.ps1 -Push` faz git push sem re-validar o estado local | `export.ps1:34-35` | **Important** | O export faz validação de JSON/Python antes, mas não re-executa `audit.py` e `pytest` antes do push. Isso contradiz a regra "No push without green". |

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
| 2.3.1 | `qa-ci` tem `exec`/`get_output` mas a descrição diz "Read-only with exec for real test/build/lint runs" | `agents/qa-ci.md` | Minor | Uso de `exec` é adequado para verificação, mas o risco de poluição entre "verificar" e "modificar" precisa ser claro. O perfil não tem `write`/`edit`, o que é correto. |
| 2.3.2 | `reviewer` tem `allowed-tools` incluindo `exec` e `get_output` | `agents/reviewer.md` | Minor | Revisores podem executar testes para verificar, mas idealmente não deveriam escrever. `exec` é aceitável para testes, mas `write`/`edit` deveriam estar ausentes. |
| 2.3.3 | `qa-ci` não é usado no mapeamento de fluxos do README | `README.md:151-167` | Minor | O perfil existe mas não é mencionado na documentação de fluxos. Risco de descoberta baixa. |
| 2.3.4 | `.devin/agents/` mistura domínio, issue tracker e triagem, mas não há agente de `reviewer` de projeto | `.devin/agents/` | Minor | Projetos consumidores podem precisar de reviewer local, mas só há agentes de domínio/issue/triagem. |

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
| 3.3.1 | Várias skills não têm `triggers` no frontmatter | `skills/*/SKILL.md` | Minor | `AGENTS.md:175-178` lista `triggers` como opcional, mas sua ausência reduz a precisão da descoberta automática. |
| 3.3.2 | `leo` skill mistura orquestração com descrições extensas | `skills/leo/SKILL.md` | Minor | Skill orquestradora é crítica e carregada frequentemente; poderia ser mais concisa ou dividida em módulos. |
| 3.3.3 | Habilidades similares (`cost-optimization`, `agent-cost-guard`, `effort-calibration`) podem confundir o usuário sobre qual invocar | `docs/SKILL-TIERS.md` | Minor | Há sobreposição de responsabilidades; não há skill de roteamento claro além de `ask-matt`. |
| 3.3.4 | `ontology-validator`, `task-sizer`, `secure-defaults-check` foram criadas mas não têm scripts de automação | `skills/*` | Minor | Skills são documentação-only; o audit não verifica se têm implementação executável. |
| 3.3.5 | `agent-cost-guard` não integra com `scripts/validate-tool-args.py` de forma explícita | `skills/agent-cost-guard/SKILL.md`, `scripts/validate-tool-args.py` | Minor | A validação de `max_parallel` está no script, mas a skill não menciona o script como mecanismo de enforcement. |

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
| 4.3.1 | `check-push-green.py` timeout de 60s pode ser curto para suites grandes | `scripts/check-push-green.py:24` | Minor | Suites de teste maiores podem estourar 60s, fazendo o hook "fails open" e permitindo push com testes lentos. |
| 4.3.2 | `silent-error-review.py` pode gerar falsos positivos | `tests/held-out/mutation/test_silent_error_new_indicators.py` | Minor | Testes de mutação mostram histórico de ajustes; o regex ainda pode confundir warning+error. |
| 4.3.3 | `context-pressure.py` não tem teste de unidade | `scripts/context-pressure.py` | Minor | Script mede pressão de contexto mas não há teste automatizado direto. |
| 4.3.4 | `validate-tool-args.py` não bloqueia `max_parallel` não-inteiro (corrigido em `c86342d`) | `scripts/validate-tool-args.py` | Minor | Correção recente valida tipo, mas não há teste específico para string/ float. |
| 4.3.5 | `PermissionRequest` não tem handler ativo | `config.json`, `hooks.v1.json` | Minor | Evento é suportado mas sem hook; isso é aceitável, mas documentar como intencional. |
| 4.3.6 | `SessionEnd` e `Stop` compartilham `memory-stop.py`; `Stop` também chama `refine-review-prompt.py` | `config.json`, `hooks.v1.json` | Minor | Duplicação leve; `memory-stop.py` em dois eventos pode gerar logs duplicados. |

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
| 5.3.2 | Não há documentação do número de tools do `atlassian` no bundle | `docs/TOOLS-MAP.md` | Minor | TOOLS-MAP.md menciona `atlassian` mas não lista a contagem real de tools. |
| 5.3.3 | `mcp_config.json` não é validado por `audit.py` | `audit.py` | Minor | Audit valida JSON mas não a estrutura MCP (server, transport, tool count). |
| 5.3.4 | Não há mecanismo de fallback se `atlassian` não estiver autenticado | `mcp_config.json` | Minor | Configuração contém URL mas não indica se requer autenticação prévia. |

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
| 6.3.1 | `AGENTS.md` é longo (~250 linhas) e carrega em toda sessão | `AGENTS.md` | **Important** | Regras pinned ocupam contexto; versão atual tem 26 regras, algumas com parágrafos longos. Isso contradiz a própria regra 18 de manter regras enxutas. |
| 6.3.2 | `.devin/rules/` está vazio | `Get-ChildItem .devin/rules` | Minor | O bundle não usa regras específicas por domínio em `.devin/rules/`, apesar da convenção existir. |
| 6.3.3 | `.devin/adr/` contém apenas `README.md` | `find .devin/adr` | Minor | Não há ADRs reais documentando decisões arquiteturais do bundle (ex: por que placeholder `{{APPDATA}}/devin`, por que 82 skills, por que SWE-1.7). |
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
| 7.3.2 | `config.json` não é validado por schema | `audit.py` | Minor | JSON é validado, mas não há schema check de hooks/eventos/sintaxe. |
| 7.3.3 | `manifest.json` não versiona scripts nem agentes por hash | `manifest.json` | Minor | Scripts e agentes não têm hash/export_hash; só skills têm. Isso dificulta detectar drift. |
| 7.3.4 | `config.json` atribui `attribution: false` sem explicar o impacto | `config.json:11` | Minor | `attribution` desligado pode afetar logs de uso/custo; deveria ser documentado. |

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
| 8.3.1 | `audit.py` não valida `install.ps1`/`install.sh`/`export.ps1`/`export.sh` | `audit.py` | **Important** | Os scripts de sincronização são críticos para a função do repo, mas não têm checks estruturais. |
| 8.3.2 | `audit.py` não valida conteúdo de `AGENTS.md` contra número de regras | `audit.py:82-100` | **Important** | O audit valida que 26 regras estão presentes, mas o padrão de numeração inclui 27 números (1-27) com 26 regras presentes. |
| 8.3.3 | Não há testes para `config.json` schema ou hooks | `tests/validation/` | Minor | Testes não cobrem validação do schema de `config.json` ou `hooks.v1.json`. |
| 8.3.4 | `tests/` não cobrem todos os 82 skills | `tests/validation/test_skill_format_passes.py` | Minor | Apenas formato de frontmatter é testado, não conteúdo/qualidade das skills. |
| 8.3.5 | `audit.py` emite warnings repetidos sobre "unable to find all commit-graph files" | `git status`, `git log` | Minor | Warning não impede funcionamento, mas indica configuração de git incompleta. |

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
| 9.3.1 | `.devin/rules/` está vazio | `Get-ChildItem .devin/rules` | Minor | O bundle não usa regras específicas do projeto além de `global_rules.md`. |
| 9.3.2 | `.devin/adr/` só tem `README.md` | `find .devin/adr` | Minor | Faltam ADRs documentando decisões do bundle. |
| 9.3.3 | `refinements.log.jsonl` não tem verificação de conteúdo além de ID único | `audit.py` | Minor | Audit valida unicidade de IDs, mas não valida se cada entrada tem reprodução/evidência (Rule 15). |
| 9.3.4 | `scratch/` contém esforços antigos sem status claro | `.devin/scratch/` | Minor | Alguns diretórios podem estar abandonados; não há mecanismo de arquivamento. |
| 9.3.5 | `__pycache__` existe em `.devin/` | `.devin/__pycache__/` | Minor | Cache Python não deveria ser rastreado; `.gitignore` cobre, mas a presença indica execução de scripts no diretório. |

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
| 10.3.2 | `README.md` não menciona `qa-ci` agent | `README.md:151-167` | Minor | Perfil `qa-ci` existe mas não é documentado. |
| 10.3.3 | `CHANGELOG.md` não menciona as 6 novas skills da Fase 4/5 | `CHANGELOG.md:1-15` | Minor | Versão 3.1.0 lista melhorias gerais, mas não detalha as novas skills. |
| 10.3.4 | `docs/TOOLS-MAP.md` não atualiza tool count do MCP `atlassian` | `docs/TOOLS-MAP.md:127-135` | Minor | Documentação menciona verificação, mas não fornece contagem. |
| 10.3.5 | `CONTRIBUTING.md` e `SECURITY.md` não são citados no audit | `audit.py` | Minor | Audit valida existência, mas não conteúdo. |

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
