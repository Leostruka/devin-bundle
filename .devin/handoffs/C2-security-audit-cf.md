# Contract C2: vendor Cloudflare `security-audit` skill

- Role: `implementer`
- Lane: worktree `D:\Programing\ai_workspace\devin-bundle\.worktrees\sec-audit-cf`, branch `skill/security-audit-cf`
  - setup: `git worktree add .worktrees/sec-audit-cf -b skill/security-audit-cf`
- Objective: vendor `github.com/cloudflare/security-audit-skill` (MIT) as
  `skills/security-audit-cf/` — distinct name, our `security-audit` stays untouched.
- Output:
  - `skills/security-audit-cf/` containing SKILL.md + its ledger/validator
    files (incl. the two `.cjs` validators). Preserve content faithfully;
    add a short preamble noting MIT source + name change rationale.
  - Frontmatter `name: security-audit-cf`, description with "Use when".
  - Do NOT edit manifest.json, README.md, TOOLS-MAP.md, or `skills/security-audit/`.
- Boundaries: no Node deps, no edits outside the new skill dir. Fetch from
  the upstream repo's default branch (git clone --depth 1 or raw URLs).
- Termination: max 20 turns.
- VFs (in worktree): `python audit.py` == 0 errors; `.cjs` files parse
  (`node --check` if node exists, else note skip);
  `pytest -q tests/validation/test_skill_format_passes.py` green.
- Report: `.devin/handoffs/C2-security-audit-cf-out.md`.
