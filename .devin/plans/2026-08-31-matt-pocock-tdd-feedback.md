# Plano: TDD / red-green-refactor para agentes de IA

**Bloqueado por:** nenhum.

**Objetivo:** fortalecer skill `tdd` para que agentes escrevam teste vermelho antes da implementação e reflitam sobre isso explicitamente, dificultando trapaça em testes.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamps: `01:02:20.240–01:10:35.920`
- Conceitos: red-green-refactor, agentes que trapaceiam testes, feedback loops como teto de qualidade.

## Hipóteses a testar

1. `tdd` skill atual não deixa explícito que o teste deve falhar (red) antes do implementation.
2. Agentes podem gerar teste frouxo ou após a implementação.
3. A qualidade dos feedback loops do projeto limita a qualidade do código da IA.

## Falha a observar

- `skills/tdd/SKILL.md` pode ser insuficiente para forçar red-green-refactor.
- Não há verificador de que testes foram escritos antes do código.

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `skills/tdd/SKILL.md`.
- [ ] 0.2 — Pesquisar fontes de TDD (Kent Beck, Pragmatic Programmer).
- [ ] 0.3 — Verificar se `validate-tool-args.py` ou `check-push-green.py` já checam ordem de teste.

## FASE 1 — Observar

Comando: `read skills/tdd/SKILL.md` e procurar por "red" e "green".
Resultado: ausência de red-green-refactor explícito.

## FASE 2 — Criticar

- Regra violada: Rule 10 (declare without verifying).
- Comportamento: skill menciona TDD, mas não força ciclo.
- Intenção: cobrir TDD como prática.
- Falha: agente escreve teste após código e teste é fraco.

## FASE 3 — Gerar alternativas

1. Reescrever `tdd/SKILL.md` com red-green-refactor passo a passo.
2. Adicionar hook `PreToolUse` para exigir teste escrito antes de `edit`/`write` em code? Impossível/tarde demais.
3. Criar skill `red-green-refactor` separada.

## FASE 4 — Revisar

Aplicar alternativa 1; se muito grande, split com 3.

## FASE 5 — Validar

- Teste: agente segue a skill para adicionar função faltante.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Testes melhores no bundle. Ajuda? Sim.
2. Menos regressões. Ajuda? Sim.
3. Melhor integração com feedback loops. Ajuda? Sim.

## FASE 7 — Ecological check

- Não tornar `tdd` skill muito longa.
- Não conflitar com `testing` skills existentes.

## Arquivos esperados

- `skills/tdd/SKILL.md` (atualizado)
- `ledgers/tdd-pocock.md`
