# Ledger: prd-to-issues (destination document + vertical slices)

## Gates FASE 0

- [x] 0.1 Ler planning-pipeline e writing-plans
  OUTCOME: Entender templates atuais.
  CHECK: read skills/planning-pipeline/SKILL.md e skills/writing-plans/SKILL.md
  EXPECT: Resumo dos templates.
  EVIDENCE: Lidos `skills/planning-pipeline/SKILL.md` (modos Spec/Tickets/Questionnaire; Tickets já menciona vertical slices) e `skills/writing-plans/SKILL.md` (header, task structure, placeholders, self-review). Templates atuais não têm seção "módulos propostos" nem distinção explícita de ativos descartáveis vs vivos.

- [x] 0.2 Inspecionar planos existentes
  OUTCOME: Padrão horizontal vs vertical identificado.
  CHECK: grep -n "schema\|API\|UI\|vertical\|tracer" docs/plans/*.md
  EXPECT: Matches listados.
  EVIDENCE: `grep` em `docs/plans/*.md` retornou matches principalmente em `2026-08-31-matt-pocock-prd-to-issues.md` (conceitos) e `2026-08-26-melhoria-ux-seletores.md` usa `## Task 1: Padronizar seleção de número de instâncias`, `## Task 2: Refatorar exibição de branchs`, `## Task 3: Melhorar UX do Show-TerminalList`, `## Task 4: Validação` — tarefas por componente, não por fatia end-to-end; não há "Proposed Modules" no cabeçalho.

- [x] 0.3 Verificar project-setup / writing-for-agents
  OUTCOME: Saber se já existe tratamento.
  CHECK: grep -n "módulos propostos\|proposed modules\|vertical slice" skills/project-setup/SKILL.md skills/writing-for-agents/SKILL.md
  EXPECT: Resultado documentado.
  EVIDENCE: `grep` retornou 0 matches em ambos os arquivos. O tratamento não existe nessas skills.

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` → "ALL 31 CHECKS PASSED - NO ERRORS, NO WARNINGS"; `python -m pytest tests/held-out/ -q` → "135 passed".

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir alterações.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Decisão registrada.
  EVIDENCE: Decisão: aplicar alternativas 1 + 3 — (1) adicionar seção "Proposed Modules and Interfaces" e marcação de ativos ao template de `writing-plans`; (3) fortalecer o modo Tickets de `planning-pipeline` para PRD como destination document, fatias verticais/tracer bullets e declaração de módulos/interfaces antes das tarefas.

## Gates FASE 1–10

- [x] 1. Observar planos existentes
  OUTCOME: Confirmar que planos são horizontais.
  CHECK: grep -A2 "### Task" docs/plans/*.md | head -60
  EXPECT: Evidência de fases por camada.
  EVIDENCE: `grep -A2 "### Task"` não retornou matches; os planos usam `## Task N` e estão organizados por componente/área (UI seletores, colunas, validação), não por fatias verticais end-to-end. Faltam "módulos propostos" e "tracer bullets".

- [x] 2. Criticar (Rule 10)
  OUTCOME: Justificar por que horizontal atrasa feedback.
  CHECK: Documentar no ledger.
  EXPECT: Crítica escrita.
  EVIDENCE: Plano por componente atrasa feedback: o revisor só consegue validar a funcionalidade quando todas as camadas terminam; a IA perde o contexto entre camadas e retrabalha interfaces descobertas ad hoc; sem módulos/interfaces declarados antecipadamente, cada tarefa recria contratos. Rule 10 (não executar sem planejar, não declarar sem verificar) é violada quando as tarefas não são verificáveis isoladamente.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas listadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE: (1) Adicionar seção "Módulos propostos" ao template de `writing-plans`; (2) Criar skill `prd-to-issues` que gera issues de fatia vertical; (3) Atualizar `planning-pipeline` Tickets mode para enfatizar vertical slices.

- [x] 4. Revisar e selecionar alternativas
  OUTCOME: Aplicar 1 + 3 (template + enfatizar vertical slices).
  CHECK: Decisão no ledger.
  EXPECT: Escopo definido.
  EVIDENCE: Escopo definido: alterar `skills/writing-plans/SKILL.md` (adicionar "Proposed Modules and Interfaces", asset lifespan, vertical-slice scan) e `skills/planning-pipeline/SKILL.md` (Spec como PRD destination, declaração de módulos/interfaces antes dos tickets, regras e perguntas de tracer bullet, campos "Proposed modules / interfaces affected" nos templates de ticket). Não criar nova skill; não alterar planos antigos.

- [x] 5. Validar com código
  OUTCOME: Templates atualizados; plano de exemplo segue novo formato.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` → 0 errors, 31 checks OK; `python -m pytest tests/held-out/ -q` → 135 passed. Plano de exemplo `docs/plans/2026-08-31-prd-vertical-slice-example.md` criado com header novo, módulos propostos e tarefa 1 como fatia vertical com ativo `tmp_sample.csv` descartável.

- [x] 6. Future pace
  OUTCOME: 3 cenários avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Não.
  EVIDENCE: (1) Novo plano entrega valor end-to-end mais cedo — Sim, cada tarefa é uma fatia demoável; (2) Revisor pode validar fatia isolada — Sim, o header declara módulos/interfaces e cada tarefa tem teste e deliverable end-to-end; (3) Menos retrabalho por IA perdida — Sim, as interfaces são declaradas antes das tarefas e os ativos descartáveis são deletados antes do merge.

- [x] 7. Ecological check
  OUTCOME: Planos antigos não alterados; novo template não obrigatório para pequenos planos.
  CHECK: diff docs/plans/*.md
  EXPECT: Apenas templates novos ou atualizados.
  EVIDENCE: `git diff -- docs/plans/*.md` não retornou mudanças em planos antigos. `git status --short` mostra `docs/plans/2026-08-31-prd-vertical-slice-example.md` como novo arquivo não rastreado. O novo template inclui `## Proposed Modules and Interfaces (optional for small plans)` e `**Assets:** ... Omit this section if every file is living`, portanto campos são opcionais para planos pequenos.

- [x] 8. Simular
  OUTCOME: Gerar plano de teste com fatia vertical.
  CHECK: Revisar plano gerado.
  EXPECT: Presença de módulos propostos e fatia vertical.
  EVIDENCE: Plano gerado em `docs/plans/2026-08-31-prd-vertical-slice-example.md`: contém `## Proposed Modules and Interfaces` com funções e endpoints; `## Tarefa 1: Usuário pode visualizar a importação de CSV` cobre parse, endpoint e teste (fatia vertical); inclui `tmp_sample.csv` como ativo prototype/disposable com step de remoção.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: **MELHOROU**. Baseline: skills e planos não tinham PRD destination, módulos propostos, fatias verticais explícitas nem distinção de ativos descartáveis. Final: `writing-plans` e `planning-pipeline` agora forçam esses elementos; exemplo demonstra o formato; `audit.py` 0 erros / 31 checks OK; `pytest tests/held-out/` 135 passed; nenhum plano antigo foi alterado.

- [ ] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: pending
