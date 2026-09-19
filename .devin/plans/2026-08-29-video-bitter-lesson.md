# Plano: aplicar “The Bitter Lesson” ao devin-bundle

**Bloqueado por:** nenhum.

**Objetivo:** testar se o bundle contém otimizações específicas que pioram com a evolução dos modelos e substituir somente falhas reproduzíveis por mecanismos gerais, escaláveis e verificáveis.

## Evidência de entrada

- URL fornecida: `https://www.youtube.com/watch/HtsFKx9mAu8`.
- URL canônica verificada: https://www.youtube.com/watch?v=HtsFKx9mAu8
- Título verificado por YouTube oEmbed: `The bitter lesson`.
- Autor verificado por YouTube oEmbed: `Matt Pocock`.
- Transcript: fornecido pelo usuário via Tactiq; não confirmado como caption oficial.
- Fonte primária citada pelo vídeo: Rich Sutton, “The Bitter Lesson”, 13 de março de 2019.

## Hipóteses a testar

1. Regras ou skills específicas de modelo podem ficar obsoletas mais rápido que princípios gerais.
2. Gates determinísticos e testes held-out podem escalar melhor que instruções extensas específicas de modelo.
3. A tese de Sutton não implica abandonar toda otimização; o texto reconhece ganhos de curto prazo e critica dependência de conhecimento humano que não escala.
4. A paráfrase do vídeo em `00:00:57.920–00:01:07.280` é mais absoluta que o artigo e deve ser tratada como interpretação do apresentador.

## FASE 0 — obrigatória

- [ ] Invocar `unlazy` e criar `.devin/ledgers/bitter-lesson.md`.
- [ ] Criar gates 0.1–0.7 e 1–10 com `OUTCOME`, `CHECK`, `EXPECT` e `EVIDENCE`.

### 0.1 — Pesquisar Devin CLI

- [ ] Ler documentação oficial de rules, skills, hooks, subagents, modelos e lifecycle.
- [ ] Registrar capacidades confirmadas, URLs e data de consulta.
- [ ] Verificar quais mecanismos são gerais e quais dependem de um modelo específico.

### 0.2 — Confirmar pela estrutura real

- [ ] Inventariar `AGENTS.md`, `config.json`, `agents/`, `skills/`, `scripts/`, hooks e validadores.
- [ ] Executar `devin --version`, `devin models list` e `devin doctor`.
- [ ] Produzir tabela documentação × disco com match/mismatch.

### 0.3 — Pesquisar fontes confiáveis

- [ ] Ler integralmente o artigo de Sutton na fonte primária.
- [ ] Verificar exemplos factuais usados na análise em fontes primárias.
- [ ] Registrar autor, data, URL, citação e escopo de cada fonte.
- [ ] Não usar o transcript como prova de fatos externos.

### 0.4 — Pesquisar melhores práticas

- [ ] Comparar instruções específicas de modelo, princípios invariantes, gates e avaliações held-out.
- [ ] Pesquisar context-window management, cache stability, tool-use e test-time compute.
- [ ] Associar cada prática a uma fonte verificável.

### 0.5 — Não repetir erros anteriores

- [ ] Executar `git log --oneline -30` e `git log --diff-filter=D --oneline`.
- [ ] Ler commits de revert, prune e correções de política de modelos.
- [ ] Registrar hash, falha anterior e lição aplicável.

### 0.6 — Baseline

- [ ] Executar `python audit.py`.
- [ ] Executar `python -m pytest tests/held-out -q`.
- [ ] Medir tamanho de `AGENTS.md`, quantidade de regras específicas de modelo e referências a modelos obsoletas.
- [ ] Preservar o transcript bruto em `.devin/notes/youtube/HtsFKx9mAu8/raw-transcript.md` com hash SHA-256.

### 0.7 — Síntese

- [ ] Produzir lista priorizada de candidatas com evidência e métrica real.
- [ ] Separar: afirmação explícita do vídeo, fonte primária, inferência e decisão proposta.
- [ ] Selecionar somente candidatas com falha reproduzível.

## LOOP DE MELHORIA — executar uma candidata por vez

### Passo 1 — OBSERVAR

- [ ] Executar comando que reproduza a falha atual.
- [ ] Registrar comando, saída, arquivo e linha.
- [ ] Se não houver falha reproduzível, parar e classificar INCONCLUSIVO.

### Passo 2 — CRITICAR

- [ ] Identificar a regra do `AGENTS.md` afetada.
- [ ] Registrar comportamento atual, intenção positiva e motivo da falha.
- [ ] Comparar a falha à tese restrita do artigo, sem usar a paráfrase absoluta do vídeo.

### Passo 3 — GERAR ALTERNATIVAS

- [ ] Comparar no mínimo três opções:
  1. manter a otimização específica e adicionar validade/versionamento;
  2. substituir por princípio geral mais gate determinístico;
  3. remover a otimização e confiar em modelo + avaliação externa.
- [ ] Pontuar risco, custo de contexto, compatibilidade e probabilidade de ganho real.

### Passo 4 — REVISAR

- [ ] Escrever teste vermelho no seam comportamental mais alto.
- [ ] Aplicar somente a alternativa escolhida.
- [ ] Não ampliar o escopo para regras sem falha reproduzida.

### Passo 5 — VALIDAR

- [ ] Executar teste específico e registrar antes/depois.
- [ ] Executar `python audit.py`.
- [ ] Executar `python -m pytest tests/held-out -q` sem editar held-out.
- [ ] Reverter se held-out regredir.

### Passo 6 — FUTURE PACE

- [ ] Simular modelo primário atual.
- [ ] Simular troca futura de modelo/família.
- [ ] Simular tarefa simples em que a regra específica não deveria ativar.
- [ ] Exigir benefício em pelo menos dois cenários.

### Passo 7 — ECOLOGICAL CHECK

- [ ] Verificar conflitos com rules, skills, hooks e política de custos.
- [ ] Medir impacto no contexto sempre carregado.
- [ ] Confirmar que gates não bloqueiam comportamentos válidos.

### Passo 8 — SIMULAR

- [ ] No Windows, salvar `APPDATA`/`USERPROFILE`, redirecioná-los para `.devin/scratch/bitter-lesson-install/`, executar `install.ps1 -Force` e restaurar as variáveis no `finally`.
- [ ] No Unix, definir `DEVIN_HOME=/tmp/devin-bundle-bitter-lesson` e executar `install.sh --force`.
- [ ] Confirmar por caminho absoluto que nenhum arquivo foi gravado no home real.
- [ ] Executar audit e held-out no estado instalado.
- [ ] Descrever qual decisão operacional muda em tarefa real.

### Passo 9 — CLASSIFICAR

- [ ] Comparar métrica real com baseline.
- [ ] Classificar MELHOROU, PIOROU, NEUTRO ou INCONCLUSIVO.
- [ ] Reverter PIOROU; não chamar proxy de melhoria.

### Passo 10 — REPETIR OU CONVERGIR

- [ ] Repetir somente para a próxima candidata priorizada.
- [ ] Parar quando nenhuma nova falha reproduzível existir.
- [ ] Executar revisão independente antes do commit.

## Saídas

- [ ] Nota temporal com citações e distinção entre fala, fonte e inferência.
- [ ] Ledger completo em `.devin/ledgers/bitter-lesson.md`.
- [ ] Mudança mínima validada, ou relatório INCONCLUSIVO sem mudança.
- [ ] PR próprio com classificação, métricas e plano de testes.

## Aceitação

- [ ] Cada uso do vídeo possui timestamp.
- [ ] Cada fato externo relevante possui fonte primária.
- [ ] A análise não transforma “general methods scale” em “nenhuma otimização importa”.
- [ ] Toda mudança corrige falha reproduzível.
- [ ] O transcript bruto permanece separado e inalterado após captura.
- [ ] Audit e held-out passam.

## Transcript fornecido — preservar literalmente na execução

```text
00:00:00.080 If you're building anything that
00:00:01.360 involves AI, then you have to know about
00:00:03.840 the bitter lesson. The bitter lesson is
00:00:05.680 an article by Rich Sutton from March
00:00:07.919 13th, 2019. And the best quote from it
00:00:10.480 is also the first sentence. The biggest
00:00:12.320 lesson that can be read from 70 years of
00:00:14.480 AI research is that general methods that
00:00:16.880 leverage computation are ultimately the
00:00:18.960 most effective and by a large margin. In
00:00:22.000 other words, as the cost per unit of
00:00:24.080 computation falls, in other words, as
00:00:26.480 computation gets cheaper, as computer
00:00:28.480 power gets cheaper, you can throw more
00:00:30.480 computing power at the problem and it
00:00:32.479 will generally outperform any
00:00:34.239 optimizations that you've done on top.
00:00:36.000 Most AI research has been conducted as
00:00:37.760 if the computation available to the
00:00:39.120 agent were constant. In other words,
00:00:40.800 we're behaving as if the ground we're
00:00:42.960 standing on is solid, but it's not. As
00:00:45.200 computers get more powerful for cheaper,
00:00:47.200 it doesn't matter if you found this
00:00:48.559 crazy new technique for improving your
00:00:50.239 AI app. Eventually, the computers will
00:00:52.399 get so powerful, the AI will get so
00:00:54.239 powerful that will outperform your
00:00:56.000 solution and your optimization. Well,
00:00:57.920 that was probably just a waste of time
00:00:59.440 that you could have just spent waiting
00:01:00.960 for the AI to get better. That is the
00:01:02.879 bitter lesson that nothing really
00:01:04.640 matters in AI research apart from just
00:01:07.280 improving the power of these machines.
00:01:09.040 Now, this is controversial, I would say.
00:01:11.280 If you see someone on the internet
00:01:12.400 talking about the bitter lesson, this is
00:01:14.080 the lesson they're talking about. So,
00:01:15.520 what do you think? Is it worth it to
00:01:16.799 optimize our applications or are we just
00:01:18.479 going to get beaten by computation?
```
