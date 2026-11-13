# GATES: continuous-improvement — infraestrutura/alinhamento

## FASE 0 — Deep Research

- [ ] G0.1: Doc Devin CLI confirmada
  CHECK: web_search docs.devin.ai skills hooks config.json + 3 URLs com citações
  EXPECT: lista de capacidades confirmadas com URLs
  EVIDENCE: pending

- [ ] G0.2: Estrutura real do bundle mapeada
  CHECK: `Get-ChildItem -Recurse -File | Group-Object Directory | Select-Object Count, Name` + `git status`
  EXPECT: tabela resumo dos componentes + status git
  EVIDENCE: pending

- [ ] G0.3: Fontes confiáveis coletadas
  CHECK: web_search arxiv/anthropic/z.ai/cognition context window GLM-5.2 SWE-1.7
  EXPECT: 3+ fontes com URL, autor, data
  EVIDENCE: pending

- [ ] G0.4: Melhores práticas priorizadas
  CHECK: síntese em `ledgers/improvement-infra-alinhamento-plan.md`
  EXPECT: plano com candidatas de melhoria e evidência
  EVIDENCE: pending

- [ ] G0.5: Histórico de erros revisado
  CHECK: `git log --oneline -30` + `git log --diff-filter=D`
  EXPECT: lista de deleções/reverts e lições
  EVIDENCE: pending

- [ ] G0.6: Baseline do estado atual
  CHECK: `python audit.py` + `git status --short`
  EXPECT: output do audit + resumo de mudanças
  EVIDENCE: pending

- [ ] G0.7: Síntese final de melhorias
  CHECK: leitura do plano escrito
  EXPECT: lista priorizada de melhorias candidatas
  EVIDENCE: pending

## LOOP de Melhoria (10 passos)

- [ ] G1.1: Falha reproduzível identificada
  CHECK: comando + output concreto
  EXPECT: reprodução documentada
  EVIDENCE: pending

- [ ] G2.1: Crítica e intenção positiva
  CHECK: texto da regra violada + reframe
  EXPECT: análise completa
  EVIDENCE: pending

- [ ] G3.1: 3+ alternativas geradas
  CHECK: tabela com alternativas, riscos e probabilidade
  EXPECT: tabela preenchida
  EVIDENCE: pending

- [ ] G4.1: Alternativa aplicada
  CHECK: `git diff --stat`
  EXPECT: arquivos alterados e diff resumido
  EVIDENCE: pending

- [ ] G5.1: Validação com held-out
  CHECK: `python audit.py` + testes existentes
  EXPECT: nenhuma regressão
  EVIDENCE: pending

- [ ] G6.1: Future pace
  CHECK: 3 cenários hipotéticos avaliados
  EXPECT: ≥2/3 beneficiados
  EVIDENCE: pending

- [ ] G7.1: Ecological check
  CHECK: verificar impacto em regras, hooks, skills, context window
  EXPECT: lista de efeitos colaterais
  EVIDENCE: pending

- [ ] G8.1: Simulação
  CHECK: `python audit.py` e verificação de carregamento
  EXPECT: 0 erros após carregar
  EVIDENCE: pending

- [ ] G9.1: Classificação
  CHECK: comparação de métrica real vs baseline
  EXPECT: classe MELHOROU/PIOROU/NEUTRO/INCONCLUSIVO
  EVIDENCE: pending

- [ ] G10.1: Repetição ou convergência
  CHECK: todas as candidatas revisadas?
  EXPECT: decisão de continuar ou parar
  EVIDENCE: pending
