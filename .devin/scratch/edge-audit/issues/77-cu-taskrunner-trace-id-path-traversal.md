# 77 -- cu_taskrunner trace_id used unvalidated in path join (traversal)
- **Status**: open
- **Category**: security
- **Severity**: P2
- **File**: extensions/computer-use/cu_taskrunner.py:38-39, 92-96
## Evidence
`_trace_dir` is a bare `os.path.join(STORE, trace_id)` with no validation that `trace_id` is the `uuid4().hex[:12]` format `start()` mints (line 71). `status`/`stop`/`_exec` take `trace_id` straight from argv (`status <trace_id>`, `stop <trace_id>`). Passing `../../outside` makes `_read_status` read `STORE/../../outside/status.json` and `stop()` line 99 writes `status.json` there via `_write_status`, and line 103 will `taskkill`/`os.kill` whatever `pid` that file claims.
## Recommendation
Reject any `trace_id` not matching `^[0-9a-f]{12}$` at the entry points (`status`, `stop`, `_exec`) before path use; alternatively resolve and verify `os.path.realpath` stays under `os.path.realpath(STORE)` as sc_files.py already does.
## Verification
`python cu_taskrunner.py status "../"` and `stop "../x"` with a planted `status.json` showing `"state":"running","pid":<victim>` outside STORE; observe the write/kill target escapes `cu_tasks/`.

## Answer
`_trace_dir` now validates trace_id against `^[0-9a-f]{12}$` plus a realpath containment check under STORE, raising ValueError otherwise. `_read_status` catches it (returns None), so `status`/`stop`/`list` reject traversal ids; the `_exec` CLI entry validates before use. Tests cover `../`, `..\`, embedded separators, trailing space, non-hex, and a planted dir outside the store.

Status: resolved
