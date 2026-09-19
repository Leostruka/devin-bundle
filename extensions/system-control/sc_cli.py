"""System Control CLI: read-only host inventory.

stdout carries exactly one JSON object per invocation; diagnostics go
to stderr. Exit codes: 0 verified read, 1 runtime failure (including
subprocess timeouts), 2 rejected request.
"""

import json
import subprocess
import sys
import uuid

import sc_backend
import sc_contract as contract
import sc_process

_COMMANDS = ("capabilities", "process-list", "process-get",
             "service-status")


def _emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")


def _diag(msg):
    sys.stderr.write(f"system-control: {msg}\n")


def _opts(argv, allowed):
    """Strict flag parsing: known flags only, no duplicates, no
    trailing positionals."""
    out = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            raise contract.InvalidRequest(f"unexpected argument: {a}")
        key = a[2:]
        if key not in allowed:
            raise contract.InvalidRequest(f"unknown flag: {a}")
        if key in out:
            raise contract.InvalidRequest(f"duplicate flag: {a}")
        if i + 1 >= len(argv):
            raise contract.InvalidRequest(f"missing value for {a}")
        out[key] = argv[i + 1]
        i += 2
    return out


def _int_arg(value, flagname):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise contract.InvalidRequest(
            f"{flagname} must be an integer")
    if v < 0:
        raise contract.InvalidRequest(
            f"{flagname} must be non-negative")
    return v


def _reply(code, status, request_id, backend, message):
    _emit(contract.result(ok=False, status=status,
                          request_id=request_id, backend=backend,
                          error=message))
    return code


def _verified(result_obj, request_id):
    result_obj["request_id"] = request_id
    _emit(result_obj)
    return 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    request_id = uuid.uuid4().hex[:12]
    name = "none"
    if not args:
        return _reply(2, "rejected", request_id, name,
                      "missing command")
    cmd, rest = args[0], args[1:]
    if cmd not in _COMMANDS:
        return _reply(2, "rejected", request_id, name,
                      f"unknown command: {cmd}")
    try:
        backend = sc_backend.current()
        name = sc_backend.backend_name(backend)
        if cmd == "capabilities":
            if rest:
                raise contract.InvalidRequest(
                    "capabilities takes no arguments")
            return _verified(contract.result(
                ok=True, status="verified", request_id=request_id,
                backend=name, value=backend.capabilities()),
                request_id)
        if cmd == "process-list":
            opts = _opts(rest, {"pid", "limit"})
            pid = opts.get("pid")
            return _verified(sc_process.snapshot(
                pid=_int_arg(pid, "--pid") if pid is not None else None,
                limit=_int_arg(opts.get("limit", 100), "--limit"),
                backend=backend), request_id)
        if cmd == "process-get":
            opts = _opts(rest, {"pid", "start-time"})
            if "pid" not in opts or "start-time" not in opts:
                raise contract.InvalidRequest(
                    "process-get requires --pid and --start-time")
            try:
                value = backend.process_get(
                    _int_arg(opts["pid"], "--pid"),
                    _int_arg(opts["start-time"], "--start-time"))
            except LookupError as exc:
                return _reply(2, "rejected", request_id, name,
                              str(exc))
            return _verified(contract.result(
                ok=True, status="verified", request_id=request_id,
                backend=name, value=value), request_id)
        if cmd == "service-status":
            if len(rest) != 1 or rest[0].startswith("--"):
                raise contract.InvalidRequest(
                    "service-status requires exactly one name")
            return _verified(contract.result(
                ok=True, status="verified", request_id=request_id,
                backend=name,
                value=backend.service_status(rest[0])), request_id)
    except contract.InvalidRequest as exc:
        return _reply(2, "rejected", request_id, name, str(exc))
    except subprocess.TimeoutExpired as exc:
        return _reply(1, "timeout", request_id, name, str(exc))
    except Exception as exc:
        _diag(exc)
        return _reply(1, "unknown", request_id, name, str(exc))
    return _reply(2, "rejected", request_id, name,
                  f"unhandled command: {cmd}")


if __name__ == "__main__":
    sys.exit(main())
