# Plano: push/pull de padrões e code review automatizado

**Bloqueado por:** nenhum.

**Objetivo:** atualizar `code-review`, `receiving-code-review` e `impeccable` para declarar quando padrões/critérios devem ser "empurrados" para o reviewer (push) versus "puxados" pelo implementer (pull), e estudar a arquitetura Sand Castle para revisão paralela.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamps: `01:27:40.239–01:32:20.000`
- Conceitos: push vs pull de padrões, Sand Castle (planner, implementers, merger, Docker sandbox).

## Hipóteses a testar

1. `code-review` não distingue entre padrões que devem ser empurrados para o reviewer e puxados pelo implementer.
2. Não há skill para orquestrar múltiplos implementers em paralelo com merger.
3. O bundle pode se beneficiar de uma skill `sand-castle` de referência, mesmo sem implementar a lib.

## Falha a observar

- `skills/code-review/SKILL.md` não tem seção push/pull.
- Não há referência a Sand Castle ou fluxo de merger.

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `skills/code-review/SKILL.md`, `receiving-code-review/SKILL.md`, `impeccable/SKILL.md`.
- [ ] 0.2 — Ler `skills/dispatching-parallel-agents/SKILL.md`.
- [ ] 0.3 — Pesquisar Sand Castle (repositório de Pocock ou `web_search`).

## FASE 1 — Observar

Comando: `grep -n "push\|pull\|Sand Castle\|merger" skills/code-review/SKILL.md skills/dispatching-parallel-agents/SKILL.md`
Resultado: ausência de push/pull e Sand Castle.

## FASE 2 — Criticar

- Regra violada: Rule 3 (update outdated skills).
- Comportamento: code review unificado sem distinção de quem carrega os padrões.
- Intenção: revisar código de forma completa.
- Falha: implementer pode não saber dos padrões; reviewer pode sobrecarregar o contexto.

## FASE 3 — Gerar alternativas

1. Adicionar seção "Push vs pull" em `code-review`.
2. Criar skill `parallel-review` inspirada no Sand Castle.
3. Atualizar `receiving-code-review` para categorizar feedback em push/pull.

## FASE 4 — Revisar

Aplicar alternativa 1 + 3, deixando 2 para depois.

## FASE 5 — Validar

- Teste: simular review onde padrões devem ser puxados/puxados.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Revisor recebe padrões explícitos. Ajuda? Sim.
2. Implementer sabe quando consultar skill. Ajuda? Sim.
3. Paralelização de subagentes fica mais documentada. Ajuda? Sim.

## FASE 7 — Ecological check

- Não criar dependência de Docker no bundle.
- Sand Castle fica como referência, não implementação.

## Arquivos esperados

- `skills/code-review/SKILL.md` (atualizado)
- `skills/receiving-code-review/SKILL.md` (atualizado)
- `ledgers/push-pull-review-pocock.md`
