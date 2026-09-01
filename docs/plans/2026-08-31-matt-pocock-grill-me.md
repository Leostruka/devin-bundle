# Plano: evoluir skill `grilling` para alinhamento com recomendações

**Bloqueado por:** nenhum.

**Objetivo:** atualizar `grilling` para (a) perguntar de forma mais assertiva, (b) oferecer recomendação junto de cada pergunta e (c) exportar o asset da conversa como design concept.

## Evidência de entrada

- URL: `https://www.youtube.com/watch?v=-QFHIoCo-Ko`
- Timestamp: `00:15:02.480–00:22:03.600`
- Prática: Pocock inicia toda peça de trabalho com `/grill me` e a conversa vira asset.

## Hipóteses a testar

1. A skill `grilling` atual não oferece uma recomendação para cada pergunta.
2. `grilling` não tem parada inteligente, podendo ser muito curta ou muito longa.
3. O asset da conversa pode ser reutilizado como contexto para `writing-plans`.

## Falha a observar

- `skills/grilling/SKILL.md` não tem instrução para oferecer recomendação junto à pergunta.
- Não há exportador para design concept.

## FASE 0 — obrigatória

- [ ] 0.1 — Ler `skills/grilling/SKILL.md` e `grilling-frontier.md`.
- [ ] 0.2 — Comparar com o exercício do workshop (clientbrief.mmd).
- [ ] 0.3 — Verificar se há exemplos no bundle.

## FASE 1 — Observar

Comando: `read skills/grilling/SKILL.md`
Resultado: sem recomendação obrigatória e sem export.

## FASE 2 — Criticar

- Regra violada: Rule 4 (invoke matching skills) / Rule 7 (opinion-silent).
- Comportamento atual: pergunta sem sinal.
- Intenção positiva: evitar assumir respostas do usuário.
- Falha: sem recomendação, o usuário gasta mais tokens respondendo.

## FASE 3 — Gerar alternativas

1. Adicionar "recomendação padrão" a cada pergunta no SKILL.md.
2. Criar `/grill-me-with-recommendations` skill separada.
3. Usar `ask_user_question` com `options` em vez de texto livre.

## FASE 4 — Revisar

Aplicar alternativa 1 para manter a skill existente.

## FASE 5 — Validar

- Teste escolhido: invocar `/grilling` com `clientbrief.mmd` e ver se gera recomendações.
- Held-out: `python -m pytest tests/held-out/ -q`.

## FASE 6 — Future pace

1. Usuário passa 50% menos mensagens. Ajuda? Sim.
2. Asset exportável vira PRD. Ajuda? Sim.
3. Pareamento com PO melhora. Ajuda? Sim.

## FASE 7 — Ecological check

- Não aumentar muito a skill (Rule 18).
- Não quebrar `grilling-frontier`.

## FASE 8 — Simular

- Instalar skill, invocar com brief de exemplo.

## FASE 9 — Classificar

Esperada: MELHOROU se a skill fizer menos perguntas e melhores.

## Arquivos esperados

- `skills/grilling/SKILL.md` (atualizado)
- `ledgers/grilling-matt-pocock.md` (novo)
