#!/usr/bin/env python3
"""Browser events daemon — holds the bound browser's websocket open and
buffers CDP/BiDi events continuously (console, errors, network, dialogs,
navigation). This is the full-fidelity counterpart of the JS collector:
subresources, redirects and pre-injection events are all captured.

Same shape as the cu_session daemon: loopback socket, one JSON line per
connection, session-tagged pidfile, idle TTL exit. Requires an explicit
`browser.py bind` first — the daemon attaches only to the bound browser.

Ops ({op, arg?}):
  status | drain | console | errors | requests | nav | dialogs |
  respond accept|dismiss | tabs | pin <targetId> | har [path] | stop
"""
import json
import os
import socket
import sys
import tempfile
import time
import uuid

import cu_browser

EVENTS_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-bevents.json")
IDLE_S = float(os.environ.get("CU_BEVENTS_IDLE", "600"))
AUTO_ACCEPT = ("alert", "beforeunload")


class EventBuffer:
    """Classifies raw ws event frames into drainable buckets."""

    def __init__(self, ws, dialect):
        self.ws = ws
        self.dialect = dialect
        self.endpoint = None
        self.target = None
        self.console = []
        self.errors = []
        self.requests = {}   # requestId -> record
        self.dialogs = []
        self.nav = []

    def pump(self):
        ev = self.ws.events
        while ev:
            self.add(ev.popleft())

    @staticmethod
    def _bidi_rid(p):
        r = p.get("request")
        return r.get("request") if isinstance(r, dict) else r

    def add(self, msg):
        m = msg.get("method")
        p = msg.get("params") or {}
        if m == "Runtime.consoleAPICalled":
            args = " ".join(
                str(a.get("value", a.get("description", "")))
                for a in p.get("args", []))
            self.console.append({"type": p.get("type"),
                                 "text": args[:500],
                                 "ts": p.get("timestamp")})
        elif m == "Runtime.exceptionThrown":
            d = p.get("exceptionDetails", {})
            self.errors.append({"text": d.get("text"),
                                "url": d.get("url"),
                                "line": d.get("lineNumber")})
        elif m in ("Log.entryAdded", "log.entryAdded"):
            e = p.get("entry", p)
            self.console.append({"type": e.get("source", e.get("type")),
                                 "level": e.get("level"),
                                 "text": e.get("text"),
                                 "ts": e.get("timestamp")})
        elif m == "Network.requestWillBeSent":
            r = p.get("request", {})
            self.requests[p.get("requestId")] = {
                "url": r.get("url"), "method": r.get("method"),
                "type": p.get("type"), "ts": p.get("timestamp"),
                "done": False}
        elif m == "Network.responseReceived":
            rec = self.requests.get(p.get("requestId"))
            if rec is not None:
                resp = p.get("response", {})
                rec["status"] = resp.get("status")
                rec["mime"] = resp.get("mimeType")
        elif m in ("Network.loadingFinished", "Network.loadingFailed"):
            rec = self.requests.get(p.get("requestId"))
            if rec is not None:
                rec["done"] = True
                if rec.get("ts"):
                    rec["ms"] = round(
                        (p.get("timestamp", rec["ts"]) - rec["ts"])
                        * 1000, 1)
                if m.endswith("Failed"):
                    rec["error"] = p.get("errorText")
        elif m == "Page.javascriptDialogOpening":
            self._dialog(p)
        elif m == "Page.frameNavigated":
            f = p.get("frame", {})
            self.nav.append({"url": f.get("url"), "ts": time.time()})
        elif m == "network.beforeRequestSent":
            r = p.get("request", {})
            self.requests[self._bidi_rid(p)] = {
                "url": r.get("url") if isinstance(r, dict) else None,
                "method": r.get("method") if isinstance(r, dict) else None,
                "ts": p.get("timestamp"), "done": False}
        elif m in ("network.responseStarted", "network.responseCompleted"):
            rec = self.requests.get(self._bidi_rid(p))
            if rec is not None:
                resp = p.get("response", {})
                if resp.get("status") is not None:
                    rec["status"] = resp.get("status")
                if m.endswith("Completed"):
                    rec["done"] = True
                    if rec.get("ts"):
                        rec["ms"] = round(
                            (p.get("timestamp", rec["ts"]) - rec["ts"])
                            * 1000, 1)
        elif m == "network.fetchError":
            rec = self.requests.get(self._bidi_rid(p))
            if rec is not None:
                rec["done"] = True
                rec["error"] = p.get("errorText")
        elif m == "browsingContext.userPromptOpened":
            self._dialog(p)
        elif m in ("browsingContext.navigationStarted",
                   "browsingContext.load"):
            self.nav.append({"url": p.get("url"), "ts": time.time(),
                             "event": m.rsplit(".", 1)[-1]})

    def _dialog(self, p):
        t = p.get("type")
        if t in AUTO_ACCEPT:
            try:
                self._respond_dialog(True, p)
            except Exception:
                pass
        else:
            self.dialogs.append({"type": t, "message": p.get("message"),
                                 "context": p.get("context"),
                                 "ts": time.time()})

    def _respond_dialog(self, accept, p=None, text=None):
        if self.dialect == "cdp":
            self.ws.call("Page.handleJavaScriptDialog",
                         {"accept": accept})
        else:
            params = {"accept": accept}
            if p and p.get("context"):
                params["context"] = p["context"]
            if text:
                params["userText"] = text
            self.ws.call("browsingContext.handleUserPrompt", params)

    def respond(self, accept, text=None):
        """Answer the oldest pending dialog (confirm/prompt — alert and
        beforeunload are auto-accepted on arrival)."""
        self.pump()
        if not self.dialogs:
            return {"ok": False, "error": "no_dialog"}
        p = self.dialogs.pop(0)
        try:
            self._respond_dialog(accept, p, text)
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": True, "answered": p["type"], "accept": accept}

    def drain(self, bucket=None):
        self.pump()
        if bucket == "requests":
            out = list(self.requests.values())
            self.requests = {}
            return out
        if bucket is None:
            out = {"console": self.console, "errors": self.errors,
                   "requests": list(self.requests.values()),
                   "dialogs": self.dialogs, "nav": self.nav}
            self.console, self.errors = [], []
            self.requests, self.dialogs, self.nav = {}, [], []
            return out
        out = getattr(self, bucket, [])
        setattr(self, bucket, [])
        return out

    def har(self, path):
        self.pump()
        entries = list(self.requests.values())
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": "cu-har-lite/1",
                       "entries": entries}, f)
        return {"ok": True, "entries": len(entries), "path": path}

    def tabs(self):
        if self.dialect == "cdp":
            ep = (self.endpoint or "").rstrip("/")
            try:
                items = cu_browser._http_json(ep + "/json/list") or []
            except Exception:
                return {"ok": False, "error": "targets unreachable"}
            return {"ok": True, "tabs": [
                {"id": t["id"], "title": t.get("title"),
                 "url": t.get("url")}
                for t in items if t.get("type") == "page"]}
        tree = self.ws.call("browsingContext.getTree", {})
        return {"ok": True, "tabs": [
            {"id": c["context"], "url": c.get("url")}
            for c in (tree or {}).get("contexts", [])
            if not c.get("parent")]}


def _write_pidfile(port, session, dialect):
    data = {"pid": os.getpid(), "port": port, "session": session,
            "dialect": dialect, "started": time.time()}
    tmp = EVENTS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, EVENTS_PATH)


def _connect(timeout=10.0):
    """Attach to the bound browser for event capture. Returns
    (ws, dialect, target) or None."""
    b = cu_browser.binding()
    if b is None:
        return None
    ep = b["endpoint"]
    tid = b.get("target_id")
    try:
        found = cu_browser._discover_cdp(ep, timeout, target_id=tid)
        if found:
            ws_url, target = found
            ws = cu_browser._WSClient(ws_url, "cdp", 30.0)
            for dom in ("Page.enable", "Runtime.enable",
                        "Network.enable", "Log.enable"):
                try:
                    ws.call(dom)
                except Exception:
                    pass
            return ws, "cdp", target, ep
        ws, target = cu_browser._connect_bidi(ep, timeout, target_id=tid)
        ws.call("session.subscribe", {"events": [
            "log.entryAdded",
            "network.beforeRequestSent", "network.responseStarted",
            "network.responseCompleted", "network.fetchError",
            "browsingContext.userPromptOpened",
            "browsingContext.navigationStarted",
            "browsingContext.load"]})
        return ws, "bidi", target, ep
    except Exception:
        return None


def daemon_main():
    conn = _connect()
    if conn is None:
        # no binding or unreachable — caller's start times out on pidfile
        return
    ws, dialect, target, ep = conn
    ws.start_reader()
    buf = EventBuffer(ws, dialect)
    buf.endpoint = ep
    buf.target = target

    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(4)
    srv.settimeout(1.0)
    session = uuid.uuid4().hex[:12]
    _write_pidfile(srv.getsockname()[1], session, dialect)
    last = time.time()
    stopping = False
    try:
        while not stopping and time.time() - last < IDLE_S:
            try:
                c, _ = srv.accept()
            except socket.timeout:
                continue
            with c:
                try:
                    c.settimeout(30)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = c.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    env = json.loads(data.decode("utf-8"))
                    if env.get("session") != session:
                        resp = {"ok": False, "error": "stale session"}
                    else:
                        resp = _op(buf, env.get("op") or {},
                                   env.get("arg"))
                        if env.get("op") == "stop":
                            stopping = True
                    c.sendall(json.dumps(resp).encode() + b"\n")
                    last = time.time()
                except Exception:
                    pass
    finally:
        srv.close()
        ws.close()
        try:
            os.remove(EVENTS_PATH)
        except OSError:
            pass


def _op(buf, op, arg):
    if op == "status":
        buf.pump()
        return {"ok": True, "dialect": buf.dialect,
                "target": buf.target,
                "counts": {"console": len(buf.console),
                           "errors": len(buf.errors),
                           "requests": len(buf.requests),
                           "dialogs": len(buf.dialogs),
                           "nav": len(buf.nav)}}
    if op == "drain":
        return {"ok": True, "events": buf.drain()}
    if op in ("console", "errors", "requests", "nav", "dialogs"):
        return {"ok": True, op: buf.drain(op)}
    if op == "respond":
        return buf.respond(accept=(arg != "dismiss"))
    if op == "tabs":
        return buf.tabs()
    if op == "pin":
        return cu_browser.pin_target(arg or None)
    if op == "har":
        path = arg or os.path.join(tempfile.gettempdir(),
                                   f"cu-har-{int(time.time())}.json")
        return buf.har(path)
    if op == "stop":
        return {"ok": True, "stopped": True}
    return {"ok": False, "error": f"unknown op {op!r}"}


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        daemon_main()
