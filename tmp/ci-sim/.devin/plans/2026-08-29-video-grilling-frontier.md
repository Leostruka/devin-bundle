# Plano: avaliar frontier rounds no skill grilling

**Bloqueado por:** conclusão e merge do plano `video-bitter-lesson`.

**Objetivo:** medir se perguntas independentes em lote reduzem turnos sem degradar clareza, carga cognitiva ou cobertura, e decidir entre default adaptativo, modos separados ou manutenção do comportamento atual.

## Evidência de entrada

- URL fornecida: `https://www.youtube.com/watch/U832hShMVnc`.
- URL canônica verificada: https://www.youtube.com/watch?v=U832hShMVnc
- Título verificado por YouTube oEmbed: `I'm thinking about changing my most popular skill`.
- Autor verificado por YouTube oEmbed: `Matt Pocock`.
- Transcript: fornecido pelo usuário via Tactiq; não confirmado como caption oficial.
- Estado local verificado: `skills/grilling/SKILL.md` já usa frontier rounds para perguntas independentes e uma pergunta por vez somente quando existe dependência.

## Afirmações do vídeo a testar

- `00:00:08.760–00:00:15.840`: o comportamento anterior fazia uma pergunta por vez.
- `00:00:15.840–00:00:30.280`: o autor relata maior velocidade ao responder perguntas independentes em lote por ditado.
- `00:00:31.880–00:00:53.040`: frontier rounds reduzem alternância de turnos e revelam a próxima camada de decisões.
- `00:00:55.680–00:01:12.640`: uma pergunta por vez pode parecer mais natural e mensurável; lotes podem ser intensos.
- `00:01:13.960–00:01:17.800`: decisão aberta entre mudar o skill atual e criar outro skill.

## FASE 0 — obrigatória

- [ ] Invocar `unlazy` e criar `.devin/ledgers/grilling-frontier.md`.
- [ ] Criar gates 0.1–0.7 e 1–10 com `OUTCOME`, `CHECK`, `EXPECT` e `EVIDENCE`.

### 0.1 — Pesquisar Devin CLI

- [ ] Verificar documentação oficial sobre skills, argumentos, prompts, ask/plan mode e `ask_user_question`.
- [ ] Registrar capacidades, limites de perguntas/opções e URLs.
- [ ] Confirmar como skills locais são descobertos e instalados.

### 0.2 — Confirmar pela estrutura real

- [ ] Ler integralmente `skills/grilling/SKILL.md`, skills chamadores e testes relacionados.
- [ ] Buscar todas as referências a “one question”, “batch”, “frontier” e “grill me”.
- [ ] Produzir tabela transcript × comportamento atual × testes.

### 0.3 — Pesquisar fontes confiáveis

- [ ] Usar o vídeo apenas para relato do autor e decisão de design.
- [ ] Verificar afirmações sobre Devin CLI em documentação oficial.
- [ ] Pesquisar fontes primárias sobre carga cognitiva e questionários somente se usadas para justificar decisão.
- [ ] Rotular preferências de UX como opinião, não fato universal.

### 0.4 — Pesquisar melhores práticas

- [ ] Comparar pergunta sequencial, lote fixo e frontier rounds adaptativos.
- [ ] Medir custo por turnos, perguntas repetidas, respostas omitidas e tempo de interação.
- [ ] Avaliar acessibilidade para ditado e usuários que preferem ritmo gradual.

### 0.5 — Não repetir erros anteriores

- [ ] Executar `git log --oneline -30 -- skills/grilling`.
- [ ] Ler commits de consolidação e alterações de batching.
- [ ] Registrar comportamento removido, revertido ou corrigido e motivo.

### 0.6 — Baseline

- [ ] Executar `python audit.py`.
- [ ] Executar `python -m pytest tests/held-out -q`.
- [ ] Preservar transcript bruto em `.devin/notes/youtube/U832hShMVnc/raw-transcript.md` com SHA-256.
- [ ] Criar fixtures equivalentes para decisões independentes, dependentes e mistas.
- [ ] Medir turnos, cobertura, repetições e perguntas prematuras no comportamento atual.

### 0.7 — Síntese

- [ ] Produzir candidatas priorizadas com falha reproduzível e métrica.
- [ ] Separar fala explícita, estado atual, inferência e decisão proposta.
- [ ] Encerrar INCONCLUSIVO se o comportamento atual já satisfizer os critérios sem falha.

## LOOP DE MELHORIA — executar uma candidata por vez

### Passo 1 — OBSERVAR

- [ ] Reproduzir uma falha com fixture e comando exato.
- [ ] Registrar transcript da interação, quantidade de turnos e critério violado.
- [ ] Não tratar preferência pessoal como falha.

### Passo 2 — CRITICAR

- [ ] Identificar regra ou contrato afetado.
- [ ] Registrar comportamento atual, intenção positiva e causa da falha.
- [ ] Preservar ambas as intenções: velocidade e ritmo cognitivo controlável.

### Passo 3 — GERAR ALTERNATIVAS

- [ ] Comparar no mínimo:
  1. frontier rounds adaptativos no skill atual;
  2. modos explícitos `sequential` e `frontier` no mesmo skill;
  3. skills separados para sequencial e lote.
- [ ] Pontuar descoberta, manutenção, contexto, número de turnos e compatibilidade.

### Passo 4 — REVISAR

- [ ] Escrever testes vermelhos no seam de seleção de perguntas.
- [ ] Implementar somente a alternativa escolhida.
- [ ] Manter perguntas dependentes fora do mesmo lote.
- [ ] Evitar criar novo skill sem ganho mensurável de descoberta ou comportamento.

### Passo 5 — VALIDAR

- [ ] Reexecutar as três fixtures.
- [ ] Comparar turnos, cobertura, repetição e omissão contra baseline.
- [ ] Executar `python audit.py` e `python -m pytest tests/held-out -q`.
- [ ] Reverter se held-out falhar.

### Passo 6 — FUTURE PACE

- [ ] Usuário com ditado e respostas longas.
- [ ] Usuário iniciante que prefere uma decisão por vez.
- [ ] Design misto com dependências entre perguntas.
- [ ] Exigir benefício em pelo menos dois cenários sem regredir o terceiro.

### Passo 7 — ECOLOGICAL CHECK

- [ ] Verificar chamadores `project-setup`, `planning-pipeline` e `domain-modeling`.
- [ ] Medir aumento de tokens e complexidade de descoberta.
- [ ] Confirmar limite de 1–4 perguntas e 2–4 opções de `ask_user_question`.
- [ ] Verificar que o lote não contém perguntas cuja resposta depende de outra no mesmo lote.

### Passo 8 — SIMULAR

- [ ] No Windows, salvar `APPDATA`/`USERPROFILE`, redirecioná-los para `.devin/scratch/grilling-frontier-install/`, executar `install.ps1 -Force` e restaurar as variáveis no `finally`.
- [ ] No Unix, definir `DEVIN_HOME=/tmp/devin-bundle-grilling-frontier` e executar `install.sh --force`.
- [ ] Confirmar por caminho absoluto que nenhum arquivo foi gravado no home real.
- [ ] Executar sessões simuladas das três fixtures.
- [ ] Rodar audit e held-out.
- [ ] Descrever a mudança operacional observável.

### Passo 9 — CLASSIFICAR

- [ ] Classificar com números: turnos, cobertura, omissões e repetições.
- [ ] MELHOROU exige ganho real e ausência de regressão cognitiva.
- [ ] NEUTRO exige registrar estagnação; PIOROU exige reversão.

### Passo 10 — REPETIR OU CONVERGIR

- [ ] Repetir somente para falha seguinte da síntese.
- [ ] Após três reformulações sem ganho, registrar estagnação.
- [ ] Revisar independentemente antes do commit.

## Saídas

- [ ] Nota temporal e transcript bruto separados.
- [ ] Ledger `.devin/ledgers/grilling-frontier.md`.
- [ ] Matriz de fixtures e métricas antes/depois.
- [ ] Mudança validada ou conclusão INCONCLUSIVA/NEUTRA sem alteração desnecessária.
- [ ] PR próprio com classificação e evidências.

## Aceitação

- [ ] Perguntas independentes podem ser agrupadas dentro do limite da ferramenta.
- [ ] Perguntas dependentes permanecem sequenciais.
- [ ] A escolha entre mudar ou dividir o skill usa métricas, não preferência.
- [ ] Nenhum skill novo duplica comportamento sem benefício mensurável.
- [ ] Transcript bruto permanece inalterado.
- [ ] Audit e held-out passam.

## Transcript fornecido — preservar literalmente na execução

```text
00:00:00.000 I've been debating changing, modifying,
00:00:02.320 one of my most famous skills, one of my
00:00:04.320 most used skills, and I need your advice
00:00:07.440 on whether I should do it. The way that
00:00:08.760 this Grill Me skill works by default is
00:00:10.920 that you use it instead of plan mode,
00:00:12.600 and it asks you one question at a time.
00:00:15.840 And I've modified it locally to instead
00:00:18.520 ask me all the questions that it has at
00:00:21.400 once. I found that this lets me just
00:00:23.160 whack through a bunch of text really
00:00:25.560 fast because I use dictation, and so I
00:00:27.760 just say, &quot;Blah blah blah blah blah blah
00:00:28.840 blah answer all the questions and we're
00:00:30.280 good to go.&quot; It avoids the annoying
00:00:31.880 thing in Grill Me where it feels like
00:00:34.000 it's taking ages for you to actually get
00:00:36.360 to a shared understanding because the
00:00:37.880 agent is asking you a question, and then
00:00:39.760 you answer it, asking you a question,
00:00:41.520 answer it. So, this way it just gives
00:00:44.480 you the frontier of questions, the stuff
00:00:46.920 that it knows about, and then you blast
00:00:49.080 it out, and then it carries on. It
00:00:51.320 pushes back the frontier, gives you the
00:00:53.040 next level of design decisions.
00:00:55.680 But, I don't know. People love the fact,
00:00:57.280 and I used to love the fact that Grill
00:00:59.000 Me asked me one question at a time. That
00:01:00.840 felt really natural, felt like I was
00:01:02.680 just working things through at a
00:01:04.080 measurable pace. Whereas this does feel
00:01:06.800 intense, like you're having to do a lot
00:01:08.280 of work, but it does feel um a lot
00:01:10.880 faster. And speed is what we're all
00:01:12.640 about these days. So, what do you think?
00:01:13.960 Should I change the skill to match my
00:01:15.760 recommendation, or should I ship a new
00:01:17.800 skill, Batch Me or something?
```
