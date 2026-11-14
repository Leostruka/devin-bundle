# R21: used -> declared dependency direction had no enforcement

## Status: resolved

## Finding

R20 added `test_extension_declared_deps_used` (declared -> used, catches
orphaned requirements). The inverse direction had zero coverage: an
extension could import a third-party package at module scope without
declaring it in `requirements*.txt`, and nothing failed.

## Audit method

AST scan of every `extensions/**/*.py` (skipping `.venv`, `__pycache__`,
`node_modules`, test files/dirs), collecting **module-scope** imports only
(function/try-scope imports are lazy optionals by construction).

Module roots classified as internal: stdlib, every `.py` basename and
package directory anywhere under `extensions/` (the sanctioned
cross-extension `sys.path.insert` pattern used by `decision_contract`,
`laya_client`, `cu_dom_picker`, etc.).

## Result

Only remaining gap: `bpy` and `mathutils` in `blender-operator`. These are
provided by Blender's embedded Python interpreter (the extension code runs
inside the Blender process); they are not pip-provisionable for the bundle
environment. Documented as a host-provided exception, not a defect.

No undeclared hard dependency exists today.

## Fix

`test_extension_used_deps_declared` in
`tests/validation/test_install_export_scripts.py`:

- module-scope imports per extension must be in stdlib, the extension's
  own `requirements*.txt`, the extensions-internal module set, or the
  documented host-provided allowlist `{'bpy', 'mathutils'}`;
- lazy imports (function/try scope) are intentionally exempt;
- requirements parsing factored into `_extension_declared_imports()`
  shared with `test_extension_declared_deps_used`.

## Validation

`python -m pytest tests/validation/test_install_export_scripts.py`
