"""Linux adapter: /proc/<pid>/stat inventory; systemctl service query.

Read-only. Process start_time is epoch seconds derived from
boot-relative start ticks plus btime.
"""

import os
import re
import shutil

from backends import run_bounded
from sc_backend import BackendUnavailable
from sc_contract import InvalidRequest

name = "linux"

_PROC = "/proc"
_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_.@\-]+$")


def _boot_time():
    with open("/proc/stat", "r", encoding="utf-8") as fh:
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
    with open(f"{_PROC}/{pid}/stat", "r",
              encoding="utf-8") as fh:
        comm, ticks = _parse_stat(fh.read())
    return {"pid": pid,
            "start_time": boot_time + int(ticks / _clock_ticks()),
            "name": comm}


def capabilities():
    proc = os.path.isdir(_PROC)
    systemd = _systemd()
    return [
        {"name": "process.observe", "supported": proc,
         "reason": None if proc else "/proc not mounted",
         "mode": "procfs"},
        {"name": "service.observe", "supported": systemd,
         "reason": None if systemd else "systemd not detected",
         "mode": "systemctl"},
        {"name": "events.process", "supported": proc,
         "reason": None if proc else "/proc not mounted",
         "mode": "poll"},
    ]


def process_event_provider():
    from backends import make_process_provider
    return make_process_provider(lambda: process_list(), name)


def process_list(pid=None):
    if not os.path.isdir(_PROC):
        raise BackendUnavailable("/proc not mounted")
    if pid is not None:
        pid = _pid(pid)
    boot = _boot_time()
    if pid is not None:
        return [_read_proc(pid, boot)]
    out = []
    for entry in os.listdir(_PROC):
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
    try:
        proc = _read_proc(pid, _boot_time())
    except OSError:
        raise LookupError(f"process not found: {pid}")
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
