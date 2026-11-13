# Plano: aplicar smart zone / dumb zone e context clearing ao devin-bundle

**Bloqueado por:** nenhum.

**Objetivo:** tornar visível e acionável o risco de "dumb zone" e normalizar `clear` em vez de `compact` quando o contexto está pesado.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamp: `00:00:59.280–00:11:09.680`
- Transcript: fornecido via Tactiq.
- Fonte: interpretação de Matt Pocock sobre contexto de LLMs; marcador ~100k tokens para início da "dumb zone".

## Hipóteses a testar

1. O bundle não avisa quando a sessão está próxima da "dumb zone".
2. Agentes e skills que usam `compact` podem estar perdendo sinal em vez de ganhá-lo.
3. `context-window-hygiene` pode incluir uma recomendação explícita de `/clear` acima de um threshold.

## Falha a observar

- `context-budget.py` exibe bytes/tokens, mas não dispara um aviso quando o uso passa de ~100k.
- Skills longas podem ser carregadas sem checagem de budget.

## FASE 0 — obrigatória

- [ ] 0.1 — `web_search` + `webfetch` em docs.devin.ai sobre context window, compact e clear.
- [ ] 0.2 — Confirmar `config.json` e hooks atuais (`context-budget.py`, `constraint-pinning.py`).
- [ ] 0.3 — Procurar fontes primárias sobre lost-in-the-middle (arXiv:2606.22528v2 etc.).
- [ ] 0.4 — `python audit.py` + `python -m pytest tests/held-out/ -q` para baseline.
- [ ] 0.5 — Síntese de melhorias candidatas.

## FASE 1 — Observar

Comando: `python scripts/context-budget.py` em sessão longa.
Resultado esperado: output numérico, sem aviso de zona.

## FASE 2 — Criticar

- Regra violada: Rule 18 (context window lean).
- Comportamento atual: agente compacta em vez de limpar.
- Intenção positiva: preservar histórico de conversa.
- Por que falha: histórico compactado mantém ruído e gasta atenção.

## FASE 3 — Gerar alternativas

1. Adicionar threshold de ~100k tokens em `context-budget.py` e emitir nudge no `SessionStart`.
2. Criar `/smart-zone` skill que recomenda `clear` quando o contexto está alto.
3. Atualizar `context-window-hygiene` para mencionar a crítica de Pocock a `compact`.

## FASE 4 — Revisar

Aplicar a alternativa com maior ROI (prob. alternativa 1).

## FASE 5 — Validar

- Teste escolhido: `python scripts/context-budget.py` com valores acima do threshold.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Sessão de 120k tokens → nudge lembra de limpar. Ajuda? Sim.
2. Skill sendo invocada → budget visível. Ajuda? Sim.
3. CI/hook → bloqueia avanço na dumb zone. Ajuda? Sim.

## FASE 7 — Ecological check

- Não exibir valores de segredo (Rule 19).
- Não aumentar o system prompt (Rule 18).

## FASE 8 — Simular

- Carregar hooks, invocar skill, verificar audit/held-out.

## FASE 9 — Classificar

Esperada: MELHOROU se o nudge reduzir sessões longas sem quebrar nada.

## Arquivos esperados

- `scripts/context-budget.py` (modificado)
- `skills/context-window-hygiene/SKILL.md` (atualizado)
- Possível novo `skills/smart-zone/SKILL.md`
