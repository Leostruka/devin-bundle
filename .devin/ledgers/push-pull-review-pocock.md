# Ledger: push-pull-review (padrões empurrados/puxados + Sand Castle)

## Gates FASE 0

- [x] 0.1 Ler code-review, receiving-code-review, impeccable
  OUTCOME: Entender skills atuais.
  CHECK: read skills/code-review/SKILL.md, skills/receiving-code-review/SKILL.md, skills/impeccable/SKILL.md
  EXPECT: Resumo.
  EVIDENCE: read skills/code-review/SKILL.md (202 linhas), skills/receiving-code-review/SKILL.md (209 linhas), skills/impeccable/SKILL.md (118 linhas).

- [x] 0.2 Ler dispatching-parallel-agents
  OUTCOME: Entender paralelização atual.
  CHECK: read skills/dispatching-parallel-agents/SKILL.md
  EXPECT: Resumo.
  EVIDENCE: read skills/dispatching-parallel-agents/SKILL.md (400+ linhas); fluxo de subagentes por tarefa, worktree, review por tarefa e final.

- [x] 0.3 Pesquisar Sand Castle
  OUTCOME: Mapear repositório/lib de Pocock.
  CHECK: web_search "Matt Pocock Sand Castle TypeScript multiple agents"
  EXPECT: Link(s) listados.
  EVIDENCE: GitHub API query: https://api.github.com/search/repositories?q=sandcastle+in:name -> repo `mattpocock/sandcastle` (https://github.com/mattpocock/sandcastle), desc "Orchestrate sandboxed coding agents in TypeScript with sandcastle.run()"; README salvo em `.devin/ledgers/sandcastle-readme.md`.

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` -> 0 errors, 0 warnings, 31 checks OK; `python -m pytest tests/held-out/ -q` -> 135 passed.

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir alterações.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Decisão registrada.
  EVIDENCE: Decisão: aplicar alternativas 1 (seção push/pull em code-review) + 3 (receiving-code-review categoriza feedback em push/pull); opcionalmente incluir note em impeccable. Sand Castle fica como referência textual, sem skill nova e sem Docker.

## Gates FASE 1–10

- [x] 1. Observar skills atuais
  OUTCOME: Confirmar ausência de push/pull e Sand Castle.
  CHECK: grep -n "push\|pull\|Sand Castle\|merger" skills/code-review/SKILL.md skills/dispatching-parallel-agents/SKILL.md
  EXPECT: 0 matches.
  EVIDENCE: grep case-insensitive em skills/ retornou 0 ocorrências de "Sand Castle" ou "merger" em code-review/dispatching-parallel-agents; apenas matches de "push/pull" em outros contextos (git push/pull, push back, etc.).

- [x] 2. Criticar (Rule 3)
  OUTCOME: Justificar falta de distinção push/pull.
  CHECK: Documentar no ledger.
  EXPECT: Crítica escrita.
  EVIDENCE: Crítica: code-review trata padrões como um único bloco a ser carregado no reviewer, sem declarar o que o implementer deve puxar por conta (ex: skills de tdd, verification-before-completion, projeto global_rules). Isso viola Rule 3 (skills desatualizadas) porque perde a distinção de Pocock (01:27:40) e sobrecarrega o contexto do reviewer com coisas que o implementer já deveria ter verificado.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas listadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE: (1) Adicionar seção "Push vs pull" em code-review; (2) Criar skill `parallel-review` inspirada no Sand Castle; (3) Atualizar `receiving-code-review` para categorizar feedback em push/pull.

- [x] 4. Revisar e selecionar alternativas
  OUTCOME: Aplicar 1 + 3 (seção push/pull em code-review + receiving-code-review).
  CHECK: Decisão no ledger.
  EXPECT: Escopo definido.
  EVIDENCE: Selecionadas alternativas 1 e 3, com referência a Sand Castle como padrão em code-review; alternativa 2 (nova skill) adiada. Incluir note opcional em impeccable.

- [x] 5. Validar com código
  OUTCOME: Skills atualizadas.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` -> 0 errors, 0 warnings, 31 checks OK; `python -m pytest tests/held-out/ -q` -> 135 passed; `python scripts/validate-skill-format.py` -> 151 passing, 0 failing.

- [x] 6. Future pace
  OUTCOME: 3 cenários avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Não.
  EVIDENCE: (1) Revisor recebe padrões explícitos (pushed standards/spec) -> ajuda? Sim, pois reduz adivinhação. (2) Implementer sabe quando consultar skill (pulled tdd/verification/impeccable) -> ajuda? Sim, pois reduz feedback repetido. (3) Paralelização de subagentes fica mais documentada via referência Sand Castle -> ajuda? Sim, pois alinha mentalmente com planner/implementers/merger.

- [x] 7. Ecological check
  OUTCOME: Sem Docker no bundle; Sand Castle apenas referência.
  CHECK: Revisar skills atualizadas.
  EXPECT: Garantias presentes.
  EVIDENCE: Nenhuma alteração em `docker`, `package.json`, instalação de dependência, ou arquivos de configuração de container. Sand Castle citado apenas como modelo mental em `code-review/SKILL.md`, com link para `mattpocock/sandcastle` e nota explícita de que o bundle não adota a lib nem Docker.

- [x] 8. Simular
  OUTCOME: Simular review com padrões push/pull.
  CHECK: Teste mental/subagente.
  EXPECT: Padrões categorizados corretamente.
  EVIDENCE: Simulação mental: (a) padrão "spec" é pushed no prompt do Spec sub-agent; (b) padrão "tdd" é pulled pelo implementer e spot-checked pelo Standards sub-agent; (c) feedback "use `verification-before-completion`" em `receiving-code-review` é classificado como pulled. Todos categorizados de acordo com as novas seções.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: Baseline: 0 erros, 135 passed. Pós-mudança: 0 erros, 135 passed, skill format 100. Skills agora declaram push/pull e referenciam Sand Castle sem Docker. Classificação: **MELHOROU**.

- [ ] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: pending
