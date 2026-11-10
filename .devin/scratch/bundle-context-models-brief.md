# devin-bundle - Contexto, Blueprint, Organização + Modelos Gratuitos (SWE-2 / SWE-2 Flash)

Gerado em 2026-11-09. Fontes internas: `.devin/CONTEXT.md`, `.devin/ARCHITECTURE_MANIFEST.md`, `.devin/docs/PROJECT-STATE-2026-11-08.md`, `.devin/docs/MODEL-GUIDE.md`, `.devin/SWE2_MIGRATION_LOG.md`, `data/bundle-models.json`, `README.md`, `manifest.json`, `config.json`, `hooks.v1.json`. Fontes externas citadas no fim.

---

## 1. O QUE É O PROJETO (resumo executivo)

`devin-bundle` é o repositório que **versiona e sincroniza um setup completo do Devin CLI** entre máquinas (Windows, Linux, macOS, WSL). Ele distribui regras globais, skills, perfis de subagentes, hooks de governança, scripts, extensões e metadados via instaladores/exportadores cross-platform.

- **Bundle** = este repo Git (artefatos distribuíveis).
- **Live configuration** = a cópia instalada em `%APPDATA%\devin` / `~/.config/devin`.
- **Export** = live -> repo (com mascaramento de segredos).
- **Install** = repo -> live.
- Versão atual: `3.19.0`; CLI validada: `3000.12.28`.

### Usuários
- Maintainer: cura e exporta o setup canônico.
- Installer: restaura em outra máquina.
- Devin CLI agent: consome regras/skills/hooks instalados.

### Fluxos principais
- **Export**: lê live config -> descobre skills -> mascara segredos -> atualiza artefatos do repo -> valida -> commit/push opcional.
- **Install**: lê repo -> cria diretório alvo -> copia/mescla/pula conforme flags -> restaura segredos só se pedido -> reporta diffs e backups.
- **Validate**: `python audit.py` (39 checks) + `python -m pytest` (~2360 testes) + `export.ps1 -DryRun`.

### Invariantes
- Nenhum artefato carrega assinatura de IA (Rule 2).
- Push só com checks verdes (Rule 5).
- Segredos sempre mascarados nos artefatos distribuíveis.
- Nome do diretório da skill == nome no frontmatter; `manifest.json` sincronizado com disco.
- Hooks informativos falham aberto; guards de segurança (`pre-exec-guard`, `pre-write-guard`) falham fechado.
- Afirmações de melhoria exigem evidência reproduzível + teste held-out (Rule 15).

---

## 2. BLUEPRINT / ORGANIZAÇÃO DO REPO

```
devin-bundle/
├── AGENTS.md              # Regras globais canônicas (29 regras; distribuída pelo bundle)
├── README.md              # Documento principal (PT); ecossistema + fluxo ideia->entrega
├── manifest.json          # Inventário de skills + hashes de export (181 skills)
├── config.json            # Template de config do CLI (agent.model: swe-2-high)
├── hooks.v1.json          # Pipeline de hooks (PreToolUse/PostToolUse/Stop/etc.)
├── audit.py               # Auditor de consistência (39 checks sequenciais)
├── install.ps1/.sh        # Instaladores cross-platform
├── export.ps1/.sh         # Exportadores cross-platform (com -DryRun)
├── devin-N.ps1/.cmd       # Launcher multi-instância (sessões paralelas nomeadas)
├── devin-session-launcher.ps1
├── agents/                # 20 perfis de subagentes (researcher, architect, reviewer, ...)
├── skills/                # 181 skills invocáveis (skills/<nome>/SKILL.md)
├── scripts/               # ~45 hooks/guards - Python stdlib-only (rodam em interpretador nu)
├── extensions/            # 28 ferramentas locais (computer-use, laya-tools, gcal, rust-core...)
├── data/                  # bundle-models.json, bundle-identity.json, recipes.json, ...
├── tests/                 # pytest: validation/ (escolhidos) + held-out/ (gap checks)
├── .devin/                # Config do próprio projeto
│   ├── CONTEXT.md, ARCHITECTURE_MANIFEST.md, global_rules.md
│   ├── docs/              # MODEL-GUIDE, SKILL-TIERS, TOOLS-MAP, HOOKS-PIPELINE, PROJECT-STATE...
│   ├── adr/               # 8 ADRs (001-placeholder -> 008-vendored-skill-policy)
│   ├── plans/ research/   # roadmaps e pesquisas datadas
│   ├── issues/ scratch/   # tracker local de issues (DAG, Markdown)
│   ├── evals/             # evidência congelada + held-out (campanha Laya)
│   └── skills/            # skills locais do repo (rts-*, etc.)
└── .github/workflows/     # CI: py_compile, ai-signature, skill-format, pytest matrix 3OSx2py
```

### Camadas do ecossistema (README)
1. **Regras globais**: AGENTS.md, comportamento base, pinned rules sobrevivem compaction.
2. **Skills**: 181 workflows invocáveis; tiers em `docs/SKILL-TIERS.md`; meta-router `leo`/`ask-bundle`.
3. **Perfis de subagentes**: `agents/*.md` com pin de modelo (researcher/architect/reviewer -> `swe-2-max`; debugger/implementer/qa-ci -> `swe-2-medium`).
4. **Ferramentas e MCP**: extensions whitelistadas via wrapper; mínimo de servidores MCP.
5. **Hooks**: governança determinística: guards Pre/PostToolUse, constraint-pinning pós-compaction, stop-guard, check-push-green.
6. **Configuração/distribuição**: install/export com ledger de hashes; drift detectado no audit.
7. **Extensões**: 28 CLIs locais (computer-use, voicebox TTS, remotion render, gcal, laya...).
8. **Atlas público**: site GitHub Pages com inventário navegável.

### Paradigma (ARCHITECTURE_MANIFEST)
- Procedural/funcional; OOP só em extensions com estado. Stdlib-first; hooks sem deps pip.
- Testes: pytest contract tests (string/schema), split validation vs held-out.
- Error model: hooks informativos fail-open; guards `fail_closed: true`; blocos ao agente = `{"decision":"block"}` + exit 2.
- Contratos de encoding: todo I/O texto pin `encoding="utf-8"` (checks 36-39 do audit).

### Estado atual (PROJECT-STATE 2026-11-08)
- PR #422 aberto (branch `fix/gcal-validation-ics`): gcal + status-vocab + laya + hardening de extensões.
- Laya: 14 perfis avaliados com evidência held-out; só `media-intent-v1` forte; todos `mode: off` (#431 = checklist de ativação deliberado).
- Frontier aberta: #346 (umbrella calendar), #431 (Laya), edge-audit (61 issues) para triagem.

### Paradigma SWE-2 (migração concluída, merge 2026-09-16)
- Roteamento por **nível de esforço** (medium/high/max), não por tamanho de modelo.
- Prompts declaram WHAT + critérios de aceitação; HOW fica para o raciocínio nativo.
- Proibido chain-of-thought forçado ("pense passo a passo" = anti-padrão).
- `subagent_explore` built-in NUNCA é despachado (router pago possível) -> usar `researcher` custom.

---

## 3. MODELOS GRATUITOS, EXPLICAÇÃO PROFUNDA

### Família SWE-2 (flagship)
- **Base**: post-train da Cognition sobre **Kimi K3** (MoE 2.8T total / ~104B ativos), com RL em larga escala para coding agentic.
- **Contexto**: 262K tokens. **Velocidade**: ~60 tok/s.
- **Esforço**: 3 variantes no `model_uid`: `swe-2-medium`, `swe-2-high`, `swe-2-max`. Não é flag separada: a variante define o effort (UI: `Alt+T`).
  - Medium: entra em ação rápido, primeira edição real na mediana do passo 18 (vs 48 do SWE-1.7); ~53 passos médios por tarefa.
  - High: ~80 passos; planeja/explora mais; **default do bundle**.
  - Max: ~98 passos; máximo de tokens/verificação para tarefas abertas.
- **Comportamento**: tool-use nativo, raciocínio nativo, self-compaction treinada (subagentes preservam constraints melhor), output conciso por design.
- **Janela free**: grátis em Devin Desktop + CLI (self-serve) **até 30/11/2026**. Depois: list pricing ~$3.00/1M input, $15.00/1M output, $0.30/1M cache read. Não se aplica a sessões cloud.

### Família SWE-2 Flash (fast lane, lançada 04/11/2026)
- **Base**: post-train sobre **Inkling-Small** da Thinking Machines: MoE **276B total / 12B ativos** (6 de 256 experts roteados + 2 shared, 42 camadas), base Apache-2.0, multimodal (texto/imagem/áudio).
- **Receita nova**: primeira vez que a Cognition adiciona um estágio de **mid-training** (trilhões de tokens) antes do RL. Resultado: Terminal-Bench 4.0 de 0.9% -> 20.0% e FrontierCode 2.0 de 3.2% -> 24.0% sobre a base.
- **Contexto**: 262K. **Velocidade**: ~200 tok/s (**3x SWE-2**). **Custo**: **1/5 do preço do SWE-2** após a janela.
- **Variantes**: `swe-2-flash-medium`, `swe-2-flash-high`, `swe-2-flash-max`.
- **Janela free**: grátis **até 04/12/2026 18:00 UTC** em Desktop + CLI para Pro/Max/Teams.
- **Detalhe-chave de plano**: após a janela, **`swe-2-flash-medium` permanece no plano Free**; `flash-high` e `flash-max` exigem plano pago (~$0.10/1M input, $0.01 cache read, $0.125 cache write, $0.50/1M output).
- **Pesos**: NÃO públicos. Cognition retém por capacidade cyber-ofensiva (ExploitBench 11.3% -> 34.8% com treino direcionado). Programa de compartilhamento seguro para parceiros/pesquisadores em elaboração. Sem API fora do Devin.

### Benchmarks (self-reported pela Cognition, sem avaliação independente)

| Eval | SWE-2 Flash | SWE-2 | Leitura |
|---|---|---|---|
| FrontierCode 2.0 | **24.0** | 23.8 | Flash empata/vence |
| FrontierCode 1.1 Main | 45.5 | **50.0** | SWE-2 vence |
| DeepSWE 1.1 | 60.1 | **73.0** | SWE-2 vence folgado |
| Terminal-Bench 4.0 | 20.0 | **27.3** | SWE-2 vence |
| Terminal-Bench 2.1 | 89.2 | 92.8 | SWE-2 leve |
| SWE-Atlas QA | 50.0 | 56.3 | SWE-2 |
| SWE-Bench Pro v2 Hard | 89.9 | 90.6 | ~empate |
| ExploitBench | 34.8 | 36.1 | ~empate |

**Conclusão dos números**: Flash ~= SWE-2 em coding rotineiro e frontier-code leve; SWE-2 claramente superior em trabalho agentic pesado de terminal/RL (DeepSWE, Terminal-Bench 4.0). Flash é posicionado pela Cognition para: automações, code review, docs, feature dev rotineira, exatamente o perfil dos subagentes de execução bounded.

---

## 4. AJUSTAR O BUNDLE PARA APROVEITAR SWE-2 + SWE-2 FLASH

### O que já existe (feito em 06/11, issue R4-01)
- `data/bundle-models.json`: 6 variantes registradas (`role: fast` nos Flash).
- `data/model-context-windows.json`: ids Flash com 262144.
- `docs/MODEL-GUIDE.md`: linha "fast lane" + nota de lançamento.
- `docs/TOOLS-MAP.md`: linha `swe-2-flash-{medium,high,max}`.

### Gaps atuais
1. **Nenhum agent/ faz pin em Flash**. Todos usam `swe-2-max`/`swe-2-medium`.
2. **`role: fast` não é consumido**: `context-pressure.py`/`recipes.json` resolvem só medium/high/max.
3. **Datas de janela desatualizadas**: docs dizem "até 11/30" para Flash; oficial é 04/12 18:00 UTC. E nada registra que **SWE-2 deixa de ser free em 30/11**. A política FREE-ONLY inteira assume SWE-2 grátis.
4. **`preferred_family_models` no config.json** só mapeia `swe-2 -> swe-2-max`; sem entrada `swe-2-flash`.
5. Sem campo `free_until` no registry; flip de custo não é automático.

### Recomendações concretas

**Agora (dentro das janelas free, até 30/11 e 04/12):**
- Repinar subagentes de **execução bounded** para Flash: `implementer`, `debugger`, `qa-ci` -> `swe-2-flash-medium` ou `-high` (3x mais rápido, custo zero na janela, qualidade ~= SWE-2 medium em tarefas rotineiras).
- Repinar subagentes de **volume mecânico**: `issue-tracker`, `triage-labels`, `copywriter`, `sentinel`/`watchdog` -> Flash.
- **Manter `swe-2-max`** para julgamento: `researcher`, `architect`, `reviewer`, `advisor` (DeepSWE 73 vs 60; trabalho agentic pesado é onde SWE-2 ganha).
- Parent pode continuar `swe-2-high` enquanto free; alternativa: `swe-2-flash-high` para sessões de volume (docs, review mecânico, batch).
- Adicionar `preferred_family_models.swe-2-flash` em `config.json` (ex.: `swe-2-flash-high`).

**Estruturais (independentes de janela):**
- `bundle-models.json`: campo `free_until: "2026-12-04T18:00Z"` (Flash) / `"2026-11-30"` (SWE-2) + `free_tier_permanent: true` só em `swe-2-flash-medium`.
- `recipes.json`/`context-pressure.py`: mapear `preferred_model_role: fast` -> família flash.
- Env overrides já existem (`BUNDLE_*`); adicionar `BUNDLE_FAST_MODEL` se quiser toggle sem editar JSON.
- `docs/MODEL-GUIDE.md`: corrigir datas, documentar que SWE-2 vira pago 30/11 e que `swe-2-flash-medium` é o único free permanente.

**Após 30/11 (decisão de política necessária):**
- SWE-2 sai do free -> a política FREE-ONLY colapsa para `swe-2-flash-medium` apenas. Opções: (a) manter SWE-2 aceitando custo $3/$15; (b) mover parent para `swe-2-flash-high` (plano pago, ~1/5 do preço) com `swe-2-flash-medium` para subagents bounded; (c) revisar quando Cognition publicar preços finais.
- Flash High/Max pós-janela: ~$0.10/$0.50 por 1M, ordens de magnitude mais barato que SWE-2 para o mesmo papel de esforço.

---

## 5. FONTES

- https://cognition.com/blog/swe-2-flash - announcement + tabela de benchmarks (04/11/2026)
- https://cognitionai.mintlify.app/desktop/models - pricing oficial: Flash free até 04/12 18:00 UTC; Flash Medium no plano Free; SWE-2 free até 30/11, depois $3/$15
- https://cognition.com/blog/swe-2 - esforço, passos médios (53/80/98), primeira edição passo 18 vs 48, 58% menos turns, 81% mais barato vs SWE-1.7
- https://www.unite.ai/cognition-launches-swe-2-flash-for-faster-lower-cost-coding-agents/
- https://neuralbrew.ai/en/articles/2026/11/cognition-swe-2-flash-code-model-inkling-small-weights-withheld/
- https://www.orcarouter.ai/blog/swe-2 - base Kimi K3 2.8T, stack NVFP4/FP8, speculative decoding
- Interno: `.devin/scratch/reels-4/issues/R4-01-swe2-flash-model-entry.md`, `.devin/SWE2_MIGRATION_LOG.md`
