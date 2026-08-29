# Plano de planos: vídeos sobre melhoria de agentes

**Objetivo:** executar dois ciclos independentes e sequenciais de melhoria, cada um em PR próprio, usando integralmente `continuous-improvement` e evidência temporal fornecida pelo usuário.

## Ordem obrigatória

1. [Vídeo 1 — The bitter lesson](2026-08-29-video-bitter-lesson.md)
2. [Vídeo 2 — evolução do Grill Me](2026-08-29-video-grilling-frontier.md)

O plano 2 começa somente após o plano 1 ser classificado, revisado, mesclado e validado em `main`.

## Contrato comum de execução

Para cada plano:

- [ ] Invocar `unlazy` antes de qualquer ciclo.
- [ ] No plano 1, criar `.devin/ledgers/bitter-lesson.md`; no plano 2, criar `.devin/ledgers/grilling-frontier.md`.
- [ ] Cada gate 0.1–0.7 e 1–10 deve conter `OUTCOME`, `CHECK`, `EXPECT` e `EVIDENCE`; não avançar com evidência pendente.
- [ ] Executar a FASE 0 completa de `continuous-improvement` antes de editar.
- [ ] Preservar o transcript fornecido como artefato bruto, sem correções silenciosas.
- [ ] Validar ID, título e autor contra YouTube oEmbed.
- [ ] Registrar o transcript como evidência fornecida pelo usuário via Tactiq, não como caption oficial do YouTube.
- [ ] Reproduzir uma falha atual com comando ou tool-call exato; sem reprodução, classificar como INCONCLUSIVO.
- [ ] Separar afirmações do vídeo, fatos verificados externamente e inferências do agente.
- [ ] Verificar afirmações factuais relevantes em fontes primárias.
- [ ] Gerar pelo menos três alternativas antes de implementar.
- [ ] Implementar somente uma alternativa selecionada.
- [ ] Escrever teste vermelho antes da alteração comportamental.
- [ ] Não modificar `tests/held-out/`.
- [ ] Executar teste específico, `python audit.py` e `python -m pytest tests/held-out -q`.
- [ ] Simular Windows com `APPDATA` e `USERPROFILE` redirecionados dentro de `.devin/scratch/`; simular Unix com `DEVIN_HOME` sob `/tmp`; restaurar variáveis e confirmar que o home real não mudou.
- [ ] Executar future pace em três cenários e ecological check.
- [ ] Medir resultado real contra o baseline; percepção subjetiva não conta como melhoria.
- [ ] Classificar como MELHOROU, PIOROU, NEUTRO ou INCONCLUSIVO.
- [ ] Reverter ciclos PIOROU.
- [ ] Criar PR independente e aguardar checks verdes antes do merge.

## Limites

- O transcript não prova que a interpretação do apresentador coincide integralmente com a fonte citada.
- Conteúdo Tactiq é entrada fornecida pelo usuário; preservar proveniência e timestamps.
- Nenhuma conclusão depende de trecho ausente.
- Nenhuma mudança no bundle ocorre durante a fase de análise.
- Não instalar dependências, plugins ou MCPs para executar estes planos.

## Critério global de conclusão

- [ ] Os dois planos foram executados na ordem definida.
- [ ] Cada ciclo possui ledger, reprodução, três alternativas e classificação.
- [ ] Cada afirmação usada possui timestamp ou fonte primária.
- [ ] Os transcripts brutos permanecem byte-identificáveis e separados da análise.
- [ ] Cada implementação possui PR próprio com CI verde.
- [ ] `python audit.py` retorna zero erros e zero warnings.
- [ ] A suíte held-out final retorna zero falhas.

## Fontes primárias iniciais

- Rich Sutton, “The Bitter Lesson”, 13 de março de 2019: http://www.incompleteideas.net/IncIdeas/BitterLesson.html
- YouTube oEmbed — vídeo 1: https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=HtsFKx9mAu8&format=json
- YouTube oEmbed — vídeo 2: https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=U832hShMVnc&format=json
- Devin CLI stable changelog: https://docs.devin.ai/cli/changelog/stable
- Devin CLI skills: https://docs.devin.ai/cli/extensibility/skills/overview
- Diretiva local: `skills/continuous-improvement/SKILL.md`
