# Auditoria Arquitetural e de Boas Práticas — `devin-bundle`

- **Repositório:** `leostruka/devin-bundle` (cópia local auditada)
- **Data:** 2026-09-09
- **Escopo:** configurações globais exportáveis do bundle (arquivos instalados em `%APPDATA%/devin` / `~/.config/devin` e templates `.devin/`)
- **Artefato:** relatório gerado exclusivamente em `.devin/GLOBAL_BUNDLE_AUDIT.md`
- **Ação:** análise estratégica; nenhum arquivo de código foi alterado

## 1. Objetivo e metodologia

O objetivo desta auditoria é avaliar se cada componente do bundle pode ser exportado para qualquer projeto/usuário sem conhecimento prévio de domínios, caminhos, modelos, nomes de pessoas ou organizações. Foram inspecionados:

- `manifest.json`, `config.json`, `AGENTS.md`, `mcp_config.json`, `hooks.v1.json`, `.devin/hooks.v1.json`
- Perfis de agentes em `agents/` e `.devin/agents/`
- 82 skills em `skills/<nome>/SKILL.md`
- 17 scripts Python de hook em `scripts/`
- Instaladores/exportadores `install.ps1`, `install.sh`, `export.ps1`, `export.sh`
- Documentação, ADRs, ledgers, testes e notas locais

Padrões de busca executados com `grep`:

- nomes próprios/organizacionais: `Leostruka`, `leand`, `matt-pocock`, `pocock`
- tecnologias/dominios específicos: `youtube`, `atlassian`, `jira`, `confluence`
- modelos: `glm-5-2`, `swe-1-7`, `swe-1.7`, `subagent_explore`
- versão CLI: `3000.6.14`
- caminhos locais: `%APPDATA%`, `~/.config/devin`, `C:\`, `D:\`
- plataformas: `Windows`, `PowerShell`, `WSL`, `Linux`, `macOS`

## 2. Checklist de universalidade

### 2.1 Metadados globais do bundle

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `README.md` | Referencia `github.com/Leostruka/devin-bundle` em badges e instruções de clone (l. 3, 14, 22), ano/copyright `2026 Leostruka` (l. 561), explica instalação via `install.ps1` / `install.sh` com paths Windows/Unix (l. 13-25, 426-477) e versão CLI `3000.6.14` (l. 40). | Hardcoded local (autor, repo, plataforma, versão). | Parametrizar `{{BUNDLE_OWNER}}`, `{{BUNDLE_REPO}}`, `{{BUNDLE_NAME}}`, `{{VALIDATED_CLI_VERSION}}`; manter instruções multi-plataforma, mas retirar clone do repo do autor como passo obrigatório. |
| `CHANGELOG.md` | Histórico detalhado de evolução do bundle com correções de paths (`C:\Users\leand...`, l. 501, 700), menções a Matt Pocock, Jira, Atlassian, GLM-5.2/SWE-1.7 e `3000.6.14`. | Hardcoded local e histórico de trabalho pessoal. | Manter como log do bundle, mas mascarar/remover paths de usuário; separar notas de release públicas de diário de trabalho. |
| `LICENSE` | Copyright `2026 Leostruka` (l. 3). | Hardcoded local (detentor). | Usar `{{BUNDLE_OWNER}}` ou manter como placeholder. |
| `manifest.json` | Inventário completo com `original_path: "%APPDATA%\\devin\\skills\\..."` para todos os skills (82x) e agents (6x); `rules.targets` hardcoded `windows`/`linux`/`macos` com `%APPDATA%`/`~/.config` (l. 6-10); timestamps `exported_at` e hashes de exportação. | Parcialmente globalizável (os metadados de export refletem a máquina de origem; os destinos são os paths canônicos do Devin CLI). | `original_path` e `exported_at` são audit-trail aceitáveis, mas devem ser gerados dinamicamente pelo exportador, não versionados como runtime; `rules.targets` é correto, porém pode ser movido para `install.json`. |

### 2.2 Regras globais

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `AGENTS.md` | Regras globais em português/inglês com menções específicas a `GLM-5.2 High` e `SWE-1.7` na Rule 20 (l. 31, 168, 201-214), citação de preços/custo, `docs/MODEL-GUIDE.md`, e pinned constraints. | Hardcoded local (política de modelos do autor). | Criar `bundle-models.json` ou variáveis de ambiente `BUNDLE_DEFAULT_MODEL`, `BUNDLE_SUBAGENT_MODEL`; AGENTS.md referenciar esse arquivo. Separar regras universais (comportamentais) das regras de routing de modelos. |

### 2.3 Configurações de runtime

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `config.json` | `agent.model: "glm-5-2"` (l. 8); `org_id: "MASKED"` (l. 4); hooks usam placeholder `{{APPDATA}}/devin/scripts/...` (l. 32-67 etc.); UI específica (`theme_mode: dark`, `mouse_capture: true`, `pty_for_noninteractive_exec: true`, `auto_update: true`). | Parcialmente globalizável: modelo e preferências UI são opiniões locais; `{{APPDATA}}` é um bom placeholder; `org_id` é mascarado. | Tornar `agent.model` e `theme_mode` parametrizáveis via `bundle-models.json`/env; manter `org_id: MASKED`; manter `{{APPDATA}}`. |
| `hooks.v1.json` e `.devin/hooks.v1.json` | Mesmo conteúdo: comandos `python scripts/...` relativos. | Preparado para exportação, mas assume que o diretório `scripts/` está no PATH ou no cwd do projeto. | Normalizar para `python "{{APPDATA}}/devin/scripts/..."` ou descobrir `DEVIN_HOME` no hook. |
| `mcp_config.json` | Servidor `atlassian` hardcoded (l. 3-6). | Hardcoded local (servidor específico do autor). | Converter em template: `mcp_config.json.example` sem servidor ativo; gerar `mcp_config.json` a partir de `BUNDLE_MCP_SERVERS` ou do exportador. |
| `.devin/mcp_config.json` | `mcpServers: {}` (vazio). | Preparado para exportação global (template limpo). | Manter como template vazio e copiar para `.devin/mcp_config.json` no `project-setup`. |

### 2.4 Perfis de agentes (raiz e `.devin/`)

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `agents/*.md` (6 perfis) | Todos usam `model: swe-1-7` (architect, debugger, implementer, qa-ci, researcher, reviewer). Não há distinção entre `swe-1-7` (Max) e `swe-1-7-medium`. | Parcialmente globalizável: o modelo é hardcoded, mas o perfil é reutilizável. A falta de granularidade Max/Medium é o principal gap. | Dividir conforme carga cognitiva (ver Matriz de Delegação). Ler modelos de `bundle-models.json`/env. |
| `.devin/agents/*.md` | Referenciam `.devin/CONTEXT.md`, `.devin/adr/`, `.devin/scratch/`, vocabuários locais (domain.md, issue-tracker.md, triage-labels.md, reviewer.md). | Projeto local (não exportado pelo `install.sh`/`install.ps1`). | Manter como templates; remover menções a nomes de projetos/ADRs específicos e usar placeholders. |

### 2.5 Dados de contexto e scripts de hook

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `data/model-context-windows.json` | Lista hardcoded de modelos `glm-5-2`, `swe-1-7`, `swe-1-7-medium`, `swe-1-7-lightning`, `swe-1-6` com janelas. | Hardcoded local (catálogo de modelos do autor). | Parametrizar: `models` deve ser gerido pelo `bundle-models.json`; manter overrides por env `DEVIN_MODEL_REGISTRY`. |
| `scripts/context-pressure.py` | `DEFAULT_WINDOW = 200_000` (GLM-5.2), comentário sobre Matt Pocock (l. 15), `RECIPES` com `preferred_model` hardcoded (`claude-sonnet-4-6`, `gemini-3-7-flash`, `swe-1-7`, `glm-5-2`). | Hardcoded local (default de modelo e referências pessoais). | Ler defaults de `bundle-models.json`; remover referências a pessoas; recipes em config separada. |
| `scripts/context-budget.py` | `SMART_ZONE_TOKENS = 100_000`, comentários sobre Matt Pocock (l. 23, 27, 55). | Hardcoded local (threshold e referências pessoais). | Mover thresholds para `data/context-budget.json`; remover referências pessoais. |
| `scripts/memory-retrieval.py` | `BASE = '.devin/memory'` hardcoded (l. 14). | Preparado para padrão Devin, mas não parametrizável. | Aceitar `DEVIN_MEMORY_DIR` ou `BUNDLE_MEMORY_DIR` com fallback `.devin/memory`. |
| `scripts/memory-post-edit.py`, `memory-post-exec.py`, `memory-stop.py` | Operam sobre `.devin/memory/`. | Idem acima. | Ler diretório de memória de variável/argumento. |
| `scripts/validate-skill-format.py`, `validate-tool-args.py`, etc. | Validadores genéricos, sem hardcoded local. | Preparado para exportação. | Manter. |
| `scripts/mermaid-parse-check.js` | Helper de parsing. | Preparado. | Manter. |
| `audit.py` | Valida estrutura, JSON, manifest, hashes, secret masking. Auto-detecta live base com `%APPDATA%` / `~/.config` (l. 474-481). | Preparado para exportação (usa variáveis de ambiente canônicas). | Adicionar checks para hardcoded local (autor, paths, modelos). |

### 2.6 Instaladores e exportadores

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `install.ps1` / `export.ps1` | PowerShell com paths `APPDATA`, `%USERPROFILE%`, conversões de encoding/case-sensitivity específicas Windows/WSL. Instala `docs/` no Windows (install.ps1 l. 549-561), mas `install.sh` não instala docs. | Parcialmente globalizável: plataforma específica, e inconsistência entre OS. | Unificar lógica comum em Python puro (`install.py`, `export.py`) com front-ends leves PS/Bash; parametrizar `BUNDLE_DIR` e `DEVIN_HOME`; sincronizar o que é exportado em ambas as plataformas. |
| `install.sh` / `export.sh` | Bash com `~/.config`, `XDG_CONFIG_HOME`, macOS/Darwin sed; não instala `docs/` nem `hooks.v1.json`. | Idem acima. | Mesma recomendação. |
| `devin-N.cmd` / `devin-N.ps1` / `devin-session-launcher.ps1` | Launchers Windows. | Hardcoded local (plataforma Windows, alias pessoais). | Mover para `tools/windows/` ou converter em templates. |

### 2.7 Documentação

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `docs/SKILL-TIERS.md` | Categoriza skills com nomes como `setup-matt-pocock-skills`, `jira`, `youtube-fetcher` e cita `GLM-5.2/SWE-1.7` (l. 10-15, 183-207). | Hardcoded local (referências a pessoas, modelos e integrações específicas). | Renomear/desacoplar nomes pessoais; referenciar modelos de `bundle-models.json`; manter referências funcionais. |
| `docs/MODEL-GUIDE.md` | Catálogo de modelos com preços, contextos, política free/paid; `glm-5-2`, `swe-1-7`, `swe-1-7-medium` etc. (tabela l. 156-163 e seções). | Hardcoded local (guia de modelos do autor). | Transformar em `bundle-models.json` ou `models.toml` que alimenta tanto a doc quanto os scripts; manter MODEL-GUIDE como explicação, mas sem hardcoded. |
| `docs/TOOLS-MAP.md` | Mapeia tools, subagentes e MCP Atlassian; comentário "não funciona no WSL sem credenciais Windows" (l. 129). | Hardcoded local (servidor atlassian, nota WSL específica). | Mover MCP Atlassian para `mcp_config.json.example`; notas de WSL para troubleshooting local. |
| `docs/DEVIN-CLI-COMPATIBILITY.md` | Versão `3000.6.14` e detalhes de versões intermediárias (l. 5-14). | Hardcoded local (versão específica). | Parametrizar `{{VALIDATED_CLI_VERSION}}` e `{{CLI_VERSIONS}}`; gerar a partir do exportador. |
| `docs/AI-CODING-DICTIONARY.md` | Glossário genérico. | Preparado para exportação. | Manter. |
| `docs/plans/*.md` | Planos de trabalho com nomes de pessoas (`matt-pocock`, `Matt Pocock`), vídeos YouTube, datas e repositórios. | Projeto local (não exportado por padrão). | Manter em `.devin/plans/` ou `docs/plans/` como documentação de projeto, não parte do bundle global. |

### 2.8 Skills (`skills/`)

Foram avaliadas as 82 skills declaradas em `manifest.json` (l. 13-669). A seguir, as observadas como específicas ou acopladas a domínio/modelo/pessoa. As demais 50+ skills genéricas (git, tdd, testing, deploy, database, docker, i18n, api-design, security, a11y, etc.) estão classificadas como **Preparadas para exportação global**, desde que os scripts auxiliares respeitem `BUNDLE_MODELS`.

| Skill | Padrão atual | Acoplamento | Recomendação | Delegação |
|-------|--------------|-------------|--------------|-----------|
| `youtube-fetcher` | Adapter exclusivo para URLs YouTube; paths `.devin/notes/youtube/`; host allowlist fixa (`youtube.com`, `youtu.be`); adaptado de JimmySadek (l. 2-67). | Hardcoded local (domínio único). | Transformar em `video-transcript-fetcher` genérico com adapters plugináveis; YouTube vira adapter opcional. | Medium |
| `jira` | Operações via MCP `atlassian` e site `guilhermerissi04112006.atlassian.net` com `cloudId` fixo (l. 24-28); comandos `mcp__atlassian__*`. | Hardcoded local (instância Jira específica). | Parametrizar `JIRA_SITE`, `JIRA_CLOUD_ID` via env/`bundle-integrations.json`; manter Atlassian como exemplo. | Medium |
| `setup-matt-pocock-skills` | Nome e propósito amarrados ao workshop de Matt Pocock (l. 2, 7). | Hardcoded local (nome de pessoa/tema). | Renomear para `setup-engineering-skills` ou `project-engineering-flow`; mover conteúdo para config parametrizável. | Max |
| `mcp-context-audit` | Exemplos com `atlassian` (l. 54, 60, 66, 21 do script). | Parcialmente local (exemplo específico). | Usar placeholder `{{EXAMPLE_MCP_SERVER}}`; manter ferramenta genérica. | Medium |
| `mcp-lazy-enablement` | Cita Jira e Atlassian como exemplo (l. 25, 50). | Parcialmente local. | Generalizar exemplos para "MCP específico da tarefa". | Max |
| `context-window-hygiene` | Citações a Matt Pocock e vídeo do YouTube (l. 16, 51, 103-105). | Parcialmente local (referências pessoais). | Remover nomes; manter conceitos (smart/dumb zone). | Max |
| `memory-hygiene` | Cita "Kill your MEMORY.md (Matt Pocock, YouTube)" (l. 65). | Parcialmente local. | Remover referência pessoal; manter tese. | Max |
| `effort-calibration` | Cita "Your effort level is TOO DAMN HIGH (Matt Pocock, YouTube)" (l. 71). | Parcialmente local. | Idem. | Max |
| `primeagent-reference` | Cita GLM-5.2/SWE-1.7 e benchmarks específicos (l. 135, 368, 432, 545, 792). | Hardcoded local (modelos). | Ler modelos de `bundle-models.json`; manter links para PrimeAgent como referência, não prescrição. | Max |
| `continuous-improvement` | Cita GLM-5.2/SWE-1.7 (l. 51, 151, 291). | Hardcoded local (modelos). | Parametrizar modelos; manter loop. | Max |
| `leo` | Referencia `3000.6.14`, `glm-5-2`, `swe-1-7`, `subagent_explore` PAGO (l. 88-89, 193); manda rodar `python audit.py` e `python -m pytest` (l. 7). | Hardcoded local (versão CLI, modelos, ferramentas de verificação). | Parametrizar via `bundle-models.json` e `bundle-verification.json`; comandos de verificação devem ser descobertos do projeto. | Max |
| `dispatching-parallel-agents` | Cita `subagent_general` herda GLM-5.2, `swe-1-7` vs GLM-5.2 performance (l. 144, 431-441, 453-457). | Hardcoded local (modelos e comparações). | Parametrizar modelos; manter lógica de roteamento. | Max |
| `self-extend` | Menciona paths `~/.config/devin/` e `%APPDATA%\devin\` como destinos (l. 10, 41). | Preparado para exportação (paths canônicos do CLI). | Manter. | Max |
| `obsidian-workflow` | Menciona `tree`/`ls -R`/`Get-ChildItem` por plataforma (l. 972). | Preparado (comandos multi-plataforma). | Manter. | Medium |
| `context7` | Instruções Windows/Linux para usar CLI `context7` (l. 22-28). | Preparado (documenta instalação por plataforma). | Manter. | Medium |
| `improve-codebase-architecture` | Abre HTML no OS temp com `xdg-open`/`open`/`start` (l. 68). | Preparado (multi-plataforma). | Manter. | Max |
| `code-review` | Cita `mattpocock/sandcastle` como modelo mental (l. 54); skill usa conceito push/pull. | Parcialmente local (referência pessoal). | Generalizar para "modelo push/pull de revisão"; manter Sand Castle como referência opcional. | Max |
| `tool-and-skill-discovery` | Cita `github:Leostruka/devin-bundle` como this bundle (l. 45) e exemplo Windows `%APPDATA%`. | Hardcoded local (autor/repo). | Parametrizar `{{BUNDLE_REPO}}`; manter path canônico. | Max |
| `ask-matt` | Cita `setup-matt-pocock-skills` (l. 95); nome do skill amarra pessoa. | Hardcoded local (nome). | Renomear skill/fluxo para `ask-bundle` ou `route-skills`; atualizar referência. | Max |
| `triage` | Indica `setup-matt-pocock-skills` (l. 43). | Parcialmente local. | Generalizar para setup de issue tracker. | Max |
| `project-setup` | Cria `.devin/global_rules.md` e `.devin/skills/setup-matt-pocock-skills/` (l. 95, 111, 211). | Parcialmente local (referência a skill pessoal). | Generalizar para fluxo de engenharia parametrizável. | Max |
| `writing-for-agents`, `writing-skills` | Genéricas. | Preparado. | Manter. | Max |
| `grilling`, `wayfinder`, `prototype`, `planning-pipeline`, `writing-plans`, `executing-plans`, `codebase-design`, `domain-modeling`, `improve-codebase-architecture`, `legacy-refactor`, `handoff` | Planejamento e arquitetura. | Preparado (exceto menções a modelos acima). | Manter; garantir que chamem `bundle-models.json`. | Max |
| `tdd`, `implement`, `git-helper`, `using-git-worktrees`, `gh`, `pr-review`, `finishing-a-development-branch`, `setup-pre-commit`, `e2e-testing`, `docker`, `i18n`, `database`, `api-design`, `security-audit`, `a11y-audit`, `performance`, `observability-quality`, `mutation-testing`, `verification-before-completion`, `diagnosing-bugs`, `debug-ci-failures`, `resolving-merge-conflicts` | Execução, testes, revisão concreta, ferramentas. | Preparado (salvo modelos acima). | Manter; `setup-pre-commit` e similares devem descobrir toolchain do projeto. | Medium |

### 2.9 Repositório local (não exportado globalmente)

Os itens a seguir fazem parte do workspace do bundle e **não são copiados** para `%APPDATA%/devin` ou `~/.config/devin` pelo `install.sh`/`install.ps1` (exceto `docs/`, que o `.ps1` copia inconsistentemente). Classificam-se como **Projeto local**.

| Item | Padrão atual | Acoplamento | Recomendação |
|------|--------------|-------------|--------------|
| `.devin/CONTEXT.md` | Vocabulário e fronteiras do bundle. | Projeto local. | Manter; é regra de projeto. |
| `.devin/global_rules.md` | Regras de projeto; referencia `.devin/CONTEXT.md` e `.devin/scratch/` (l. 5, 13, 25). | Projeto local. | Manter como template genérico. |
| `.devin/hooks.v1.json` | Template de hooks com `python scripts/...`. | Template globalizável. | Manter em `.devin/` como template; gerar `hooks.v1.json` do projeto a partir dele. |
| `.devin/mcp_config.json` | Vazio. | Template globalizável. | Manter. |
| `.devin/agents/*.md` | Agentes locais (domain, issue-tracker, triage-labels, reviewer). | Projeto local. | Manter como templates; generalizar vocabuários. |
| `.devin/adr/` | ADRs `001-apdata-placeholder.md`, `002-subagent-model-swe-1-7.md`. | Projeto local. | Manter como registro de decisões do bundle. |
| `.devin/notes/` | Notas, transcrições de YouTube, knowledge graph. | Projeto local. | Não exportar; manter como conhecimento de projeto. |
| `.devin/ledgers/` | Registros de melhoria contínua, PoC, experimentos. | Projeto local. | Não exportar. |
| `.devin/scratch/` | Issues e stubs locais. | Projeto local. | Não exportar. |
| `ledgers/` (raiz) | Diários de trabalho, planos de melhoria. | Projeto local. | Mover para `.devin/ledgers/` para respeitar regra de ouro (artefatos de IA sobre IA em `.devin/`). |
| `docs/plans/` | Planos com menções a Matt Pocock, YouTube, datas. | Projeto local. | Mover para `.devin/plans/` e limpar referências pessoais. |
| `tests/` e `tests/fixtures/` | Testes do bundle; fixtures específicas para `youtube-fetcher`, `mcp`, `grilling-frontier`. | Projeto local. | Manter; fixtures de domínio devem ser acompanhadas de adapters genéricos. |
| `.github/` (templates, CI) | Templates de issue/PR e `ci.yml` genérico. | Preparado para exportação (não copiado pelo instalador, mas repo template). | Manter; CI deve validar universalidade futuramente. |

## 3. Matriz de Delegação (SWE-1.7 Max vs SWE-1.7 Medium)

A tabela a seguir indica onde cada componente deve ser roteado considerando a carga cognitiva e a natureza do trabalho. `Max` = planejamento, arquitetura, orquestração, decisões com trade-offs. `Medium` = execução isolada, manipulação de arquivo, testes, verificações mecânicas.

### 3.1 Perfis de subagentes

| Perfil | Responsabilidade | Roteamento | Justificativa |
|--------|------------------|------------|---------------|
| `architect` | Decisões arquiteturais, trade-offs, deep module design. | **Max** | Planejamento e design de alto nível. |
| `researcher` | Reconhecimento de codebase, fontes externas, síntese. | **Max** | Leitura/síntese complexa e exploração não linear. |
| `reviewer` | Revisão de spec e standards, julgamento de conformidade. | **Max** | Requer julgamento sobre spec e arquitetura. |
| `debugger` | Reprodução e análise sistemática de falhas. | **Medium** | Tarefa focada de investigação com heurísticas. |
| `implementer` | Código, testes, verificação de escopo delimitado. | **Medium** | Execução isolada. |
| `qa-ci` | Verificação independente de testes, build, lint. | **Medium** | Execução de gates. |

### 3.2 Skills por domínio

| Domínio | Skills | Roteamento | Justificativa |
|---------|--------|------------|---------------|
| Ideação e decisão | `grilling`, `wayfinder`, `prototype`, `research` | **Max** | Decisões antes de construir. |
| Planejamento e orquestração | `planning-pipeline`, `writing-plans`, `executing-plans`, `leo`, `afk-loop`, `autonomous-gates`, `unlazy` | **Max** | Orquestração e planejamento multi-passo. |
| Arquitetura e design | `codebase-design`, `improve-codebase-architecture`, `domain-modeling`, `legacy-refactor`, `primeagent-reference` | **Max** | Design, modelagem, refatoração estratégica. |
| Implementação e testes | `implement`, `tdd`, `setup-pre-commit`, `e2e-testing`, `mutation-testing`, `verification-before-completion`, `diagnosing-bugs`, `debug-ci-failures` | **Medium** | Execução de código/testes. |
| Git, PR e entrega | `git-helper`, `using-git-worktrees`, `gh`, `pr-review`, `finishing-a-development-branch`, `deploy` | **Medium** | Operações mecânicas e verificações. |
| Qualidade e revisão | `code-review` (spec), `receiving-code-review`, `security-audit`, `a11y-audit`, `observability-quality` | **Max/Medium** | Spec/review → Max; verificações de conformidade → Medium. |
| Infra e especialidades | `api-design`, `database`, `docker`, `performance`, `i18n` | **Mixed** | Design (Max); execução de scripts/Docker (Medium). |
| Contexto e memória | `context-folding`, `context-window-hygiene`, `memory-hygiene`, `project-memory`, `handoff` | **Max** | Gestão de contexto e abstração. |
| Integrações específicas | `youtube-fetcher`, `jira`, `mcp-context-audit`, `mcp-lazy-enablement`, `obsidian-workflow`, `data-analyst` | **Medium** | Uso de ferramentas/integrações concretas. |
| Configuração do ecossistema | `project-setup`, `self-extend`, `setup-matt-pocock-skills`, `devin-manager`, `continuous-improvement` | **Max** | Decisões de setup e melhoria. |
| Dicionário/glossário | `ai-coding-dictionary`, `ask-matt`, `tool-and-skill-discovery` | **Max** | Roteamento e explicação de conceitos. |

### 3.3 Scripts e rotinas

| Rotina | Roteamento | Justificativa |
|--------|------------|---------------|
| `context-pressure.py`, `context-budget.py` | **Medium** | Medição periódica e aviso. |
| `memory-retrieval.py`, `memory-post-*.py` | **Medium** | Operações de memória. |
| `constraint-pinning.py`, `behavioral-nudge.py` | **Medium** | Re-injeção de regras. |
| `check-ai-signature.py`, `check-push-green.py`, `destructive-gate.py` | **Medium** | Validações automáticas. |
| `validate-*.py`, `mermaid-parse-check.js` | **Medium** | Validações de formato/sintaxe. |
| `refine-review-prompt.py` | **Max** | Geração de prompts de revisão/self-improvement. |

## 4. Recomendações de refatoração para template global

1. **Modelos e model routing**
   - Criar `bundle-models.json` (ou `models.toml`) central com modelos suportados, janelas, preços, aliases free/paid.
   - `AGENTS.md`, `config.json`, `data/model-context-windows.json`, `scripts/context-pressure.py`, `scripts/context-budget.py`, `docs/MODEL-GUIDE.md`, `docs/SKILL-TIERS.md` e todas as skills devem ler desse arquivo.
   - Introduzir `BUNDLE_MODELS` e `BUNDLE_DEFAULT_MODEL` como variáveis de ambiente.

2. **Integrações e plugins**
   - Criar diretório `integrations/` (ou `plugins/`) contendo `jira`, `youtube-fetcher`, `obsidian-workflow`, `atlassian-mcp`.
   - Cada integração lê `bundle-integrations.json` com credenciais/URLs/parametrizadas.
   - `mcp_config.json` raiz vira `mcp_config.json.example`; o exportador gera `mcp_config.json` com integrações ativas.

3. **Identidade e branding**
   - Substituir `Leostruka`, `devin-bundle`, `2026 Leostruka` em `README.md`, `LICENSE`, `manifest.json`, `tool-and-skill-discovery` por placeholders.
   - Criar `bundle-identity.json` (`name`, `owner`, `repo`, `license`, `validated_cli_version`).
   - `install.ps1`/`install.sh` expandem esses placeholders no `README.md`/badges durante export.

4. **Instalador unificado**
   - Extrair lógica comum para `install.py`/`export.py` em Python 3 stdlib.
   - `install.ps1` e `install.sh` viram wrappers que chamam o Python.
   - Garantir que `docs/`, `data/`, `scripts/`, `agents/`, `skills/` sejam instalados de forma idêntica em Windows, Linux, macOS e WSL.

5. **Hooks e scripts resilientes**
   - `memory-*.py` aceitam `DEVIN_PROJECT_DIR` ou `BUNDLE_MEMORY_DIR`.
   - `context-pressure.py` e `context-budget.py` leem thresholds e defaults de `data/` e `bundle-models.json`.
   - `hooks.v1.json` e `.devin/hooks.v1.json` usam `{{APPDATA}}/devin/scripts` ou resolvem `DEVIN_HOME`.

6. **Agentes com Max/Medium**
   - Criar versões de perfis: `architect.md`, `researcher.md`, `reviewer.md` com `model: swe-1-7` (Max).
   - Criar `debugger.md`, `implementer.md`, `qa-ci.md` com `model: swe-1-7-medium` (Medium).
   - Atualizar `leo`, `dispatching-parallel-agents` e `docs/TOOLS-MAP.md` para refletir o split.

7. **Documentação local vs bundle**
   - Mover `ledgers/`, `docs/plans/`, `.devin/notes/`, `.devin/ledgers/` e `.devin/scratch/` para dentro de `.devin/` (já estão, exceto `ledgers/` e `docs/plans/`).
   - Documentar claramente que `docs/` pode ser copiado opcionalmente, mas o bundle runtime depende apenas de `AGENTS.md`, `agents/`, `skills/`, `scripts/`, `data/`, `config.json`, `mcp_config.json`.

## 5. Condição de parada

- [x] Plano de auditoria aprovado pelo usuário.
- [x] Estrutura do bundle inspecionada com `find_file_by_name`, `read`, `grep`.
- [x] Checklist de universalidade produzido para todos os diretórios e arquivos de configuração global.
- [x] Para cada item: padrão atual, nível de acoplamento e recomendação de refatoração documentados.
- [x] Matriz de Delegação (Max vs Medium) incluída para agentes, skills e rotinas.
- [x] Relatório salvo estritamente em `.devin/GLOBAL_BUNDLE_AUDIT.md`.

## 6. Conclusão

O `devin-bundle` é um ecossistema maduro e bem estruturado, mas ainda carrega camadas de acoplamento local que impedem sua exportação limpa para qualquer projeto:

1. **Acoplamento a identidade:** `Leostruka`, `devin-bundle`, `2026 Leostruka` aparecem em README, LICENSE e skills.
2. **Acoplamento a modelos:** `glm-5-2` e `swe-1-7` estão hardcoded em regras, configurações, scripts, data e documentação, sem abstração central.
3. **Acoplamento a integrações específicas:** `atlassian`/`jira` e `youtube-fetcher` são domínios únicos, com instâncias/URLs/canais fixos.
4. **Acoplamento a pessoas:** referências a Matt Pocock/pocock e derivados (`setup-matt-pocock-skills`) poluem skills e docs.
5. **Instalador plataforma-divergente:** Windows instala `docs/`, Unix não; lógica duplicada entre PS e Bash.
6. **Roteamento de modelos homogêneo:** todos os perfis customizados usam `swe-1-7`, desperdiçando o potencial de `swe-1-7-medium` para tarefas de execução.

A refatoração sugerida prioriza a criação de `bundle-identity.json`, `bundle-models.json` e `bundle-integrations.json` como camadas de abstração, transformando o bundle em um template verdadeiramente agnóstico. A separação de responsabilidades entre `SWE-1.7 Max` (planejamento/arquitetura/orquestração) e `SWE-1.7 Medium` (execução/verificação/manipulação de arquivos) deve ser refletida nos perfis `agents/*.md` e nas rotinas de orquestração `leo` e `dispatching-parallel-agents`.

