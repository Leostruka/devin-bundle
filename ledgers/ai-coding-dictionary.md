# CONTINUOUS-IMPROVEMENT LEDGER: AI coding dictionary

## FASE 0 — DEEP RESEARCH

### 0.1 — Devin CLI / skills context
- Skills are markdown files in `.devin/skills/<name>/SKILL.md` loaded by Devin CLI.
- `docs/` is for bundle documentation.

### 0.2 — Bundle structure check
- `skills/teach/GLOSSARY-FORMAT.md` exists but is for teaching workspaces, not a general AI coding glossary.
- No `docs/AI-CODING-DICTIONARY.md` or central AI coding glossary exists.

### 0.3 — Primary source
- Source: tactiq.io transcript of Matt Pocock video "A dictionary of AI Coding".
- Claim: terms like "harness engineering", "context engineering", "prompt engineering" are confusing; a plain markdown dictionary helps users and agents learn AI coding terms.

### 0.4 — Best practices
- Centralized, plain-text glossaries reduce term confusion and improve shared vocabulary.
- Agent-facing docs should live in `.devin/` or `docs/` per bundle conventions.

### 0.5 — Past history
- No prior dictionary/glossary files in `git log --oneline --all -- docs/`.

### 0.6 — Baseline state
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.

### 0.7 — Synthesis
- Candidata: create `docs/AI-CODING-DICTIONARY.md` with core AI coding terms and cross-link it from `teach` and `using-skills` skills.

---

## LOOP DE MELHORIA

### Passo 1 — OBSERVAR
- Comando: `ls docs/AI-CODING-DICTIONARY.md`
- Saída: `File not found`
- Comando: `grep -R "harness engineering\|context engineering\|prompt engineering" skills/ docs/ AGENTS.md README.md`
- Saída: no central definitions for these terms.

### Passo 2 — CRITICAR
- Regra violada: Rule 12 (maximum precision), Rule 7 (telegraphic), Rule 4 (use ubiquitous language).
- Comportamento atual: bundle uses AI coding jargon without a canonical reference.
- Intenção positiva: communicate efficiently using domain terms.
- Por que falha: users/agents may interpret terms differently; jargon like "harness engineering" can be confusing without a shared definition.

### Passo 3 — GERAR ALTERNATIVAS
| Alt | Descrição | Risco | Prob. melhoria real |
|-----|-----------|-------|---------------------|
| 1 | Create `docs/AI-CODING-DICTIONARY.md` and reference from `teach` | Médio | Alta |
| 2 | Add terms to `AGENTS.md` glossary section | Médio — AGENTS.md is large | Média |
| 3 | Create a dedicated `ai-coding-dictionary` skill | Baixo | Média |

### Passo 4 — REVISAR
- Aplicar alternativa 1 + 3: create `docs/AI-CODING-DICTIONARY.md` and a lightweight `ai-coding-dictionary` skill that points to it.

### Passo 5 — VALIDAR
- `python audit.py` → 0 errors, 0 warnings
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed

### Passo 6 — FUTURE PACE
- Cenário 1: user asks "what is context engineering?" → skill gives canonical answer. Sim.
- Cenário 2: agent in `teach` needs to explain an AI coding term → references dictionary. Sim.
- Cenário 3: onboarding a new user to AI coding → dictionary accelerates shared vocabulary. Sim.

### Passo 7 — ECOLOGICAL CHECK
- No conflict with rules.
- Adds one doc + one skill.
- Slight context increase; skill is reference-only, not loaded by default.

### Passo 8 — SIMULAR
- `python audit.py` → 0 erros
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed
- Impacto: agent can direct users to `ai-coding-dictionary` for AI coding term definitions.

### Passo 9 — CLASSIFICAR
- Classificação: **MELHOROU**

### Passo 10 — REPETIR OU CONVERGIR
- Convergir: melhoria única, validada.

---

## ACTIONS DONE

- [x] Create `docs/AI-CODING-DICTIONARY.md`
- [x] Create `skills/ai-coding-dictionary/SKILL.md`
- [x] Add to `manifest.json`
- [x] Update README.md + TOOLS-MAP.md skill count
- [ ] Cross-link from `teach` and `using-skills` if appropriate
- [x] Run audit + pytest after edits

## EVIDENCE FINAL

- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.
- `git status --short`:
  ```
   M README.md
   M docs/TOOLS-MAP.md
   M manifest.json
  ?? docs/AI-CODING-DICTIONARY.md
  ?? ledgers/ai-coding-dictionary.md
  ?? skills/ai-coding-dictionary/
  ```
