# CONTINUOUS-IMPROVEMENT LEDGER: review cadence (shift left/right)

## FASE 0 — DEEP RESEARCH

### 0.1 — Devin CLI / skills context
- Skills are markdown files loaded by Devin CLI from `.devin/skills/<name>/` or `~/.config/devin/skills/<name>/`.
- Router skills like `ask-matt` decide which skill to use.

### 0.2 — Bundle structure check
- `skills/ask-matt/SKILL.md` maps flows from idea to ship.
- `skills/grilling/SKILL.md` is the interview primitive for big work.
- `skills/effort-calibration/SKILL.md` adapts reasoning budget to task difficulty.
- `skills/implement/SKILL.md` and `skills/executing-plans/SKILL.md` handle execution.
- `skills/code-review/SKILL.md` handles human-review-like diff review.
- No skill dedicated to deciding how much human review / upfront alignment a task needs based on its size/risk.

### 0.3 — Primary source
- Source: tactiq.io transcript of Matt Pocock video "Do you even need human review?".
- Claim: shift checkpoints left for big work (align early, review at end), shift checkpoints right for small work (single prompt, review at end only). Big work: use skills like Grill Me / Grill with Docs / Wayfinder. Small work: one prompt, small diff.

### 0.4 — Best practices
- Right-sized process reduces waste; over-planning small changes is wasteful, under-planning large changes is risky.
- Decision tree with observable predicates (diff size, blast radius, risk) is more reliable than heuristics.

### 0.5 — Past history
- No prior reverts of review-cadence or checkpoint-placement files.

### 0.6 — Baseline state
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.

### 0.7 — Synthesis
- Candidata: create `skills/review-cadence/SKILL.md` that gives a decision tree for when to shift review/planning left (big/risky) vs right (small/safe), and cross-link it from `ask-matt`.

---

## LOOP DE MELHORIA

### Passo 1 — OBSERVAR
- Comando: `grep -R "shift left\|shift right\|review cadence\|human review" skills/ docs/ AGENTS.md README.md`
- Saída: 0 matches (only in this ledger). No skill maps review/planning checkpoints to work size/risk.

### Passo 2 — CRITICAR
- Regra violada: Rule 4 (ubiquitous language), Rule 7 (telegraphic), Rule 12 (precision). The bundle has strong process skills but no guidance on when to use heavy vs light process.
- Comportamento atual: `ask-matt` routes to `grilling`, `wayfinder`, `implement`, etc. without an explicit "how much review/planning does this need?" gate.
- Intenção positiva: give users a complete idea-to-ship flow.
- Por que falha: agents may over-engineer small changes (rename, color tweak, 2-line bug) by running full grilling/planning, wasting time; or under-plan large risky changes.

### Passo 3 — GERAR ALTERNATIVAS
| Alt | Descrição | Risco | Prob. melhoria real |
|-----|-----------|-------|---------------------|
| 1 | Create `skills/review-cadence/SKILL.md` with decision tree | Baixo | Alta |
| 2 | Add a section to `ask-matt` | Médio | Média |
| 3 | Add a hook that estimates diff size/risk before routing | Alto | Baixa |

### Passo 4 — REVISAR
- Aplicar alternativa 1 + 2: criar skill `review-cadence` e cross-link em `ask-matt`.

### Passo 5 — VALIDAR
- `python audit.py` → 0 errors, 0 warnings (60 skills)
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed

### Passo 6 — FUTURE PACE
- Cenário 1: user asks "just change a button color" → skill says one prompt, review at end. Sim.
- Cenário 2: user wants a new feature with many files → skill says align early with `grilling`. Sim.
- Cenário 3: user has a 2-line bug fix → skill says single prompt, review diff. Sim.

### Passo 7 — ECOLOGICAL CHECK
- No conflict with rules.
- Adds one skill; `ask-matt` references it.
- Adds small context only when skill is invoked.

### Passo 8 — SIMULAR
- `python audit.py` → 0 errors, 0 warnings
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed
- Impacto: agent can route small changes more efficiently.

### Passo 9 — CLASSIFICAR
- Classificação: **MELHOROU**

### Passo 10 — REPETIR OU CONVERGIR
- Convergir: melhoria única, validada.

---

## EVIDENCE FINAL

- `skills/review-cadence/SKILL.md` criado.
- `skills/ask-matt/SKILL.md` cross-linkado.
- `manifest.json` atualizado (60 skills).
- `README.md` e `docs/TOOLS-MAP.md` atualizados.
- `python audit.py` → 0 errors, 0 warnings (60 skills).
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.
- `git status --short`:
  ```
   M README.md
   M docs/TOOLS-MAP.md
   M manifest.json
   M skills/ask-matt/SKILL.md
  ?? ledgers/review-cadence.md
  ?? skills/review-cadence/
  ```
