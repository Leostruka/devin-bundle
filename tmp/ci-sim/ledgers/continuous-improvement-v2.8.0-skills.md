# GATES: continuous-improvement — v2.8.0 skill coverage

## FASE 0 — Deep Research

- [ ] G0.1: Tokens e overhead das 11 skills medidos
  CHECK: `Get-Item` bytes ÷ 4 por skill + total
  EXPECT: tabela de ~tok/skill
  EVIDENCE: pending

- [ ] G0.2: Cross-skill overlap mapeado
  CHECK: `grep` por palavras-chave em skills existentes vs novas
  EXPECT: lista de conflitos
  EVIDENCE: pending

- [ ] G0.3: Integridade do bundle verificada
  CHECK: `python audit.py` + `python -m pytest tests/held-out/ -q`
  EXPECT: 0 erros, 135 passed
  EVIDENCE: pending

- [ ] G0.4: Síntese de ajustes
  CHECK: `.devin/plans/v2.8.0-skill-audit.md` escrito
  EXPECT: plano com mudanças
  EVIDENCE: pending

## LOOP de Melhoria

- [ ] G1.1: Falha reproduzível
  CHECK: output de G0.2 mostrando overlap ou de G0.1 mostrando overhead
  EXPECT: evidência concreta
  EVIDENCE: pending

- [ ] G2.1: Crítica e intenção positiva
  CHECK: texto da regra violada + reframe
  EXPECT: análise
  EVIDENCE: pending

- [ ] G3.1: 3+ alternativas
  CHECK: tabela
  EXPECT: preenchida
  EVIDENCE: pending

- [ ] G4.1: Ajuste aplicado
  CHECK: `git diff --stat`
  EXPECT: arquivos alterados
  EVIDENCE: pending

- [ ] G5.1: Validação
  CHECK: `python audit.py` + `pytest -q`
  EXPECT: 0 erros, 135 passed
  EVIDENCE: pending

- [ ] G9.1: Classificação
  CHECK: métrica real vs baseline
  EXPECT: MELHOROU/NEUTRO/PIOROU
  EVIDENCE: pending
