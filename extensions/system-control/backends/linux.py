"""Linux adapter: /proc/<pid>/stat inventory; systemctl service query.

Read-only. Process start_time is epoch seconds derived from
boot-relative start ticks plus btime.
"""

import math
import os
import re
import select
import shutil
import time

from backends import run_bounded
from sc_backend import BackendUnavailable
from sc_contract import InvalidRequest

name = "linux"

PROC_ROOT = "/proc"
_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_.@\-]+$")
_WAIT_SLICE_S = 0.25


def _boot_time():
    with open(f"{PROC_ROOT}/stat", "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("btime "):
                return int(line.split()[1])
    raise BackendUnavailable("btime missing from /proc/stat")


def _clock_ticks():
    try:
        return os.sysconf("SC_CLK_TCK")
    except (ValueError, OSError, AttributeError):
        return 100


def _systemd():
    return (os.path.isdir("/run/systemd/system")
            and shutil.which("systemctl") is not None)


def _parse_stat(text):
    """Parse /proc/<pid>/stat; comm may contain spaces/parens."""
    rparen = text.rfind(")")
    comm = text[text.index("(") + 1:rparen]
    fields = text[rparen + 2:].split()
    start_ticks = int(fields[19])  # field 22 overall
    return comm, start_ticks


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


def _read_proc(pid, boot_time):
    pid = _pid(pid)
    with open(f"{PROC_ROOT}/{pid}/stat", "r",
              encoding="utf-8") as fh:
        comm, ticks = _parse_stat(fh.read())
    return {"pid": pid,
            "start_time": boot_time + ticks // _clock_ticks(),
            "name": comm}


def capabilities():
    proc = os.path.isdir(PROC_ROOT)
    systemd = _systemd()
    return [
        {"name": "process.observe", "supported": proc,
         "reason": None if proc else "/proc not mounted",
         "mode": "procfs"},
        {"name": "process.wait", "supported": proc,
         "reason": None if proc else "/proc not mounted",
         "mode": ("pidfd" if hasattr(os, "pidfd_open")
                  else "procfs-poll")},
        {"name": "service.observe", "supported": systemd,
         "reason": None if systemd else "systemd not detected",
         "mode": "systemctl"},
        {"name": "service.restart", "supported": False,
         "reason": "broker_required", "mode": None},
        {"name": "events.process", "supported": proc,
         "reason": None if proc else "/proc not mounted",
         "mode": "poll"},
    ]


def process_event_provider():
    from backends import make_process_provider
    return make_process_provider(lambda: process_list(), name)


def process_list(pid=None):
    if not os.path.isdir(PROC_ROOT):
        raise BackendUnavailable("/proc not mounted")
    if pid is not None:
        pid = _pid(pid)
    boot = _boot_time()
    if pid is not None:
        return [_read_proc(pid, boot)]
    out = []
    for entry in os.listdir(PROC_ROOT):
        if entry.isdigit():
            try:
                out.append(_read_proc(entry, boot))
            except (OSError, ValueError, IndexError):
                continue  # process exited mid-scan
    out.sort(key=lambda p: p["pid"])
    return out


def process_get(pid, start_time=None):
    pid = _pid(pid)
    if start_time is not None:
        start_time = _nonneg_int(start_time, "start_time")
    boot = _boot_time()
    try:
        proc = _read_proc(pid, boot)
    except OSError:
        raise LookupError(f"process not found: {pid}")
    except (ValueError, IndexError):
        raise LookupError(f"unreadable stat for pid: {pid}")
    if (start_time is not None
            and proc["start_time"] != start_time):
        raise LookupError("stale pid identity")
    return proc


def service_status(name):
    if not _SERVICE_NAME.match(name or ""):
        raise InvalidRequest("invalid service name")
    if not _systemd():
        raise BackendUnavailable("systemd not detected")
    rc, out, _ = run_bounded([
        "systemctl", "show", name,
        "--property=ActiveState", "--value"])
    if rc != 0:
        raise LookupError(f"service not found: {name}")
    return {"name": name,
            "state": out.decode("utf-8", "replace").strip()
            or "unknown"}


def _fd_ready(fd, timeout_s):
    """Readable-or-error probe; a bad fd counts as ready (exited)."""
    try:
        r, _, x = select.select([fd], [], [fd], timeout_s)
    except (OSError, TypeError, ValueError):
        return True
    return bool(r or x)


def _wait_pidfd(fd, timeout_s):
    """Bounded wait on a pidfd; waitid si_status when available."""
    deadline = time.monotonic() + timeout_s
    can_waitid = (hasattr(os, "waitid") and hasattr(os, "P_PIDFD")
                  and hasattr(os, "WEXITED"))
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"ok": False, "status": "timeout"}
        if not _fd_ready(fd, min(remaining, _WAIT_SLICE_S)):
            continue
        if can_waitid:
            try:
                info = os.waitid(os.P_PIDFD, fd, os.WEXITED)
            except OSError:
                # Kernels 5.3-5.4 lack waitid(P_PIDFD); a ready fd
                # already proves the process exited.
                return {"ok": True, "exit_code": None}
            if info is None:
                continue
            return {"ok": True,
                    "exit_code": getattr(info, "si_status", None)}
        return {"ok": True, "exit_code": None}


def _wait_poll(pid, start_time, timeout_s):
    """procfs liveness poll in <=250ms slices."""
    deadline = time.monotonic() + timeout_s
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return {"ok": False, "status": "timeout"}
        time.sleep(min(remaining, _WAIT_SLICE_S))
        try:
            process_get(pid, start_time)
        except LookupError as exc:
            if "stale" in str(exc):
                return {"ok": False, "status": "rejected",
                        "error": str(exc)}
            return {"ok": True, "exit_code": None}


def wait_process(identity, timeout_s):
    """Wait for exit on a verified pid+start_time identity.

    Identity is verified via process_get BEFORE any wait — stale or
    dead identities reject without blocking. Prefers os.pidfd_open
    when present (waitid si_status when available, else select);
    falls back to a procfs liveness poll. The fd is always closed.
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
    pidfd_open = getattr(os, "pidfd_open", None)
    if pidfd_open is not None:
        fd = None
        try:
            fd = pidfd_open(pid)
        except (AttributeError, OSError):
            fd = None
        if fd is not None:
            try:
                # The pidfd pins the pid; re-reading stat detects a
                # reaped+reused pid between verify and open.
                if process_get(pid)["start_time"] != start_time:
                    return {"ok": False, "status": "rejected",
                            "error": "stale pid identity"}
            except LookupError as exc:
                return {"ok": False, "status": "rejected",
                        "error": str(exc)}
            try:
                return _wait_pidfd(fd, timeout_s)
            finally:
                try:
                    os.close(fd)
                except OSError:
                    pass
    return _wait_poll(pid, start_time, timeout_s)


def restart_service(name, *, allowed=None):
    """Never direct: restart only via the T10 privileged broker."""
    raise BackendUnavailable("restart requires privileged broker")
