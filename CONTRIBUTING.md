# Contributing

## How to Contribute

### Reporting Issues

Use [GitHub Issues](../../issues). Choose the appropriate template:
- **Bug report:** something in the bundle doesn't work as documented
- **Feature request:** a new skill, hook, rule, or improvement
- **Skill proposal:** a recurring workflow that should become a skill

### Proposing Changes

1. **Fork** the repo
2. **Clone** your fork
3. Create a branch: `git checkout -b feat/my-improvement`
4. **Make changes** following the standards below
5. **Test locally:** `.\export.ps1 -DryRun` (Windows) or `./export.sh --dry-run` (Linux)
6. **Commit** with a clear message (see format below)
7. **Push** to your fork
8. Open a **Pull Request** using the PR template

### Commit Message Format

```
<type>: <short description>

<optional body explaining why>
```

Types: `feat`, `fix`, `docs`, `refactor`, `prune`, `export`, `chore`

Examples:
- `feat: add context-folding skill (RLM-style)`
- `fix: check-push-green now detects .NET projects`
- `docs: update README with 9/9 adaptation status`

### Skill Quality Standards

Every skill must pass this checklist (from `AGENTS.md` Rule 3):

1. **Frontmatter** — `name:` (lowercase, hyphens, max 64, matches directory) and `description:` (starts with "Use when", describes the trigger)
2. **Discovery-friendly** — description uses keywords an agent would search for
3. **Devin-native tools** — uses Devin CLI tool names (`exec`, `read`, `edit`, `write`, `grep`, `run_subagent`, etc.)
4. **Devin-native paths** — references `.devin/`, `~/.config/devin/`, `%APPDATA%\devin\`
5. **No AI signatures** — no "Generated with Devin" or similar
6. **No platform leakage** — no references to non-Devin AI tools or runtimes
7. **Evidence-backed** — if the skill claims numbers or facts, cite the primary source

### Rule Standards

Rules in `AGENTS.md` must be:
- **Negative constraints** ("don't X") — evidence: arXiv:2604.11088 shows only negative constraints are individually beneficial
- **Always-on** — applies to every project and session
- **Evidence-backed** — cite the source for the constraint

### Hook Standards

Hooks in `hooks.v1.json` must:
- Have a corresponding Python script in `scripts/`
- Use `exit 0` for allow, `exit 1` for block
- Handle malformed input gracefully (exit 0 on parse error)
- Have a timeout set
- Be idempotent

### Export Before PR

Before opening a PR, run the exporter to sync the bundle:
```powershell
.\export.ps1 -DryRun    # validate
.\export.ps1            # apply
```

This ensures the bundle is in sync with the live config.

### CI Checks

All PRs must pass CI (`.github/workflows/ci.yml`):
- JSON syntax validation (all `.json` files)
- Python syntax validation (all `.py` files)
- Skill frontmatter validation (all `SKILL.md` files)
