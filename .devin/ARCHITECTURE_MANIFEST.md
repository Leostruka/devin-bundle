# Architecture Manifest — devin-bundle

## 1. Paradigm

- **Primary:** procedural / functional (scripts, hooks, skills). OOP only in
  `extensions/` where a subsystem needs stateful objects.
- **Rules:** small functions, stdlib-first Python; no class without state to
  justify it; shell scripts stay linear (no functions unless reused 3+ times).

## 2. Design Patterns

- **Allowed:** gate/hook scripts (stdin JSON → exit 0/2), template method in
  install/export steps, folder-per-module (`skills/<name>/`,
  `extensions/<name>/`, `extensions/rust-core/crates/<name>/`).
- **Forbidden:** singletons, global mutable config objects, deep class
  hierarchies, metaprogramming in hook scripts.

## 3. Style Contracts

- **Formatter / linter:** none enforced; match surrounding file style.
- **Naming:** `snake_case` Python, `kebab-case` script/skill names, `SCREAMING`
  env vars, `NNN-slug.md` ADRs.
- **Imports / dependencies:** Python stdlib only in `scripts/` (hooks must run
  on bare interpreters); PyO3 pinned in rust-core crates; no new deps without
  user approval.
- **Comments/docs:** header docstring on every hook script documenting stdin
  payload, exit codes, and gate list; no inline narration.

## 4. Testing Strategy

- **Framework + layout:** pytest; `tests/validation/` (chosen tests) and
  `tests/held-out/` (gap checks) per Rule 16.
- **Coverage philosophy:** contract tests for scripts/skills (string
  presence, syntax, JSON schema); no arbitrary coverage gates.
- **Gates before commit/push:** `python audit.py`, `pytest -q`,
  `bash -n install.sh`, PowerShell tokenize on `*.ps1`,
  `cargo build --release` when rust-core changes.

## 5. Error Handling

- **Error model:** hooks fail-open (exit 0) on parse/runtime errors; install
  scripts warn non-blocking and continue; agent-facing blocks use
  `{"decision": "block", "reason": ...}` + exit 2.
- **Logging:** stderr for warnings; stdout reserved for hook JSON decisions
  and installer status; never print secrets.
- **Boundaries:** errors caught at script top level; hook gate checks each
  wrapped in try/except.

## 6. Directory Boundaries

- **Layout:** `skills/` = invocable workflows, `scripts/` = hook scripts
  (stdlib-only), `extensions/` = local tools (`computer-use`, `media-tools`,
  `rust-core` Cargo workspace), `agents/` = subagent profiles, `docs/` =
  reference docs, `data/` = model data, `.devin/` = project config
  (adr/, ledgers/, rules/, plans/), `tests/` = pytest suites.
- **Forbidden crossings:** `scripts/` hooks never import from `extensions/`;
  `.devin/ledgers/` files are gitignored (never ship); hook scripts never
  read `credentials.toml` or `.env`.

## Non-negotiables

- No AI signatures or Co-Authored-By in any artifact (Rule 2).
- No secrets in VCS; MASKED placeholders only (Rule 24).
- Installers never force-install toolchains; missing deps = warning.
