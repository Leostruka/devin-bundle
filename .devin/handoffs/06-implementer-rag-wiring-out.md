# Handoff - 06-implementer-rag-wiring

- **Contract**: 06-implementer-rag-wiring
- **Status**: DONE
- **Date**: (run date)

## Changes

| File | Change |
|---|---|
| `manifest.json` | Added `rag` skill entry (name/source/purpose only, cu-realtime minimal-entry precedent; purpose = SKILL.md `description` verbatim). `skill_count` 67 → 68. `docs` array resynced per DOC-005: path-qualified real files - root `AGENTS.md`, `README.md`, `CHANGELOG.md` + all 7 installed `.devin/docs/*.md` files (adds `3D-STACK-INSTALL.md`, `DEVIN-CLI-COMPATIBILITY.md`, `RULES-DIRECTORY.md`; drops unresolvable bare names). |
| `.devin/docs/SKILL-TIERS.md` | Added `rag` row to the Research section (retrieval-over-corpus is a search/research concern; honest fit). Tok = 5691 bytes / 4 ≈ 1423. |
| `README.md` | Badge `skills-67` → `skills-68`; "As 67 skills" → "As 68 skills"; repo-tree comment "66 workflows" → "68"; docs table "das 67 skills" → "das 68 skills". |
| `.devin/docs/TOOLS-MAP.md` | No edit needed - already asserted `68 skills` (line 124). |
| `audit.py` | §24 `doc_checks`: `'8 eventos'` → `'8 events'`; tool-count check now expects `'26 active + 2 mode-dependent'` (the EN text TOOLS-MAP:7 contains; 26+2=28); excluded-tools check now expects `'Excluded tools' ... 'exit_plan_mode'` (the 9-tool EN enumeration at TOOLS-MAP:45-47). Assertion logic unchanged - still literal-presence checks. Full sweep: no other pt-BR literals remain in audit.py (grep for eventos/ferramentas/excluídas/accents → only the 3 fixed lines). |

## Verification (VFs)

- VF1 `python audit.py` → **0 errors, 16 warnings** (all pre-existing: live-vs-bundle drift, `__pycache__`, one script hash mismatch for `validate-tool-args.py`). Not introduced by this contract.
- VF2 `python -c "import json;m=json.load(open('manifest.json'));print(m['skill_count'], any(s['name']=='rag' for s in m['skills']))"` → `68 True` ✓
- VF3 `grep -n "rag" .devin/docs/SKILL-TIERS.md` → `rag` table row at line 104 ✓
- VF4 manifest `rag.purpose` == SKILL.md `description` (exact compare via python) → `True` ✓
- VF5 `pytest -q` → full run: `1576 passed, 1 failed, 4 skipped in 190s`. The single failure (`test_consolidated_hooks.py::test_stop_guard_passes_clean`) was caused by this handoff file itself containing em-dashes, which `no-em-dash` correctly blocked via stop-guard. After removing them, `pytest tests/validation/test_consolidated_hooks.py` → **8 passed**. Net: suite green. (Side observation, not fixed - out of scope: `check-ai-signature.py` can crash with `AttributeError: 'NoneType'.split` when a `git diff` subprocess hits `UnicodeDecodeError` on cp1252; the block verdict still emitted correctly.)

## Boundaries honored

- No changes to `skills/rag/`, hooks, `config.json`, other `.devin/docs/` files, `version`, `rule_count`, `agent_count`.
- Frozen inputs untouched (hashes not re-verified post-edit since files were never written).
