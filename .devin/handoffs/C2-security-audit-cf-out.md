# C2 — Vendor cloudflare/security-audit as security-audit-cf

## Status: DONE_WITH_CONCERNS

## Files added (all under `skills/security-audit-cf/` in worktree `.worktrees/sec-audit-cf`)

Vendored from `github.com/cloudflare/security-audit-skill` (MIT), `skills/security-audit/` directory:

- SKILL.md (frontmatter renamed to `security-audit-cf`, `description:` contains "Use when", vendoring note added near top)
- AI-AND-LLM.md, ATTACK-CLASSES.md, CLIENT-SIDE.md, CLOUD-AND-DEPLOYMENT.md
- DATA-ISOLATION-AND-LIFECYCLE.md, DESKTOP-MOBILE-AND-LOCAL-IPC.md, HUNTING.md
- MEMORY-SAFETY-AND-BINARY.md, PROTOCOLS-RPC-AND-MESSAGING.md, RECONNAISSANCE.md
- RESOURCE-EXHAUSTION-AND-AVAILABILITY.md, SUPPLY-CHAIN-AND-RELEASE.md
- VALIDATION-AND-REPORTING.md, WEB-PROTOCOL-AND-AUTH.md
- report-schema.json
- validate-coverage-ledger.cjs, validate-coverage-ledger.test.cjs
- validate-findings.cjs, validate-findings.test.cjs
- LICENSE.upstream (upstream MIT license text)

## Verification

- `node --check` on all 4 `.cjs` files: OK (syntax valid)
- `python -m pytest -q tests/validation/test_skill_format_passes.py`: 2 passed
- `python audit.py`: `security-audit-cf` skill itself passes its format check (name match, description, "Use when") — it no longer appears in ERRORS.

### audit.py residual errors (6) — boundary-blocked, not fixable under contract

audit.py enforces disk/manifest/README/TOOLS-MAP consistency. The remaining errors all require editing `manifest.json`, `README.md`, `TOOLS-MAP.md`, which step 5 forbids:

```
- Manifest mismatch
- manifest skill_count mismatch
- README count wrong: 156 skills
- README skills badge wrong (expected skills-156)
- TOOLS-MAP.md skills count stale: expected 156 skills
- README.md diagram skills count stale: expected 156 skills
```

Follow-up needed (outside this contract): register `security-audit-cf` in manifest.json and refresh README/TOOLS-MAP counts to 156.

## Commit

- Worktree: `.worktrees/sec-audit-cf`, branch `skill/security-audit-cf`
- `1c8622c feat(skills): vendor cloudflare security-audit as security-audit-cf (MIT)`
- 21 files changed, 5299 insertions
- Not pushed; main checkout untouched.
