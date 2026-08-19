# Contributing

## How to Contribute

1. **Fork** the repo, **clone** your fork
2. Branch: `git checkout -b feat/my-improvement`
3. Make changes following the standards below
4. Test locally: `.\export.ps1 -DryRun` (Windows) or `./export.sh --dry-run` (Linux)
5. Commit with a clear message (format below)
6. Push to your fork, open a **Pull Request** using the PR template

## Commit Message Format

```
<type>: <short description>

<optional body explaining why>
```

Types: `feat`, `fix`, `docs`, `refactor`, `prune`, `export`, `chore`

## Standards (read the source, not this section)

- **Skills:** see Rule 3 in [AGENTS.md](AGENTS.md) for the 8-point quality checklist.
  Validate with `python scripts/validate-skill-format.py`.
- **Rules:** negative constraints ("don't X"), always-on, evidence-backed. See [AGENTS.md](AGENTS.md).
- **Hooks:** see `hooks.v1.json` for the contract and `scripts/` for implementations.
  Each hook has a Python script, exit 0/allow, exit 1/block, timeout, idempotent.
- **CI:** see `.github/workflows/ci.yml` for what PRs must pass
  (JSON syntax, Python syntax, skill frontmatter validation).

## Export Before PR

```powershell
.\export.ps1 -DryRun    # validate
.\export.ps1            # apply
```

This ensures the bundle is in sync with the live config.

## Reporting Issues

Use [GitHub Issues](../../issues). Templates: bug report, feature request, skill proposal.
