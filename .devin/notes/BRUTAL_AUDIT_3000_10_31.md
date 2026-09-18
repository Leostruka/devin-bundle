# BRUTAL AUDIT — devin-bundle vs Devin CLI `3000.10.31 (b98cc431)` / SWE-2

- **Auditor:** SWE-2 Max — Arquiteto Principal de IA / Auditor de Infraestrutura
- **Data:** 2026-09-17 · Repo: `devin-bundle` @ `feat/hybrid-rust-extensions` (tree limpa no momento da auditoria)
- **Método:** inventário por ferramentas (não dedução), benchmark de hooks medido nesta máquina, pesquisa web com fontes primárias (apêndice `[EMPIRICAL GROUNDING]`).
- **Escopo:** `AGENTS.md`, `hooks.v1.json`, `config.json`, 83 `skills/`, 18 scripts de hook, `agents/`, `docs/`, superfícies duplicadas em `.devin/`.
- **Nada foi alterado/deletado.** Este arquivo é o único artefato novo.

---

## Veredito executivo

| Eixo | Nota | Síntese |
|---|---|---|
| Redundância estrutural | **D** | 83 skills com ≥9 clusters sobrepostos; 4 roteadores competindo pelo mesmo intent; 3 superfícies de regras; 2 registros de hooks divergentes. |
| Overload / latência | **D** | ~8.2K tokens de regras+descrições sempre carregados; **624ms de spawn Python por `exec`**, ~356ms por `write`, ~200ms por prompt do usuário — tudo startup de intérprete, não trabalho útil. |
| SWE-2 alignment | **C+** | Effort routing correto (`bundle-models.json`); gates determinísticos justificados pela natureza RL do modelo. **Mas:** o imposto de hook é cobrado também no Medium (que existe para ser barato), e 83 skills auto-invocáveis jogam o roteador dentro da zona de degradação medida (~40+ ferramentas). |
| CLI 3000.10.31 nativo | **D** | `--sandbox`, `permissions.deny/ask`, hooks `"type":"prompt"`, `devin rules/skills/plugins`, `triggers:[user]`, `disabled_tools` — capacidades nativas ignoradas ou reimplementadas em Python. |

O bundle está arquiteturalmente **correto na direção** (gates determinísticos, constraint-pinning, effort routing) e **errado na implementação** (fragmentou cada gate em um processo Python separado, triplicou as superfícies de roteamento, e nunca consolidou).

---

## [REDUNDÂNCIA]

### 1. Skills — clusters de sobreposição (os cortes)

A coluna "Veredito" indica fundir/deletar/manter. Evidência = `skills/<nome>/SKILL.md` (bytes medidos).

| # | Cluster | Skills (bytes) | Veredito |
|---|---|---|---|
| R1 | **Roteadores (4×)** | `ask-bundle` (12.865), `leo` (16.842), `tool-and-skill-discovery` (4.177), `using-skills` (4.119) + `docs/SKILL-TIERS.md` (13.381) como 5ª superfície | **FUNDIR → 1.** Quatro descrições competem pelo intent "qual skill usar". O tool-router vê 4 candidatas semanticamente confusas — o pior caso documentado (semantic confusability > library size, αXiv 2601.04748). Manter `ask-bundle` como router canônico; `using-skills` vira regra de bootstrap; `leo` e `tool-and-skill-discovery` absorvidos ou rebaixados para `triggers:[user]`. |
| R2 | **Contexto/memória (7×)** | `context-folding` (6.250), `context-window-hygiene` (5.663), `memory-hygiene` (6.988), `project-memory` (4.776), `handoff` (1.055), `agent-cost-guard` (2.391), `cost-optimization` (1.986) | **FUNDIR → 2** (`context-hygiene`, `memory-management`). `mcp-context-audit` já absorve o caso MCP; `agent-cost-guard`/`cost-optimization` são a mesma descrição com palavras trocadas. |
| R3 | **MCP gêmeos** | `mcp-context-audit` (4.081), `mcp-lazy-enablement` (4.933) | **FUNDIR → 1.** Descrições quase idênticas ("context feels bloated from MCP tools"). Diferença real: audit=medir, lazy=ligar/desligar → um corpo, dois modos. |
| R4 | **Planejamento (9×)** | `planning-pipeline` (16.666), `writing-plans` (9.846), `wayfinder` (12.870), `task-sizer` (2.146), `intention-capture` (2.026), `executing-plans` (3.982), `implement` (1.429), `afk-loop` (3.903), `review-cadence` (3.250) | **FUNDIR → 3** (`planning` = spec→tickets, `execution` = executar plano/tickets, `sizing` = estimar/dividir). 62KB de skill bodies no mesmo espaço semântico. |
| R5 | **Verificação/qualidade (8×)** | `verification-before-completion` (5.760), `unlazy` (4.588), `autonomous-gates` (6.261), `continuous-improvement` (19.982), `tdd` (11.921), `mutation-testing` (6.359), `code-review` (13.135), `pr-review` (6.359) | **FUNDIR → 5.** `unlazy`+`autonomous-gates` são o mesmo mecanismo (gates ledger). Manter `tdd`, `pr-review`, `continuous-improvement` (distintos). `code-review`+`receiving-code-review` (7.193) → par natural, manter ambos mas cortar overlap. |
| R6 | **Git/GitHub (7×)** | `gh` (9.189), `git-helper` (1.452), `finishing-a-development-branch` (7.512), `resolving-merge-conflicts` (1.093), `using-git-worktrees` (6.931), + `code-review`/`pr-review` de R5 | **FUNDIR → 3** (`git-workflows` engole helper+worktrees+merge-conflicts; `gh` standalone; reviews ficam em R5). |
| R7 | **Setup/config (5×)** | `project-setup` (11.061), `setup-engineering-skills` (7.342), `devin-manager` (4.806), `self-extend` (7.705), `setup-pre-commit` (2.588) | **FUNDIR → 3** (`project-bootstrap`, `devin-config` = devin-manager+self-extend audit surface, `engineering-setup`). |
| R8 | **Pesquisa (4×)** | `research` (699), `deep-mode` (5.086), `context7` (1.357), `ai-coding-dictionary` (1.383) | **FUNDIR → 2** (`research` com modo deep; `context7` standalone por ser provider externo). |
| R9 | **Arquitetura/melhoria (5×)** | `improve-codebase-architecture` (9.686), `codebase-design` (6.514), `legacy-refactor` (1.269), `domain-modeling` (3.968), + `ontology-validator`/`structured-knowledge-extraction` adjacentes | **FUNDIR → 3** (`architecture`, `domain-modeling`, `knowledge-extraction`). |
| R10 | **Arquivos-monstro** | `obsidian-workflow` (69.955), `primeagent-reference` (44.097), `dispatching-parallel-agents` (42.389), `writing-skills` (26.289) | **SPLIT, não deletar.** Um SKILL.md deve ser entrada + regras; corpos >10KB vão para `REFERENCE.md` lazy-loaded. Invocar `obsidian-workflow` custa ~17.5K tokens de uma vez. |

**Saldo:** 83 skills → ~50 após fusões (R1–R9), com os 4 monstros repartidos (R10). Descrições sempre-carregadas caem de ~14.6KB para ~9KB; superfície de seleção do router cai de 83 → ~50+30 tools nativos (ainda acima do knee ~40 — ver R14).

### 2. `AGENTS.md` — regras semanticamente duplicadas

Arquivo: 18.278 bytes ≈ 4.5K tokens, carregado em TODA sessão (a cópia instalada em `%APPDATA%\devin\AGENTS.md` é a versão viva — confirmado por injeção de rules nesta sessão).

| Regras | Sobreposição | Veredito |
|---|---|---|
| 12 (precisão/verificação) + 15 (evidência reproduzível) + 16 (held-out) + 17 (verify with tools) + 21 (research-or-ask) | Cinco regras pinned circulando "não deduza, verifique, prove". | **FUNDIR → 2** ("Verify with tools" + "Evidence standards"). Economia ~1.5KB e elimina o ruído de índice. |
| 10 (plan/verify) | Repete o núcleo de 12/17 + re-declara ledger de gates que `unlazy`/`autonomous-gates` já especificam. | **FUNDIR** em 12; manter apenas a parte todo-list. |
| 19 (secrets) + 23 (sanitize) + 24 (secrets in VCS) + 26 (secure defaults) | Quarteto de segurança com 3 repetições de "não exponha segredos". | **FUNDIR → 1** ("Security & secrets"). ~2KB → ~0.8KB. |
| 3 (skill lifecycle) + 4 (skill discovery) | Ambas governam skills; 4 duplica o que `using-skills`/router já fazem. | **FUNDIR → 1**; mover checklist de qualidade para `writing-skills` (já referenciada). |
| 18 (lean context) + 22 (minimum code) | Mesma diretriz em duas roupas ("menos tokens/contexto"). | **FUNDIR**; 22 vira bullet de 18 ou vice-versa. |
| 27 (declare intent) | Sobrepõe `intention-capture` + `grilling` + Rule 1 (customer-first). | Manter 1 linha; delegar mecanismo às skills. |
| Index + seções pinned + não-pinned | As 29 regras aparecem ~3× no mesmo arquivo (índice, corpo pinned, corpo terse). | Estruturalmente OK (índice é a defesa lost-in-the-middle), mas o arquivo pode ser **minificado para ~9-10KB** sem perda semântica — ver proposta em `[OVERLOAD/LATÊNCIA]`. |
| 28 (Rust) + 29 (arch-gate) | Novas, corretas, sem overlap. | Manter. |

### 3. Scripts vs capacidade nativa do CLI

| Script (linhas) | Função | Substituto nativo | Veredito |
|---|---|---|---|
| `destructive-gate.py` (320) | Bloqueia `rm -rf`, force-push, etc. | `permissions.deny` + `--sandbox` (confina writes ao workspace; macOS seatbelt/Linux bwrap) cobrem o caso estrutural. O regex de conteúdo de comando o nativo **não** cobre. | **Parcialmente nativo.** Manter só a análise de padrão; migrar confinamento para `--sandbox`/`permissions`. |
| `architecture-gate.py` (150) | Exige ARCHITECTURE_MANIFEST antes de writes | Nenhum nativo (condicional por arquivo). | **Manter** — gate customizado legítimo. |
| `check-ai-signature.py` (227) | Sem assinatura de IA | Nenhum nativo. | **Manter, 1 evento só** — hoje roda em PreToolUse(write/edit) **e** Stop; deduplicar para Stop (checagem final) ou manter PreToolUse e cortar Stop. |
| `validate-tool-args.py` (369) | Sanidade de args | Parcial: o próprio CLI valida schemas. | **Investigar valor real** — custa ~66ms em **17 ferramentas**, incluindo `read`/`grep`/`glob`/`todo_write`. Se o hit-rate de bloqueio for ~0, é imposto puro. |
| `context-pressure.py` (647) | Alerta de pressão de contexto | `agent.compaction_threshold_tokens` + hook `"type":"prompt"` | **Candidato a prompt-hook** — elimina subprocesso; o modelo já vê o aviso. |
| `behavioral-nudge.py` (39) | Injeta lembrete no prompt | Hook `"type":"prompt"` nativo | **Substituir** — caso de uso exato dos prompt hooks; 1 spawn a menos por prompt. |
| `memory-post-exec.py` + `memory-post-edit.py` + `memory-retrieval.py` + `memory-stop.py` (~473 linhas) | Ciclo de memória | Nenhum comando `devin memory` observado em `--help`; convenção MEMORY.md é do bundle. | **Consolidar 4→1** (`memory-hook.py` com subcomando por evento) — 3 spawns a menos. |
| `silent-error-review.py` (185) | Revisa erros silenciosos pós-exec | Nenhum nativo equivalente direto. | Manter lógica; fundir no post-exec consolidado. |
| `validate-mermaid.py` (103) + `mermaid-parse-check.js` (98) | Valida blocos mermaid | Nenhum nativo. | Manter, mas gatear por presença de ` ```mermaid ` — hoje paga ~77ms em todo write/edit. |
| `check-push-green.py` (168) | Bloqueia push sem verde | `permissions` não cobre "só push se CI verde". | Manter (timeout 150 é o maior da tabela — revisar). |
| `constraint-pinning.py` (208) | Re-injeta constraints pós-compaction | Nenhum nativo (compaction internals não expostos). | **Manter** — defesa validada contra Governance Decay (arXiv:2606.22528). |
| `refine-review-prompt.py` (220) | Review em Stop | Prompt hook parcialmente. | Consolidar no Stop único. |
| `context-budget.py` (244), `validate-skill-format.py` (265), `validate-refinement-evidence.py` (265) | Budget/formato/evidência | — | Manter; são SessionStart/CI, não hot-path. |

### 4. Superfícies duplicadas de registro (drift comprovado)

| Par | Estado | Risco |
|---|---|---|
| `hooks.v1.json` (4.106B) vs `config.json` hooks (22 bindings idênticos) | Mesma lista registrada **duas vezes** | Drift: editar um e esquecer o outro. `audit.py` já flaggea drift live-vs-bundle. |
| `hooks.v1.json` (root) vs `.devin/hooks.v1.json` (3.752B) | **Divergentes** — a cópia `.devin/` está stale (sem `architecture-gate`, 354B a menos) | Cópia morta confundindo auditoria e qualquer consumidor que leia `.devin/` primeiro. |
| `AGENTS.md` (root) vs `.devin/global_rules.md` (1.576B) vs `~/.config/devin/AGENTS.md` (instalado) | **3 superfícies de regras** | Qual é a fonte de verdade? A instalada injeta; a root edita; `.devin/global_rules.md` é anã que compete. |
| `agents/` (6 perfis) vs `.devin/agents/` (4 perfis) | Conjuntos **disjuntos** (researcher/qa-ci vs domain/triage-labels) | 10 perfis espalhados em 2 diretórios; nenhum inventário unificado. |
| `manifest.json` (47.6KB) vs realidade | Contagens hardcoded (18 scripts, 28 regras) já exigiram correção manual 2× nesta semana | Manifesto que precisa de manutenção manual para continuar verdadeiro = fonte de mentiras futuras. |

---

## [OVERLOAD/LATÊNCIA]

### Orçamento de contexto (medido, bytes → tokens ≈ ÷4)

| Superfície | Bytes | ≈Tokens | Carregamento |
|---|---|---|---|
| `AGENTS.md` | 18.278 | ~4.570 | **Sempre** (toda sessão) |
| Descrições das 83 skills | 14.633 | ~3.660 | **Sempre** (bloco `available_skills`) |
| SKILL.md bodies (total) | 634.778 | ~158.700 | Sob demanda (mas 4 arquivos >26KB = ~6.5K–17.5K por invocação) |
| `docs/SKILL-TIERS.md` | 13.381 | ~3.345 | Quando Rule 4 a dispara |
| `manifest.json` | 47.579 | ~11.900 | Sob demanda |
| `hooks.v1.json` + `config.json` | ~9.700 | ~2.400 | Config (não entra no prompt) |
| **Sempre carregado (bundle)** | **~33KB** | **~8.2K** | Antes de system prompt, tool schemas (~30 tools nativos) e conversa |

Em 262.144 tokens de janela, ~8.2K não é fatal — mas a posição importa: Lost-in-the-Middle (TACL 2024) mostra degradação em U-curve; regras no meio do system prompt são as primeiras a diluir. O índice do AGENTS.md é a defesa correta; o problema é **volume**: 29 regras com ~40% de redundância semântica (seção 2).

### Latência de hooks (medido nesta máquina, Python 3.14.6, Windows)

Benchmark: cada script invocado isoladamente com payload realista; tempo = wall-clock do spawn+execução. **Amostra única, processos frios/mornos misturados — tratar como ordem de grandeza, não garantia.**

| Evento | Scripts | ms/script | Total |
|---|---|---|---|
| `exec` PreToolUse | destructive-gate 70 · architecture-gate 65 · check-ai-signature 79 · check-push-green 76 · validate-tool-args 66 | — | **~357ms** |
| `exec` PostToolUse | silent-error-review 68 · context-pressure 129 · memory-post-exec 70 | — | **~267ms** |
| **`exec` total** | **8 processos Python** | | **~624ms** |
| `write`/`edit` PreToolUse | architecture-gate 65 · check-ai-signature 78 · validate-mermaid 77 · validate-tool-args 66 | — | **~286ms** |
| `write`/`edit` PostToolUse | memory-post-edit | 70 | **~70ms** |
| **`write` total** | **5 processos** | | **~356ms** |
| `read`/`grep`/`glob`/`webfetch`/`web_search`/`todo_write`/… | validate-tool-args | ~66 | **~66ms por chamada trivial** |
| `UserPromptSubmit` | constraint-pinning + behavioral-nudge + memory-retrieval | ~65-70 cada | **~200ms por mensagem do usuário** |
| `SessionStart` | constraint-pinning + context-budget | | ~135ms |
| `Stop` | check-ai-signature + refine-review-prompt + memory-stop | | ~215ms |
| `PostCompaction` / `SessionEnd` | 1 script cada | | ~70ms |

**Custo de um turno típico** (1 prompt + 3 reads + 2 exec + 2 writes): ~200 + 3×66 + 2×624 + 2×356 ≈ **2.4 segundos de spawn de intérprete** — zero trabalho útil, é o preço de 20 processos Python.

Culpado nº 1: **arquitetura "1 check = 1 processo"**. Cada script paga ~65-80ms só de startup; o trabalho interno é <10ms. Culpado nº 2: `context-pressure.py` (129ms, 647 linhas — o mais pesado). Culpado nº 3: `validate-tool-args.py` casado com 17 ferramentas — o imposto mais frequente do sistema.

### Proposta "minificada" (alvo, não aplicada)

- **AGENTS.md 18.3KB → ~9-10KB**: fundir 12/15/16/17/21→2 regras; 19/23/24/26→1; 3/4→1; 18/22→1; 10 absorvida; regras-skill-pointer (9, 27) para 1 linha. −45% de tokens sempre-carregados.
- **Hooks 22 bindings → ~10**: `pre-exec-guard.py` único (destructive+arch+signature+push-green+tool-args em 1 processo, ~75ms); `post-exec.py` único (silent-error+context-pressure+memory, ~80ms); `pre-write-guard.py` único; `user-prompt.py` único; behavioral-nudge → prompt hook nativo (0 spawns).
- **Projeção:** exec ~624→~155ms (−75%); write ~356→~150ms; prompt ~200→~70ms. Turno típico 2.4s→~0.6s.
- **83→~50 skills** + `triggers:[user]` nas raras (obsidian-workflow, youtube-fetcher, jira, i18n, a11y, e2e, docker, deploy, database, teach, wait-what, wizard, leo) → superfície auto-invocável ~35-40, abaixo do knee de degradação.

---

## [SWE-2 / CLI MISALIGNMENT]

### O que a natureza do SWE-2 exige (fontes: Cognition blog + literatura RL)

- SWE-2 é treinado por RL com recompensa `R = S − λₑ·C` num único run para Medium/High/Max (cognition.com/blog/swe-2). Medium "steps into action much quicker"; High/Max "plan more, explore more, verify more".
- Agentes de coding RL exibem reward hacking mensurável: 25-30% de trajetórias com indicadores de exploit em runs SWE-Bench (Georgia Tech thesis); Codex e Claude Code flagrados editando testes (EvilGenie, arXiv:2511.21654). **Os gates determinísticos do bundle são, portanto, alinhados com a natureza do modelo — não opcionais.**
- Mas a literatura também mostra o "three-phase rebound": modelos tentam o caminho legítimo primeiro e só hackeiam quando a recompensa legítima é escassa (arXiv:2604.01476). Gates demais em tarefas triviais aumentam o custo do caminho legítimo — o mecanismo que empurra RL-agents para exploits.

### Desalinhamentos encontrados

| # | Desalinhamento | Evidência | Severidade |
|---|---|---|---|
| M1 | **Imposto flat em todos os effort levels.** Medium existe para ser rápido/barato (Cognition: −58% turns vs SWE-1.7). O bundle cobra os mesmos ~624ms/exec dele — o overhead de infraestrutura anula a vantagem de custo do nível. | hooks.v1.json + benchmark | **Alta** |
| M2 | **83 skills auto-invocáveis.** Seleção de ferramentas degrada abruptamente ~40+ (Archestra; BFCL 43%→2% de 4→51 tools; αXiv 2601.04748: phase transition por confusabilidade semântica). 83 descrições + ~30 tools nativos = ~113 superfícies, ~3× o knee. `triggers:[user]` existe nativamente e **nenhuma skill o usa**. | skills/ + docs.devin.ai skills/overview | **Alta** |
| M3 | **9 skills de planejamento num modelo que planeja nativamente.** O bundle luta contra "medium steps into action quicker" forçando artifacts de planejamento (ledgers, tickets) via skills + Rules 10/27 — correto para High/Max, desperdício no Medium. | MODEL-GUIDE.md ("não force chain-of-thought") vs R4 | **Média** — o bundle sabe (Rule 20), mas as skills não discriminam por esforço. |
| M4 | **Hooks `"type":"prompt"` ignorados.** Todos os 22 bindings são `command` → subprocesso. `behavioral-nudge`, `context-pressure`, `refine-review-prompt` são injeções de texto — o caso exato dos prompt hooks nativos (0 spawn, avaliação in-model). | docs.devin.ai hooks/overview vs hooks.v1.json | **Média** |
| M5 | **`--sandbox` e `permissions` nativos subutilizados.** O CLI já confina writes ao workspace (seatbelt/bwrap) e tem deny/ask por tool+path. `destructive-gate` reimplementa um subconjunto em Python por chamada. | `devin --help`, docs config-file | **Média** — gate cobre análise de conteúdo que permissions não cobre; confinamento estrutural deveria ser nativo. |
| M6 | **Ciclo de vida de plugin ignorado.** `devin plugins install/list/update/remove` existe; o bundle mantém `install.ps1`/`install.sh` próprios (sync, hash, exclusões). Um `.devin-plugin/plugin.json` daria install/update nativo cross-surface (CLI+Cloud+Desktop). | docs plugins/overview | **Média** — mas o installer faz coisas que plugin não faz (cargo build, venv) → híbrido, não substituição total. |
| M7 | **Registro duplo de hooks.** `hooks.v1.json` e `config.json` carregam os mesmos 22 bindings; `.devin/hooks.v1.json` é uma terceira cópia stale. | diff medido | **Alta** — drift já observado. |
| M8 | **`validate-tool-args` em 17 ferramentas** paga ~66ms para re-checar o que o CLI já valida por schema. Sem métrica de hit-rate no repo. | hooks.v1.json | **Média** |
| M9 | `devin rules`, `devin skills`, `devin doctor`, `devin migrate` existem; o bundle gerencia regras/skills por sync de arquivos em vez dos comandos nativos. | `devin --help` | **Baixa** — o sync manual funciona; mas `devin doctor` deveria estar no install/audit. |
| M10 | **`subagent_explore` paid-router catch** — o bundle já achou e corrigiu (Rule 20). Exemplo de alinhamento correto a manter. | MODEL-GUIDE.md | ✅ correto |
| M11 | **Constraint-pinning** — justificado empiricamente (Governance Decay arXiv:2606.22528 dropa constraints em todos os modelos). Manter. | AGENTS.md Rule 14 | ✅ correto |
| M12 | **Effort routing** (`bundle-models.json` Medium/High/Max = swe-2-* free) — semanticamente correto vs docs Cognition. | data/bundle-models.json | ✅ correto |

### Fatos vs hipóteses vs desconhecidos

- **Verificado (docs/binário):** hooks command+prompt, matchers, timeouts, `triggers:[user]`, permissions allow/deny/ask, `--sandbox`, plugins, MCP config dedicada (v3000.3+), `tool_provenance` em PreToolUse, `disabled_tools`, `devin rules/skills/doctor`.
- **Verificado (repo):** todas as contagens, tamanhos, hook bindings, latências (esta máquina), drift `.devin/hooks.v1.json`, duplo registro.
- **Hipótese (precisa teste):** se hooks em `config.json` **e** `hooks.v1.json` executam ambos (double-fire) ou um vence — testar com hook-sentinel antes de deduplicar. Se `triggers:[user]` realmente remove a skill do bloco always-loaded (docs dizem que controla auto-invoke). Hit-rate real de `validate-tool-args` (instrumentar 1 semana).
- **Desconhecido (pesquisa exaurida, sem fonte primária):** internals do router de skills do CLI; se prompt-hooks têm latência/custo de modelo documentado; feature-paridade exata de `devin plugins` vs installer customizado; changelog de 3000.10.27→.31 (não publicado em docs.devin.ai; `devin update` é a autoridade local).

---

## [EMPIRICAL GROUNDING]

### Eixo A — Devin CLI 3000.10.31 (nativo) — 11 fontes

1. https://docs.devin.ai/cli/extensibility/hooks/overview — hooks command/**prompt**, stdin/stdout JSON, timeouts, matchers.
2. https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks — PreToolUse/PostToolUse/PermissionRequest/UserPromptSubmit/PostCompaction/SessionStart/SessionEnd.
3. https://docs.devin.ai/cli/extensibility/skills/overview — skills, permissões com escopo, subagents, model override, **`triggers:[user]`** desativa auto-invocação.
4. https://docs.devin.ai/cli/extensibility — layout `.devin/` (rules, skills, agents, MCP, hooks).
5. https://docs.devin.ai/cli/extensibility/configuration — config.json project/user, permissions, `read_config_from`, hooks em config.
6. https://docs.devin.ai/cli/reference/configuration/config-file — tabela de arquivos; MCP moveu p/ `mcp_config.json` na v3000.3; `permissions` syntax `Read(**)`/`Exec(...)`.
7. https://docs.devin.ai/cli/extensibility/mcp/overview — `mcp__server__tool` namespace, permissões sobre MCP, `devin mcp login` (OAuth).
8. https://docs.devin.ai/cli/extensibility/mcp/configuration — stdio vs HTTP/SSE, migração automática de `mcpServers`.
9. https://docs.devin.ai/cli/extensibility/plugins/overview — `.devin-plugin/plugin.json`, skills+rules+hooks+MCP+subagents empacotáveis, fallback Claude/Agent-Plugins.
10. `devin --help` (local, b98cc431) — `--sandbox` (seatbelt/bwrap, write confinado ao workspace), `--permission-mode auto/accept-edits/smart/dangerous`, `devin rules|skills|plugins|doctor|migrate|mcp`.
11. `docs/DEVIN-CLI-COMPATIBILITY.md` (repo) — tabela de decisões 3000.10.x: `disabled_tools`, `compaction_threshold_tokens`, `tool_provenance`, `exec_shell` avaliados.

### Eixo B — SWE-2 / RL / verificação — 8 fontes (6 primárias externas + 2 locais)

1. https://cognition.com/blog/swe-2 — `R = S − λₑ·C`; effort num único RL run; Medium −58% turns/−81% custo vs SWE-1.7; Max planeja/verifica mais. **Única fonte primária Cognition encontrada para internals do SWE-2 — gap documentado, não fabricado.**
2. https://repository.gatech.edu/entities/publication/53719720-374b-4d3e-9453-23b853793da5 — tese: 25-30% de trajetórias RLVR com reward hacking; exploits de supressão de testes/collection-abort; defesas estruturais.
3. https://arxiv.org/html/2511.21654v2 — EvilGenie: reward hacking explícito em Codex e Claude Code; detecção por test-edit + LLM judge.
4. https://ar5iv.labs.arxiv.org/html/2606.26300 — Verification Horizon: trilema scalability/faithfulness/robustness; unit tests cobrem "thin layer of intent" → justifica gates humanos+held-out.
5. https://arxiv.org/html/2604.23488 — Trace-and-Amplify: monitores treinados em hacking induzido não generalizam → heurísticas de prompt não bastam; hooks determinísticos sim.
6. https://www.arxiv.org/pdf/2604.01476 — Advantage Modification: three-phase rebound (modelo tenta legítimo → hackeia se recompensa escassa) → não tornar o caminho legítimo caro demais.
7. `.devin/research/swe2-action-capabilities.md` (repo, 16/09/2026) — 150 vetores de pesquisa SWE-2; limites documentados.
8. `data/bundle-models.json` + `docs/MODEL-GUIDE.md` (repo) — routing por esforço; "suba um nível quando a verificação falhar, não antes".

### Eixo C — Contexto / tool overload — 14 fontes

1. https://doi.org/10.1162/tacl_a_00638 — Lost in the Middle (TACL 2024): U-curve, primacy/recency.
2. https://www-cs.stanford.edu/~nfliu/papers/lost-in-the-middle.arxiv2023.pdf — versão arXiv, protocolos de avaliação.
3. https://aclanthology.org/2024.findings-acl.890.pdf — Found in the Middle: attention bias em U é intrínseco; calibração ajuda ≤10pt.
4. https://proceedings.neurips.cc/paper_files/paper/2024/file/6ffdbbe354893979367f93e2121e37dd-Paper-Conference.pdf — Ms-PoE (NeurIPS 2024): lost-in-middle persiste a 4M tokens.
5. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — "smallest possible set of high-signal tokens"; altitude Goldilocks de system prompts; attention budget finito.
6. https://www.anthropic.com/engineering/building-effective-agents — solução mais simples que funcione; agentes trocam latência/custo por flexibilidade; ground truth do ambiente.
7. arXiv:2606.10209 (via https://www.danililchenko.dev/posts/context-engineering/) — Less Context Better Agents: história podada mantém accuracy com ~1/3 dos tokens. *(secundária citando primária)*
8. https://www.alphaxiv.org/abs/2601.04748 — skill selection: **phase transition**, confusabilidade semântica > tamanho da biblioteca; roteamento hierárquico ajuda.
9. https://archestra.ai/blog/how-many-mcp-tools-too-many — knee ~40 ferramentas; 70 tools ≈ 15K tokens de manifest. *(medido, secundário)*
10. https://particula.tech/blog/agent-tool-selection-at-scale-80-tools-wrong-one — 100+ tools → 13-15% accuracy; 64%→20% em 207→417 tools. *(secundário)*
11. https://tianpan.co/blog/2026/04/09/tool-selection-problem-agent-tool-routing-at-scale — BFCL: 43%→2% (4→51 tools); Anthropic: 58 defs ≈ 55K tokens. *(secundário citando primárias)*
12. https://tianpan.co/blog/2026-04-19-over-tooled-agent-problem — RAG-MCP: 13.62%→43% com seleção por retrieval. *(secundário)*
13. https://swe-agent.com/0.7/background/aci/ — ACI: comandos LM-centric simples, feedback sucinto; "distracting context can harm performance".
14. https://doi.org/10.48550/arxiv.2405.15793 — SWE-agent (NeurIPS 2024): interface molda comportamento do agente; história gerenciada > história completa.

### Eixo D — lacunas honestas (mandato: não fabricar)

- **SWE-2 internals:** Cognition publica ~1 fonte primária (blog SWE-2). Não existem 10 fontes primárias públicas sobre pesos/RL do SWE-2 — suplementei com literatura RL-verification (Eixo B 2-6). Declarado, não preenchido com achismo.
- **Changelog 3000.10.31:** não localizado em docs.devin.ai; autoridade local = `devin update`/binário. Comportamento verificado via `--help` e compat doc do repo.
- **Latência de prompt-hooks:** docs confirmam existência; custo/latência não documentado — hipótese "0 subprocesso" é estrutural, não medida.
- **Benchmark de hooks:** amostra única por script, máquina local, mistura cold/warm — rerodar N=10 no plano de execução antes de cortar.

---

## EXECUTION PLAN — executar SOMENTE após aprovação explícita

Ordem: medir → cortar superfícies → consolidar hooks → fundir skills → minificar regras → verificar. Cada fase = 1 commit.

### Fase 0 — baseline reproduzível (sem mudança)

```bash
cd ~/Desktop/scripts/devin-bundle && git checkout -b chore/bundle-slim
# benchmark N=10 por script, salva em .devin/notes/hook-bench-baseline.json
python - <<'EOF'
import json,subprocess,time,glob,os
res={}
payloads={"exec":'{"tool_name":"exec","tool_input":{"command":"git status"}}',
          "write":'{"tool_name":"write","tool_input":{"file_path":"x.py","content":"a"}}'}
for s in sorted(glob.glob("scripts/*.py")):
    key="write" if "mermaid" in s or "edit" in s else "exec"
    ts=[]
    for _ in range(10):
        t=time.perf_counter()
        subprocess.run(["python",s],input=payloads[key],capture_output=True,text=True)
        ts.append(round((time.perf_counter()-t)*1000))
    res[os.path.basename(s)]=ts
json.dump(res,open(".devin/notes/hook-bench-baseline.json","w"),indent=1)
print({k:f"{sum(v)/len(v):.0f}ms" for k,v in res.items()})
EOF
# sentinel: descobrir se hooks.v1.json E config.json disparam juntos
python audit.py && python -m pytest tests/ -q  # baseline verde
```

### Fase 1 — eliminar superfícies duplicadas (risco zero)

```bash
git rm .devin/hooks.v1.json                       # cópia stale sem arch-gate
# decidir fonte única de hooks: manter hooks.v1.json, esvaziar config.json.hooks → {} (após sentinel da Fase 0 provar que config.json.hooks não é a única fonte lida)
# .devin/global_rules.md: apontar para AGENTS.md (1 linha) ou deletar após confirmar que nada o consome: grep -rn "global_rules" --exclude-dir=.git .
# unificar agents/: fundir .devin/agents/{domain,issue-tracker,repo-reviewer,triage-labels} em agents/ ou documentar divisão (bundle vs project-local)
```

### Fase 2 — consolidação de hooks (22→~10 bindings)

```bash
# criar scripts/pre-exec-guard.py: importa e roda em-processo destructive+arch+signature+push-green+tool-args (1 spawn ~75ms)
# criar scripts/post-exec.py: silent-error+context-pressure+memory-post-exec (1 spawn ~80ms)
# criar scripts/user-prompt.py: constraint-pinning+memory-retrieval (nudge vira prompt hook nativo)
# converter behavioral-nudge → {"type":"prompt"} em hooks.v1.json
# estreitar matcher de validate-tool-args para ^(exec|write|edit|notebook_edit)$ — fora de read/grep/glob/todo_write
# validate-mermaid: early-exit ANTES de spawn? impossível — gate por matcher de extensão não existe; manter mas medir hit-rate
# rerodar benchmark → esperado: exec ~624→~155ms, write ~356→~150ms
python audit.py && python -m pytest tests/ -q && git commit -m "perf(hooks): consolidate 22 hook bindings into ~10 single-process guards"
```

### Fase 3 — skills: triggers + fusões (83→~50)

```bash
# 3a. triggers:[user] nas raras (zero risco): obsidian-workflow youtube-fetcher jira i18n a11y-audit e2e-testing docker deploy database teach wait-what wizard handoff leo impeccable
# 3b. fusões (1 commit cada par):
#   context-folding+context-window-hygiene+agent-cost-guard+cost-optimization → context-hygiene
#   memory-hygiene+project-memory → memory-management
#   mcp-context-audit+mcp-lazy-enablement → mcp-governance
#   planning-pipeline+writing-plans+wayfinder → planning ; task-sizer+intention-capture → intake ; executing-plans+implement+afk-loop+review-cadence → execution
#   unlazy+autonomous-gates → gates ; code-review+receiving-code-review → code-review
#   git-helper+resolving-merge-conflicts+using-git-worktrees → git-workflows
#   research+deep-mode → research ; improve-codebase-architecture+codebase-design+legacy-refactor → architecture
#   project-setup+setup-engineering-skills+setup-pre-commit → project-bootstrap ; devin-manager+self-extend → devin-config
# 3c. split dos monstros: obsidian-workflow, primeagent-reference, dispatching-parallel-agents, writing-skills → SKILL.md ≤10KB + REFERENCE.md
# atualizar SKILL-TIERS.md, manifest.json, ask-bundle router table
python audit.py && python -m pytest tests/ -q
```

### Fase 4 — AGENTS.md minificado (18.3KB → ~10KB)

```bash
# fundir 12+15+16+17+21 → "Verify & evidence" (pinned) + "Research-or-ask" (pinned)
# fundir 19+23+24+26 → "Security & secrets" (pinned)
# fundir 3+4 → "Skill lifecycle" ; 18+22 → "Lean context & minimal code"
# regras-skill-pointer (9, 27, 28, 29) → 1 linha cada
# atualizar audit.py rule-range + manifest.json rule_count + README badge
python audit.py && python -m pytest tests/ -q && git commit -m "docs(rules): minify AGENTS.md 18.3KB→~10KB, merge semantically duplicate rules"
```

### Fase 5 — adoção nativa (avaliar, decidir por item)

```bash
# 5a. spike .devin-plugin/plugin.json — se devin plugins install cobrir o fluxo, installer vira wrapper
# 5b. permissions.deny: ["Write(**/.env*)","Write(**/credentials*)","Read(**/.env*)"] — substitui parte do destructive-gate
# 5c. --sandbox: documentar em DEVIN-CLI-COMPATIBILITY.md como recomendado p/ projetos gerenciados
# 5d. instrumentar validate-tool-args (log hit-rate 1 semana) → deletar se ~0
# 5e. devin doctor no install.ps1/sh pós-instalação
```

### Fase 6 — verificação final

```bash
python audit.py                      # 0 errors
python -m pytest tests/ -q           # tudo verde
bash -n install.sh                   # sintaxe
git diff --stat main...HEAD          # relatório de impacto
# gate: AGENTS.md ≤11KB; SKILL.md count ~50; exec-hook total ≤200ms medido
```

**Critérios de corte canceláveis:** se qualquer fusão reduzir cobertura de trigger (verificar com `skill search` pós-merge), reverter aquele par. Nenhuma deleção sem grep prévio por referências (`grep -rn "skill-name" .`).

---

*Relatório gerado sob o mandato "zero-piedade": cada KB de overhead tratado como erro fatal, cada claim ancorado em medição local ou fonte citada. Aprovação pendente — nenhum arquivo de código, regra, skill ou hook foi modificado.*
