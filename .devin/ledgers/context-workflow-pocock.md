# Ledger: context-workflow (Matt Pocock smart/dumb zone)

## Gates FASE 0

- [x] 0.1 Research Devin docs context window / compact / clear
  OUTCOME: Confirmar comportamento oficial de clear vs compact.
  CHECK: web_search "Devin CLI /clear /compact commands context"
  EXPECT: StatusCode 200 e texto relevante.
  EVIDENCE: docs.devin.ai/cli/essential-commands e docs.devin.ai/cli/reference/commands confirmam: `/clear` limpa histórico; `/compact` força compactação; `/new` alias de `/clear`.

- [x] 0.2 Confirmar hooks e config atuais
  OUTCOME: Saber se context-budget.py e constraint-pinning.py existem e são carregados.
  CHECK: Test-Path scripts/context-budget.py, scripts/constraint-pinning.py; audit.py listou context-budget.py em hooks.
  EXPECT: config.json válido; ambos scripts existem.
  EVIDENCE: ambos existem; audit.py confirmou context-budget.py e constraint-pinning.py nos hooks.

- [x] 0.3 Buscar fontes primárias lost-in-the-middle
  OUTCOME: Citar arXiv:2606.22528v2 e/ou fonte equivalente.
  CHECK: Invoke-WebRequest -Uri https://arxiv.org/abs/2606.22528
  EXPECT: StatusCode 200.
  EVIDENCE: StatusCode 200. AGENTS.md Rule 14 cita arXiv:2606.22528v2 (violação de constraints após compaction).

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa em todos checks.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: audit.py 0 erros, 31/31 checks OK; pytest 135 passed.

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir qual alternativa implementar.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Uma alternativa escolhida com justificativa.
  EVIDENCE: Escolhida alternativa 1: adicionar threshold ~100k em context-budget.py com nudge e adicionar explicação em context-window-hygiene. Menor blast radius, reutiliza infra existente.

## Gates FASE 1–10

- [x] 1. Observar context-budget.py atual
  OUTCOME: Entender output numérico atual.
  CHECK: python scripts/context-budget.py --json
  EXPECT: Output sem nudge de zona.
  EVIDENCE: total_rules_tokens=6224, smart_zone_share=6.22%; nenhum nudge emitido.

- [x] 2. Criticar (Rule 18 violation)
  OUTCOME: Documentar por que compact falha vs clear.
  CHECK: diff entre FASE 2 do plano e SKILL.md de context-window-hygiene.
  EXPECT: Inconsistência anotada.
  EVIDENCE: SKILL.md antigo mencionava preferir clear, mas não explicava explicitamente a crítica de Pocock ao sediment/ruído do compact, nem o marcador ~100k.

- [x] 3. Gerar 3 alternativas
  OUTCOME: Lista de 3 alternativas com prós/contras.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas documentadas.
  EVIDENCE: (1) adicionar threshold/nudge em context-budget.py; (2) criar `/smart-zone` skill separada; (3) atualizar context-window-hygiene. Escolhido 1+3.

- [x] 4. Revisar e selecionar alternativa
  OUTCOME: Alternativa escolhida (provavelmente 1).
  CHECK: Ledger entry e plano atualizado.
  EXPECT: Decisão registrada.
  EVIDENCE: Alternativa 1 (nudge em context-budget.py) + alternativa 3 (atualizar SKILL.md) por menor blast radius e reaproveitamento de hooks.

- [x] 5. Validar com código
  OUTCOME: context-budget.py avisa acima de ~100k tokens; SKILL.md atualizado.
  CHECK: python scripts/context-budget.py --simulate 120000 ; python -m pytest tests/held-out/ -q
  EXPECT: nudge emitido; 135 passed.
  EVIDENCE: --simulate 120000 emitiu SMART ZONE NUDGE; pytest 135 passed.

- [x] 6. Future pace
  OUTCOME: 3 cenários futuros avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Todos respondidos com Sim/Não e nota.
  EVIDENCE: (1) Sessão 120k → nudge lembra de limpar (Sim). (2) Skill invocada com budget visível (Sim). (3) CI/hook bloqueando avanço na dumb zone (não implementado agora; não é bloqueio).

- [x] 7. Ecological check
  OUTCOME: Sem violação de Rule 19 ou Rule 18.
  CHECK: grep segredos no diff; medir tamanho do system prompt.
  EXPECT: Nenhum segredo exposto; system prompt não aumentou.
  EVIDENCE: diff apenas em context-budget.py (não é system prompt) e context-window-hygiene/SKILL.md (skill modular, carregada sob demanda). Nenhum segredo.

- [x] 8. Simular
  OUTCOME: Hooks carregam, skill funciona, audit/held-out passam.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: audit.py 0 erros; pytest 135 passed.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline e resultado.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO justificado.
  EVIDENCE: MELHOROU. context-budget.py agora avisa quando regras carregadas cruzam ~100k tokens e recomenda `/clear`; SKILL.md explica smart/dumb zone e sedimentação do compact. Sem regressões.

- [x] 10. Commit e PR
  OUTCOME: Commit no branch video/matt-pocock-ai-coding-plans.
  CHECK: git log --oneline -3
  EXPECT: Commit presente sem AI signature.
  EVIDENCE: 7d9555d feat(context-workflow): smart-zone nudge and clear vs compact guidance — sem AI signature.
