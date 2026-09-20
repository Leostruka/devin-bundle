"""macOS adapter: bounded ps projection; launchctl for named services.

Read-only. External commands use argument arrays, shell=False,
timeout and capped output via backends.run_bounded.
"""

import math
import os
import re
import select
import shutil
import subprocess
import time

from backends import run_bounded
from sc_backend import BackendUnavailable
from sc_contract import InvalidRequest

name = "macos"

_LABEL = re.compile(r"^[A-Za-z0-9_.\-]+$")
_LSTART = "%a %b %d %H:%M:%S %Y"
_WAIT_SLICE_S = 0.25


def _launchctl():
    return shutil.which("launchctl")


def capabilities():
    ps = shutil.which("ps") is not None
    lc = _launchctl() is not None
    return [
        {"name": "process.observe", "supported": ps,
         "reason": None if ps else "ps not found",
         "mode": "subprocess"},
        {"name": "service.observe", "supported": lc,
         "reason": None if lc else "launchctl not found",
         "mode": "subprocess"},
        {"name": "process.wait", "supported": ps,
         "reason": None if ps else "ps not found",
         "mode": ("kqueue" if hasattr(select, "kqueue")
                  else "ps-poll")},
        {"name": "service.restart", "supported": False,
         "reason": "broker_required", "mode": "broker"},
        {"name": "endpoint_security", "supported": False,
         "reason": "entitlement_required", "mode": "endpoint_security"},
        {"name": "events.process", "supported": ps,
         "reason": None if ps else "ps not found",
         "mode": "poll"},
    ]


def process_event_provider():
    from backends import make_process_provider
    return make_process_provider(lambda: process_list(), name)


def _nonneg_int(value, what):
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise InvalidRequest(f"{what} must be an integer")
    if v < 0:
        raise InvalidRequest(f"{what} must be non-negative")
    return v


def _pid(value):
    return _nonneg_int(value, "pid")


def process_list(pid=None):
    if shutil.which("ps") is None:
        raise BackendUnavailable("ps not found")
    argv = ["ps", "-axo", "pid=,lstart=,comm="]
    if pid is not None:
        argv += ["-p", str(_pid(pid))]
    try:
        rc, out, err = run_bounded(argv)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BackendUnavailable(f"ps failed: {exc}")
    if rc != 0:
        if pid is not None and not out.strip():
            raise LookupError(f"process not found: {pid}")
        raise BackendUnavailable(
            f"ps failed: {err.decode('utf-8', 'replace').strip()}")
    procs = []
    for line in out.decode("utf-8", "replace").splitlines():
        fields = line.split(None, 6)
        if len(fields) < 7:
            continue
        try:
            started = int(time.mktime(time.strptime(
                " ".join(fields[1:6]), _LSTART)))
            pid_val = int(fields[0])
        except ValueError:
            continue
        procs.append({"pid": pid_val,
                      "start_time": started,
                      "name": fields[6]})
    procs.sort(key=lambda p: p["pid"])
    return procs


def process_get(pid, start_time=None):
    pid = _pid(pid)
    if start_time is not None:
        start_time = _nonneg_int(start_time, "start_time")
    for proc in process_list(pid):
        if proc["pid"] == pid:
            if (start_time is not None
                    and proc["start_time"] != start_time):
                raise LookupError("stale pid identity")
            return proc
    raise LookupError(f"process not found: {pid}")


def service_status(name):
    if not _LABEL.match(name or ""):
        raise InvalidRequest("invalid service label")
    lc = _launchctl()
    if not lc:
        raise BackendUnavailable("launchctl not found")
    rc, out, _ = run_bounded(
        [lc, "print", f"gui/{os.getuid()}/{name}"])
    if rc != 0:
        raise LookupError(f"service not found: {name}")
    text = out.decode("utf-8", "replace")
    m = re.search(r"state\s*=\s*(\w+)", text)
    return {"name": name,
            "state": m.group(1).lower() if m else "unknown"}


def _lookup_result(exc):
    """Distinguish stale-identity rejection from a real exit."""
    if "stale" in str(exc):
        return {"ok": False, "status": "rejected",
                "error": str(exc)}
    return {"ok": True, "exit_code": None}


def _wait_poll(pid, start_time, timeout_s):
    """ps liveness poll in <=250ms slices."""
    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"ok": False, "status": "timeout"}
        time.sleep(min(remaining, _WAIT_SLICE_S))
        try:
            process_get(pid, start_time)
        except LookupError as exc:
            return _lookup_result(exc)


def _wait_kqueue(pid, start_time, timeout_s):
    """kqueue EVFILT_PROC/NOTE_EXIT wait, bounded by deadline.

    Re-checks process_get between kevent slices so an exit that
    raced registration is still observed. kqueue always closed.
    """
    try:
        kq = select.kqueue()
    except OSError:
        return _wait_poll(pid, start_time, timeout_s)
    try:
        ev = select.kevent(pid, select.KQ_FILTER_PROC,
                           select.KQ_EV_ADD, select.KQ_NOTE_EXIT)
        ev_error = getattr(select, "KQ_EV_ERROR", 0x4000)
        errs = kq.control([ev], 0)
        if errs and getattr(errs[0], "flags", 0) & ev_error:
            return _wait_poll(pid, start_time, timeout_s)
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"ok": False, "status": "timeout"}
            events = kq.control(None, 1,
                                min(remaining, _WAIT_SLICE_S))
            if events:
                return {"ok": True, "exit_code": None}
            try:
                process_get(pid, start_time)
            except LookupError as exc:
                return _lookup_result(exc)
    finally:
        if kq is not None:
            try:
                kq.close()
            except OSError:
                pass


def wait_process(identity, timeout_s):
    """Wait for exit on a verified pid+start_time identity.

    Identity is verified via process_get BEFORE any wait — stale or
    dead identities reject without blocking. Uses kqueue
    EVFILT_PROC/NOTE_EXIT when select.kqueue is importable, else a
    bounded ps liveness poll.
    """
    if not isinstance(identity, dict):
        raise InvalidRequest("identity must be an object")
    pid = _pid(identity.get("pid"))
    if identity.get("start_time") is None:
        raise InvalidRequest("identity requires start_time")
    start_time = identity.get("start_time")
    try:
        timeout_s = float(timeout_s)
    except (TypeError, ValueError):
        raise InvalidRequest("timeout_s must be a number")
    if not math.isfinite(timeout_s) or timeout_s < 0:
        raise InvalidRequest(
            "timeout_s must be a non-negative finite number")
    try:
        proc = process_get(pid, start_time)
    except LookupError as exc:
        return {"ok": False, "status": "rejected", "error": str(exc)}
    start_time = proc["start_time"]
    if hasattr(select, "kqueue"):
        return _wait_kqueue(pid, start_time, timeout_s)
    return _wait_poll(pid, start_time, timeout_s)


def restart_service(name, *, allowed=None):
    """Never direct: restart only via the privileged broker."""
    raise BackendUnavailable("restart requires privileged broker")
