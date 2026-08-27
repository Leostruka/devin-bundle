# GATES: cross-skill integration

## FASE 0 — Deep Research

- [ ] G0.1: Mapear onde cada skill é mencionada em outras skills.
  CHECK: grep -R "context7\|/context7\|deep-mode\|/deep-mode\|/research\|research" skills/ | wc -l
  EXPECT: >0
  EVIDENCE: pending

- [ ] G0.2: Listar skills que consomem documentação/externo e não referenciam context7.
  EVIDENCE: pending

- [ ] G0.3: Listar skills que requisitam busca profunda e não referenciam research/deep-mode.
  EVIDENCE: pending

- [ ] G0.4: Listar outras oportunidades de cross-skill.
  EVIDENCE: pending

## Melhorias

- [ ] G1.1: Atualizar skills para usar context7 onde documentação externa é relevante.
  EVIDENCE: pending

- [ ] G1.2: Atualizar skills para usar research/deep-mode onde busca profunda é requisitada.
  EVIDENCE: pending

- [ ] G1.3: Atualizar outras cross-references de skills.
  EVIDENCE: pending

## Validação

- [ ] G2.1: audit.py 0 erros.
  CHECK: python audit.py
  EXPECT: Errors: 0
  EVIDENCE: pending

- [ ] G2.2: pytest 139 passed.
  CHECK: python -m pytest tests/held-out/ tests/validation/ -q
  EXPECT: passed
  EVIDENCE: pending

- [ ] G2.3: install global com novas skills.
  CHECK: .\install.ps1 -Force | Select-String -Pattern "context7|research|deep-mode"
  EVIDENCE: pending
