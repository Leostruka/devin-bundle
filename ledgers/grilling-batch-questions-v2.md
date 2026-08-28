# CONTINUOUS-IMPROVEMENT LEDGER: batched frontier rounds in grilling

## FASE 0 — DEEP RESEARCH

### 0.1 — Devin CLI / skills context
- Skills are markdown files in `.devin/skills/<name>/SKILL.md` loaded by Devin CLI.
- `grilling` is an existing skill for brainstorming and stress-testing designs.

### 0.2 — Bundle structure check
- `skills/grilling/SKILL.md` exists and already contains "frontier rounds" concept.
- `skills/grilling/` has `visual-companion.md`, scripts for server.
- No prior reverts of `grilling/SKILL.md` in `git log --oneline -20 -- skills/grilling/SKILL.md` (hashes: e34b7c2, e74a07d, 2451629, 2aaffe0, ecfc60c, 1811137, b410b95).

### 0.3 — Primary source
- Source: tactiq.io transcript of Matt Pocock video `/grill-me` (user-provided).
- Claim: original `grill-me` asked questions one at a time; improved version asks rounds of independent questions, respecting dependencies.

### 0.4 — Best practices
- Reducing round-trips in conversational agents lowers latency and context-switch cost.
- Batching questions while preserving dependency order is standard decision-tree / frontier algorithm.

### 0.5 — Baseline state
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.

### 0.6 — Synthesis
- Candidata: strengthen `grilling` SKILL.md to explicitly batch independent questions, warn against one-at-a-time yes/no tail, and make Stateless ("grill me") mode use frontier rounds.

---

## LOOP DE MELHORIA

### Passo 1 — OBSERVAR
- Comando: `grep -n "one at a time" skills/grilling/SKILL.md`
- Saída observada:
  ```
  116:3. **Ask clarifying questions** — one at a time (brainstorm mode)
  179:  -> Ask clarifying questions (brainstorm, one at a time)
  ```
- Comando: `grep -nE "Stateless|frontier|round|grill me" skills/grilling/SKILL.md`
- Saída observada: skill has frontier rounds in Grill Mode (lines 81-94), but Stateless mode description (line 14) does not mention frontier rounds. Brainstorm mode description (line 21) says "one question at a time". No explicit anti-pattern for yes/no tail.

### Passo 2 — CRITICAR
- Regra violada: Rule 7 (telegraphic / efficient), Rule 18 (lean context).
- Comportamento atual: skill accepts "one at a time" as the default for brainstorming and does not explicitly protect against a yes/no tail.
- Intenção positiva: avoid overwhelming the user with too many questions at once.
- Por que falha: at the end of a session the agent tends to ask a series of yes/no confirmation questions one at a time, wasting turns (per video evidence).

### Passo 3 — GERAR ALTERNATIVAS
| Alt | Descrição | Risco | Prob. melhoria real |
|-----|-----------|-------|---------------------|
| 1 | Add explicit anti-pattern "Yes-tail" in Grill Mode and clarify that independent questions are batched | Baixo | Alta |
| 2 | Change Stateless mode description to mention frontier rounds explicitly | Baixo | Alta |
| 3 | Change Brainstorm "one at a time" to "one at a time only when dependent, otherwise batch" | Médio | Alta |

### Passo 4 — REVISAR
- Aplicar alternativas 1, 2 e 3 em `skills/grilling/SKILL.md`.

### Passo 5 — VALIDAR
- `python audit.py` → 0 errors, 0 warnings
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed

### Passo 6 — FUTURE PACE
- Cenário 1: user says "grill me" with no repo → batched frontier rounds make it faster. Sim.
- Cenário 2: end of grilling session with multiple yes/no confirmations → avoids one-at-a-time tail. Sim.
- Cenário 3: questions with dependencies → frontier rules preserve order. Sim.

### Passo 7 — ECOLOGICAL CHECK
- No conflict with other rules.
- Other skills do not depend on exact wording of `grilling`.
- Adds a few lines only.

### Passo 8 — SIMULAR
- `python audit.py` → 0 erros
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed
- `install.ps1 -Force` → to be run after user approval
- Impacto comportamental: agent will batch independent questions during grilling/brainstorming.

### Passo 9 — CLASSIFICAR
- Classificação: **MELHOROU**

### Passo 10 — REPETIR OU CONVERGIR
- Convergir: melhoria única, validada.

---

## PENDING ACTIONS

- [x] Apply edits to `skills/grilling/SKILL.md`
- [x] Run audit + pytest after edits
- [ ] Run `install.ps1 -Force` after user approval

## EVIDENCE FINAL

- `skills/grilling/SKILL.md` modificado.
- `git status --short`:
  ```
   M skills/grilling/SKILL.md
  ?? ledgers/grilling-batch-questions-v2.md
  ```
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.
