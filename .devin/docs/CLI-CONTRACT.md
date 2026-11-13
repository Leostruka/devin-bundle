# CLI envelope contract v2

JSON responses from bundle CLIs/extensions follow a shared envelope so
agents can identify provenance and version at call time.

## Shape

Success and error responses are flat JSON objects. Every response carries:

```json
{
  "api_version": 2,
  "status": "ok | missing | error | rejected | timeout | degraded",
  "meta": {
    "answered_by": {
      "bundle": "3.21.0",
      "wrapper": "<extension-name>"
    }
  }
}
```

Domain fields stay flat alongside (`command`, `stdout`, `stderr`,
`duration_s`, `action`, `result`, `error`, `ok`, ...). `ok` is kept where
a wrapper already emitted it; `status` remains the primary signal.
Consumers MUST ignore unknown keys (forward-compatible).

## Provenance

`meta.answered_by.bundle` is the bundle version read from the nearest
`manifest.json` ancestor of the running file. It resolves identically
from the repo layout (`extensions/<name>/wrapper.py`) and the live
install (`%APPDATA%/devin/extensions/<name>/wrapper.py`), because
`manifest.json` sits at the install root in both. A stale live copy is
thus identifiable at call time instead of only at ledger reconcile
(the class fixed in #582).

If no manifest is found, `bundle` is `""` (honest unknown, never
fabricated).

## Implementation patterns

Two patterns, pick by wrapper shape:

- **Pattern A - `envelope()` funnel exists**: add `api_version` +
  `meta` inside `envelope()` (agent-reach, voicebox, hyperframes,
  stock-footage).
- **Pattern B - ad-hoc payloads**: inject in the single `emit()` (or
  final print) funnel via `setdefault`, so every payload path is
  covered without refactoring call sites (gcal, offsec-tools,
  rea-ops, rz-ops, blender-operator, comfyui-operator).

`_bundle_version()` is duplicated per wrapper on purpose: extensions
install as flat self-contained dirs, no shared import path exists.

## Out of scope

- `system-control` `sc_*` suite: governed by `sc_contract.py`
  (`SCHEMA_VERSION`), a separate wire contract. Evaluate separately.
- Media/internal tools (grainrad, jxl, playblast, craft-bridge,
  api-bridge): lower agent-call frequency.
- `--detail brief|compact|full`: implemented on `stock-footage search`
  (default `full` = back-compat). Deferred elsewhere; passthrough
  wrappers defer verbosity to upstream tools.

## References

- Issue #593, PRs #594 (pilot), #595 (rollout waves 1-3)
- Astryx CLI contract inspiration: `meta.answeredBy`, `apiVersion`
  (meta/astryx packages/cli/README)
