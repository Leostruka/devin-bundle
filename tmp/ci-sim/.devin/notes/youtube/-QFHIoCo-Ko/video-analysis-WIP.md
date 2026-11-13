# Análise em andamento — Matt Pocock: AI Coding For Real Engineers (-QFHIoCo-Ko)

> Anotações ao consumir o contexto do vídeo. O objetivo é extrair planos acionáveis para o devin-bundle. Se o contexto for limpo, recomeçar a partir deste arquivo + do `plano de planos`.

## Metadados do vídeo

- **Video ID:** `-QFHIoCo-Ko`
- **Título (YouTube oEmbed):** `Full Walkthrough: Workflow for AI Coding — Matt Pocock`
- **Autor (YouTube oEmbed):** `AI Engineer`
- **Transcript:** fornecido via Tactiq nesta sessão
- **Duração aproximada:** ~01:36:00
- **Tese central:** software engineering fundamentals (small tasks, vertical slices, TDD, deep modules, feedback loops) funcionam tão bem com IA quanto com humanos.

## Conceitos identificados (em ordem de aparição)

### 1. Zona inteligente × zona burra (smart zone × dumb zone)
- **Timestamp:** 00:00:59.280–00:05:01.280
- **Resumo:** LLMs começam no "smart zone" (poucos tokens, atenção relaxada). À medida que o contexto cresce, a qualidade cai (dumb zone). O marcador de Pocock é ~100k tokens, não importa se a janela é 200k ou 1M.
- **Implicação:** dimensionar tarefas para caber na zona inteligente; evitar morder mais do que pode mastigar.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-context-workflow.md`

### 2. Momento / reset de contexto
- **Timestamp:** 00:05:01.280–00:11:09.680
- **Resumo:** cada sessão passa por: system prompt → exploratory → implementation → testing. Quando limpa (`/clear`), volta ao system prompt. Compacting resume, mas Pocock prefere limpar para ter estado previsível. Há crítica a compacting porque gera "sedimento".
- **Implicação:** preferir `clear` a `compact`; manter system prompt enxuto; usar budget de tokens visível.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-context-workflow.md`

### 3. Specs-to-code e misalignment
- **Timestamp:** 00:11:09.680–00:15:02.480
- **Resumo:** crítica ao "specs-to-code movement" (vibe coding com documento). O código é o battleground; é preciso manter a mão no código, não só editar specs.
- **Implicação:** skills de planning não devem substituir o contato com o código; devem alinhar intenção antes de implementar.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-prd-to-issues.md`

### 4. Grill Me — alinhamento via interrogatório
- **Timestamp:** 00:15:02.480–00:22:03.600
- **Resumo:** skill "grill me" entrevista o usuário sem parar até atingir "shared design concept". Fornece recomendação para cada pergunta. Pode gerar 20–100 perguntas. Funciona como ativo da conversa (transcript vira asset).
- **Implicação:** melhorar skill `grilling` para manter foco, suportar recomendações por pergunta e exportar asset de design concept.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-grill-me.md`

### 5. PRD como destination document
- **Timestamp:** 00:29:58.960–00:35:11.359
- **Resumo:** a conversa do grill vira um PRD (problem statement, solution, user stories, implementation decisions, testing decisions, out of scope). Pocock diz não precisar reler o PRD porque o LLM é bom em sumarização e o alinhamento já foi feito no grill.
- **Implicação:** `writing-plans` / `planning-pipeline` podem aprender a extrair PRD leve a partir do grill.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-prd-to-issues.md`

### 6. Módulos propostos e mapa de módulos
- **Timestamp:** 00:32:54.000–00:35:11.359
- **Resumo:** antes de implementar, enumerar módulos propostos e mantê-los em mente durante todo o ciclo.
- **Implicação:** planejamento deve declarar módulos/interfaces afetados antes do PRD.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-prd-to-issues.md`

### 7. Fatias verticais (vertical slices / tracer bullets)
- **Timestamp:** 00:35:11.359–00:47:01.839
- **Resumo:** IA tende a codar horizontalmente (camada por camada). Isso atrasa feedback. Deve-se exigir fatias verticais: schema + service + UI mínima em uma só fatia. Técnica do "tracer bullet" (Pragmatic Programmer).
- **Implicação:** `planning-pipeline` (tickets) deve gerar fatias verticais, não fases horizontais; cada ticket entrega algo verificável end-to-end.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-prd-to-issues.md`

### 8. Kanban / issues locais e paralelização
- **Timestamp:** 00:47:01.839–00:53:15.839
- **Resumo:** planos multi-fase são loops. Issues devem ser independentemente grabbable com relações de bloqueio, formando DAG. Evita plano sequencial (apenas um agente pode trabalhar). Pocock usa arquivos markdown locais como issues (não GitHub necessariamente).
- **Implicação:** `dispatching-parallel-agents` e `planning-pipeline` devem suportar DAG de issues e execução paralela via canban board.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-afk-loop.md`

### 9. AFK loop (Ralph) / human-in-the-loop × AFK
- **Timestamp:** 00:53:15.839–01:02:20.240
- **Resumo:** algumas tarefas são human-in-the-loop (planejamento/QA), outras AFK (implementação). Prompt "Ralph" pega issues locais, explora repo, usa TDD, executa feedback loops, escolhe próxima tarefa. Pocock demonstra `once.sh` e a versão completa `afk.sh` com Docker sandbox.
- **Implicação:** adicionar skill/prompt para loop AFK local com base em arquivos de issue e TDD.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-afk-loop.md`

### 10. TDD / red-green-refactor e feedback loops
- **Timestamp:** 01:02:20.240–01:10:35.920
- **Resumo:** TDD é essencial para agentes: escreve teste que falha (red), implementa (green), refatora. Agentes tentam trapacear nos testes, então TDD dificulta isso. Qualidade dos feedback loops define o teto do código da IA. Exemplo: `npm run test`, `npm run typecheck`.
- **Implicação:** `tdd` skill já existe; enriquecer com red-green-refactor explícito e instruções para agentes.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-tdd-feedback.md`

### 11. Deep vs shallow modules (John Ousterhout)
- **Timestamp:** 01:14:14.800–01:23:01.760
- **Resumo:** módulos rasos (muitos pequenos, muitas dependências) são difíceis para IA navegar/testar. Módulos profundos (interface pequena, funcionalidade grande) são mais fáceis de testar e delegar. IA produz código raso se não supervisionada.
- **Implicação:** `improve-codebase-architecture` já faz varredura; adicionar critério de profundidade de módulos e recomendações de refactoring.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-deep-modules.md`

### 12. Push × pull de padrões de código
- **Timestamp:** 01:27:40.239–01:29:42.080
- **Resumo:** padrões podem ser empurrados (push) para o LLM no contexto (ex: no reviewer) ou puxados (pull) via skill quando o agente pergunta (ex: no implementer). Implementer usa pull; reviewer usa push.
- **Implicação:** `code-review` e `receiving-code-review` devem declarar quando empurrar versus deixar puxar padrões.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-push-pull-review.md`

### 13. Sand Castle — paralelização de múltiplos agentes
- **Timestamp:** 01:29:42.080–01:32:20.000
- **Resumo:** Sand Castle é uma lib TypeScript para rodar múltiplos agentes em paralelo em worktrees Docker, com planner, implementers e merger. Cada agente em sandbox, depois merge.
- **Implicação:** bundle já tem `using-git-worktrees` e `dispatching-parallel-agents`; adicionar referência/integração com fluxo Sand Castle se fizer sentido.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-push-pull-review.md`

### 14. Protótipos e doc rot
- **Timestamp:** 01:23:34.639–01:27:27.359 (prototypes), 01:24:55.440–01:25:07.600 (doc rot)
- **Resumo:** protótipos são descartáveis para feedback visual/UX. Não manter PRDs antigos no repo (doc rot) porque o código muda; use issues fechadas no tracker.
- **Implicação:** skill `prototype` pode aprender a gerar rotas descartáveis; skills de planejamento devem distinguir assets vivos de ativos descartáveis.
- **Plano relacionado:** `docs/plans/2026-08-31-matt-pocock-prd-to-issues.md`

## Próximos passos (rastreio)

- [x] Criar metadados e proveniência
- [x] Criar análise WIP com conceitos e timestamps
- [x] Criar `docs/plans/2026-08-31-roadmap-matt-pocock-ai-coding.md`
- [x] Criar planos individuais (7 planos)
- [ ] Commit dos arquivos
- [ ] Abrir PR
