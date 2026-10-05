"""cu_events.py — event-driven hint refresher (P1+P11 integration).

A resident daemon: out-of-context SetWinEventHook on a pump thread ->
hwnd/event filter -> per-hwnd debounce -> UIA hint re-enum -> per-hwnd
sidecar. Agents read the pre-computed sidecar (~0ms) instead of paying
the cold `screenshot --hints` (~591ms) on every turn.

    cu_events.py start --hwnd 123456 [--hwnd 789]   # detached daemon
    cu_events.py watch --hwnd 123456
    cu_events.py hints --hwnd 123456                # cached hint set
    cu_events.py drain                            # matched events log
    cu_events.py status | stop

Safety: WINEVENT_OUTOFCONTEXT = notifications only, never injects into
foreign processes (P1 research); loopback-only socket like cu_session.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
EVENTS_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-events.json")
HINT_FMT = os.path.join(tempfile.gettempdir(), "devin-cu-evhints-%d.json")
IDLE_S = float(os.environ.get("CU_EVENTS_IDLE", "600"))
DEBOUNCE_S = float(os.environ.get("CU_EVENTS_DEBOUNCE", "0.15"))
EVENT_BUF = 200

EVENT_SYSTEM_FOREGROUND = 0x0003
EVENT_OBJECT_DESTROY = 0x8001
EVENT_OBJECT_SHOW = 0x8002
EVENT_OBJECT_LOCATIONCHANGE = 0x800B
EVENT_OBJECT_NAMECHANGE = 0x800C
_EVENT_LO = EVENT_SYSTEM_FOREGROUND
_EVENT_HI = EVENT_OBJECT_NAMECHANGE
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002
WM_QUIT = 0x0012
OBJID_WINDOW = 0
REFRESH_EVENTS = {0x8000, EVENT_OBJECT_SHOW, EVENT_OBJECT_LOCATIONCHANGE,
                  EVENT_OBJECT_NAMECHANGE, EVENT_SYSTEM_FOREGROUND}
if sys.platform == "win32":
    WINEVENTPROC = ctypes.WINFUNCTYPE(
        None, wt.HANDLE, wt.DWORD, wt.HWND, wt.LONG, wt.LONG,
        wt.DWORD, wt.DWORD)
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
else:
    WINEVENTPROC = None
    user32 = None
    kernel32 = None


def _hints_path(hwnd):
    return HINT_FMT % int(hwnd)


def _write_hints(hwnd, elements, window, generation):
    data = {"hwnd": hwnd, "generation": generation,
            "ts": time.time(), "window": window,
            "elements": elements or [], "count": len(elements or [])}
    tmp = _hints_path(hwnd) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _hints_path(hwnd))


def _read_hints(hwnd):
    try:
        with open(_hints_path(hwnd), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _enum_hwnd(hwnd, timeout=6.0):
    """UIA clickable enum for one hwnd on a COM thread (cu_hints
    internals keep object lifetimes inside one apartment)."""
    if sys.platform != "win32":
        return [], None
    sys.path.insert(0, HERE)
    import cu_hints
    q = queue.Queue(maxsize=1)

    def work():
        q.put(cu_hints._enum_impl("events", hwnd=hwnd))

    t = threading.Thread(target=lambda: cu_hints._com_thread(work),
                         daemon=True)
    t.start()
    try:
        return q.get(timeout=timeout)
    except queue.Empty:
        return [], None


class _HookPump(threading.Thread):
    """Hook install + GetMessage loop must share one thread (P1)."""

    def __init__(self, events_q):
        super().__init__(daemon=True)
        self.q = events_q
        self.ready = threading.Event()
        self.tid = None
        self.installed = 0

    def run(self):
        self.tid = kernel32.GetCurrentThreadId()

        def _cb(hook, event, hwnd, id_obj, id_child, tid, ms):
            if id_obj == OBJID_WINDOW:
                self.q.put((time.perf_counter(), event, int(hwnd or 0)))

        self._cb = WINEVENTPROC(_cb)  # keep alive for hook lifetime
        h = user32.SetWinEventHook(_EVENT_LO, _EVENT_HI, None, self._cb,
                                   0, 0, WINEVENT_OUTOFCONTEXT
                                   | WINEVENT_SKIPOWNPROCESS)
        self.installed = 1 if h else 0
        self.ready.set()
        msg = wt.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if h:
            user32.UnhookWinEvent(h)

    def stop(self):
        if self.tid:
            user32.PostThreadMessageW(self.tid, WM_QUIT, 0, 0)


class _Refresher:
    """Debounce: an event burst marks the hwnd dirty; the re-enum runs
    once after DEBOUNCE_S of quiet — a move burst = one refresh."""

    def __init__(self):
        self.q = queue.Queue()
        self.watched = {}          # hwnd -> generation counter
        self.dirty = {}            # hwnd -> last event ts
        self.buf = []              # matched events for drain
        self.hook_ok = 0
        self.stats = {"seen": 0, "skipped": 0, "refreshed": 0,
                      "enum_fail": 0}
        self._stop = threading.Event()

    def handle(self, ts, event, hwnd):
        self.stats["seen"] += 1
        if hwnd in self.watched and event in REFRESH_EVENTS:
            self.dirty[hwnd] = ts + DEBOUNCE_S
            self.buf.append({"t": round(ts, 3), "event": hex(event),
                             "hwnd": hwnd})
            if len(self.buf) > EVENT_BUF:
                self.buf.pop(0)
        else:
            self.stats["skipped"] += 1

    def _refresh_due(self):
        now = time.perf_counter()
        for hwnd, due in list(self.dirty.items()):
            if due <= now:
                self.dirty.pop(hwnd)
                els, win = _enum_hwnd(hwnd)
                if els or win:
                    self.watched[hwnd] += 1
                    _write_hints(hwnd, els, win, self.watched[hwnd])
                    self.stats["refreshed"] += 1
                else:
                    self.stats["enum_fail"] += 1

    def run(self):
        while not self._stop.is_set():
            try:
                e = self.q.get(timeout=DEBOUNCE_S / 2)
                self.handle(*e)
            except queue.Empty:
                pass
            self._refresh_due()


def _daemon_info():
    try:
        with open(EVENTS_PATH, encoding="utf-8") as f:
            d = json.load(f)
        os.kill(d["pid"], 0) if sys.platform != "win32" else None
        return d
    except Exception:
        return None


def _request(payload, timeout=15.0):
    """One loopback JSON-line round trip; validates session."""
    import socket
    d = _daemon_info()
    if not d:
        return {"ok": False, "error": "events daemon not running"}
    payload = dict(payload, session=d["session"])
    try:
        conn = socket.create_connection(("127.0.0.1", d["port"]),
                                        timeout=timeout)
        conn.sendall(json.dumps(payload).encode() + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = conn.recv(65536)
            if not chunk:
                break
            data += chunk
        conn.close()
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": f"daemon request failed: {e}"}


def daemon_main(hwnds):
    """Loopback daemon: hook pump -> debounced refresh -> sidecars."""
    if sys.platform != "win32":
        print(json.dumps({"ok": False, "error": "windows only"}))
        return
    import socket
    import cu_dpi
    cu_dpi.set_dpi_awareness()

    ref = _Refresher()
    for h in hwnds:
        ref.watched[int(h)] = 0
        ref.dirty[int(h)] = time.perf_counter()  # prime sidecar
    pump = _HookPump(ref.q)
    pump.start()
    pump.ready.wait(5)
    ref.hook_ok = pump.installed

    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    srv.settimeout(0.25)
    session = uuid.uuid4().hex[:12]
    with open(EVENTS_PATH + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(), "port": srv.getsockname()[1],
                   "session": session, "started": time.time()}, f)
    os.replace(EVENTS_PATH + ".tmp", EVENTS_PATH)

    last = time.time()

    def tick():
        try:
            e = ref.q.get(timeout=0.05)
            ref.handle(*e)
        except queue.Empty:
            pass
        ref._refresh_due()

    def op(cmd):
        nonlocal last
        last = time.time()
        a = cmd.get("op")
        h = cmd.get("hwnd")
        if a == "status":
            return {"ok": True, "hook": ref.hook_ok,
                    "watched": dict(ref.watched), "stats": ref.stats,
                    "buf": len(ref.buf)}
        if a == "drain":
            out, ref.buf = list(ref.buf), []
            return {"ok": True, "events": out}
        if a == "watch" and h:
            h = int(h)
            if h not in ref.watched:
                ref.watched[h] = 0
                els, win = _enum_hwnd(h)
                if els or win:
                    ref.watched[h] = 1
                    _write_hints(h, els, win, 1)
            return {"ok": True, "watched": h,
                    "generation": ref.watched[h]}
        if a == "unwatch" and h:
            ref.watched.pop(int(h), None)
            return {"ok": True}
        if a == "hints" and h:
            return {"ok": True, "hints": _read_hints(int(h))}
        if a == "stop":
            return {"ok": True, "bye": True}
        return {"ok": False, "error": f"unknown op {a!r}"}

    try:
        while time.time() - last < IDLE_S:
            tick()
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            with conn:
                try:
                    conn.settimeout(30)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    env = json.loads(data.decode("utf-8"))
                    if env.get("session") != session:
                        resp = {"ok": False, "error": "stale session"}
                    else:
                        resp = op(env.get("cmd") or {})
                    conn.sendall(json.dumps(resp).encode() + b"\n")
                    if resp.get("bye"):
                        raise SystemExit
                except SystemExit:
                    raise
                except Exception:
                    pass
    except SystemExit:
        pass
    finally:
        srv.close()
        pump.stop()
        try:
            os.remove(EVENTS_PATH)
        except OSError:
            pass


def _spawn(hwnds):
    argv = [sys.executable, os.path.abspath(__file__), "--daemon"]
    for h in hwnds:
        argv += ["--hwnd", str(h)]
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(argv, creationflags=flags,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     stdin=subprocess.DEVNULL, close_fds=True)
    dl = time.time() + 10
    while time.time() < dl:
        d = _daemon_info()
        if d:
            return d
        time.sleep(0.1)
    return None


def main():
    p = argparse.ArgumentParser(prog="cu_events.py")
    p.add_argument("cmd", nargs="?", default="status",
                   choices=["start", "stop", "status", "watch",
                            "unwatch", "hints", "drain"])
    p.add_argument("--hwnd", type=int, action="append", default=[],
                   help="window to watch (repeatable)")
    p.add_argument("--daemon", action="store_true", help=argparse.SUPPRESS)
    args = p.parse_args()

    if args.daemon:
        daemon_main(args.hwnd)
        return
    if args.cmd == "start":
        if _daemon_info():
            print(json.dumps({"ok": True, "already": True,
                              **_daemon_info()}))
            return
        d = _spawn(args.hwnd)
        print(json.dumps({"ok": bool(d), **(d or
                          {"error": "daemon failed to start"})}))
        return
    if args.cmd == "stop":
        print(json.dumps(_request({"cmd": {"op": "stop"}})))
        return
    print(json.dumps(_request({"cmd": {"op": args.cmd,
                                       "hwnd": args.hwnd[0]
                                       if args.hwnd else None}})))


if __name__ == "__main__":
    main()
