# `.devin/agents/` — project-local subagent profiles

Scope split (two agent surfaces, intentionally disjoint):

- **`agents/` (repo root)** — bundle-distributed profiles, installed to
  `~/.config/devin/agents/` / `%APPDATA%\devin\agents\`. Available to every
  project for this user: `architect`, `debugger`, `implementer`, `qa-ci`,
  `researcher`, `reviewer`.
- **`.devin/agents/` (this dir)** — project-local profiles, loaded only inside
  this repository. Roles specific to this project's local issue workflow:
  `domain`, `issue-tracker`, `repo-reviewer`, `triage-labels`.

Do not merge the two dirs: promoting project-local profiles into `agents/`
would distribute repo-specific roles globally; demoting `agents/` here would
hide the shared profiles from other projects.
