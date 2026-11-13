# CONTINUOUS-IMPROVEMENT LEDGER: bundle self-improvement

## FASE 0 — DEEP RESEARCH

### 0.1 — Devin CLI / bundle context
- Bundle is a Devin CLI skill/rule/hook distribution.
- Discovery happens via `README.md`, `docs/SKILL-TIERS.md`, `ask-matt`, and `using-skills`.

### 0.2 — Bundle structure check
- `README.md` lists skills but does not mention `ai-coding-dictionary` or `review-cadence`.
- `docs/SKILL-TIERS.md` has a section for `continuous-improvement` under "Artefatos de pesquisa" but no entry for `ai-coding-dictionary` or `review-cadence`.
- `docs/AI-CODING-DICTIONARY.md` exists and is in `manifest.json` docs list.

### 0.3 — Primary source
- User request: "use continuous improvement e outras ferramentas para melhorar a si mesmo, ajuste o que for necessário".
- Bundle needs its own docs to surface new skills for discovery.

### 0.4 — Best practices
- New skills and docs must be discoverable via README and SKILL-TIERS.
- Token counts in SKILL-TIERS help agents decide whether to load a skill.

### 0.5 — Baseline state
- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.

### 0.6 — Synthesis
- Candidata: update `README.md` and `docs/SKILL-TIERS.md` to surface `ai-coding-dictionary`, `review-cadence`, and `docs/AI-CODING-DICTIONARY.md`.

---

## LOOP DE MELHORIA

### Passo 1 — OBSERVAR
- Comando: `grep -n "ai-coding-dictionary\|review-cadence\|AI-CODING-DICTIONARY" README.md docs/SKILL-TIERS.md`
- Saída: 0 matches.
- Falha: new skills and dictionary are not discoverable from primary index docs.

### Passo 2 — CRITICAR
- Regra violada: Rule 4 (ubiquitous language), Rule 12 (precision), Rule 3 (update wrong skills).
- Comportamento atual: bundle adds skills but leaves index docs stale.
- Intenção positiva: keep README/SKILL-TIERS concise.
- Por que falha: users and agents can't find new skills without searching the skill directory.

### Passo 3 — GERAR ALTERNATIVAS
| Alt | Descrição | Risco | Prob. melhoria real |
|-----|-----------|-------|---------------------|
| 1 | Add `ai-coding-dictionary` and `review-cadence` to `docs/SKILL-TIERS.md` | Baixo | Alta |
| 2 | Add a "Docs" section to `README.md` linking `AI-CODING-DICTIONARY.md` | Baixo | Alta |
| 3 | Update `ask-matt` to mention new skills in main flow | Médio | Média |

### Passo 4 — REVISAR
- Aplicar alternativas 1 e 2.

### Passo 5 — VALIDAR
- `python audit.py` → 0 errors, 0 warnings (60 skills, README/TOOLS-MAP counts OK)
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed

### Passo 6 — FUTURE PACE
- Cenário 1: user opens README → finds AI coding dictionary link. Sim.
- Cenário 2: agent reads SKILL-TIERS → finds `review-cadence` and `ai-coding-dictionary`. Sim.
- Cenário 3: new contributor sees skill inventory. Sim.

### Passo 7 — ECOLOGICAL CHECK
- No conflict with rules.
- Adds a few lines to README and SKILL-TIERS.
- No code changes.

### Passo 8 — SIMULAR
- `python audit.py` → 0 errors
- `python -m pytest` → 139 passed
- Impacto: README e SKILL-TIERS mais completos.

### Passo 9 — CLASSIFICAR
- **MELHOROU**

### Passo 10 — REPETIR OU CONVERGIR
- Convergir.
