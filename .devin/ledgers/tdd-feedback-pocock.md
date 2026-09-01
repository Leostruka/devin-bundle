# Ledger: tdd-feedback (red-green-refactor para agentes)

## Gates FASE 0

- [x] 0.1 Ler tdd SKILL.md
  OUTCOME: Entender skill atual.
  CHECK: read skills/tdd/SKILL.md
  EXPECT: Resumo.
  EVIDENCE: `read skills/tdd/SKILL.md` (187 lines). Skill une iron-law e seams-first; já possui seção Red-Green-Refactor, mas sem contrato explícito, reflexão anti-cheat nem teto de feedback loop.

- [x] 0.2 Pesquisar fontes TDD
  OUTCOME: Citar Kent Beck / Pragmatic Programmer.
  CHECK: web_search "Kent Beck red green refactor" e/ou Inspecionar livro
  EXPECT: Fontes listadas.
  EVIDENCE: Fontes primárias em `docs/plans/2026-08-31-roadmap-matt-pocock-ai-coding.md` linhas 59-60: Andrew Hunt & David Thomas, *The Pragmatic Programmer* (tracer bullets); Kent Beck, *Test-Driven Development by Example* (red-green-refactor). Também citado em `.devin/notes/youtube/-QFHIoCo-Ko/video-analysis-WIP.md` linha 54 (tracer bullets) e linha 73 (TDD/feedback loops).

- [x] 0.3 Verificar validadores existentes
  OUTCOME: Saber se validate-tool-args.py ou check-push-green.py checam ordem.
  CHECK: grep -n "test.*before\|red.*green" scripts/*.py
  EXPECT: Resultado documentado.
  EVIDENCE: `grep -n "test.*before\|red.*green" scripts/*.py` retornou 0 matches. Leitura de `scripts/validate-tool-args.py` (304 linhas) e `scripts/check-push-green.py` (136 linhas) confirma que nenhum valida a ordem teste-antes-código; `check-push-green.py` só bloqueia push se suite falhar ou se houver gap validation/held-out.

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` -> Errors: 0, Warnings: 0, ALL 31 CHECKS PASSED; `python -m pytest tests/held-out/ -q` -> 135 passed in 4.76s.

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir atualização da skill.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Decisão registrada.
  EVIDENCE: Decisão: aplicar alternativa 1 — atualizar `skills/tdd/SKILL.md` com contrato RED-VERIFY_RED-GREEN-VERIFY_GREEN-REFLECT-REFACTOR, seção ANTI-CHEAT e seção `Feedback Loops Are the Quality Ceiling`. Alternativa 2 (hook PreToolUse) inviável fora do escopo de hooks do bundle; alternativa 3 (skill separada) duplicaria `tdd`.

## Gates FASE 1–10

- [x] 1. Observar SKILL.md atual
  OUTCOME: Confirmar ausência de red-green-refactor explícito.
  CHECK: grep -n "red\|green\|refactor" skills/tdd/SKILL.md
  EXPECT: Poucos ou nenhum match.
  EVIDENCE: Baseline: `grep -in "red\|green\|refactor" skills/tdd/SKILL.md` -> 16 matches, incluindo seção `Red-Green-Refactor`, mas sem contrato ordenado, sem passo REFLECT e sem seção de feedback loop. Após edição: 38 matches, com contrato `RED→verify RED→GREEN→verify GREEN→REFLECT→REFACTOR`, `ANTI-CHEAT` e `Feedback Loops Are the Quality Ceiling`.

- [x] 2. Criticar (Rule 10)
  OUTCOME: Justificar por que teste após código é fraco.
  CHECK: Documentar no ledger.
  EXPECT: Crítica escrita.
  EVIDENCE: Rule 10: "Don't execute without planning, don't declare without verifying". A skill declarava TDD, mas não obrigava o agente a (a) verificar RED antes de GREEN, (b) refletir se o teste pode ser trapaceado, (c) usar o feedback loop do projeto. Isso permite testes escritos após o código, testes tautológicos ou testes que qualquer implementação errada passa — violando o espírito do TDD.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas listadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE: (1) Reescrever `skills/tdd/SKILL.md` com contrato red-green-refactor e anti-cheat; (2) Adicionar hook `PreToolUse` para exigir teste antes de `edit`/`write` em code (imposível/tarde demais no bundle atual); (3) Criar skill `red-green-refactor` separada.

- [x] 4. Revisar e selecionar alternativa
  OUTCOME: Atualizar tdd/SKILL.md com red-green-refactor.
  CHECK: Decisão no ledger.
  EXPECT: Escopo definido.
  EVIDENCE: Selecionada alternativa 1. Escopo: adicionar `The Red-Green-Refactor Contract`, `ANTI-CHEAT — Reflect on the Test`, `Feedback Loops Are the Quality Ceiling`, atualizar `Red Flags` e `Verification Checklist`, e adicionar cross-skill `verification-before-completion`.

- [x] 5. Validar com código
  OUTCOME: SKILL.md atualizado.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: Após edição: `python audit.py` -> Errors: 0, Warnings: 0, ALL 31 CHECKS PASSED; `python -m pytest tests/held-out/ -q` -> 135 passed.

- [x] 6. Future pace
  OUTCOME: 3 cenários avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Não.
  EVIDENCE: (1) Testes melhores no bundle? Sim — reflexão anti-cheat reduz testes tautológicos. (2) Menos regressões? Sim — testes honestos detectam comportamento faltante. (3) Melhor integração com feedback loops? Sim — skill agora obriga identificar e rodar o loop de feedback do projeto a cada ciclo.

- [x] 7. Ecological check
  OUTCOME: Skill não fica muito longa; não conflita com testing skills.
  CHECK: wc -l skills/tdd/SKILL.md ; grep "testing"
  EXPECT: Tamanho controlado; sem conflito.
  EVIDENCE: `wc -l skills/tdd/SKILL.md` -> 235 linhas (baseline 187, +48). `skills/e2e-testing/SKILL.md` cobre jornadas E2E; `skills/mutation-testing/SKILL.md` cobre mutação sistemática; `skills/verification-before-completion/SKILL.md` cobre evidência de verificação; `skills/code-review/SKILL.md` cobre revisão. A skill `tdd` permanece meta/protocolo e faz cross-reference, sem duplicar conteúdo.

- [x] 8. Simular
  OUTCOME: Agente segue skill para adicionar função faltante.
  CHECK: Testar mentalmente/subagente.
  EXPECT: Teste vermelho antes do código.
  EVIDENCE: Simulação: adicionar `calculate_total(cart)`. Passos do agente segundo `skills/tdd/SKILL.md`: (1) concorda seam (função pública); (2) escreve `test_calculate_total` com valor esperado independente; (3) roda e vê RED (falha por função inexistente); (4) escreve implementação mínima; (5) vê GREEN; (6) ANTI-CHEAT: "se retornar 0 ou hardcoded, o teste falha?"; (7) se sim, refatora; (8) repete. Contrato e checklist em SKILL.md suportam a sequência.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: MELHOROU — baseline e pós-edição passam em audit (0 errors/31 checks) e held-out (135 passed); skill agora força RED antes de GREEN, exige reflexão anti-cheat e inclui o feedback loop do projeto como teto de qualidade.

- [ ] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: pending
