# Task 1 brief — Read-only host inventory

## Context

This is the first vertical slice of `.devin/plans/2026-09-19-system-control.md`. Build a separate `extensions/system-control/` extension. Do not import from `computer-use`. The plan and research documents already exist as untracked lead-owned artifacts.

## Binding constraints

- Python 3.9+ stdlib only; no dependencies.
- Procedural/small functions; no singleton or deep class hierarchy.
- stdout: exactly one JSON object. Diagnostics: stderr.
- No privileged daemon, mutation, unrestricted shell, or secret output.
- Process identity is `pid + start_time`, never PID alone.
- Unknown schema/command/backend fails closed with a typed response.
- External commands use argument arrays, `shell=False`, timeout and output cap.
- Tests first: verify RED before production code, then GREEN.
- Do not read or edit `tests/held-out/`; those are lead/QA-owned.
- Do not edit plan/research documents.
- Run task tests and `python audit.py` before commit.

## Files

Create:
- `extensions/system-control/sc_contract.py`
- `extensions/system-control/sc_backend.py`
- `extensions/system-control/sc_process.py`
- `extensions/system-control/sc_cli.py`
- `extensions/system-control/backends/__init__.py`
- `extensions/system-control/backends/windows.py`
- `extensions/system-control/backends/linux.py`
- `extensions/system-control/backends/macos.py`
- `extensions/system-control/schemas/v1.json`
- `tests/test_sc_contract.py`
- `tests/test_sc_inventory.py`
- `tests/test_sc_cli.py`

## Exact interfaces

- `sc_contract.validate_request(value: dict) -> dict`
- `sc_contract.target(pid: int, start_time: int) -> dict`
- `sc_contract.result(*, ok: bool, status: str, request_id: str, backend: str, privilege: str = "user", precondition=None, value=None, postcondition=None, cursor=None, spill=None, dropped: int = 0, error=None) -> dict`
- `sc_contract.untrusted(value) -> dict`
- `sc_backend.BackendUnavailable(RuntimeError)`
- `sc_backend.current() -> object`
- `sc_backend.capabilities(backend=None) -> list[dict]`
- Backend protocol: `capabilities()`, `process_list(pid=None)`, `process_get(pid, start_time=None)`, `service_status(name)`.
- `sc_process.snapshot(*, pid=None, limit=100, backend=None) -> dict`
- CLI: `capabilities`, `process-list`, `process-get`, `service-status`.

`SCHEMA_VERSION = 1`. Statuses: `dispatched`, `verified`, `rejected`, `timeout`, `unknown`, `cancelled`. `result()` always contains `evidence:{cursor,spill,dropped}` with defaults `null`, `null`, `0`. Capability entries use `{name,supported,reason,mode}`.

## Required tests

```python
def test_response_distinguishes_dispatch_from_verification():
    r = contract.result(ok=True, status="dispatched", request_id="r1", backend="fake")
    assert r["ok"] is True
    assert r["status"] == "dispatched"
    assert "postcondition" in r


def test_process_target_requires_start_time():
    with pytest.raises(ValueError, match="start_time"):
        contract.validate_request({
            "version": 1, "request_id": "r1",
            "capability": "process.observe", "target": {"pid": 12},
            "args": {}, "deadline_ms": 1000,
        })
```

```python
class FakeBackend:
    name = "fake"
    def capabilities(self):
        return [
            {"name": "process.observe", "supported": True, "reason": None, "mode": "native"},
            {"name": "service.observe", "supported": True, "reason": None, "mode": "native"},
        ]
    def process_list(self, pid=None):
        return [{"pid": 7, "start_time": 99, "name": "worker"}]
    def process_get(self, pid, start_time=None):
        return self.process_list(pid)[0]
    def service_status(self, name):
        return {"name": name, "state": "running"}


def test_snapshot_is_bounded_and_typed():
    r = process.snapshot(limit=1, backend=FakeBackend())
    assert r["status"] == "verified"
    assert r["value"] == [{"pid": 7, "start_time": 99, "name": "worker"}]
```

Add CLI tests proving one JSON object and exit codes 0/1/2. Add backend tests for explicit unsupported capability and stable process identity.

## Implementation decisions

- Required request keys: `version`, `request_id`, `capability`, `args`, `deadline_ms`.
- Require `target.pid` and `target.start_time` together.
- Reject schema versions other than 1.
- Require dict `args`; integer deadline from 1 through 300000.
- `platform.system()` selects Windows/Linux/macOS module. Import failure returns typed unsupported capabilities; no fallback shell.
- Windows initial adapter: `Get-CimInstance` JSON subprocess for process snapshot; `sc.exe query` fixed args for explicit service name.
- Linux: `/proc/<pid>/stat` and boot-relative start ticks; service observation only when systemd detected.
- macOS: bounded `ps -axo pid,lstart,comm`; `launchctl print` only for explicit label.
- Unknown subcommand: exit 2 and `status:"rejected"`. Runtime failure: exit 1. Verified read: exit 0.

## Verification

RED:
`python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q`
Expected: fail because modules are absent.

GREEN:
`python -m pytest tests/test_sc_contract.py tests/test_sc_inventory.py tests/test_sc_cli.py -q`
Expected: all pass.

Audit:
`python audit.py`
Expected: exit 0, zero errors.

Before commit, also run the repository suite required by Rule 5. Commit message:
`feat(system-control): add read-only host inventory`

Stage the lead-owned `.devin/plans/2026-09-19-system-control.md`, `.devin/research/swe2-full-system-control.md`, and `tests/held-out/system-control/` without reading or modifying them, so the branch captures approved context and QA assets.
