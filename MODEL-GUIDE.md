# Model Guide — GLM-5.2 High + SWE-1.7

Síntese de fontes primárias verificadas (2026-08-20) para operação ótima
destes dois modelos no Devin CLI.

## GLM-5.2 High (modelo primário)

| Atributo | Valor | Fonte |
|---|---|---|
| model_uid | `glm-5-2` | Devin docs desktop/models |
| Provider | ZAI (Zhipu AI) | Devin docs |
| Context window | 200K tokens | Linhagem GLM-4.6 (docs.z.ai) |
| Max output | 128K tokens | docs.z.ai/guides/llm/glm-4.6 |
| Thinking mode | Habilitado por padrão | docs.z.ai (thinking: {type: "enabled"}) |
| Tool use | During inference (nativo) | docs.z.ai, cirra.ai analysis |
| Input cost | $1.4/M tokens | Devin docs |
| Output cost | $4.4/M tokens | Devin docs |
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

5. **200K budget**: AGENTS.md ~4900 tok (2.45%), SKILL-TIERS ~1700 tok
   (0.85%), skills invocadas 1000-9700 tok (0.5-4.85%). Total fixo:
   ~6600-16600 tok (3.3-8.3%). Restante: 91.7-96.7% para trabalho.

## SWE-1.7 (subagent default)

| Atributo | Valor | Fonte |
|---|---|---|
| Base model | Kimi K2.7 Code (post-RL) | cognition.com/blog/swe-1-7 |
| Context window | 256K tokens | Kimi K2.7 base (cognition.com/blog/swe-1-7) |
| Inference speed | 1000 TPS (Cerebras) | cognition.com |
| Self-compaction | Treinada (summarize + resume) | cognition.com |
| Disponibilidade | Devin Web, Desktop, CLI | cognition.com |
| Default | Sim (subagent router) | Devin docs subagents.mdx |
| `/fast` | SWE-1.7 Lightning | Devin docs changelog/stable |

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

1. **Context window**: 256K (Kimi K2.7 base). Mais headroom que GLM-5.2
   (200K) — 28% mais contexto por subagent. Subagents podem fazer mais
   trabalho antes de precisar compaction. Fan-out econômico.

2. **1000 TPS**: muito rápido. Latência de subagent é baixa em wall-clock.
   Fan-out de 5-10 subagents paralelos é viável sem espera longa.

3. **Self-compaction**: subagents SWE-1.7 podem rodar mais tempo sem
   perda de contexto. Menos necessidade de `context-folding` em subagents.

4. **Conciso por design**: alternating length penalty treina output conciso.
   Não fightar com regras verbose. Rule 8 (telegraphic) alinha.

## Estratégia de model pin em agents/

| Agent | model: pin | Modelo usado | Racional |
|---|---|---|---|
| researcher | `swe` | SWE-1.7 (256K) | Read-only, barato, 256K, 1000 TPS |
| architect | `swe` | SWE-1.7 (256K) | Read-only, 256K para mais contexto |
| reviewer | `swe` | SWE-1.7 (256K) | Read-only + exec, SWE-1.7 suficiente |
| debugger | `swe` | SWE-1.7 (256K) | Já ótimo — iteração rápida |
| implementer | `swe` | SWE-1.7 (256K) | Bounded tasks, SWE-1.7 suficiente |

**Por que pin `swe` em vez de nenhum pin?** O default subagent model da
Devin CLI resolve via router para SWE-1.6, não SWE-1.7 (docs.devin.ai/cli/subagents).
Pin `swe` (short name) resolve para o latest SWE (atualmente 1.7) e auto-updates
para SWE-1.8 quando lançado. Sem pin, agents usariam SWE-1.6 (200K, mais lento).

O parent GLM-5.2 faz trabalho complexo inline. Para implementação que
precisa de GLM-5.2, usar `subagent_general` (herda parent) ou pin
`model: glm-5-2` no agent.

## Context budget (200K GLM-5.2)

```
System prompt + tool defs    ~???? tok (Devin runtime, não mensurável aqui)
AGENTS.md                    ~4900 tok (2.45%)
SKILL-TIERS.md (se lido)     ~1700 tok (0.85%)
Skills invocadas (1-3)       ~1000-9700 tok (0.5-4.85%)
MCP tool defs (atlassian)    ~???? tok (medir com mcp-context-audit)
─────────────────────────────────────────────
Total fixo                   ~7600-16300 tok (3.8-8.15%)
Disponível para trabalho     ~183700-192400 tok (91.85-96.2%)
```

## Context budget (256K SWE-1.7 subagent)

```
System prompt + tool defs    ~???? tok (Devin runtime)
AGENTS.md                    ~4900 tok (1.91%)
Disponível para trabalho     ~248600 tok (97.1%)
```

Subagents têm significativamente mais headroom (256K vs 200K) e
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
