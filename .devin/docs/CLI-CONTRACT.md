# CLI envelope contract v2

JSON responses from bundle extension wrappers follow a shared envelope
so agents can identify provenance and version at call time.

Scope note: `extensions/*` wrappers only. `scripts/` tools emit ad-hoc
JSON consumed by hooks/repo runs (drift already covered by the install
ledger's `scripts/` tracking); hook-internal JSON goes to the hook
runtime, not agents.

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

Only a JSON object with a `"name"` key counts as the bundle manifest:
malformed JSON, non-dict JSON (`null`, `[]`), and unrelated files yield
`bundle: ""` (honest unknown, never fabricated). The walk uses
`Path(__file__).absolute()` so a junctioned/symlinked install reports
the version of the tree it was invoked from, not the resolved target.

## Implementation pattern (uniform)

Every covered wrapper carries the same three-function block:

- `_bundle_version()` - cached manifest lookup described above.
- `_answered_by()` - returns `{"bundle": ..., "wrapper": "<name>"}`.
- `_stamp(payload)` - in-place: forces `api_version = 2`, replaces a
  non-dict `meta` with `{}`, then `setdefault("answered_by", ...)` so a
  passthrough payload's own `answered_by` is preserved.

`_stamp` runs at every JSON funnel: inside `envelope()` builders
*after* `env.update(extra)` (so `extra` cannot clobber the contract
keys), inside `emit()`/`_out()`/final-print for ad-hoc payloads, and on
help/usage JSON paths (routed through `emit()`). Non-dict payloads pass
through untouched.

The helpers are duplicated per wrapper on purpose: extensions install
as flat self-contained dirs, no shared import path exists. Exception:
files inside the same dir that already cross-import share the helpers
through a per-dir module - `scrape-tools/st_common.py`,
`computer-use/cu_envelope.py`, `laya-tools/laya_envelope.py`,
`asr/asr_envelope.py`, `ai-tools/ai_envelope.py`,
`media-tools/media_envelope.py`, `remotion-render/remotion_envelope.py`,
`image-forensics/forensics_envelope.py`,
`design-intelligence/design_envelope.py`, and
`scripts/bundle_envelope.py` (`bind(wrapper)` for per-file names).
Deduplicated after independent review - one fix site per dir instead
of ~70 identical copies. Dirs with only 1-2 emitters keep a local
copy (ppisp-prep, harness-tree, craft-bridge, mesh-utils,
laya-compactor, diagram-tools, code-graph, blender-operator,
api-bridge).

## Covered entry points

Dedicated wrappers: agent-reach, voicebox, hyperframes, gcal,
offsec-tools, rea-ops, rz-ops, stock-footage, blender-operator,
comfyui-operator, laya-tools.

Utility CLIs (wave 5, #604): `scrape-tools/{scrape,parse,dom_elements}.py`
(shared stamp via `st_common.emit`) and `asr/{bootstrap,transcribe}.py`
(local `_emit`).

`code-graph/query.py`: `--json` keeps the historical bare-array output;
`--envelope` (top-level or per-subcommand) wraps results in
`{"ok", "result": [...], api_version, meta}`, and the missing-index
exit also emits a stamped `{"ok": false, "status": "missing"}` JSON
under `--json`/`--envelope`.

computer-use (wave 6, #604): the 8 skill-invoked entry CLIs -
`terminal.py`, `screenshot.py`, `mouse.py`, `type_text.py`, `record.py`,
`profile.py`, `env.py`, `browser.py` - stamp every `print(json.dumps(..))`
site via a local `_dumps(payload, **kw)` funnel (`json.dumps` composed
with `_stamp`). Shared modules that emit on a CLI's behalf are stamped
too: `cu_motion.py` (JsonParser usage errors), `cu_target.py`
(typed rejections), `cu_actions.py` (exception wrapper),
`cu_scope.py` (window-discovery CLI), and `cu_session_dispatch.py`
(daemon-unavailable paths under `$CU_SESSION=1`). The remaining
`__main__`-only utility CLIs (`cu_bench`, `cu_dom_picker`, `cu_events`,
`cu_notify`, `cu_ocr`, `cu_overlay`, `cu_probe`, `cu_session`,
`cu_taskrunner`, `cu_wgc`) are stamped as well - the extension's whole
JSON-on-stdout surface now carries v2.

Skill-referenced extension CLIs (wave 8, #604): `ai-tools` (9 files),
`media-tools` (6), `remotion-render` (3), `design-intelligence` (3),
`image-forensics` (3) - same `_dumps` funnel. Non-stdout `json.dumps`
(e.g. `look_ledger` jsonl ledger writes) is intentionally NOT stamped;
only stdout JSON is the agent contract. Three crash-on-missing-arg bugs
were fixed in passing (`metadata.py`, `plan_check.py` no-args IndexError,
`look_ledger.py` unhandled file errors) - all now emit `{"ok": false}`
JSON with non-zero exit.

Remaining emitters (wave 9, #604): `laya-compactor`, `ppisp-prep`,
`mesh-utils`, `api-bridge`, `diagram-tools`, `craft-bridge`,
`harness-tree`, plus `scripts/graph-query.py` (agent-facing
graph-before-grep retrieval). `ns.py resume` gained a JSON error path
(FileNotFoundError crash -> `{"ok": false}` + exit 1).

Final sweep (wave 10, #604): `extensions/laya-tools` sub-tools
(fit_calibration, layad, capture_eval, doc_coverage, eval_decisions,
explore, filebool, laya_worker, review_gate, bootstrap),
`extensions/blender-operator/camera_blocking.py`,
`extensions/code-graph/detect_changes.py`, and the nine
skill-referenced non-hook `scripts/` tools (check-tools,
context-budget, decision-queue, done-evaluator, focus, install-ledger,
dep-audit, spec-consistency, subagent-trace). `fit_calibration.py` and
`capture_eval.py` gained JSON error paths (OSError tracebacks ->
`{"ok": false}` + non-zero exit). This closes the agent-facing emit
surface: every `print(json.dumps` outside `system-control`'s separate
contract and hook-runtime infrastructure now carries v2.

## Adding a wrapper

1. Copy the `_bundle_version()` + `_answered_by()` + `_stamp()` block
   from any wrapped extension; call `_stamp(...)` at every JSON output
   funnel, including help/usage paths. If the extension already has a
   shared module (e.g. `st_common.py`), host the trio there once and
   route sibling prints through `emit(payload)`.
2. Add a `(path, argv, wrapper-name)` row to `PROBES` in
   `tests/test_envelope_contract_v2.py` - the test runs the wrapper in
   a real subprocess and asserts `api_version == 2`,
   `answered_by.wrapper`, and `answered_by.bundle == manifest.json`
   version. Pick an argv that emits JSON without side effects.
3. Probe live: run the wrapper once and confirm
   `meta.answered_by.bundle` equals `manifest.json` version.

## Out of scope

- `system-control` `sc_*` suite: governed by `sc_contract.py`
  (`SCHEMA_VERSION`), a separate wire contract. Evaluate separately.
- `code-graph/query.py --json` bare-array output: kept for
  back-compat; the opt-in `--envelope` flag is the contract path.
- `scripts/*.py` hooks (43 files): their stdout JSON is consumed by the
  Devin CLI hook runtime (permission decisions, nudges, gates), not
  parsed by agents as tool output - infrastructure, not an "answered_by"
  surface. Same verdict for hook-protocol payloads outside the hook
  registry (`skill-picker.py`, `refine-review-prompt.py`, token-saver,
  pulse, rl-resume-detect): they print `hookSpecificOutput`/gate
  `decision` objects, not tool output.
- Bare-array JSON outputs are not envelope carriers: `_stamp` only
  stamps dicts, so `skills/*/scripts/query-memory.py --json`,
  `fold_store.py list|grep`, and any list-shaped emit stay as-is
  (`fold_store.py save` emits a dict and IS stamped - wave 11 fix).
- Protocol surfaces, not tool output: `computer-use/mcp_server.py`
  (JSON-RPC loop - extra keys could break strict MCP clients),
  `computer-use/cu_session.py` `--worker`/daemon transports (JSON-lines
  stdin/stdout pipe and loopback socket - inner script payloads are
  already self-stamped by their own `_dumps`), and
  `system-control/sc_cli.py` `_emit` (SCHEMA_VERSION contract) use
  `sys.stdout.write(json.dumps(...))`/raw `json.dumps` deliberately
  unstamped.
- `busybar`: no stdout-JSON emitters (`push.py` json.dumps is an HTTP
  payload, `listen.py` is a daemon listener).
- `--detail brief|compact|full`: implemented on `stock-footage search`
  (default `full`). Note `full` output also gained an additive
  `result.detail` echo key - consumers ignoring unknown keys are
  unaffected. Deferred elsewhere; passthrough wrappers defer verbosity
  to upstream tools.

## References

- Issue #593, PRs #594 (pilot), #595 (rollout waves 1-3), #601
  (runtime-verified guard + hardened provenance)
- Astryx CLI contract inspiration: `meta.answeredBy`, `apiVersion`
  (meta/astryx packages/cli/README)
