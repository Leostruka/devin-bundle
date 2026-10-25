"""Detached background task runner with durable trace store.

Long-running computer-use operations (recordings, automation scripts) run in
detached subprocesses so the caller (CLI or MCP) can keep working. Each task
gets a trace directory under .devin/scratch/cu_tasks/<trace_id>/ with:

    status.json   lifecycle: queued -> running -> done | failed | stopped
    stdout.log    captured stdout
    stderr.log    captured stderr

Adapted from ARTEMIS's task runner + status.json pattern; stdlib-only.

CLI:
    python cu_taskrunner.py start -- <command...>   -> prints trace_id
    python cu_taskrunner.py status <trace_id>
    python cu_taskrunner.py list
    python cu_taskrunner.py stop <trace_id>
"""

import json
import os
import signal
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
STORE = os.path.join(ROOT, ".devin", "scratch", "cu_tasks")


def _trace_dir(trace_id):
    return os.path.join(STORE, trace_id)


def _read_status(trace_id):
    try:
        with open(os.path.join(_trace_dir(trace_id), "status.json"),
                  encoding="utf-8") as f:
            return json.load(f)
    except OSError:
        return None


def _write_status(trace_id, st):
    path = os.path.join(_trace_dir(trace_id), "status.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, path)


def start(command):
    """Spawn `command` detached; return trace_id."""
    trace_id = uuid.uuid4().hex[:12]
    tdir = _trace_dir(trace_id)
    os.makedirs(tdir, exist_ok=True)
    st = {"trace_id": trace_id, "state": "queued", "command": command,
          "pid": None, "started": time.time(), "ended": None,
          "returncode": None}
    _write_status(trace_id, st)

    out = open(os.path.join(tdir, "stdout.log"), "w", encoding="utf-8")
    err = open(os.path.join(tdir, "stderr.log"), "w", encoding="utf-8")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen(
        command, stdout=out, stderr=err, cwd=ROOT,
        creationflags=flags, start_new_session=(os.name != "nt"))
    st["pid"], st["state"] = proc.pid, "running"
    _write_status(trace_id, st)

    watcher = subprocess.Popen(
        [sys.executable, __file__, "_watch", trace_id, str(proc.pid)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags, start_new_session=(os.name != "nt"))
    watcher.poll()
    return trace_id


def status(trace_id):
    """Read status; refresh state if the pid exited without a watcher."""
    st = _read_status(trace_id)
    if not st:
        return None
    if st["state"] == "running" and st.get("pid"):
        if not _pid_alive(st["pid"]):
            st["state"] = "done" if st.get("returncode") in (None, 0) else "failed"
            st["ended"] = st.get("ended") or time.time()
            _write_status(trace_id, st)
    return st


def _pid_alive(pid):
    if os.name == "nt":
        import ctypes
        r = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if r:
            ctypes.windll.kernel32.CloseHandle(r)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def stop(trace_id):
    st = status(trace_id)
    if not st:
        return {"error": "no such trace_id"}
    if st["state"] != "running":
        return {"state": st["state"]}
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(st["pid"])],
                           capture_output=True)
        else:
            os.killpg(st["pid"], signal.SIGTERM)
    except OSError:
        pass
    st["state"], st["ended"] = "stopped", time.time()
    _write_status(trace_id, st)
    return st


def list_tasks():
    if not os.path.isdir(STORE):
        return []
    out = []
    for tid in sorted(os.listdir(STORE)):
        st = status(tid)
        if st:
            out.append({k: st.get(k) for k in
                        ("trace_id", "state", "started", "ended", "returncode")})
    return out


def _watch(trace_id, pid):
    """Watcher child: wait on the target pid, then finalize status."""
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x100000, False, int(pid))
        code = None
        if h:
            ctypes.windll.kernel32.WaitForSingleObject(h, 0xFFFFFFFF)
            buf = ctypes.c_ulong(0)
            ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(buf))
            code = buf.value
            ctypes.windll.kernel32.CloseHandle(h)
        rc = code
    else:
        rc = None
        try:
            while _pid_alive(int(pid)):
                time.sleep(0.5)
        except OSError:
            pass
    st = _read_status(trace_id) or {}
    if st.get("state") == "stopped":
        return
    st["state"] = "done" if rc in (None, 0) else "failed"
    st["returncode"] = rc
    st["ended"] = time.time()
    _write_status(trace_id, st)
    _notify_done(trace_id, st)


def _notify_done(trace_id, st):
    """Fire the composite notifier on terminal state; never raises."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "cu_notify", os.path.join(HERE, "cu_notify.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cmd = " ".join(st.get("command") or [])[:80]
        mod.notify(f"cu task {st['state']}: {trace_id}", cmd,
                   level="error" if st["state"] == "failed" else "info")
    except Exception:
        pass


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    if args[0] == "_watch":
        _watch(args[1], args[2])
        return 0
    if args[0] == "start" and "--" in args:
        cmd = args[args.index("--") + 1:]
        if not cmd:
            print("start requires a command after --", file=sys.stderr)
            return 2
        print(start(cmd))
        return 0
    if args[0] == "status" and len(args) == 2:
        st = status(args[1])
        print(json.dumps(st, indent=1) if st else "no such trace_id")
        return 0 if st else 1
    if args[0] == "list":
        print(json.dumps(list_tasks(), indent=1))
        return 0
    if args[0] == "stop" and len(args) == 2:
        print(json.dumps(stop(args[1]), indent=1))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
