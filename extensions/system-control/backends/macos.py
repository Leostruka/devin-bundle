"""macOS adapter: bounded ps projection; launchctl for named services.

Read-only. External commands use argument arrays, shell=False,
timeout and capped output via backends.run_bounded.
"""

import os
import re
import shutil
import time

from backends import run_bounded
from sc_backend import BackendUnavailable
from sc_contract import InvalidRequest

name = "macos"

_LABEL = re.compile(r"^[A-Za-z0-9_.\-]+$")
_LSTART = "%a %b %d %H:%M:%S %Y"


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
    ]


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
    rc, out, _ = run_bounded(argv)
    if rc != 0:
        raise BackendUnavailable("ps failed")
    procs = []
    for line in out.decode("utf-8", "replace").splitlines():
        fields = line.split(None, 6)
        if len(fields) < 7:
            continue
        try:
            started = int(time.mktime(time.strptime(
                " ".join(fields[1:6]), _LSTART)))
        except ValueError:
            continue
        procs.append({"pid": int(fields[0]),
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
