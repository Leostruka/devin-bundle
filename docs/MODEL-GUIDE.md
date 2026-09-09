# Model Guide

Síntese da política de modelos do bundle. Valores concretos estão em `data/bundle-models.json`; as variáveis de ambiente `BUNDLE_DEFAULT_MODEL`, `BUNDLE_MAX_MODEL` e `BUNDLE_MEDIUM_MODEL` podem sobrescrever os padrões. A versão validada do CLI está em `data/bundle-identity.json`.

## Primary model (parent)

O modelo primário (parent) é definido por `BUNDLE_DEFAULT_MODEL` (ou `data/bundle-models.json.default_parent_model`).

| Atributo | Valor | Fonte |
|---|---|---|
| model_uid | `{{BUNDLE_DEFAULT_MODEL}}` | `data/bundle-models.json` / `devin models list` |
| Provider | veja `data/bundle-models.json` | Devin docs / provider docs |
| Context window | `context_window` do registro | `data/bundle-models.json` |
| Max output | veja registro | provider docs |
| Thinking mode | configurável pelo `model_uid` | Devin docs |
| Tool use | nativo durante inferência | Devin docs |
| Custo | `cost_tier: free` para o default | `data/bundle-models.json` / `devin models list` |
| Cache read | veja registro | Devin docs |
| Credit multiplier | veja registro | Devin docs |

### Variantes do parent

As variantes do parent (e.g., Max, No Thinking, 1M context) estão em `data/bundle-models.json`. Escolha o `model_uid` que define o `reasoning_effort` desejado. O default do bundle é o modelo gratuito com thinking mode alto.

### Reasoning effort (controlado pelo model_uid)

No Devin CLI, `reasoning_effort` não é um campo separado na config — é
determinado pelo `model_uid` escolhido. A UI oferece `Alt+T` para alternar.

| Exemplo de variante | reasoning_effort | Quando usar | Custo |
|---|---|---|---|
| `no-thinking` | off | Extração, reescrita, classificação, transform determinística. Poucas constraints interagindo. Check barato. | veja `data/bundle-models.json` |
| default parent (`{{BUNDLE_DEFAULT_MODEL}}`) | high | Debugging bounded, multi-file edit, tool selection, decisão com várias constraints. Tests + review. | **Gratuito** no bundle default |
| `max` variant | max | Long-horizon planning, arquitetura ambígua, root-cause difícil, decisão custosa/irreversível. | veja `data/bundle-models.json` |

**Mapeamento de valores**: `none`/`minimal` → off; `low`/`medium`/`high` → high;
`xhigh`/`max` → max. Não existem níveis intermediários — só 3 paths: off,
high, max.

**Recomendação geral**: `max` para coding tasks. A variante `max` pode ser paga —
o default do bundle é o modelo gratuito com thinking mode alto. Troque para `max`
apenas quando o default não resolver e o custo for justificado (verifique `cost_tier`
em `data/bundle-models.json`).

### Linhagem

A linhagem do primary model está documentada nos tech reports do provider. Consulte
`data/bundle-models.json` e o site do provider para detalhes de capacidade, contexto
e variantes.

### Implicações para o harness

1. **Tool-use nativo**: o primary model decide quando invocar ferramentas durante
   inferência. O harness não deve over-specificar regras de tool-use —
   Rule 17 (verify with tools) alinha naturalmente. Não adicionar regras
   como "sempre use read antes de editar" — o modelo decide.

2. **Thinking mode**: raciocínio interno antes do output. Tokens de thinking
   não são output — Rule 8 (telegraphic) aplica só ao output. Não há
   necessidade de instruir o modelo a "pensar passo a passo" — já faz.

3. **Prompt caching**: manter AGENTS.md e system prompt cache-stable. Regras pinned no topo = prefixo estável = cache hit. Não reordenar regras pinned frequentemente. Mudanças no final do AGENTS.md (non-pinned) não invalidam o cache do prefixo.

4. **Lost-in-the-middle (arXiv:2307.03172)**: curva U-shaped confirmada.
   Constraints críticas no início (pinned rules), contexto recente no fim,
   evitar dependência de informação no meio do contexto. Constraint-pinning
   (Rule 14) é a defesa correta.

5. **Budget**: porcentagens fixas da `context_window` em `data/bundle-models.json`
   são consumidas por AGENTS.md, SKILL-TIERS.md, skills invocadas e tool defs.
   O restante fica disponível para trabalho.

## Subagent models

O subagent default é definido por `BUNDLE_MAX_MODEL` (ou `data/bundle-models.json.default_subagent_model`). A alternativa mais leve é `BUNDLE_MEDIUM_MODEL` (ou `data/bundle-models.json.medium_role_model`).

| Atributo | Valor | Fonte |
|---|---|---|
| Base model | veja `data/bundle-models.json` | provider docs / Devin docs |
| Context window | `context_window` do registro | `data/bundle-models.json` |
| Inference speed | veja registro | provider docs |
| Self-compaction | Treinada (summarize + resume) | provider docs |
| Disponibilidade | Devin Web, Desktop, CLI | Devin docs |
| Custo | **Gratuito** para os defaults do bundle | `data/bundle-models.json` |

### Routing e benchmarks

Benchmarks de subagentes vs parent variam por provider e versão. Consulte `data/bundle-models.json` e os tech reports dos modelos para os números mais atuais.

A regra geral: tarefas de coding são delegadas para subagentes (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`); reasoning diverso, arquitetura e coordenação ficam no parent (`{{BUNDLE_DEFAULT_MODEL}}`).

### Variantes de subagent

| Campo | Descrição | Contexto | Custo | Notas |
|---|---|---|---|---|
| `{{BUNDLE_MAX_MODEL}}` | Subagent Max | veja `data/bundle-models.json` | **Free** | Usado em agents/ de planejamento/review |
| `{{BUNDLE_MEDIUM_MODEL}}` | Subagent Medium | veja `data/bundle-models.json` | **Free** | Alternativa mais leve para execução |
| `paid_model_alias` | Paid alias | veja `data/bundle-models.json` | veja registro | **NÃO usar** sem verificar `data/bundle-models.json` |
| default router | CLI fallback | veja `data/bundle-models.json` | possivelmente pago | Use pin para evitar custos inesperados |

**⚠️ CRÍTICO**: aliases não canônicos podem apontar para um modelo pago — **não use** sem verificar `data/bundle-models.json`.
 Os agents/ devem fazer pin com os modelos canônicos (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`) do bundle.

**⚠️ CRÍTICO — `subagent_explore` (built-in) pode ser pago**: o profile built-in
`subagent_explore` roda no default router do CLI, que pode cobrar por token.
Não há override local — apenas enterprise settings podem mudar isso.
**NUNCA dispatchar `subagent_explore`.** Usar o profile customizado `researcher`
(`agents/researcher.md`, pin `model: {{BUNDLE_MAX_MODEL}}`, gratuito, veja `data/bundle-models.json`)
que tem as mesmas capacidades read-only. Fonte: docs.devin.ai/cli/subagents.

### Self-compaction (diferencial chave)

Os subagentes do bundle são treinados para:
1. Escrever summaries informativos e concisos do estado de trabalho.
2. Resumir a partir desses summaries eficientemente.

Técnica: alternating length penalty — incentiva output conciso sem sacrificar correção.

Isso significa que os subagentes preservam constraints melhor que modelos genéricos
durante compaction. Mas Governance Decay (arXiv:2606.22528v2) mostra que compaction
dropa constraints em TODOS os modelos testados — constraint-pinning ainda é necessário.

O hook `constraint-pinning.py` tem heuristic `summary_retains_constraints()` que
verifica se key phrases sobreviveram. Para subagentes treinados, o summary é mais
likely de reter constraints → pinning fires less often → comportamento correto
(pin só quando necessário).

### Implicações para subagent dispatch

1. **Context window**: a janela do subagent está em `data/bundle-models.json`. Subagents podem fazer mais trabalho antes de precisar compaction. Fan-out econômico.
2. **Alto TPS**: subagentes são rápidos. Fan-out de 5-10 subagents paralelos é viável sem espera longa.
3. **Self-compaction**: subagents podem rodar mais tempo sem perda de contexto. Menos necessidade de `context-folding` em subagents.
4. **Conciso por design**: alternating length penalty treina output conciso. Não fightar com regras verbose. Rule 8 (telegraphic) alinha.
5. **Coding superiority**: benchmarks mostram vantagem dos subagentes para coding. Para tarefas de coding (implementação, debugging, refactoring), o parent deve delegar para subagentes em vez de implementar inline.

### Matriz de routing: parent inline vs subagent

| Task type | Best function | Como executar | Por quê |
|---|---|---|---|
| Implementação de código | Subagent Medium | `implementer` subagent | Coding strength |
| Debugging de código | Subagent Medium | `debugger` subagent (parent planeja) | Coding strength + AgentCARD: planner é bottleneck |
| Code review | Subagent Medium/Max | `reviewer` subagent | Sufficient for routine review |
| Research/exploração | Subagent Max | `researcher` subagent | Alto contexto, TPS, free |
| Arquitetura (routine) | Subagent Max | `architect` subagent | Sufficient for routine design |
| Arquitetura (high-stakes) | Parent model | inline ou `subagent_general` | Needs parent reasoning |
| Final whole-branch review | Parent model | inline ou `subagent_general` | Judgment task, max capability |
| Reasoning diverso | Parent model | inline | Primary model for diverse reasoning |
| Fix-loop escalation (R4-5) | Parent model | `subagent_general` | Fresh eyes + parent reasoning |
| Coordenação/orquestração | Parent model | inline (parent) | Parent role, never delegate |

### Subagent vs compaction: quando usar cada um

Fonte: dreaming.press/posts/subagents-vs-compaction-isolate-context

| Resposta | Mecanismo | Custo | Sobrevive reset? | Quando usar |
|---|---|---|---|---|
| **Subagent** | Fresh window, só final message retorna | ~15x tokens, sem herança automática | N/A — parent nunca teve o lixo | Subtask separável com resultado sumarizável (research sweep, file exploration, parallel review) |
| **Compaction** | Sumariza transcript, dropa verbatim | Lossy: specifics omitidos gone for good | Não — summary ainda em-window | Thread contínua de raciocínio que deve ficar coerente |
| **Context editing** | Evicta tool results antigos, keep 3 | Invalida prompt cache prefix | Parcial — results re-fetchable | Loop vivo que precisa de tool results recentes |

**Regra de composição**: subagents mantêm o orchestrator lean; compaction
mantém cada loop long-lived sob seu cap. Use subagents para evitar que
trabalho bulk entre no parent window; use compaction quando o trabalho
já está no parent e precisa continuar coerente.

Para o parent (`{{BUNDLE_DEFAULT_MODEL}}`) despachando subagents (`{{BUNDLE_MAX_MODEL}}`):
- Pesquisa/exploração extensa → subagent (alto headroom, TPS alto, gratuito quando `cost_tier: free`, retorna só síntese)
- Implementação bounded → subagent implementer (model: `{{BUNDLE_MEDIUM_MODEL}}`, gratuito)
- Debugging iterativo que precisa de contexto acumulado → inline + compaction
- Arquitetura/decisão que precisa ver tudo → inline (parent, gratuito quando `cost_tier: free`)

## Estratégia de model pin em agents/

| Agent | model: pin | Modelo usado | Racional |
|---|---|---|---|
| researcher | `{{BUNDLE_MAX_MODEL}}` | Subagent Max (veja `data/bundle-models.json`) | Read-only, gratuito, alto contexto, alto TPS |
| architect | `{{BUNDLE_MAX_MODEL}}` | Subagent Max | Read-only, gratuito, contexto extra |
| reviewer | `{{BUNDLE_MAX_MODEL}}` | Subagent Max | Read-only + exec, gratuito |
| debugger | `{{BUNDLE_MEDIUM_MODEL}}` | Subagent Medium | Iteração rápida, gratuito |
| implementer | `{{BUNDLE_MEDIUM_MODEL}}` | Subagent Medium | Bounded tasks, gratuito |

**Por que pin e não alias?** Aliases não canônicos podem apontar para um modelo pago.
Use os modelos canônicos do bundle (`{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}`)
que são gratuitos e têm a maior `context_window`. Sem pin, o router pode
resolver para um modelo pago. Quando novas versões saírem, atualize os agents/
para os novos modelos listados em `data/bundle-models.json`.

O parent (`{{BUNDLE_DEFAULT_MODEL}}`) faz trabalho complexo inline. Para implementação
que precisa do parent, usar `subagent_general` (herda parent, **gratuito**
quando parent é free) ou pin `model: {{BUNDLE_DEFAULT_MODEL}}` no agent.

### Profiles built-in vs custom agents (custo)

| Profile | Modelo | Custo | Quando usar |
|---|---|---|---|
| `subagent_general` | Herda parent (`{{BUNDLE_DEFAULT_MODEL}}`) | **Gratuito** (quando parent é free) | Implementação que precisa do parent, contexto isolado |
| `subagent_explore` | Default router do CLI | **PAGO** (possível) | **EVITAR** — usar custom agent `researcher` (gratuito) em vez |
| Custom agents (researcher, architect, etc.) | `{{BUNDLE_MAX_MODEL}}` / `{{BUNDLE_MEDIUM_MODEL}}` (pin) | **Gratuito** (quando free no registro) | Pesquisa, arquitetura, review, debug, implementação |

**⚠️ Nunca usar `subagent_explore`** — ele pode resolver para um modelo pago.
Os custom agents com os pins canônicos são gratuitos e têm mais contexto.
Fonte: docs.devin.ai/cli/subagents.

## Modelos pagos — política CONDICIONAL

**Gratuitos e ilimitados** na assinatura são definidos em `data/bundle-models.json`
com `cost_tier: free`:

- `{{BUNDLE_DEFAULT_MODEL}}` — parent (default)
- `{{BUNDLE_MAX_MODEL}}` — subagent Max
- `{{BUNDLE_MEDIUM_MODEL}}` — subagent Medium

**Pagos**: quaisquer entradas com `cost_tier: paid` em `data/bundle-models.json`,
incluindo aliases/short names. Sempre verifique o registro antes de usar um
modelo não-canônico.

### Política CONDICIONAL ao modelo do parent

**Caso 1 — Parent FREE (`cost_tier: free`): subagents DEVEM ser FREE.**

Protocolo FREE-ONLY:
1. Parent (`{{BUNDLE_DEFAULT_MODEL}}`) — tentativa inicial
2. Subagent Max fan-out (`{{BUNDLE_MAX_MODEL}}`) — paralelismo
3. Subagent Medium (`{{BUNDLE_MEDIUM_MODEL}}`) — alternativa de reasoning
4. Parent com thinking effort `max` (via `Alt+T`) — mais raciocínio, mesmo modelo gratuito
5. Repetir com contexto mais limpo (`clear` + recarregar apenas o necessário)
6. Se todos os gratuitos falharem: **parar e reportar ao usuário** — não escalar para pago

Neste caso: **NUNCA usar `subagent_explore`**, **NUNCA usar aliases pagos não verificados**
sem verificar `data/bundle-models.json`, **NUNCA usar modelos pagos** para subagents.

**Caso 2 — Parent PAGO (usuário escolheu um modelo pago): subagents podem usar pagos.**

O usuário já optou por pagar pelo parent. Neste caso:
- `subagent_explore` (default router, possivelmente pago) é permitido se for mais barato que o parent
- `subagent_general` herda o modelo pago do parent (já está pago)
- Custom profiles com os pins canônicos continuam FREE — preferir quando possível
- Para reasoning pesado, pode-se usar o mesmo modelo do parent via `subagent_general`

**Como detectar o caso**: verificar o `cost_tier` do modelo ativo no parent em `data/bundle-models.json`. Se for `free`, é Caso 1 (FREE-ONLY). Qualquer outro modelo é Caso 2.

**Regra**: quando o parent está em modelo FREE (`cost_tier: free`), **NUNCA usar
modelos pagos** para subagents. Os modelos gratuitos canônicos cobrem 100% dos casos.
Se ambos falharem, reportar ao usuário. Quando o parent está em modelo PAGO
(usuário escolheu), subagents podem usar modelos pagos.

## Context budget (parent model)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável aqui)
AGENTS.md                    ~5605 tok (2.80%)
SKILL-TIERS.md (se lido)     ~1726 tok (0.86%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (configured)   ~???? tok (medir com mcp-context-audit)
─────────────────────────────────────────────
Total fixo                   ~5605-16601 tok (2.80-8.30%)
Disponível para trabalho     consulte `context_window` em `data/bundle-models.json`
```

> Nota: este arquivo (MODEL-GUIDE.md) é leitura opcional — não carrega automaticamente.

## Context budget (subagent model)

```
System prompt + tool defs    ~???? tok (Devin runtime)
AGENTS.md                    ~5605 tok (2.14%)
Disponível para trabalho     consulte `context_window` em `data/bundle-models.json`
```

Subagents têm significativamente mais headroom e self-compaction treinada.
Preferir fan-out para pesquisa/exploração extensiva que excederia o budget do parent.

## Verificação de fontes (Rule 12)

Todas as citações arXiv no AGENTS.md foram verificadas contra fontes
primárias. Especificações de modelos devem ser verificadas contra
`data/bundle-models.json`, `devin models list` e os sites dos providers.

| Citação | Status | URL primária |
|---|---|---|
| arXiv:2307.03172 (Lost in the Middle) | Verificado | aclanthology.org/2024.tacl-1.9 |
| arXiv:2606.22528v2 (Governance Decay) | Verificado | arxiv.org/abs/2606.22528v2 |
| arXiv:2607.13083 (Phantom Guardrails) | Verificado | arxiv.org/html/2607.13083 |
| arXiv:2606.30317 (MCP Patterns) | Verificado | arxiv.org/html/2606.30317 |
| arXiv:2607.25152 (Progress Mirage) | Verificado | arxiv.org/abs/2607.25152v1 |
| ICLR 2026 Workshop (Reward Hacking) | Verificado | iclr.cc/virtual/2026/10018648 |
| Llama 4 Scout 10M | Verificado | tokenmix.ai blog (secundário, Meta primário) |
| Primary model tech report | Verificado | arxiv.org/abs/2508.06471v1 |
| Primary model specs | Verificado | provider docs |
| Subagent model specs | Verificado | provider docs |
| Primary model Devin model_uid | Verificado | docs.devin.ai/desktop/models |
| arXiv:2605.10039 (Instruction Adherence) | Verificado | arxiv.org/abs/2605.10039 |
| arXiv:2605.21384 (SpecBench) | Verificado | arxiv.org/abs/2605.21384 |
| arXiv:2603.15473 (ALTK) | Verificado | arxiv.org/abs/2603.15473 |
| arXiv:2607.07405 (Reason Less, Verify More) | Verificado | arxiv.org/abs/2607.07405 |
| arXiv:2605.09998 (Continual Harness) | Verificado | arxiv.org/abs/2605.09998 |
| arXiv:2607.17641 (VRR-Stop) | Verificado | arxiv.org/abs/2607.17641 |
| arXiv:2607.28802 (Model or Harness?) | Verificado | arxiv.org/abs/2607.28802 |
| arXiv:2512.24601 (Recursive Language Models) | Verificado | arxiv.org/abs/2512.24601 |
| arXiv:2602.03786 (AOrchestra) | Verificado | arxiv.org/abs/2602.03786 |
| arXiv:2603.02615 (RLM depth reproduction) | Verificado | arxiv.org/abs/2603.02615 |
| arXiv:2606.20629 (AgentCARD) | Verificado | arxiv.org/abs/2606.20629 |
| arXiv:2608.03535 (CodeAssay) | Verificado | arxiv.org/abs/2608.03535 |
| arXiv:2605.20251 (ProcCtrlBench) | Verificado | arxiv.org/abs/2605.20251 |
| arXiv:2607.20972 (Delivery, Not Storage) | Verificado | arxiv.org/abs/2607.20972 |
| arXiv:2608.15008 (Harness the Memory) | Verificado | arxiv.org/abs/2608.15008 |
