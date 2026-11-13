# General alignment and overlap check

## Checks performed

1. **Audit**: `python audit.py` → 0 errors, 0 warnings.
2. **Tests**: `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.
3. **Skill format**: `python scripts/validate-skill-format.py` → 119/119 passing (bundle + local + global).
4. **Manifest sync**: 60 skills on disk = 60 in manifest.
5. **README/TOOLS-MAP counts**: 60 skills, 20 rules, 17 scripts.

## Overlap analysis

| New skill | Similar existing skills | Verdict |
|-----------|-------------------------|---------|
| `review-cadence` | `effort-calibration` (reasoning budget), `code-review` (review depth), `unlazy` (ledgers for trivial edits) | No overlap: `review-cadence` decides **where** to place checkpoints (planning + review), the others decide **how much** reasoning/review/ledger effort. |
| `ai-coding-dictionary` | `domain-modeling` (project glossary), `teach` (lessons), `tool-and-skill-discovery` (find skills) | No overlap: `ai-coding-dictionary` is a canonical reference for AI-coding jargon; `domain-modeling` is project-specific glossary; `teach` is lesson delivery; `tool-and-skill-discovery` is skill lookup. |

## Cross-skill wiring review

- `ask-matt` → `review-cadence` ✅
- `using-skills` → `review-cadence` ✅
- `grilling` → `review-cadence`, `ai-coding-dictionary` ✅
- `implement` → `review-cadence` ✅
- `code-review` → `review-cadence` ✅
- `domain-modeling` → `ai-coding-dictionary` ✅
- `teach` → `ai-coding-dictionary`, `review-cadence` ✅

## Observations

- Global skill directory (`%APPDATA%/devin/skills`) does not yet contain `ai-coding-dictionary` or `review-cadence`; expected because `install.ps1` has not been run.
- No new arXiv references introduced, so `MODEL-GUIDE.md` audit remains green.
- No temp files or untracked artifacts beyond expected new files and ledgers.

## Conclusion

All checks pass. New skills are aligned with existing vocabulary, not redundant, and properly wired.
