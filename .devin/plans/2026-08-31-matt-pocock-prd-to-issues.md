# Plano: PRD como destination document e fatias verticais

**Bloqueado por:** nenhum.

**Objetivo:** fortalecer `planning-pipeline` e `writing-plans` para gerar PRDs leves e quebrá-los em issues de fatias verticais (não horizontais), com módulos propostos explícitos.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamps: `00:29:58.960–00:47:01.839`
- Conceitos: PRD destination, módulos propostos, vertical slices, tracer bullets, doc rot.

## Hipóteses a testar

1. O bundle gera planos que são horizontais (camada por camada), não verticais.
2. `writing-plans` não declara módulos/interfaces afetados antes das tarefas.
3. Não há mecanismo para marcar assets como descartáveis (protótipos) vs vivos.

## Falha a observar

- Plans do bundle listam tarefas por etapa (schema, depois API, depois UI).
- Não há campo "módulos propostos" no cabeçalho dos planos.

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `planning-pipeline/SKILL.md` e `writing-plans/SKILL.md`.
- [ ] 0.2 — Inspecionar planos existentes em `docs/plans/`.
- [ ] 0.3 — Verificar se `project-setup` ou `writing-for-agents` já tratam disso.

## FASE 1 — Observar

Comando: `grep -n "módulos propostos\|fatia vertical\|tracer bullet" docs/plans/*.md`
Resultado esperado: 0 ou poucos matches.

## FASE 2 — Criticar

- Regra violada: Rule 10 (planning/verification).
- Comportamento: tarefas horizontais dificultam feedback.
- Intenção: organizar por responsabilidade técnica.
- Falha: IA perde feedback até a última camada.

## FASE 3 — Gerar alternativas

1. Adicionar seção "Módulos propostos" ao template de `writing-plans`.
2. Criar skill `prd-to-issues` que gera issues de fatia vertical.
3. Atualizar `planning-pipeline` Tickets mode para enfatizar vertical slices.

## FASE 4 — Revisar

Aplicar alternativa 1 + 3 para manter consistência com skills existentes.

## FASE 5 — Validar

- Teste: gerar um plano de teste e verificar se há fatia vertical.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Novo plano entrega valor end-to-end mais cedo. Ajuda? Sim.
2. Revisor pode validar fatia isolada. Ajuda? Sim.
3. Menos retrabalho por IA perdida. Ajuda? Sim.

## FASE 7 — Ecological check

- Não mudar planos antigos sem revisão.
- Novo template não deve exigir campos para planos pequenos.

## Arquivos esperados

- `skills/writing-plans/SKILL.md` (atualizado)
- `skills/planning-pipeline/SKILL.md` (atualizado)
- `docs/plans/...` (exemplos usando novo template)
