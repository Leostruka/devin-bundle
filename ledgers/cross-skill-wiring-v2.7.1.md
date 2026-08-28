# Cross-skill wiring: ai-coding-dictionary + review-cadence

## Scope

Check where the two new skills (`ai-coding-dictionary`, `review-cadence`) should be referenced by existing skills, then wire them in.

## Check

- `grep -R "ai-coding-dictionary\|review-cadence" skills/` → only `ask-matt`, new skills, and `PHASE-BOUNDARIES.md` referenced `ai-coding-dictionary` (via smart-zone link) and `review-cadence` (one match in ask-matt).

## Wiring applied

| From skill | New cross-reference | Why |
|------------|---------------------|-----|
| `ask-matt` | `review-cadence` in Vocabulary | already done |
| `using-skills` | `review-cadence` for small requests | route tiny changes correctly |
| `grilling` | `review-cadence` (small request?), `ai-coding-dictionary` (jargon) | avoid over-grilling, align terms |
| `implement` | `review-cadence` (skip planning?) | decide before coding |
| `code-review` | `review-cadence` (depth of review) | match review effort to task size |
| `domain-modeling` | `ai-coding-dictionary` (AI-coding terms) | keep project glossary canonical |
| `teach` | `ai-coding-dictionary`, `review-cadence` | vocabulary + planning depth |

## Validation

- `python audit.py` → 0 errors, 0 warnings.
- `python -m pytest tests/held-out/ tests/validation/ -q` → 139 passed.
