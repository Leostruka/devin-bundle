"""Windows adapter: CIM JSON process snapshot; sc.exe service query.

Read-only. External commands use argument arrays, shell=False,
timeout and capped output via backends.run_bounded.
"""

import json
import re
import shutil
from datetime import datetime, timezone

from backends import run_bounded
from sc_backend import BackendUnavailable
from sc_contract import InvalidRequest

name = "windows"

_SERVICE_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
_CIM_DATE = re.compile(r"/Date\((\d+)\)/")


def _powershell():
    return shutil.which("pwsh") or shutil.which("powershell")


def _cim_epoch(value):
    """CIM CreationDate: ISO-8601 under pwsh 7, /Date(ms)/ under 5.1."""
    text = str(value or "")
    m = _CIM_DATE.search(text)
    if m:
        return int(m.group(1)) // 1000
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError:
        raise BackendUnavailable(
            f"unparseable CreationDate: {value!r}")


def capabilities():
    ps = _powershell()
    sc = shutil.which("sc")
    return [
        {"name": "process.observe", "supported": bool(ps),
         "reason": None if ps else "powershell not found",
         "mode": "subprocess"},
        {"name": "service.observe", "supported": bool(sc),
         "reason": None if sc else "sc.exe not found",
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
    ps = _powershell()
    if not ps:
        raise BackendUnavailable("powershell not found")
    where = (f"| Where-Object {{ $_.ProcessId -eq {_pid(pid)} }}"
             if pid is not None else "")
    rc, out, _ = run_bounded([
        ps, "-NoProfile", "-NonInteractive", "-Command",
        "Get-CimInstance Win32_Process " + where +
        " | Select-Object ProcessId, CreationDate, Name"
        " | ConvertTo-Json -Compress"])
    if rc != 0:
        raise BackendUnavailable("Get-CimInstance failed")
    data = json.loads(out.decode("utf-8", "replace") or "[]")
    if isinstance(data, dict):
        data = [data]
    return [
        {"pid": int(p["ProcessId"]),
         "start_time": _cim_epoch(p.get("CreationDate")),
         "name": p.get("Name")}
        for p in data
    ]


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
    if not _SERVICE_NAME.match(name or ""):
        raise InvalidRequest("invalid service name")
    if not shutil.which("sc"):
        raise BackendUnavailable("sc.exe not found")
    rc, out, _ = run_bounded(["sc.exe", "query", name])
    text = out.decode("utf-8", "replace")
    if rc != 0:
        raise LookupError(f"service not found: {name}")
    m = re.search(r"STATE\s*:\s*\d+\s+(\w+)", text)
    return {"name": name,
            "state": m.group(1).lower() if m else "unknown"}
