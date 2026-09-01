# Ledger: deep-modules (John Ousterhout deep vs shallow)

## Gates FASE 0

- [x] 0.1 Ler improve-codebase-architecture SKILL.md
  OUTCOME: Entender skill atual.
  CHECK: read skills/improve-codebase-architecture/SKILL.md
  EXPECT: Resumo.
  EVIDENCE: Lido `skills/improve-codebase-architecture/SKILL.md` (75 linhas). Skill já menciona "deepening", "shallow" e "deletion test", mas não cita Ousterhout nem fornece heurísticas explícitas de profundidade.

- [x] 0.2 Confirmar agents/scripts de métricas
  OUTCOME: Saber se há scripts de arquitetura.
  CHECK: ls scripts/ ; grep -n "module\|dependency" skills/improve-codebase-architecture/SKILL.md
  EXPECT: Lista de ferramentas.
  EVIDENCE: `find_file_by_name scripts/*` lista 17 scripts (validação, hooks, governança), nenhum específico de profundidade de módulos. `grep 'module|dependency'` em `skills/improve-codebase-architecture/SKILL.md` retorna 13 ocorrências (incluindo 'dependencies', 15); skill usa o conceito mas não o formaliza em heurísticas.

- [x] 0.3 Buscar citação primária Ousterhout
  OUTCOME: Citar A Philosophy of Software Design.
  CHECK: web_search "John Ousterhout Philosophy of Software Design deep modules"
  EXPECT: Fonte relevante listada.
  EVIDENCE: Ferramenta web_search indisponível; citação primária verificada nos documentos do repo: `docs/plans/2026-08-31-matt-pocock-deep-modules.md` (linha 11: "Fonte: John Ousterhout, *A Philosophy of Software Design*"), `docs/plans/2026-08-31-roadmap-matt-pocock-ai-coding.md` (linha 58), e `.devin/notes/youtube/-QFHIoCo-Ko/video-analysis-WIP.md` (linha 76: "Deep vs shallow modules (John Ousterhout)"). `skills/codebase-design/SKILL.md` já cita Ousterhout (linha 109).

- [x] 0.4 Baseline audit + held-out
  OUTCOME: Estado atual passa.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` → 0 erros, 0 warnings, 31 checks OK. `python -m pytest tests/held-out/ -q` → 135 passed in 4.66s.

- [x] 0.5 Síntese de melhorias candidatas
  OUTCOME: Decidir atualização da skill.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: Decisão registrada.
  EVIDENCE: Decisão: adicionar seção "Deep vs shallow modules" em `improve-codebase-architecture/SKILL.md` com citação a Ousterhout, heurísticas textuais para identificar módulos rasos e recomendações de refactoring que reduzam dependências rasas.

## Gates FASE 1–10

- [x] 1. Observar SKILL.md atual
  OUTCOME: Confirmar ausência de Ousterhout e de heurísticas formais.
  CHECK: grep -n "deep\|shallow\|Ousterhout" skills/improve-codebase-architecture/SKILL.md
  EXPECT: 0 matches para Ousterhout; deep/shallow presentes informalmente.
  EVIDENCE: `grep -i 'deep|shallow|Ousterhout'` retorna 10 matches em `skills/improve-codebase-architecture/SKILL.md`: 0 menções a Ousterhout. Há 7 ocorrências de "deep"/"deepening" e 3 de "shallow" (linhas 3, 8, 19, 24, 29, 34, 48, 63, 67, 70), mas nenhuma citação de Ousterhout e nenhuma lista de heurísticas.

- [x] 2. Criticar (Rule 3)
  OUTCOME: Justificar por que skill genérica perde padrão específico.
  CHECK: Documentar no ledger.
  EXPECT: Crítica escrita.
  EVIDENCE: A skill `improve-codebase-architecture` fala em "deepening" e "shallow" mas não traduz o conceito de Ousterhout em critérios operacionais. Sem uma seção de heurísticas, o agente subagente explora organicamente e pode não identificar módulos rasos (ex: pass-throughs, fan-out de dependências) — falha exatamente no padrão que Pocock destaca: IA gera módulos rasos se não supervisionada. Rule 3 do AGENTS.md exige atualizar skills erradas/missing; a skill está incompleta para o propósito.

- [x] 3. Gerar 3 alternativas
  OUTCOME: 3 alternativas listadas.
  CHECK: Revisar FASE 3 do plano.
  EXPECT: 3 alternativas.
  EVIDENCE: (1) Adicionar seção "Deep vs shallow modules" com heurísticas e recomendações de refactoring em `skills/improve-codebase-architecture/SKILL.md`. (2) Criar novo script `scripts/audit-module-depth.py` para listar módulos rasos via grep/regex. (3) Criar nova skill separada `skills/deep-modules/SKILL.md`.

- [x] 4. Revisar e selecionar alternativa
  OUTCOME: Adicionar seção deep vs shallow na skill existente.
  CHECK: Decisão no ledger.
  EXPECT: Escopo definido.
  EVIDENCE: Escolhida alternativa 1 — menor blast radius. Não adiciona script nem nova skill; aprofunda `improve-codebase-architecture` com heurísticas textuais e recomendações de refactoring, alinhado a `codebase-design` e sem dependência de parser AST.

- [x] 5. Validar com código
  OUTCOME: SKILL.md e manifest.json atualizados.
  CHECK: python audit.py ; python -m pytest tests/held-out/ -q
  EXPECT: 0 erros; 135 passed.
  EVIDENCE: `python audit.py` → 0 erros, 0 warnings, 31 checks OK. `python -m pytest tests/held-out/ -q` → 135 passed.

- [x] 6. Future pace
  OUTCOME: 3 cenários avaliados.
  CHECK: Revisar FASE 6 do plano.
  EXPECT: Sim/Não.
  EVIDENCE: (1) Agentes notam módulos rasos? Sim — heurísticas e citação de Ousterhout dão âncoras textuais para o subagente. (2) Refactorings sugeridos são mais acionáveis? Sim — cinco movimentos de refactoring ligados a categorias de dependência. (3) Tests se tornam mais fáceis? Sim — recomendação de testar pela interface do módulo aprofundado e deletar testes de wrappers rasos.

- [x] 7. Ecological check
  OUTCOME: Sem parser AST adicionado; sugestões textuais.
  CHECK: diff --stat skills/improve-codebase-architecture/SKILL.md
  EXPECT: Mudanças textuais.
  EVIDENCE: `git diff --stat -- skills/improve-codebase-architecture/SKILL.md` → 1 file changed, 31 inserções(+), 2 exclusões(-). Apenas texto; nenhum script novo, nenhuma dependência de parser AST.

- [x] 8. Simular
  OUTCOME: Verificar que o skill menciona profundidade e fornece recomendações acionáveis.
  CHECK: grep por Ousterhout/deep/shallow e por heurísticas/refactor/dependencies em SKILL.md.
  EXPECT: Skill menciona deep/shallow modules, Ousterhout e heurísticas.
  EVIDENCE: `grep -i 'Ousterhout|deep|shallow'` → 30 matches. `grep -i 'heuristics|refactor|dependency|dependencies'` → 13 matches. Nova seção "Deep vs shallow modules" e oito pontos de heurísticas/refactoring presentes.

- [x] 9. Classificar
  OUTCOME: Classificação final.
  CHECK: Comparar baseline.
  EXPECT: MELHOROU / NEUTRO / PIOROU / INCONCLUSIVO.
  EVIDENCE: Baseline: skill mencionava deep/shallow informalmente, sem Ousterhout, sem heurísticas, sem recomendações explícitas de refactoring. Após a mudança: citação primária adicionada, cinco heurísticas de módulos rasos, cinco movimentos de refactoring, integração com `codebase-design` e `DEEPENING.md`. `python audit.py` e `pytest tests/held-out/` continuam 0 erros / 135 passed. Classificação: **MELHOROU**.

- [ ] 10. Commit e PR
  OUTCOME: Commit no branch.
  CHECK: git log --oneline -3
  EXPECT: Commit sem AI signature.
  EVIDENCE: pending
