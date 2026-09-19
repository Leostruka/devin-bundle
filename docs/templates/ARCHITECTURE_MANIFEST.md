# Architecture Manifest — <project name>

<!--
  Copy this file to <project-root>/.devin/ARCHITECTURE_MANIFEST.md and fill
  every section. The architecture gate (scripts/architecture-gate.py) blocks
  source edits until this file exists. Elicit answers from the user — do not
  invent conventions the user has not confirmed. Keep it terse; this file is
  read by agents, not humans reviewing architecture theory.
-->

## 1. Paradigm

- **Primary:** <OOP | functional | procedural | mixed>
- **Rules:** <e.g. "pure functions preferred; classes only for stateful
  resources" / "data immutability by default" / "no inheritance beyond 1 level">

## 2. Design Patterns

- **Allowed:** <e.g. repository, factory, adapter, strategy, dependency
  injection via constructor>
- **Forbidden:** <e.g. singleton, god object, service locator, deep
  inheritance hierarchies>

## 3. Style Contracts

- **Formatter / linter:** <tool + config file, e.g. "black + ruff, pyproject.toml">
- **Naming:** <e.g. snake_case functions, PascalCase types, SCREAMING consts>
- **Imports / dependencies:** <e.g. stdlib-first; new deps need approval;
  no wildcard imports>
- **Comments/docs:** <e.g. docstrings on public API only; no inline narration>

## 4. Testing Strategy

- **Framework + layout:** <e.g. pytest; tests/ mirrors src/; test_*.py>
- **Coverage philosophy:** <e.g. critical paths only; no arbitrary gates>
- **Gates before commit/push:** <exact commands that must pass>

## 5. Error Handling

- **Error model:** <e.g. exceptions at boundaries, Result types internally /
  fail-open with warnings / fail-fast>
- **Logging:** <e.g. stderr warnings; never log secrets; no print in libs>
- **Boundaries:** <where errors are caught vs propagated>

## 6. Directory Boundaries

- **Layout:** <dir → responsibility map, e.g. `src/` = library, `cli/` = entry
  points, `tests/` = mirrors src>
- **Forbidden crossings:** <e.g. tests never import from cli/; domain layer
  never imports infrastructure>

## Non-negotiables

<one line each: invariants that outrank everything above, e.g. "no secrets in
VCS", "no deletion without approval">
