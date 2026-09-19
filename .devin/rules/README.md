# .devin/rules

This directory is intentionally empty in the bundle because project-specific
rules should live in the consuming project, not in the global bundle. The
bundle distributes `AGENTS.md` (global rules) and `.devin/global_rules.md`
(project rules template). If a project needs domain-specific rules, place
them here after `project-bootstrap` runs.
