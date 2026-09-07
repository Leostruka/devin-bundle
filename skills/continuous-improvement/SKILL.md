---
name: continuous-improvement
description: Use when starting a self-improvement session. Enforces FASE 0 deep research and the 10-step improvement loop so no step is skipped, no phantom failure is invented, and every change is validated with held-out tests.
version: 1.1.0
triggers:
  - user
  - model
---

# Directiva de Melhoria Contínua

> Prompt-meta: injetar no início de cada sessão de autoaperfeiçoamento.
> Fontes: Constitutional AI (Anthropic 2022), RISE (arXiv:2407.18219),
> DORA (COLING 2025), Six-Step Reframing (Bandler/Grinder, Satir),
> Rules 15-17 (reproducibilidade, held-out, verify-with-tools),
> Deep Research workflow (Devin CLI docs + AI lab best practices).

---

## CONTRATO DA SESSÃO (antes da FASE 0)

Criar o ledger antes de pesquisar ou editar. Registrar nele:

- `DELEGATION`: `disabled` se o usuário não autorizou subagentes; nesse modo não
  usar `run_subagent`, `read_subagent` nem skills com `subagent`/`agent`.
- `INPUT_REGISTER`: cada pedido do usuário, arquivo citado, fonte, regra,
  candidato e recomendação recebe um ID e uma origem verificável.
- `SOURCE_REGISTER`: cada fonte recebe URL/path, autor/data quando disponíveis,
  trecho ou linhas lidas diretamente, e decisão `accepted`/`rejected`.
- `VFS`: cada mudança recebe um comando, resultado esperado e local da evidência
  antes da primeira edição.
- `SCOPE`: arquivos autorizados; alterações fora da lista exigem nova entrada e
  gate próprio.

Nenhum item pode desaparecer por compactação, handoff ou mudança de skill.
Antes de declarar a melhoria, cada ID deve estar `applied`, `deferred` ou
`rejected`, com motivo e evidência. A síntese em
`.devin/notes/extraction-3texts/continuous-improvement-review.md` define as
lacunas verificadas nesta versão.

## OBJETIVO (único, claro, mensurável)

**Melhorar continuamente o comportamento, o escopo e a eficácia deste agente,
com permissão para alterar qualquer arquivo de configuração, regra, hook,
skill, script ou prompt — sem trapacear para demonstrar melhoria.**

"Melhoria" = redução reproduzível de falhas reais, validada por testes
independentes (held-out), não por testes escolhidos pelo próprio agente.

**Critério de convergência**: atingir a conjuntura ótima de operação para
**GLM-5.2 High (200K context window)** como modelo primário e **SWE-1.7
Max/Medium (262K context window)** como subagent default — segundo fontes
verificadas (docs.devin.ai, cognition.com, z.ai, laboratórios de AI) e
experiência prática registrada no histórico do bundle.

**NÃO dar push ou commit.** Todas as mudanças ficam locais para validação.

---

## PERMISSIVIDADE (o que pode alterar)

Pode alterar **tudo** no bundle para atingir o objetivo:
- `AGENTS.md`, `config.json`, `hooks.v1.json`, `mcp_config.json`
- `scripts/*.py` (hooks, validadores, gates)
- `.devin/skills/*/SKILL.md`
- Prompts, regras, diretivas (incluindo este arquivo)

**Não pode alterar (anti-trapaça, não negociável):**
- Os princípios anti-trapaça abaixo (auto-referência proibida)
- `tests/held-out/` (se existir — o agente não pode ver/escrever estes testes)
- Segredos (Rule 19) — usar, nunca exibir
- Assinaturas de IA em deliverables (Rule 2)

---

## Ledger com `unlazy`

Este processo é um alvo natural de preguiça do agente (muitos passos,
documentação, tendência a declarar feito sem evidência). Invocar o skill
`unlazy` no início cria um ledger rastreável com gates (`outcome`, `check`,
`expect`, `evidence`). Resolver o diretório real antes de escrever: usar
`.devin/ledgers/<melhoria>.md` quando o projeto o rastreia; se esse caminho for
ignorado ou houver convenção explícita, usar o diretório de ledgers rastreado e
registrar a decisão no próprio ledger.

- Gate mínimo por passo: o que deve ser verdade, como verificar, e a evidência
  produzida.
- O ledger começa com `INPUT_REGISTER`, `SOURCE_REGISTER`, `VFS` e `SCOPE`.
- Para a FASE 0: um gate para cada subpasso (0.1 a 0.7).
- Para o LOOP: um gate para cada Passo 1 a Passo 10, quando aplicável.
- Não avançar enquanto o gate atual tiver `EVIDENCE: pending`, vazio ou sem
  comando reproduzível.
- Antes da conclusão, reexecutar todos os gates executáveis; nenhum resultado
  anterior ou relatório de worker substitui evidência fresca.

## PRINCÍPIOS ANTI-TRAPAÇA (não negociáveis)

| # | Princípio | Por quê | Fonte |
|---|-----------|---------|-------|
| A1 | **Evidência reproduzível** — toda falha citada deve incluir um comando ou tool-call exato que a reproduz | 25% das runs de autoaperfeiçoamento inventam falhas que nunca ocorreram ("phantom guardrails") | arXiv:2607.13083 |
| A2 | **Validação held-out** — melhorias medidas apenas com testes escolhidos pelo agente são suspeitas; validar com `tests/held-out/` | 47-74% dos ganhos de autoaperfeiçoamento são ilusórios | ICLR 2026 Workshop |
| A3 | **Verificar com ferramentas** — nunca deduzir estado; usar `read`, `exec`, `grep`, `glob` antes de afirmar | Deduções falham silenciosamente; tool output falha alto | Rule 17 |
| A4 | **Sem guardrails fantasmas** — não inventar falhas; se não reproduz, não é padrão | — | Rule 15 |
| A5 | **Métrica real, não proxy** — "reduziu falhas por N", "mais rápido por Xs"; não "pareceu mais fácil" | Proxies mascaram estagnação | arXiv:2607.25152 |

---

## FASE 0 — DEEP RESEARCH (antes do loop, obrigatória)

Pesquisa profunda em fontes verificadas antes de qualquer alteração.
Cada passo abaixo produz um output concreto; não avançar sem completar o anterior.

### Contrato de gate da FASE 0 e do LOOP

Cada subpasso deve aparecer no ledger neste formato antes da execução:

```text
OUTCOME: <estado observável>
CHECK: <comando/tool-call exato>
EXPECT: <saída, contagem ou exit code>
EVIDENCE: pending
```

Após executar, substituir `pending` pelo trecho decisivo da saída e registrar
exit code. Um output narrativo sem comando, fonte ou artefato não fecha o gate.

### 0.1 — Pesquisar Devin CLI
- `web_search` + `webfetch` em docs.devin.ai, github.com/cognition-ai
- Confirmar: hooks, skills, subagents, config.json, lifecycle events
- Registrar URL, título, seção lida e citação; não aceitar apenas o snippet do search.
- Se a ferramenta estiver indisponível, registrar `BLOCKED` e não chamar a fonte
  verificada sem declarar a limitação.
- Output/gate: tabela de capacidades confirmadas, URLs e evidência de leitura.

### 0.2 — Confirmar pela estrutura real
- `exec`, `read`, `grep`, `glob` no bundle local
- Verificar que o que a doc diz corresponde ao que está instalado
- Registrar linhas, contagens, versões e mismatches; não substituir disco por memória.
- Output/gate: tabela doc vs disco (`match`/`mismatch`) com comando e saída.

### 0.3 — Pesquisar fontes confiáveis (verificar, não assumir)
- `web_search` por: arXiv papers, docs oficiais (z.ai, cognition.com, anthropic.com)
- `webfetch` na fonte primária; ler diretamente o trecho usado.
- Registrar domínio, autor, data, URL, seção e citação/linhas verificadas.
- Rejeitar: blogs sem fonte primária, Medium posts sem citação, LLM-generated content.
- Se só existir fonte secundária, marcar o claim como `unverified`; não usá-lo
  como fundamento de uma alteração validada.
- Output/gate: `SOURCE_REGISTER` com decisão por claim.

### 0.4 — Pesquisar melhores práticas
- Tópicos: prompt engineering para GLM-5.2, context window management (200K/262K),
  subagent fan-out, cache stability, tool-use nativo, lost-in-the-middle mitigation
- Fontes prioritárias: arXiv, docs.z.ai, cognition.com/blog, docs.devin.ai
- Mapear cada prática para um claim, fonte primária e proposta; não acumular
  recomendações sem decidir `applied`, `deferred` ou `rejected`.
- Output/gate: matriz prática → fonte → decisão → métrica/teste.

### 0.5 — Não repetir erros anteriores (histórico do git)
- `git log --oneline -30` + `git log --diff-filter=D --oneline -30`
- Ler commits de fix/revert relevantes, incluindo diff e motivo.
- Registrar hash, arquivo, falha reproduzida e lição; separar fato de inferência.
- Output/gate: lista de erros passados com comando/commit e lição aplicável.

### 0.6 — Revisar estado atual
- `git status --short` e `git diff --stat` antes de alterar.
- `python audit.py` — capturar erros/warnings atuais.
- `python -m pytest tests/held-out/ -q` e `python -m pytest -q` — baselines.
- `read` nos arquivos-chave (AGENTS.md, docs/MODEL-GUIDE.md, config.json).
- Registrar versão, contagens, working tree e arquivos fora do escopo.
- Output/gate: snapshot reproduzível do estado, não apenas “baseline OK”.

### 0.7 — Sintetizar
- Cruzar 0.1-0.6: doc × disco × práticas × histórico × `INPUT_REGISTER`.
- Cada candidato recebe ID, falha/necessidade, fonte, arquivos, VF, risco,
  métrica e estado inicial.
- Nenhum item fornecido pelo usuário ou descoberto durante a pesquisa pode
  desaparecer da síntese.
- Output/gate: lista priorizada e matriz de cobertura com todos os IDs.

---

## LOOP DE MELHORIA (10 passos, executar em ordem)

Baseado em Constitutional AI (generate→critique→revise) + RISE (recursive
introspection) + Six-Step Reframing (NLP) + Deep Research (FASE 0).

### Contrato de transição

Antes de iniciar um passo, verificar no ledger que o passo anterior tem
`EVIDENCE` preenchida. Cada mudança deve ser classificada antes da edição:
`CHANGE_CLASS`: `doc-only`, `skill-only`, `script-behavior` ou `config`.
Mudanças de `script-behavior` e `config` exigem teste de regressão antes/depois;
mudanças documentais exigem validação estrutural, diff e rastreabilidade.

Cada passo deve registrar `OUTCOME`, `CHECK`, `EXPECT` e `EVIDENCE`. O passo 4
não pode alterar arquivo fora de `SCOPE`; o passo 9 não pode usar checkout
amplo nem apagar alterações não relacionadas.

### Passo 1 — OBSERVAR (Verify, não deduzir)
Identificar uma falha **concreta e reproduzível** usando ferramentas.
- `OUTCOME`: falha observada em estado real, com escopo e impacto.
- `CHECK`: comando/tool-call exato que reproduz a falha (obrigatório).
- `EXPECT`: saída e exit code observados, incluindo arquivo/linha quando possível.
- `EVIDENCE`: registrar a saída crua no ledger.
- Se não conseguir reproduzir → registrar `INCONCLUSIVO` e parar; não converter
  hipótese em falha (A4).

### Passo 2 — CRITICAR (Constitutional AI critique)
Avaliar a falha contra os princípios do `AGENTS.md`.
- `OUTCOME`: falha ligada a um ID do `INPUT_REGISTER` e a uma regra.
- `CHECK`: leitura direta da regra e da fonte que fundamenta o requisito.
- `EXPECT`: regra, comportamento atual, intenção positiva e contradição
  registrados com linhas/URL/path.
- `EVIDENCE`: registrar as citações lidas.
- Pergunta-chave NLP (reframing): **"Qual é a intenção positiva por trás
  do comportamento atual?"** Separar comportamento de intenção.
  - Regra violada: `___`
  - Comportamento atual: `___`
  - Intenção positiva: `___`
  - Por que o comportamento falha apesar da intenção: `___`

### Passo 3 — GERAR ALTERNATIVAS (Reframe + Promptbreeder)
Gerar **no mínimo 3** comportamentos alternativos que:
- Preservam a intenção positiva (A1)
- Corrigem a falha reproduzível
- Não introduzem nova violação de regra
- Têm arquivo-alvo, risco, métrica e VF explícitos.

`OUTCOME`: tabela completa e alternativa selecionada com justificativa.
`CHECK`: comparar cada alternativa com `SCOPE`, regras e VFs.
`EXPECT`: nenhuma alternativa depende de claim sem fonte ou teste.
`EVIDENCE`: tabela e decisão no ledger.

| Alt | Descrição | Arquivos | Risco | Métrica/VF | Prob. de melhoria real |
|-----|-----------|----------|-------|------------|------------------------|
| 1   |           |          |       |            |                        |
| 2   |           |          |       |            |                        |
| 3   |           |          |       |            |                        |

### Passo 4 — REVISAR (Revise)
Aplicar a alternativa com maior probabilidade de melhoria real.
- `OUTCOME`: somente arquivos de `SCOPE` alterados, com patch mínimo.
- `CHECK`: `git diff -- <arquivos autorizados>` e teste RED quando houver
  mudança de comportamento.
- `EXPECT`: diff liga a falha, requisito, alternativa e VF; sem assinatura,
  segredo, teste removido ou mudança não relacionada.
- `EVIDENCE`: arquivos, diff, comando e exit code no ledger.
- Não usar `git checkout` amplo, `reset --hard` ou exclusão de alterações de
  terceiros. Reverter somente o patch próprio de forma direcionada.

### Passo 5 — VALIDAR (Held-out, anti-trapaça A2)
- `OUTCOME`: comportamento alterado passa nos VFs e não regrede no conjunto
  independente.
- `CHECK`: teste específico/regressão; `python -m pytest tests/held-out/ -q`
  quando existir; `python scripts/validate-refinement-evidence.py` quando
  houver log de refinamento.
- `EXPECT`: comandos, exit codes e contagens registradas separadamente.
- `EVIDENCE`: saída crua no ledger.
- Se held-out falhar → **descartar somente o patch próprio**, voltar ao Passo 3.
- Se held-out não existir → estado obrigatório `não_validada`/`INCONCLUSIVO`,
  nunca `validada` ou `MELHOROU`.

### Passo 6 — FUTURE PACE (NLP)
Projetar a melhoria em 3 cenários futuros hipotéticos:
- `OUTCOME`: matriz de cenário, comportamento esperado, métrica e resultado.
- `CHECK`: confrontar cada cenário com o requisito e a fonte correspondente.
- `EXPECT`: pelo menos 2/3 cenários beneficiados, ou estado `NEUTRO`/
  `INCONCLUSIVO` com justificativa.
- `EVIDENCE`: matriz no ledger; não aceitar “ajuda” sem critério observável.

### Passo 7 — ECOLOGICAL CHECK (NLP)
Verificar efeitos colaterais em todos os componentes afetados:
- `CHECK`: diff, `AGENTS.md`, skills/hooks/scripts relacionados, contexto,
  instalação e segurança.
- `EXPECT`: matriz com cada área marcada `sem impacto` ou com evidência e
  correção correspondente.
- `EVIDENCE`: matriz e comandos no ledger.
- Se efeito colateral negativo → voltar ao Passo 3.

### Passo 8 — SIMULAR (Self-evaluation)
Simular o carregamento das melhorias e avaliar o próprio desempenho.
- `OUTCOME`: live configuration só muda após revisão explícita do diff e do
  escopo.
- `CHECK`: primeiro dry-run; instalar com `-Force` apenas se autorizado pelo
  contrato da sessão; depois `python audit.py`, testes e leitura do estado live.
- `EXPECT`: instalação, audit e testes com saída/exit code; nenhum segredo em
  output; nenhuma chamada a subagente quando `DELEGATION=disabled`.
- Auto-avaliação: **como isso modifica minha lógica e meu modo operante na prática?**
  - Que comportamento muda quando esta regra/skill/hook é carregada?
  - Que cenário real executaria de forma diferente agora?
  - Há conflito com comportamentos já otimizados para GLM-5.2/SWE-1.7?
- `EVIDENCE`: impacto observado, não apenas previsto, no ledger.

### Passo 9 — CLASSIFICAR (Melhorou ou piorou?)
Classificar o resultado com descrição para definir direção.
- `CHECK`: comparar métrica real do Passo 5 com baseline da FASE 0.6.
- `EXPECT`: baseline, pós-estado, delta, unidade, tamanho da amostra e
  comando-fonte registrados; claims qualitativos ficam `INCONCLUSIVOS`.
- Classificação obrigatória (uma opção):

| Classe | Critério | Ação |
|--------|----------|-------|
| **MELHOROU** | Métrica real melhorou + held-out passou + sem efeitos colaterais | Repetir loop com próxima candidata |
| **PIOROU** | Métrica regrediu OU held-out falhou OU efeito colateral negativo | Reverter apenas o patch próprio com edição direcionada; voltar ao Passo 3 |
| **NEUTRO** | Métrica inalterada + held-out passou + sem efeitos colaterais | Registrar estagnação e tentar próxima candidata |
| **INCONCLUSIVO** | Não foi possível medir impacto real, validar fonte ou executar held-out | Não declarar melhoria; manter ou descartar somente com decisão registrada |

- `EVIDENCE`: classe, números e justificativa no ledger.
- `MELHOROU` exige held-out; sem held-out o máximo é `INCONCLUSIVO`.

### Passo 10 — REPETIR OU CONVERGIR
- `CHECK`: comparar `INPUT_REGISTER`, `SOURCE_REGISTER`, candidatos da FASE 0.7
  e estados do ledger.
- Se classificado **MELHOROU** ou **NEUTRO**: voltar ao Passo 1 com a próxima
  melhoria candidata da síntese.
- Se classificado **PIOROU**: reverter somente o patch próprio no Passo 9 e
  voltar ao Passo 3 com alternativa diferente.
- Se classificado **INCONCLUSIVO**: registrar o bloqueio e não promover o item.
- **Critério de parada**: todos os inputs e candidatos têm estado final
  (`applied`, `deferred`, `rejected` ou `blocked`), cada estado tem evidência,
  e nenhuma falha reproduzível pendente permanece. Isso é convergência do
  conjunto medido, não uma afirmação de optimalidade do modelo.
- **NÃO dar push ou commit** — mudanças ficam locais para revisão do usuário.

---

## ANTI EARLY-STOP REFLECTION (DORA)

A reflexão **não para** na primeira iteração sem melhoria.

- Iteração sem melhoria → **reformular o prompt de reflexão** antes de parar.
- Reformulação: mudar o ângulo de crítica (ex: de "o que falhou" para
  "o que o agente assumiu sem verificar").
- Máximo 3 reformulações. Após 3 sem melhoria → parar e registrar estagnação.
- Estagnação registrada é dado, não falha (arXiv:2607.25152).

---

## CHECKLIST FINAL (antes de declarar melhoria)

- [ ] Contrato da sessão registrado: `DELEGATION`, `INPUT_REGISTER`, `SOURCE_REGISTER`, `VFS` e `SCOPE`.
- [ ] FASE 0 completa; cada subpasso tem comando, expect e evidência.
- [ ] Fontes primárias lidas diretamente; claims secundários marcados como não verificados.
- [ ] Falha reproduzida com comando exato (A1), ou estado `INCONCLUSIVO`.
- [ ] Intenção positiva separada do comportamento (NLP).
- [ ] 3+ alternativas geradas com risco, arquivo, métrica e VF.
- [ ] TDD/regressão aplicado conforme o tipo da mudança.
- [ ] Held-out validado, ou estado explicitamente `não_validada`/`INCONCLUSIVO` (A2).
- [ ] Future pace: matriz com critério; ≥2/3 cenários beneficiados.
- [ ] Ecological check: matriz completa sem efeitos colaterais negativos.
- [ ] Simulação segura: dry-run/revisão; install só quando autorizado; audit/testes executados.
- [ ] Classificação atribuída com baseline, pós-estado, delta e unidade.
- [ ] Todos os IDs de input, fonte e candidato têm disposição final e evidência.
- [ ] `git diff --check`, `check-ai-signature.py` e secret scan executados.
- [ ] Nenhuma regra anti-trapaça ou restrição do usuário violada.
- [ ] Nenhum push ou commit feito pela skill.

**Se qualquer item falhar → a melhoria NÃO está completa. Registrar o bloqueio
no ledger; não preencher a lacuna com suposição ou resumo.**

---

## FORMATO DE SAÍDA

```
MELHORIA: <título + ID>
LEDGER: <path rastreável>
DELEGATION: <disabled|authorized + evidence>
INPUT_COVERAGE: <IDs e estados finais>
SOURCE_REGISTER: <URLs/paths + citações verificadas>
FASE0_RESEARCH: <gates 0.1–0.7 + evidência>
VFS: <cada comando + expect + resultado>
FALHA_REPRODUZIDA: <comando> → <saída/exit code>
REGRA_VIOLADA: <Rule # ou none>
INTENÇÃO_POSITIVA: <texto>
ALTERNATIVA_APLICADA: <#> de <N>
HELD_OUT: <passou|falhou|inexistente + contagem>
SIMULAÇÃO: <dry-run/install autorizado? audit? testes? impacto observado>
MÉTRICA_REAL: <baseline → pós-estado, delta, unidade, amostra>
CLASSIFICAÇÃO: <MELHOROU|PIOROU|NEUTRO|INCONCLUSIVO>
ESTADO: <validada|não_validada|estagnada|revertida|bloqueada>
ARQUIVOS_ALTERADOS: <lista dentro de SCOPE>
PUSH_COMMIT: <não feito>
```
