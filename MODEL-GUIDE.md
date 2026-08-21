# Model Guide — GLM-5.2 High + SWE-1.7

Síntese de fontes primárias verificadas (2026-08-20) para operação ótima
destes dois modelos no Devin CLI.

## GLM-5.2 High (modelo primário)

| Atributo | Valor | Fonte |
|---|---|---|
| model_uid | `glm-5-2` | `devin models list` |
| Provider | ZAI (Zhipu AI) | Devin docs |
| Context window | 200K tokens | `devin models list` |
| Max output | 131,072 tokens | z.ai/blog/glm-5.2, docs.z.ai |
| Thinking mode | Habilitado por padrão (high) | z.ai/blog/glm-5.2 |
| Tool use | During inference (nativo) | z.ai/blog/glm-5.2 |
| Custo | **Gratuito e ilimitado** | `devin models list` (Free) |
| Cache read | $0.26/M tokens | Devin docs |
| Cache write | $0/M | Devin docs |
| Credit multiplier | 1.5 (High) | Devin docs |
| Recomendado | sim (is_recommended: true) | Devin docs |

### Variantes GLM-5.2

| model_uid | Label | Credit | Notas |
|---|---|---|---|
| `glm-5-2` | GLM-5.2 High | 1.5 | Default, thinking mode |
| `glm-5-2-max` | GLM-5.2 Max | 3 | Maior capacidade |
| `glm-5-2-max-1m` | GLM-5.2 Max 1M | 6 | 1M context window |
| `glm-5-2-none` | GLM-5.2 No Thinking | 1 | Sem thinking, mais barato |
| `glm-5-2-none-1m` | GLM-5.2 No Thinking 1M | — | Sem thinking, 1M context |

### Reasoning effort (controlado pelo model_uid)

No Devin CLI, `reasoning_effort` não é um campo separado na config — é
determinado pelo `model_uid` escolhido. A UI oferece `Alt+T` para alternar.

| model_uid | reasoning_effort | Quando usar | Custo |
|---|---|---|---|
| `glm-5-2-none` | off | Extração, reescrita, classificação, transform determinística. Poucas constraints interagindo. Check barato (parser, schema, diff, unit test). | **Pago** (credit 1) |
| `glm-5-2` (High) | high | Debugging bounded, multi-file edit, tool selection, decisão com várias constraints. Tests + review. | **Gratuito** (credit 1.5) |
| `glm-5-2-max` (Max) | max | Long-horizon planning, arquitetura ambígua, root-cause difícil, decisão custosa/irreversível. Full evaluation ou expert review. | **Pago** (credit 3) |

**Mapeamento de valores** (fonte: glm52.ai/guides/glm-5-2-reasoning-effort,
Z.ai docs): `none`/`minimal` → off; `low`/`medium`/`high` → high;
`xhigh`/`max` → max. Não existem níveis intermediários — só 3 paths: off,
high, max.

**Recomendação Z.ai**: `max` para coding tasks. Mas `glm-5-2-max` é **pago**
— o default do bundle (`glm-5-2` = High, **gratuito**) é o equilíbrio
custo/benefício para trabalho geral. Trocar para `glm-5-2-max` via `/model`
apenas quando High não resolver e o custo for justificado (ver protocolo
de escalada abaixo).

### Linhagem

- GLM-4.5 (arXiv:2508.06471): 128K, MoE 355B/32B active, SWE-bench Verified 64.2%
- GLM-4.6: 200K (expandido de 128K), tool-use during inference, 30%+ mais
  eficiente que GLM-4.5, thinking mode, avaliado em 74 testes reais no
  Claude Code (supera Sonnet 4)
- GLM-5.2: evolução da linhagem, 200K, thinking mode, variantes 1M

### Implicações para o harness

1. **Tool-use nativo**: GLM-4.6+ decide quando invocar ferramentas durante
   inferência. O harness não deve over-specificar regras de tool-use —
   Rule 17 (verify with tools) alinha naturalmente. Não adicionar regras
   como "sempre use read antes de editar" — o modelo decide.

2. **Thinking mode**: raciocínio interno antes do output. Tokens de thinking
   não são output — Rule 8 (telegraphic) aplica só ao output. Não há
   necessidade de instruir o modelo a "pensar passo a passo" — já faz.

3. **Prompt caching barato ($0.26/M read)**: manter AGENTS.md e system
   prompt cache-stable. Regras pinned no topo = prefixo estável = cache hit.
   Não reordenar regras pinned frequentemente. Mudanças no final do
   AGENTS.md (non-pinned) não invalidam o cache do prefixo.

4. **Lost-in-the-middle (arXiv:2307.03172)**: curva U-shaped confirmada.
   Follow-up (arXiv:2407.03651 SWiM) mostra que o efeito persiste em
   contextos longos mesmo para GPT-4/Claude 3 Opus. Para GLM-5.2 200K:
   - Constraints críticas no início (pinned rules) ✓
   - Contexto recente no fim (recência) ✓
   - Evitar dependência de informação no meio do contexto
   - Constraint-pinning (Rule 14) é a defesa correta

5. **200K budget**: AGENTS.md ~5463 tok (2.73%), SKILL-TIERS ~1726 tok
   (0.86%), skills invocadas 1000-9700 tok (0.5-4.85%). Total fixo:
   ~5463-16463 tok (2.73-8.23%). Restante: 91.77-97.27% para trabalho.

## SWE-1.7 (subagent default)

| Atributo | Valor | Fonte |
|---|---|---|
| Base model | Kimi K2.7 Code (post-RL) | cognition.com/blog/swe-1-7 |
| Context window | 262K tokens | `devin models list` (swe-1-7) |
| Inference speed | 1000 TPS (Cerebras) | cognition.com |
| Self-compaction | Treinada (summarize + resume) | cognition.com |
| Disponibilidade | Devin Web, Desktop, CLI | cognition.com |
| Custo | **Gratuito** (swe-1-7, swe-1-7-medium) | `devin models list` |

### Variantes SWE-1.7 (dados reais do sistema — `devin models list`)

| model_uid | Label | Context | Custo | Notas |
|---|---|---|---|---|
| `swe-1-7` | SWE-1.7 Max | 262K | **Free** | Usado em todos os agents/ (pin `model: swe-1-7`) |
| `swe-1-7-medium` | SWE-1.7 Medium | 262K | **Free** | Alternativa mais leve, mesmo contexto |
| `swe-1-7-lightning` | SWE-1.7 Lightning Max | 202K | **$2.5/$12.5 MTok** | Alias `swe` aponta para este — **NÃO usar** |
| `swe-1-7-lightning-medium` | SWE-1.7 Lightning Medium | 202K | **$2.5/$12.5 MTok** | Pago |
| `swe-1-6` | SWE-1.6 | 200K | $0.5/$2.5 MTok | Default router sem pin |
| `swe-1-6-fast` | SWE-1.6 Fast | 200K | $0.5/$2.5 MTok | Pago |

**⚠️ CRÍTICO**: o alias `swe` aponta para `swe-1.7-lightning` (PAGO, 202K),
**não** para `swe-1.7` (gratuito, 262K). Os agents/ fazem pin `model: swe-1-7`
(não `swe`) para usar o modelo gratuito com mais contexto.

### Self-compaction (diferencial chave)

SWE-1.7 é treinada para:
1. Escrever summaries informativos e concisos do estado de trabalho
2. Resumir a partir desses summaries eficientemente

Técnica: alternating length penalty — incentiva output conciso sem
sacrificar correção. Rollouts de treino chegam a 6 horas.

Isso significa que SWE-1.7 preserva constraints melhor que modelos
genéricos durante compaction. Mas Governance Decay (arXiv:2606.22528v2)
mostra que compaction dropa constraints em TODOS os modelos testados
(7 famílias, 1323 episódios) — constraint-pinning ainda é necessário.

O hook `constraint-pinning.py` tem heuristic `summary_retains_constraints()`
que verifica se key phrases sobreviveram. Para SWE-1.7, o summary é mais
likely de reter constraints → pinning fires less often → comportamento
correto (pin só quando necessário).

### Implicações para subagent dispatch

1. **Context window**: 262K (Kimi K2.7 base, `devin models list`). Mais headroom que GLM-5.2
   (200K) — 28% mais contexto por subagent. Subagents podem fazer mais
   trabalho antes de precisar compaction. Fan-out econômico.

2. **1000 TPS**: muito rápido. Latência de subagent é baixa em wall-clock.
   Fan-out de 5-10 subagents paralelos é viável sem espera longa.

3. **Self-compaction**: subagents SWE-1.7 podem rodar mais tempo sem
   perda de contexto. Menos necessidade de `context-folding` em subagents.

4. **Conciso por design**: alternating length penalty treina output conciso.
   Não fightar com regras verbose. Rule 8 (telegraphic) alinha.

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

Para GLM-5.2 (200K parent) despachando SWE-1.7 (262K subagents, gratuito):
- Pesquisa/exploração extensa → subagent (262K headroom, 1000 TPS,
  gratuito, retorna só síntese)
- Implementação bounded → subagent implementer (model: swe-1-7, gratuito)
- Debugging iterativo que precisa de contexto acumulado → inline + compaction
- Arquitetura/decisão que precisa ver tudo → inline (GLM-5.2 High, gratuito)

## Estratégia de model pin em agents/

| Agent | model: pin | Modelo usado | Racional |
|---|---|---|---|
| researcher | `swe-1-7` | SWE-1.7 Max (262K, **Free**) | Read-only, gratuito, 262K, 1000 TPS |
| architect | `swe-1-7` | SWE-1.7 Max (262K, **Free**) | Read-only, gratuito, 262K para mais contexto |
| reviewer | `swe-1-7` | SWE-1.7 Max (262K, **Free**) | Read-only + exec, gratuito, SWE-1.7 suficiente |
| debugger | `swe-1-7` | SWE-1.7 Max (262K, **Free**) | Já ótimo — iteração rápida, gratuito |
| implementer | `swe-1-7` | SWE-1.7 Max (262K, **Free**) | Bounded tasks, gratuito, SWE-1.7 suficiente |

**Por que pin `swe-1-7` e não `swe`?** O alias `swe` aponta para
`swe-1.7-lightning` (PAGO, $2.5/$12.5 MTok, 202K). Pin `swe-1-7` usa o
modelo **gratuito** com **262K** context (mais contexto que o pago).
Sem pin, o router resolve para SWE-1.6 (pago, $0.5/$2.5 MTok, 200K).

**Trade-off**: pin `swe-1-7` é fixo — não auto-update para SWE-1.8 quando
lançado. Quando SWE-1.8 sair, atualizar os 5 agents/ para `swe-1-8` (ou
verificar se `swe-1-7` ainda é gratuito). O alias `swe` auto-update mas é
pago — não compensa.

O parent GLM-5.2 faz trabalho complexo inline. Para implementação que
precisa de GLM-5.2, usar `subagent_general` (herda parent, **gratuito**
quando parent é GLM-5.2 High) ou pin `model: glm-5-2` no agent.

### Profiles built-in vs custom agents (custo)

| Profile | Modelo | Custo | Quando usar |
|---|---|---|---|
| `subagent_general` | Herda parent (GLM-5.2 High) | **Gratuito** | Implementação que precisa de GLM-5.2, contexto isolado |
| `subagent_explore` | SWE-1.6 (default router) | **PAGO** ($0.5/$2.5 MTok) | **EVITAR** — usar custom agent `researcher` (gratuito) em vez |
| Custom agents (researcher, architect, etc.) | `swe-1-7` (pin) | **Gratuito** | Pesquisa, arquitetura, review, debug, implementação |

**⚠️ Nunca usar `subagent_explore`** — ele resolve para SWE-1.6 (pago).
Os custom agents com `model: swe-1-7` são gratuitos e têm mais contexto
(262K vs 200K). Fonte: docs.devin.ai/cli/subagents.

## Modelos pagos — fallback para casos extremos

**Gratuitos e ilimitados** na assinatura (dados de `devin models list`):
- `glm-5-2` — GLM-5.2 High (200K) — modelo primário do parent
- `swe-1-7` — SWE-1.7 Max (262K) — todos os subagents
- `swe-1-7-medium` — SWE-1.7 Medium (262K) — alternativa mais leve

**Pagos** (preços reais de `devin models list`, $/MTok In/Out):
- GLM-5.2 variantes: Max, No Thinking, 1M — $0.7/$2.2
- SWE-1.7 Lightning (alias `swe`): $2.5/$12.5 — **não usar**
- SWE-1.6: $0.5/$2.5
- Claude Opus 5: $5/$25 (fast: $10/$50)
- Claude Sonnet 5: $2/$10
- GPT-5.4: $2.5/$15 (fast: $5/$30)
- GPT-5.4 Mini (alias `gpt`): $0.75/$4.5
- GPT-5.3-Codex (alias `codex`): $1.75/$14 (fast: $3.5/$28)
- Gemini 3.7 Flash (alias `gemini`): $0.75/$3.75
- Kimi K3: $3/$15
- DeepSeek V4 Flash: $0.14/$0.28 (mais barato pago)
- Grok 4.6: $2/$6

| Modelo | model_uid | Quando usar (casos extremos) | Custo $/MTok |
|---|---|---|---|
| GLM-5.2 Max | `glm-5-2-max` | GLM-5.2 High falhou em raciocínio complexo | $0.7/$2.2 |
| DeepSeek V4 Flash | `deepseek-v4-flash-high` | Mais barato pago, 1M context | $0.14/$0.28 |
| GPT-5.4 Mini | `gpt` | Segunda opinião, 400K context | $0.75/$4.5 |
| Claude Sonnet 5 | `sonnet` | Raciocínio Anthropic, 1M context | $2/$10 |
| Claude Opus 5 | `opus` | Máxima capacidade frontier, 1M context | $5/$25 |
| GPT-5.4 | `gpt-5-4-high` | Knowledge cutoff recente, 272K | $2.5/$15 |

**Protocolo de escalada (esgotar gratuitos antes de pagar):**
1. GLM-5.2 High (default, **gratuito**) — tentativa inicial
2. SWE-1.7 fan-out (`swe-1-7`, 262K, 1000 TPS, **gratuito**) — paralelismo
3. **GLM-5.2 Max** (`/model glm-5-2-max`, $0.7/$2.2) — reasoning depth maior
4. **DeepSeek V4 Flash** ($0.14/$0.28) — mais barato pago, 1M context
5. **Opus** (`/model opus`, $5/$25) — frontier, só após 3+ tentativas documentadas
6. **GPT-5.4** ($2.5/$15) — só se Opus também falhou

**Regra**: nunca usar modelos pagos para tarefas que GLM-5.2 High e
SWE-1.7 podem fazer. Os modelos gratuitos cobrem 95%+ dos casos.

## Context budget (200K GLM-5.2)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável aqui)
AGENTS.md                    ~5367 tok (2.68%)
SKILL-TIERS.md (se lido)     ~1726 tok (0.86%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (atlassian)    ~???? tok (medir com mcp-context-audit)
─────────────────────────────────────────────
Total fixo                   ~5463-16463 tok (2.73-8.23%)
Disponível para trabalho     ~183537-194537 tok (91.77-97.27%)
```

> Nota: este arquivo (MODEL-GUIDE.md) custa ~3711 tok (1.86%) se lido.
> É leitura opcional — não carrega automaticamente.

## Context budget (262K SWE-1.7 subagent)

```
System prompt + tool defs    ~???? tok (Devin runtime)
AGENTS.md                    ~5367 tok (2.10%)
Disponível para trabalho     ~250537 tok (97.90%)
```

Subagents têm significativamente mais headroom (262K vs 200K) e
self-compaction treinada. Preferir fan-out para pesquisa/exploração
extensiva que excederia o budget do parent.

## Verificação de fontes (Rule 12)

Todas as citações arXiv no AGENTS.md foram verificadas contra fontes
primárias em 2026-08-20:

| Citação | Status | URL primária |
|---|---|---|
| arXiv:2307.03172 (Lost in the Middle) | Verificado | aclanthology.org/2024.tacl-1.9 |
| arXiv:2606.22528v2 (Governance Decay) | Verificado | arxiv.org/abs/2606.22528v2 |
| arXiv:2607.13083 (Phantom Guardrails) | Verificado | arxiv.org/html/2607.13083 |
| arXiv:2606.30317 (MCP Patterns) | Verificado | arxiv.org/html/2606.30317 |
| arXiv:2607.25152 (Progress Mirage) | Verificado | arxiv.org/abs/2607.25152v1 |
| ICLR 2026 Workshop (Reward Hacking) | Verificado | iclr.cc/virtual/2026/10018648 |
| Llama 4 Scout 10M | Verificado | tokenmix.ai blog (secundário, Meta primário) |
| GLM-4.5 tech report | Verificado | arxiv.org/abs/2508.06471v1 |
| GLM-4.6 specs | Verificado | docs.z.ai/guides/llm/glm-4.6 |
| SWE-1.7 specs | Verificado | cognition.com/blog/swe-1-7 |
| GLM-5.2 Devin model_uid | Verificado | docs.devin.ai/desktop/models |
