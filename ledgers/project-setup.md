# GATES: project-setup skill

## FASE 0 — Deep Research

- [ ] G0.1: Confirmar Devin CLI paths e lifecycle events suportados.
  CHECK: python -c "import json; data=json.load(open('C:/Users/Fingertech/Desktop/scripts/devin-bundle/config.json')); print('ok', len(data.get('hooks',{})))"
  EXPECT: ok 8
  EVIDENCE: pending

- [ ] G0.2: Verificar skills e hooks globais instalados em %APPDATA%/devin.
  CHECK: python -c "import os, glob; print(len(glob.glob(os.path.expandvars('%APPDATA%/devin/skills/*/SKILL.md'))))"
  EXPECT: 57
  EVIDENCE: pending

- [ ] G0.3: Levantar práticas validadas para project setup (citar fontes).
  EVIDENCE: pending

## Design da skill

- [ ] G1.1: Escopo da skill escrito em um parágrafo: o que setup faz, o que não faz.
  EVIDENCE: pending

- [ ] G1.2: Fluxo de 10 passos (adaptado de continuous-improvement) mapeado para setup.
  EVIDENCE: pending

## Criação

- [ ] G2.1: SKILL.md criado em skills/project-setup/.
  CHECK: test -f C:/Users/Fingertech/Desktop/scripts/devin-bundle/skills/project-setup/SKILL.md
  EXPECT: 0
  EVIDENCE: pending

- [ ] G2.2: manifest.json atualizado.
  CHECK: python -c "import json; print(any(s['name']=='project-setup' for s in json.load(open('C:/Users/Fingertech/Desktop/scripts/devin-bundle/manifest.json'))['skills']))"
  EXPECT: True
  EVIDENCE: pending

## Validação

- [ ] G3.1: audit.py passa.
  CHECK: python C:/Users/Fingertech/Desktop/scripts/devin-bundle/audit.py
  EXPECT: Errors:   0
  EVIDENCE: pending

- [ ] G3.2: pytest passa.
  CHECK: python -m pytest C:/Users/Fingertech/Desktop/scripts/devin-bundle/tests/held-out/ C:/Users/Fingertech/Desktop/scripts/devin-bundle/tests/validation/ -q
  EXPECT: passed
  EVIDENCE: pending

## Instalação

- [ ] G4.1: Install global.
  CHECK: powershell -Command "& 'C:/Users/Fingertech/Desktop/scripts/devin-bundle/install.ps1' -Force" | Select-String -Pattern 'project-setup'
  EXPECT: project-setup
  EVIDENCE: pending
