"""System Control CLI: read-only host inventory.

stdout carries exactly one JSON object per invocation; diagnostics go
to stderr. Exit codes: 0 verified read, 1 runtime failure (including
subprocess timeouts), 2 rejected request.
"""

import json
import math
import subprocess
import sys
import uuid

import sc_backend
import sc_contract as contract
import sc_policy
import sc_process

_COMMANDS = ("capabilities", "process-list", "process-get",
             "service-status", "preflight", "exec")


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
        if cmd == "preflight":
            # Policy-only: never touches backend discovery.
            name = "policy"
            if len(rest) != 1 or rest[0].startswith("--"):
                raise contract.InvalidRequest(
                    "preflight requires exactly one request JSON")
            try:
                req = json.loads(rest[0])
            except json.JSONDecodeError as exc:
                raise contract.InvalidRequest(f"invalid JSON: {exc}")
            return _verified(contract.result(
                ok=True, status="verified", request_id=request_id,
                backend=name,
                value=sc_policy.classify(req)), request_id)
        if cmd == "exec":
            # Confirmed one-shot spawn; no OS backend needed.
            name = "subprocess"
            opts = _opts(rest, {"argv-json", "request-id",
                                "confirmation-id", "cwd", "timeout"})
            for required in ("argv-json", "request-id",
                             "confirmation-id"):
                if required not in opts:
                    raise contract.InvalidRequest(
                        f"exec requires --{required}")
            try:
                argv = json.loads(opts["argv-json"])
            except json.JSONDecodeError as exc:
                raise contract.InvalidRequest(
                    f"invalid --argv-json: {exc}")
            try:
                timeout_s = float(opts.get("timeout", "30"))
            except ValueError:
                raise contract.InvalidRequest(
                    "--timeout must be a number")
            if not math.isfinite(timeout_s):
                raise contract.InvalidRequest("--timeout must be finite")
            if timeout_s.is_integer():
                timeout_s = int(timeout_s)
            cwd = opts.get("cwd")
            # Validate spawn args before consuming the confirmation so
            # bad input never burns a valid token.
            sc_process.validate_spawn(argv, cwd=cwd,
                                      timeout_s=timeout_s)
            request = {
                "version": 1,
                "request_id": opts["request-id"],
                "capability": "process.exec",
                "args": {"argv": argv, "cwd": cwd,
                         "timeout_s": timeout_s},
                "deadline_ms": max(1, int(timeout_s * 1000)),
                "policy": {"dry_run": False,
                           "confirmation_id": opts["confirmation-id"]},
            }
            if sc_policy.classify(request)["decision"] != "confirm":
                raise contract.InvalidRequest(
                    "capability does not require confirmation")
            outcome = sc_policy.consume_confirmation(
                request, opts["confirmation-id"])
            if not outcome["ok"]:
                raise contract.InvalidRequest(
                    f"confirmation rejected: {outcome['reason']}")
            res = sc_process.spawn(argv, cwd=cwd, timeout_s=timeout_s)
            res["request_id"] = opts["request-id"]
            _emit(res)
            return 0 if res["ok"] else 1
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
