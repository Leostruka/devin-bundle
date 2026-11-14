# Plan: Issue #612 - Adaptive Git/GitHub Engineering (Microsoft/GitHub standard)

Issue: https://github.com/Leostruka/devin-bundle/issues/612
Branch: `refactor/612-adaptive-git-github-engineering` (from `main` @ d9206f5)
Mode: SDD - implementer per task, task review after each, fix wave + re-review at end, controller does push/PR.

## Global Constraints

- No em/en dashes in added/modified lines of skill files and tests.
- UTF-8 pinned on all text I/O; Python 3.11 floor.
- Skill format: `name:` == dir name; `description:` starts "Use when"; `triggers: [user, model]`.
- Progressive disclosure: compact SKILL.md, depth under `reference/`.
- No AI signatures/trailers. Commits via `git commit -F <file>` using the Issue #612 density template:
  subject `<type>(<scope>): <short> (#612)` then sections `Contexto e Motivacao`, `Detalhamento Tecnico`,
  `Decisoes Arquiteturais e Trade-offs`, `Validacao`, `Refs: #612`. Commit language matches repo convention (English subjects; body PT or EN matching repo style - use English).
- `python audit.py` must end at Errors: 0; `validate-skill-format.py skills` all PASS; no test deletions.
- New JSON-emitting CLI scripts follow envelope v2 (`api_version: 2`, `meta.answered_by`, bundle version from manifest.json) + PROBES row in `tests/test_envelope_contract_v2.py`.
- `.github/workflows` edits follow `github-actions` skill rules (permissions, no `${{ github.event.* }}` in `run:`, no `pull_request_target` on fork code, timeouts); match repo's existing action-pinning convention.
- ADR lives in `.devin/adr/009-...` (real repo convention; issue text said docs/adr/ - adapted, document the adaptation in the PR).
- Cross-skill pointers added to existing skills stay minimal (a "Cross-skills"/decision pointer to the new engine), no rewrites of their bodies.

## Task 1: New skill `git-github-adaptive-engineering` + phase-zero tool + contract test

Create:
- `skills/git-github-adaptive-engineering/SKILL.md` - orchestrating skill per issue spec: Fase Zero situational awareness, adaptive decision engine (feature/fix/refactor; hotfix; arch change/RFC+ADR; repo governance/bootstrap; CI self-healing), full gh/API arsenal table, info-density standards. Delegate depth to existing skills via cross-references (`gh`, `git-workflows`, `github-actions`, `pr`, `debug-ci-failures`, `finishing-a-development-branch`, `git-helper`, `resolving-merge-conflicts`, `using-git-worktrees`, `deploy`).
- `skills/git-github-adaptive-engineering/reference/` - playbooks: `decision-flows.md` (5 flow patterns), `gh-arsenal.md` (full command/API matrix incl. sub-issues, projects v2, rulesets, environments, secrets/variables, releases, attestations), `density-templates.md` (commit -F template + PR body-file template + issue body template, all with `Refs:`/`Closes` wiring).
- `scripts/phase-zero.py` - read-only diagnostic emitting the Fase-Zero battery as JSON envelope v2: git status -sb, branch list, remotes, recent log, `gh auth status`, `gh repo view --json ...`, `.github/` tree presence, rulesets (`gh api repos/{o}/{r}/rulesets` best-effort, tolerate 404/403), workflow list. Offline-safe: each probe optional, failures captured as `{ok:false}` in the envelope not crashes.
- `tests/validation/test_git_github_adaptive_engineering.py` - contract tests: frontmatter/description "Use when", SKILL.md contains required tokens (Fase Zero, decision engine, hotfix, ADR, ruleset, `gh secret`, `gh variable`, `gh workflow`, `gh run view`, `Closes #`, `Refs:`, sub-issue, `git commit -F`, `--body-file`, Mermaid), all reference files exist, no em/en dashes, phase-zero.py `--help`/envelope probe works offline.
- PROBES row for `scripts/phase-zero.py` in `tests/test_envelope_contract_v2.py` per CLI contract convention.

Done when: `pytest tests/validation/test_git_github_adaptive_engineering.py -v` green; `python scripts/phase-zero.py --help` exit 0; validate-skill-format lists new skill PASS. Commit 1 (atomic, template).

## Task 2: Update existing Git/GitHub/versioning skills

Add the adaptive-engine pointer + any missing Fase-Zero step to: `skills/gh/SKILL.md`, `skills/git-helper/SKILL.md`, `skills/git-workflows/SKILL.md`, `skills/github-actions/SKILL.md`, `skills/pr/SKILL.md`, `skills/debug-ci-failures/SKILL.md`, `skills/deploy/SKILL.md`, `skills/resolving-merge-conflicts/SKILL.md`, `skills/using-git-worktrees/SKILL.md`, `skills/finishing-a-development-branch/SKILL.md`.
Minimal diffs; keep each skill's own depth; the engine orchestrates, these execute. Extend contract test to assert each touched file references `git-github-adaptive-engineering`.

Done when: format validator all PASS; contract test green. Commit 2 (atomic, template).

## Task 3: `.github/` governance standardization

- `ISSUE_TEMPLATE/config.yml` (contact_links to Discussions/SECURITY) + `bug_report.yml`, `feature_request.yml`, `skill_improvement.yml` issue forms; remove superseded `bug_report.md`/`feature_request.md`.
- `PULL_REQUEST_TEMPLATE.md`: add required `Closes #` issue link, architectural context/trade-offs, validation checklist incl. commit template conformance.
- `.github/release.yml`: release-note categories mapped to the new label taxonomy (type:/priority:/scope:/status:).
- `.github/dependabot.yml`: `github-actions` weekly + `pip` weekly if python dep manifests exist.
- `.github/workflows/pr-quality.yml`: PR checks - skill format validation (`python scripts/validate-skill-format.py skills`), no-em-dash scan (`scripts/no-em-dash.py` if present else inline check), PR must reference an issue (body regex `Closes #|Refs #` via env-var pattern, no inline interpolation), conventional-commit-ish title lint. `contents: read` + `pull-requests: read`, timeout, ubuntu-latest, actions pinned matching repo convention.
- CODEOWNERS already `* @Leostruka` - keep.

Done when: YAML files parse (`python -c "import yaml"` or existing validator), workflow file valid, `python audit.py` no NEW errors. Commit 3 (atomic, template).

## Task 4: Living docs, ADR, inventory sync

- `CONTRIBUTING.md`: add sections - issue-first traceability (branch `<type>/<issue>-<slug>`), commit density template, secrets/variables via `gh secret`/`gh variable`, label taxonomy pointer; keep existing content.
- `SECURITY.md`: add reporting flow + secrets handling note (check existing content first).
- `.devin/adr/009-adaptive-git-github-engineering.md` - decision record for #612 following format of 001-008.
- Inventory: `manifest.json` (new skill entry matching neighbors: name, path, purpose, `original_path: %APPDATA%\\devin\\skills\\git-github-adaptive-engineering`, `source: "devin-bundle"`, `exported_at`, `export_hash` sha256 of SKILL.md), `skill_count` 184->185, `.devin/docs/SKILL-TIERS.md` (+1 + entry under planning/ops tier w/ ~token estimate bytes/4), `.devin/docs/TOOLS-MAP.md` (185), `README.md` badge+prose 184->185.
- `CHANGELOG.md` `[Unreleased]` entry.
- README capability note for adaptive Git/GitHub engineering if a skills-index section exists.

Done when: `python audit.py` Errors: 0; validate-skill-format 185/185; focused tests green. Commit 4 (atomic, template).

## FASE 4 (controller, not delegated)

Push branch; `gh pr create --body-file` title `refactor(versioning): implement adaptive Microsoft/GitHub engineering standard (#612)`, Mermaid flow diagram, impact map, validation checklist, `Closes #612`, labels type:refactor/scope:skills/scope:governance/scope:ci/priority:high; comment on #612 with diagnosis + deliverables + PR link.
