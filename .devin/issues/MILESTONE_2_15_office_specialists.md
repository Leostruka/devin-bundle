# MILESTONE_2_15 - office specialists wave (agent coverage gaps)

status: resolved
priority: P2
source: `.devin/research/2026-11-07-office-gap-analysis.md`

## Intent

Close the persona-coverage gaps found by the office gap analysis:
skills that existed without dispatchable agent profiles. Adds 4
profiles (agents 17 -> 21): `data-analyst`, `sre`, `ux-researcher`,
`performance-engineer` - all free `swe-2-*` models per policy.

## Scope

- `agents/{data-analyst,sre,ux-researcher,performance-engineer}.md`
- `scripts/validate-tool-args.py` VALID_PROFILES +4
- `manifest.json` agents[] + agent_count 17->21
- README + TOOLS-MAP agent counts
- CHANGELOG entry

## Acceptance

- [ ] `python audit.py` green (agent disk vs manifest parity)
- [ ] `pytest tests/validation/test_profile_parity.py` green
- [ ] `python -m pytest` green
- [ ] CI green on PR

## Answer

Merged via #392 (squash a46c883). Evidence: `python audit.py` 0 errors, 21 agents disk-vs-manifest consistent; `pytest tests/validation/test_profile_parity.py` + `test_consolidated_hooks.py` green; `test_egm_upgrade_contract.py` 25 passed (caught+fixed stale export_hash after em-dash sweep); full pytest 2193 passed. CI all-green pre-merge.
