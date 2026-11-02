# R13-01: manifest forbidden-crossing vs laya-guard reality

**Severity:** P3 (declared boundary contradicts code; unenforced)
**Files:** .devin/ARCHITECTURE_MANIFEST.md, scripts/laya-guard.py

**Defect (two halves):**
1. Manifest declares "scripts/ hooks never import from
   extensions/" but `laya-guard.py:170-173` sys.path-imports
   `decision_contract` + `laya_client` from
   `extensions/laya-tools/` (deliberate: laya is the routing
   engine; fail-open when absent). Rule as written is false.
2. Nothing enforces the boundary at all: no audit check, no test
   asserts that hook scripts stay free of third-party pip imports.
   Inspired by Nx module-boundaries (Jaaidi, JS Poland): declared
   constraints rot without an automated gate.

**Fix:**
- Manifest: rewrite the crossing as "no third-party pip deps in
  scripts/; laya-guard's sys.path import of extensions/laya-tools
  is the documented exception (fail-open)".
- Add tests/validation test scanning scripts/*.py imports: every
  imported top-level module must be stdlib, an in-dir sibling
  (_hookrun), or the laya-guard->laya-tools exception.

## Answer

Manifest rewritten: boundary is "no third-party pip deps"; laya-guard
-> extensions/laya-tools documented as the deliberate fail-open
exception. New test test_scripts_import_boundary enforces it (stdlib
+ in-dir siblings + that one exception). 28/28 pass.
