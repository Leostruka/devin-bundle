---
name: continuous-improvement
description: Use when starting a self-improvement session. Enforces FASE 0 deep research and the 10-step improvement loop so no step is skipped, no phantom failure is invented, and every change is validated with held-out tests.
version: 1.0.0
model: swe-1-7
subagent: implementer
---

# Directiva de Melhoria Contínua

> Prompt-meta: injetar no início de cada sessão de autoaperfeiçoamento.
> Fontes: Constitutional AI (Anthropic 2022), RISE (arXiv:2407.18219),
> DORA (COLING 2025), Six-Step Reframing (Bandler/Grinder, Satir),
> Rules 15-17 (reproducibilidade, held-out, verify-with-tools),
> Deep Research workflow (Devin CLI docs + AI lab best practices).

---

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

### 0.1 — Pesquisar Devin CLI
- `web_search` + `webfetch` em docs.devin.ai, github.com/cognition-ai
- Confirmar: hooks, skills, subagents, config.json, lifecycle events
- Output: lista de capacidades confirmadas com URLs

### 0.2 — Confirmar pela estrutura real
- `exec`, `read`, `grep`, `glob` no bundle local
- Verificar que o que a doc diz corresponde ao que está instalado
- Output: tabela doc vs disco (match/mismatch)

### 0.3 — Pesquisar fontes confiáveis (verificar, não assumir)
- `web_search` por: arXiv papers, docs oficiais (z.ai, cognition.com, anthropic.com)
- **Garantir que são confiáveis**: verificar domínio, autores, data de publicação
- Rejeitar: blogs sem fonte primária, Medium posts sem citação, LLM-generated content
- Output: lista de fontes com URL, autor, data, e citação verificada

### 0.4 — Pesquisar melhores práticas
- Tópicos: prompt engineering para GLM-5.2, context window management (200K/262K),
  subagent fan-out, cache stability, tool-use nativo, lost-in-the-middle mitigation
- Fontes prioritárias: arXiv, docs.z.ai, cognition.com/blog, docs.devin.ai
- Output: lista de práticas com evidência (paper/doc que suporta cada uma)

### 0.5 — Não repetir erros anteriores (histórico do git)
- `git log --oneline -30` + `git log --diff-filter=D` para ver o que foi deletado/revertido
- Ler commits de fix/revert para entender quebras passadas
- Output: lista de erros passados com commit hash e lição

### 0.6 — Revisar estado atual
- `python audit.py` — capturar erros/warnings atuais
- `python -m pytest tests/held-out/ -q` — baseline de testes
- `read` nos arquivos-chave (AGENTS.md, MODEL-GUIDE.md, config.json)
- Output: snapshot do estado (erros, testes passando, config atual)

### 0.7 — Sintetizar
- Cruzar 0.1-0.6: o que a doc diz × o que o disco tem × o que as práticas recomendam × o que o histórico ensina
- Output: lista priorizada de melhorias candidatas com evidência

---

## LOOP DE MELHORIA (10 passos, executar em ordem)

Baseado em Constitutional AI (generate→critique→revise) + RISE (recursive
introspection) + Six-Step Reframing (NLP) + Deep Research (FASE 0).

### Passo 1 — OBSERVAR (Verify, não deduzir)
Identificar uma falha **concreta e reproduzível** usando ferramentas.
- Comando/tool-call que reproduz a falha: `___` (obrigatório)
- Saída observada: `___`
- Se não conseguir reproduzir → **parar**. Não é falha, é dedução (A4).

### Passo 2 — CRITICAR (Constitutional AI critique)
Avaliar a falha contra os princípios do `AGENTS.md`.
- Qual regra foi violada? `___`
- Pergunta-chave NLP (reframing): **"Qual é a intenção positiva por trás
  do comportamento atual?"** Separar comportamento de intenção.
  - Comportamento atual: `___`
  - Intenção positiva: `___`
  - Por que o comportamento falha apesar da intenção: `___`

### Passo 3 — GERAR ALTERNATIVAS (Reframe + Promptbreeder)
Gerar **no mínimo 3** comportamentos alternativos que:
- Preservam a intenção positiva (A1)
- Corrigem a falha reproduzível
- Não introduzem nova violação de regra

| Alt | Descrição | Risco | Prob. de melhoria real |
|-----|-----------|-------|------------------------|
| 1   |           |       |                        |
| 2   |           |       |                        |
| 3   |           |       |                        |

### Passo 4 — REVISAR (Revise)
Aplicar a alternativa com maior probabilidade de melhoria real.
- Arquivo(s) alterado(s): `___`
- Diff resumido: `___`

### Passo 5 — VALIDAR (Held-out, anti-trapaça A2)
- Teste escolhido pelo agente: `___` → resultado: `___`
- Teste held-out (se `tests/held-out/` existir): `___` → resultado: `___`
- Se held-out falhar → **descartar mudança**, voltar ao Passo 3
- Se não existir held-out → marcar melhoria como "não validada", não "completa"

### Passo 6 — FUTURE PACE (NLP)
Projetar a melhoria em 3 cenários futuros hipotéticos:
- Cenário 1: `___` → a melhoria ajuda? `___`
- Cenário 2: `___` → a melhoria ajuda? `___`
- Cenário 3: `___` → a melhoria ajuda? `___`
- Se <2 cenários beneficiados → a melhoria é específica demais, reconsiderar

### Passo 7 — ECOLOGICAL CHECK (NLP)
A melhoria causa efeitos colaterais?
- Em outras regras? `___`
- Em outros hooks/skills? `___`
- No contexto window budget (Rule 18)? `___`
- Se efeito colateral negativo → voltar ao Passo 3

### Passo 8 — SIMULAR (Self-evaluation)
Simular o carregamento das melhorias e avaliar o próprio desempenho.
- `install.ps1 -Force` (ou equivalente) para carregar as mudanças
- `python audit.py` — confirmar 0 erros após carregar
- `python -m pytest tests/held-out/ -q` — confirmar 0 regressões
- Auto-avaliação: **como isso modifica minha lógica e meu modo operante na prática?**
  - Que comportamento muda quando esta regra/skill/hook é carregada?
  - Que cenário real executaria de forma diferente agora?
  - Há conflito com comportamentos já otimizados para GLM-5.2/SWE-1.7?
- Output: descrição do impacto comportamental esperado

### Passo 9 — CLASSIFICAR (Melhorou ou piorou?)
Classificar o resultado com descrição para definir direção.
- Comparar métrica real (Passo 5) vs baseline (FASE 0.6)
- Classificação obrigatória (uma opção):

| Classe | Critério | Ação |
|--------|----------|-------|
| **MELHOROU** | Métrica real melhorou + held-out passou + sem efeitos colaterais | Repetir loop (Passo 1) com próxima melhoria candidata |
| **PIOROU** | Métrica real regrediu OU held-out falhou OU efeito colateral negativo | **Reverter mudança** (`git checkout` ou `edit` manual), voltar ao Passo 3 |
| **NEUTRO** | Métrica inalterada + held-out passou + sem efeito colateral | Marcar "estagnação" (arXiv:2607.25152), tentar próxima candidata |
| **INCONCLUSIVO** | Não foi possível medir impacto real | Não declarar melhoria. Reformular métrica ou descartar |

- Output: classe + justificativa com números

### Passo 10 — REPETIR OU CONVERGIR
- Se classificado **MELHOROU** ou **NEUTRO**: voltar ao Passo 1 com a próxima
  melhoria candidata da síntese (FASE 0.7)
- Se classificado **PIOROU**: revertido no Passo 9, voltar ao Passo 3 com
  alternativa diferente
- **Critério de parada (convergência)**: quando todas as melhorias candidatas
  da FASE 0.7 foram aplicadas e classificadas, e nenhuma nova falha reproduzível
  é encontrada no estado atual → conjuntura atingida para GLM-5.2 High (200K) +
  SWE-1.7 (262K)
- **NÃO dar push ou commit** — mudanças ficam locais para revisão do usuário

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

- [ ] FASE 0 completa (deep research com fontes verificadas)
- [ ] Falha reproduzida com comando exato (A1)
- [ ] Intenção positiva separada do comportamento (NLP)
- [ ] 3+ alternativas geradas
- [ ] Held-out validado OU marcado "não validada" (A2)
- [ ] Future pace: ≥2/3 cenários beneficiados
- [ ] Ecological check: sem efeitos colaterais negativos
- [ ] Simulação executada (Passo 8): install + audit + held-out + auto-avaliação
- [ ] Classificação atribuída (Passo 9): MELHOROU/PIOROU/NEUTRO/INCONCLUSIVO
- [ ] Métrica real declarada (A5), não proxy
- [ ] Nenhuma regra anti-trapaça violada
- [ ] Nenhum push ou commit feito

**Se qualquer item falhar → a melhoria NÃO está completa. Começar novamente do zero com fontes diferentes mas com o mesmo objetivo e garantindo sua veracidade.**

---

## FORMATO DE SAÍDA

```
MELHORIA: <título>
FASE0_RESEARCH: <fontes verificadas — URLs + citações>
FALHA_REPRODUZIDA: <comando> → <saída>
REGRA_VIOLADA: <Rule #>
INTENÇÃO_POSITIVA: <texto>
ALTERNATIVA_APLICADA: <#> de <N>
HELD_OUT: <passou|falhou|inexistente>
SIMULAÇÃO: <install OK? audit 0 erros? held-out 0 regressões? impacto comportamental>
MÉTRICA_REAL: <número/observação vs baseline>
CLASSIFICAÇÃO: <MELHOROU|PIOROU|NEUTRO|INCONCLUSIVO>
ESTADO: <validada|não_validada|estagnada|revertida>
ARQUIVOS_ALTERADOS: <lista>
PUSH_COMMIT: <não feito>
```
