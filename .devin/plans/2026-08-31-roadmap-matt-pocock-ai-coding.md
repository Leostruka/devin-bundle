# Plano de planos: Matt Pocock — AI Coding For Real Engineers

**Objetivo:** transformar os conceitos densos do workshop de Matt Pocock (-QFHIoCo-Ko) em planos de melhoria acionáveis para o devin-bundle, cada um com seu próprio ledger, reprodução de falha e validação held-out.

## Ordem sugerida

Os planos abaixo podem ser executados em paralelo quando independentes, mas respeitam as relações de bloqueio indicadas.

1. [Context workflow: smart/dumb zone e clear vs compact](2026-08-31-matt-pocock-context-workflow.md) — nenhum bloqueio
2. [Grill Me: alinhamento via interrogatório](2026-08-31-matt-pocock-grill-me.md) — nenhum bloqueio
3. [PRD to issues: destination document e fatias verticais](2026-08-31-matt-pocock-prd-to-issues.md) — nenhum bloqueio
4. [AFK loop: Ralph e agentes fora do teclado](2026-08-31-matt-pocock-afk-loop.md) — bloqueado por PRD to issues (precisa de issues locais)
5. [TDD e feedback loops para agentes](2026-08-31-matt-pocock-tdd-feedback.md) — nenhum bloqueio
6. [Deep vs shallow modules](2026-08-31-matt-pocock-deep-modules.md) — nenhum bloqueio
7. [Push/pull de padrões e code review](2026-08-31-matt-pocock-push-pull-review.md) — nenhum bloqueio

## Contrato comum de execução

Para cada plano:

- [ ] Invocar `unlazy` antes de qualquer ciclo.
- [ ] Criar `.devin/ledgers/<plano>.md` com gates 0.1–0.7 e 1–10.
- [ ] Cada gate deve conter `OUTCOME`, `CHECK`, `EXPECT` e `EVIDENCE`.
- [ ] Executar a FASE 0 completa de `continuous-improvement` antes de editar.
- [ ] Reproduzir uma falha atual com comando ou tool-call exato; sem reprodução, classificar como INCONCLUSIVO.
- [ ] Separar afirmações do vídeo, fatos verificados externamente e inferências do agente.
- [ ] Verificar afirmações factuais relevantes em fontes primárias.
- [ ] Gerar pelo menos três alternativas antes de implementar.
- [ ] Implementar somente uma alternativa selecionada.
- [ ] Validar com `python audit.py` e `python -m pytest tests/held-out -q`.
- [ ] Não modificar `tests/held-out/`.
- [ ] Executar future pace em três cenários e ecological check.
- [ ] Medir resultado real contra o baseline; percepção subjetiva não conta.
- [ ] Classificar como MELHOROU, PIOROU, NEUTRO ou INCONCLUSIVO.
- [ ] Criar PR independente e aguardar checks verdes antes do merge.

## Limites

- O transcript não prova que a interpretação do apresentador coincide integralmente com as fontes citadas.
- Conteúdo Tactiq é entrada fornecida pelo usuário; a proveniência foi registrada em `.devin/notes/youtube/-QFHIoCo-Ko/transcript-provenance.md`.
- Nenhuma conclusão depende de trecho ausente.
- Nenhuma mudança no bundle ocorre durante a fase de análise/planejamento.
- Não instalar dependências, plugins ou MCPs para executar estes planos.

## Critério global de conclusão

- [ ] O `plano de planos` foi revisado e aprovado.
- [ ] Cada plano individual possui objetivo, hipóteses, reprodução, três alternativas, entregáveis e classificação esperada.
- [ ] As fontes primárias dos conceitos chave foram identificadas (ex: John Ousterhout, Pragmatic Programmer, etc.).
- [ ] Cada implementação futura terá PR próprio com CI verde.
- [ ] `python audit.py` retorna zero erros e zero warnings antes de qualquer PR.

## Fontes primárias iniciais

- Matt Pocock, "Full Walkthrough: Workflow for AI Coding", AI Engineer: https://www.youtube.com/watch?v=-QFHIoCo-Ko
- YouTube oEmbed: https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=-QFHIoCo-Ko&format=json
- Rich Sutton, "The Bitter Lesson" (referido indiretamente)
- John Ousterhout, *A Philosophy of Software Design* (deep/shallow modules)
- Andrew Hunt & David Thomas, *The Pragmatic Programmer* (tracer bullets)
- Kent Beck, *Test-Driven Development by Example* (red-green-refactor)
