"""System Control CLI: read-only host inventory.

stdout carries exactly one JSON object per invocation; diagnostics go
to stderr. Exit codes: 0 verified read, 1 runtime failure (including
subprocess timeouts), 2 rejected request.
"""

import json
import math
import os
import subprocess
import sys
import uuid

import sc_backend
import sc_contract as contract
import sc_policy
import sc_process
import sc_sessions

_COMMANDS = ("capabilities", "process-list", "process-get",
             "service-status", "preflight", "exec",
             "sessions", "session", "events", "file",
             "process", "service")


def _emit(obj):
    sys.stdout.write(json.dumps(obj) + "\n")


def _diag(msg):
    sys.stderr.write(f"system-control: {msg}\n")


def _opts(argv, allowed, flags=frozenset()):
    """Strict flag parsing: known flags only, no duplicates, no
    trailing positionals. `flags` names valueless boolean switches."""
    out = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            raise contract.InvalidRequest(f"unexpected argument: {a}")
        key = a[2:]
        if key not in allowed and key not in flags:
            raise contract.InvalidRequest(f"unknown flag: {a}")
        if key in out:
            raise contract.InvalidRequest(f"duplicate flag: {a}")
        if key in flags:
            out[key] = True
            i += 1
            continue
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
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


def _session_reply(res, request_id):
    """Emit a session-op result inside the contract envelope."""
    ok = bool(res.get("ok"))
    if ok:
        status = "verified"
    elif res.get("status") == "rejected":
        status = "rejected"
    else:
        status = "unknown"
    _emit(contract.result(
        ok=ok, status=status, request_id=request_id,
        backend="sessions", value=res,
        error=None if ok else res.get("error")))
    if ok:
        return 0
    return 2 if status == "rejected" else 1


def _confirm(capability, args, opts, request_id):
    """Consume a confirmation for a CONFIRM capability; the caller must
    have finished all argument validation before invoking this.

    --request-id is mandatory: the issued token's digest binds the
    request_id, so a generated one could never match a confirmation.
    """
    if "request-id" not in opts:
        raise contract.InvalidRequest("requires --request-id")
    request = {
        "version": 1,
        "request_id": opts["request-id"],
        "capability": capability, "args": args,
        "deadline_ms": 30000,
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


def _load_session(opts):
    """Read the session dict from --session-file or --session-json."""
    has_file = "session-file" in opts
    has_json = "session-json" in opts
    if has_file == has_json:
        raise contract.InvalidRequest(
            "requires exactly one of --session-file/--session-json")
    try:
        if has_file:
            with open(opts["session-file"], encoding="utf-8") as fh:
                sess = json.load(fh)
        else:
            sess = json.loads(opts["session-json"])
    except (OSError, json.JSONDecodeError) as exc:
        raise contract.InvalidRequest(f"unknown session file: {exc}")
    if not isinstance(sess, dict):
        raise contract.InvalidRequest("unknown session file")
    return sess


def _sessions_cmd(rest, request_id):
    if not rest:
        raise contract.InvalidRequest("sessions requires a subcommand")
    sub, rest = rest[0], rest[1:]
    if sub == "start":
        _opts(rest, set())
        return _session_reply(sc_sessions.start_daemon(), request_id)
    if sub == "status":
        _opts(rest, set())
        return _session_reply(sc_sessions.daemon_status(), request_id)
    if sub == "list":
        _opts(rest, set())
        res = sc_sessions.list_sessions()
        if res.get("ok") and res.get("running") is False:
            res["sessions"] = []
        return _session_reply(res, request_id)
    if sub == "stop":
        opts = _opts(rest, {"confirmation-id", "request-id"})
        if "confirmation-id" not in opts:
            raise contract.InvalidRequest(
                "sessions stop requires --confirmation-id")
        _confirm("daemon.stop", {}, opts, request_id)
        return _session_reply(sc_sessions.stop_daemon(), request_id)
    raise contract.InvalidRequest(f"unknown sessions subcommand: {sub}")


def _session_cmd(rest, request_id):
    if not rest:
        raise contract.InvalidRequest("session requires a subcommand")
    sub, rest = rest[0], rest[1:]
    if sub == "spawn":
        if "--" not in rest:
            raise contract.InvalidRequest(
                "session spawn requires -- ARGV")
        sep = rest.index("--")
        opts = _opts(rest[:sep], {"confirmation-id", "request-id",
                                 "cwd", "capacity", "idle-ttl",
                                 "out-file"})
        argv = rest[sep + 1:]
        if "confirmation-id" not in opts:
            raise contract.InvalidRequest(
                "session spawn requires --confirmation-id")
        cwd = opts.get("cwd")
        capacity = _int_arg(opts.get("capacity", 2048), "--capacity")
        idle_ttl = _int_arg(opts.get("idle-ttl", 900), "--idle-ttl")
        if not capacity or not idle_ttl:
            raise contract.InvalidRequest(
                "--capacity/--idle-ttl must be positive")
        sc_process.validate_spawn(argv, cwd=cwd)
        _confirm("session.spawn",
                 {"argv": argv, "cwd": cwd, "capacity": capacity,
                  "idle_ttl_s": idle_ttl}, opts, request_id)
        res = sc_sessions.spawn_session(
            argv, cwd=cwd, capacity=capacity, idle_ttl_s=idle_ttl)
        if res.get("ok") and "out-file" in opts:
            sc_sessions._atomic_write(opts["out-file"], res["session"])
        return _session_reply(res, request_id)
    if sub == "send":
        opts = _opts(rest, {"confirmation-id", "request-id",
                            "session-file", "session-json", "data"})
        for req in ("confirmation-id", "data"):
            if req not in opts:
                raise contract.InvalidRequest(
                    f"session send requires --{req}")
        sess = _load_session(opts)
        err = sc_sessions._valid_session(sess)
        if err:
            raise contract.InvalidRequest(err["error"])
        if not isinstance(opts["data"], str) or not opts["data"]:
            raise contract.InvalidRequest("--data must be non-empty")
        _confirm("session.send",
                 {"session_id": sess["id"], "data": opts["data"]},
                 opts, request_id)
        return _session_reply(
            sc_sessions.send(sess, opts["data"]), request_id)
    if sub == "recv":
        opts = _opts(rest, {"session-file", "session-json", "cursor",
                            "tail", "wait", "timeout"})
        sess = _load_session(opts)
        kw = {}
        if "cursor" in opts:
            kw["cursor"] = _int_arg(opts["cursor"], "--cursor")
        if "tail" in opts:
            kw["tail"] = _int_arg(opts["tail"], "--tail")
        if "wait" in opts:
            kw["wait"] = opts["wait"]
        if "timeout" in opts:
            try:
                kw["timeout_s"] = float(opts["timeout"])
            except ValueError:
                raise contract.InvalidRequest(
                    "--timeout must be a number")
            if not math.isfinite(kw["timeout_s"]):
                raise contract.InvalidRequest("--timeout must be finite")
        return _session_reply(
            sc_sessions.recv(sess, **kw), request_id)
    if sub == "resize":
        opts = _opts(rest, {"session-file", "session-json",
                            "cols", "rows"})
        for req in ("cols", "rows"):
            if req not in opts:
                raise contract.InvalidRequest(
                    f"session resize requires --{req}")
        sess = _load_session(opts)
        return _session_reply(sc_sessions.resize(
            sess, _int_arg(opts["cols"], "--cols"),
            _int_arg(opts["rows"], "--rows")), request_id)
    if sub == "close":
        opts = _opts(rest, {"session-file", "session-json"})
        sess = _load_session(opts)
        return _session_reply(sc_sessions.close(sess), request_id)
    if sub == "cancel":
        opts = _opts(rest, {"confirmation-id", "request-id",
                            "session-file", "session-json"})
        if "confirmation-id" not in opts:
            raise contract.InvalidRequest(
                "session cancel requires --confirmation-id")
        sess = _load_session(opts)
        err = sc_sessions._valid_session(sess)
        if err:
            raise contract.InvalidRequest(err["error"])
        _confirm("session.cancel", {"session_id": sess["id"]},
                 opts, request_id)
        return _session_reply(sc_sessions.cancel(sess), request_id)
    raise contract.InvalidRequest(f"unknown session subcommand: {sub}")


def _file_reply(res, request_id):
    """Wrap the sc_files envelope in the canonical contract.result."""
    ok = bool(res.get("ok"))
    status = res.get("status", "unknown")
    _emit(contract.result(
        ok=ok, status=status, request_id=request_id,
        backend="files", value=res.get("value"),
        precondition=res.get("precondition"),
        postcondition=res.get("postcondition"),
        error=res.get("error")))
    if ok:
        return 0
    return 2 if status == "rejected" else 1


def _file_cmd(rest, request_id):
    import sc_files
    if not rest:
        raise contract.InvalidRequest("file requires a subcommand")
    sub, rest = rest[0], rest[1:]
    if sub == "inspect":
        opts = _opts(rest, {"root", "path"})
        for req in ("root", "path"):
            if req not in opts:
                raise contract.InvalidRequest(
                    f"file inspect requires --{req}")
        return _file_reply(
            sc_files.inspect_path(opts["root"], opts["path"]),
            request_id)
    if sub == "copy":
        opts = _opts(rest, {"root", "src", "dst", "expected-hash",
                            "request-id", "confirmation-id"},
                     flags={"dry-run", "overwrite"})
        for req in ("root", "src", "dst", "expected-hash",
                    "confirmation-id"):
            if req not in opts:
                raise contract.InvalidRequest(
                    f"file copy requires --{req}")
        expected = opts["expected-hash"]
        if not sc_files._valid_hash(expected):
            raise contract.InvalidRequest(
                "--expected-hash must be 64 hex chars")
        overwrite = bool(opts.get("overwrite"))
        dry_run = bool(opts.get("dry-run"))
        # Full arg validation before the confirmation is consumed.
        sc_files.validate_copy_args(opts["root"], opts["src"],
                                    opts["dst"])
        capability = ("file.copy_overwrite" if overwrite
                      else "file.copy")
        _confirm(capability,
                 {"root": opts["root"], "src": opts["src"],
                  "dst": opts["dst"], "expected_hash": expected,
                  "dry_run": dry_run, "overwrite": overwrite},
                 opts, request_id)
        return _file_reply(
            sc_files.copy_verified(opts["root"], opts["src"],
                                   opts["dst"], expected_hash=expected,
                                   dry_run=dry_run,
                                   overwrite=overwrite),
            request_id)
    raise contract.InvalidRequest(f"unknown file subcommand: {sub}")


def _float_opt(opts, key, flagname):
    try:
        v = float(opts[key])
    except ValueError:
        raise contract.InvalidRequest(
            f"{flagname} must be a number")
    if not math.isfinite(v) or v <= 0:
        raise contract.InvalidRequest(
            f"{flagname} must be positive and finite")
    return v


def _events_cmd(rest, request_id):
    import sc_telemetry
    if not rest:
        raise contract.InvalidRequest("events requires a subcommand")
    sub, rest = rest[0], rest[1:]
    if sub == "open":
        opts = _opts(rest, {"kind", "capacity", "ttl", "interval"})
        kw = {}
        if "kind" in opts:
            kw["provider"] = opts["kind"]
        if "capacity" in opts:
            kw["capacity"] = _int_arg(opts["capacity"], "--capacity")
            if not kw["capacity"]:
                raise contract.InvalidRequest(
                    "--capacity must be positive")
        if "ttl" in opts:
            kw["ttl_s"] = _float_opt(opts, "ttl", "--ttl")
        if "interval" in opts:
            kw["interval_s"] = _float_opt(
                opts, "interval", "--interval")
        return _session_reply(
            sc_telemetry.open_stream_remote(**kw), request_id)
    if sub == "drain":
        opts = _opts(rest, {"stream-id", "cursor", "limit"})
        if "stream-id" not in opts:
            raise contract.InvalidRequest(
                "events drain requires --stream-id")
        kw = {}
        if "cursor" in opts:
            kw["cursor"] = _int_arg(opts["cursor"], "--cursor")
        if "limit" in opts:
            kw["limit"] = _int_arg(opts["limit"], "--limit")
        return _session_reply(
            sc_telemetry.drain_remote(opts["stream-id"], **kw),
            request_id)
    if sub == "close":
        opts = _opts(rest, {"stream-id"})
        if "stream-id" not in opts:
            raise contract.InvalidRequest(
                "events close requires --stream-id")
        return _session_reply(
            sc_telemetry.close_stream_remote(opts["stream-id"]),
            request_id)
    if sub == "list":
        _opts(rest, set())
        return _session_reply(
            sc_telemetry.list_streams_remote(), request_id)
    raise contract.InvalidRequest(f"unknown events subcommand: {sub}")


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
        if cmd == "file":
            # Root-bound file ops; no OS inventory backend needed.
            name = "files"
            return _file_cmd(rest, request_id)
        if cmd == "events":
            # Daemon-hosted event streams; ALLOW capabilities.
            name = "sessions"
            return _events_cmd(rest, request_id)
        if cmd in ("sessions", "session"):
            # Session daemon commands; no OS inventory backend needed.
            name = "sessions"
            if cmd == "sessions":
                return _sessions_cmd(rest, request_id)
            return _session_cmd(rest, request_id)
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
        if cmd == "process":
            if not rest or rest[0] != "wait":
                raise contract.InvalidRequest(
                    "process requires the wait subcommand")
            opts = _opts(rest[1:], {"pid", "start-time", "timeout"})
            if "pid" not in opts or "start-time" not in opts:
                raise contract.InvalidRequest(
                    "process wait requires --pid and --start-time")
            identity = {"pid": _int_arg(opts["pid"], "--pid"),
                        "start_time": _int_arg(opts["start-time"],
                                               "--start-time")}
            try:
                timeout_s = float(opts.get("timeout", "30"))
            except ValueError:
                raise contract.InvalidRequest(
                    "--timeout must be a number")
            if not math.isfinite(timeout_s) or timeout_s < 0:
                raise contract.InvalidRequest(
                    "--timeout must be non-negative and finite")
            wait_fn = getattr(backend, "wait_process", None)
            if wait_fn is None:
                return _reply(1, "unknown", request_id, name,
                              "backend lacks process.wait")
            res = wait_fn(identity, timeout_s)
            ok = bool(res.get("ok"))
            status = "verified" if ok else res.get("status", "unknown")
            _emit(contract.result(
                ok=ok, status=status, request_id=request_id,
                backend=name, value=res,
                error=None if ok else res.get("error")))
            if ok:
                return 0
            return 2 if status == "rejected" else 1
        if cmd == "service":
            if not rest or rest[0] != "restart":
                raise contract.InvalidRequest(
                    "service requires the restart subcommand")
            opts = _opts(rest[1:], {"name", "allowed",
                                    "confirmation-id", "request-id"})
            for req in ("name", "allowed", "confirmation-id",
                        "request-id"):
                if req not in opts:
                    raise contract.InvalidRequest(
                        f"service restart requires --{req}")
            allowed = [s.strip() for s in opts["allowed"].split(",")
                       if s.strip()]
            if not allowed:
                raise contract.InvalidRequest(
                    "--allowed must list at least one service")
            _confirm("service.restart",
                     {"name": opts["name"], "allowed": allowed},
                     opts, request_id)
            restart_fn = getattr(backend, "restart_service", None)
            if restart_fn is None:
                return _reply(1, "unknown", request_id, name,
                              "backend lacks service.restart")
            res = restart_fn(opts["name"], allowed=allowed)
            ok = bool(res.get("ok"))
            status = ("verified" if ok
                      else res.get("status", "unknown"))
            _emit(contract.result(
                ok=ok, status=status, request_id=request_id,
                backend=name, value=res,
                precondition=res.get("precondition"),
                postcondition=res.get("postcondition"),
                error=None if ok else res.get("error")))
            if ok:
                return 0
            return 2 if status == "rejected" else 1
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
