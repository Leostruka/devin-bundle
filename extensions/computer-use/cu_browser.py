#!/usr/bin/env python3
"""Authorized-browser binding contract.

DOM/ARIA/CDP targeting is only ever allowed against a browser the caller
explicitly bound for THIS automation session. Nothing here launches a
browser, enables remote debugging, or attaches to a foreign session.

Binding lives in <temp>/devin-cu-browser.json with the same session+TTL
rules as the hint sidecar: a new session_id or an expired binding rejects.

    bind(endpoint, pid)   -> writes the binding file (explicit, opt-in)
    unbind()              -> removes it
    binding()             -> dict | None
    check(hwnd)           -> (allowed: bool, reason: str|None)
    viewport_to_desktop() -> CSS px -> desktop px (never implicit)

The CDP client itself stays a seam: `_cdp_client()` returns None unless an
approved driver module is importable — honest "unavailable", never silent.
"""
import json
import os
import tempfile
import time
from pathlib import Path

import cu_hints

BINDING_TTL_S = float(os.environ.get("CU_BROWSER_TTL", "600"))
_BINDING_OVERRIDE = None  # tests inject a path here

_COLLECTOR_JS = r"""
(()=>{if(window.__cu_collector)return'already';window.__cu_collector=1;
window.__cu_log=[];window.__cu_errors=[];window.__cu_net=[];
const cap=(a,x)=>{a.push(x);if(a.length>500)a.splice(0,a.length-500)};
const txt=v=>{try{return typeof v==='string'?v:JSON.stringify(v)}catch(e){return String(v)}};
for(const l of['log','info','warn','error','debug']){const o=console[l].bind(console);
console[l]=(...a)=>{cap(window.__cu_log,{ts:Date.now(),level:l,
text:a.map(txt).join(' ').slice(0,500)});o(...a)}}
addEventListener('error',e=>cap(window.__cu_errors,{ts:Date.now(),
text:String(e.message||e.error),src:String(e.filename||''),line:e.lineno||0}));
addEventListener('unhandledrejection',e=>cap(window.__cu_errors,{ts:Date.now(),
text:'unhandledrejection: '+txt(e.reason)}));
const F=window.fetch.bind(window);
window.fetch=(...a)=>{const t0=Date.now();
const url=txt(a[0]&&a[0].url||a[0]);const method=(a[1]&&a[1].method)||'GET';
return F(...a).then(r=>{cap(window.__cu_net,{ts:t0,kind:'fetch',method,url,
status:r.status,ms:Date.now()-t0});return r},
e=>{cap(window.__cu_net,{ts:t0,kind:'fetch',method,url,error:txt(e),
ms:Date.now()-t0});throw e})};
const X=window.XMLHttpRequest.prototype,oo=X.open.bind(X);
X.open=function(m,u,...r){this.__cu={t0:0,method:m,url:String(u)};return oo(m,u,...r)};
const os=X.send.bind(X);
X.send=function(...a){if(this.__cu){this.__cu.t0=Date.now();
this.addEventListener('loadend',()=>cap(window.__cu_net,{ts:this.__cu.t0,
kind:'xhr',method:this.__cu.method,url:this.__cu.url,status:this.status,
ms:Date.now()-this.__cu.t0}))}return os(...a)};
window.__cu_drain=n=>{const a=window[n]||[];const out=a.slice();a.length=0;return out};
return'installed'})()
"""

_FIND_JS = r"""
(()=>{
const K=%s,V=%s,N=%s,out=[];
const IMP={A:'link',BUTTON:'button',INPUT:'textbox',SELECT:'combobox',
TEXTAREA:'textbox',IMG:'img',H1:'heading',H2:'heading',H3:'heading',
H4:'heading',H5:'heading',H6:'heading',UL:'list',OL:'list',LI:'listitem',
NAV:'navigation',MAIN:'main',HEADER:'banner',FOOTER:'contentinfo',
TABLE:'table',FORM:'form',DIALOG:'dialog'};
const nm=e=>((e.getAttribute('aria-label')||'')+' '+(e.innerText||e.value||'')
+' '+(e.alt||'')+' '+(e.title||'')+' '+(e.placeholder||'')).toLowerCase();
const role=e=>e.getAttribute('role')||IMP[e.tagName]||'';
const ok=e=>{if(K==='role')return role(e)===V;
if(K==='text')return (e.innerText||'').toLowerCase().includes(V.toLowerCase());
if(K==='label')return e.tagName==='LABEL'&&
(e.innerText||'').toLowerCase().includes(V.toLowerCase());
if(K==='placeholder')return (e.placeholder||'').toLowerCase().includes(V.toLowerCase());
if(K==='alt')return (e.alt||'').toLowerCase().includes(V.toLowerCase());
if(K==='testid')return (e.getAttribute('data-testid')||'')===V;
if(K==='title')return (e.title||'').toLowerCase().includes(V.toLowerCase());
return false};
const all=document.querySelectorAll('*');
for(const e of all){if(out.length>=50)break;if(!ok(e))continue;
if(N&&!nm(e).includes(N.toLowerCase()))continue;
const r=e.getBoundingClientRect();
out.push({tag:e.tagName,role:role(e),
name:(e.getAttribute('aria-label')||e.innerText||'').slice(0,120),
text:(e.innerText||'').slice(0,120),
bounds:[r.left,r.top,r.width,r.height]})}
return out})()
"""


def boundaries(text):
    """Wrap page-extracted text as untrusted content — provenance cue for
    downstream prompts, not a security boundary."""
    import uuid
    n = uuid.uuid4().hex[:8]
    return (f"--- BEGIN UNTRUSTED PAGE CONTENT {n} ---\n{text}\n"
            f"--- END UNTRUSTED PAGE CONTENT {n} ---")


def pin_target(target):
    """Pin the binding to one page target/context (or unpin with None).
    `_cdp_client` attaches to the pinned target; foreign targets reject."""
    b = binding()
    if b is None:
        return {"ok": False, "error": "no_binding"}
    if target is None:
        b.pop("target_id", None)
    else:
        b["target_id"] = target
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(b, f)
    os.replace(tmp, _path())
    return {"ok": True}


def _path():
    if _BINDING_OVERRIDE:
        return _BINDING_OVERRIDE
    return os.path.join(tempfile.gettempdir(), "devin-cu-browser.json")


def bind(endpoint, pid):
    """Record an explicitly-authorized browser for this session.

    endpoint: e.g. "http://127.0.0.1:9222" — loopback only.
    pid:      OS process id of the browser to constrain targeting to.
    """
    if not isinstance(endpoint, str) or not endpoint.startswith(
            ("http://127.0.0.1", "http://localhost", "https://127.0.0.1",
             "https://localhost")):
        return {"ok": False, "error": "endpoint must be loopback (127.0.0.1/localhost)"}
    if not isinstance(pid, int) or pid <= 0:
        return {"ok": False, "error": "pid must be a positive int"}
    data = {"endpoint": endpoint, "pid": pid,
            "session_id": cu_hints.session_id(),
            "created_at": time.time()}
    tmp = _path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, _path())
    return {"ok": True, "binding": data}


def unbind():
    try:
        os.remove(_path())
    except OSError:
        pass
    return {"ok": True}


def binding(scope=None):
    """Current binding dict if valid for this session, else None.
    scope=(env_id, instance_id, session_id) reads the env-namespaced
    binding written by bind_remote."""
    if scope is not None:
        import cu_target
        p = cu_target.state_path(cu_target.runtime_root(), *scope,
                                 "browser-binding.json")
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception:
            return None
        env_id, instance_id, _ = scope
        import cu_guest
        if not cu_guest.binding_matches(data, env_id, instance_id):
            return None
        if time.time() - data.get("created_at", 0) > BINDING_TTL_S:
            return None
        return data
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if data.get("session_id") != cu_hints.session_id():
        return None
    if time.time() - data.get("created_at", 0) > BINDING_TTL_S:
        return None
    return data


def bind_remote(env_id, instance_id, extra=None):
    """Binding for a guest-side browser — lives under the env's private
    state namespace, stamped with (env_id, instance_id). The endpoint
    is the guest's own loopback reached via the worker channel; no CDP
    port is ever published on the host."""
    import cu_target
    data = {"env_id": env_id, "instance_id": instance_id,
            "kind": "guest",
            "session_id": cu_hints.session_id(),
            "created_at": time.time()}
    if extra:
        data.update(extra)
    p = cu_target.state_path(cu_target.runtime_root(), env_id,
                             instance_id, "default",
                             "browser-binding.json")
    cu_target.ensure_private_dir(Path(p).parent)
    tmp = str(p) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, p)
    return {"ok": True, "binding": data, "path": str(p)}


def _hwnd_pid(hwnd):
    """pid owning hwnd; 0 if unavailable. Separated for test injection."""
    if os.name != "nt":
        return 0
    import ctypes
    pid = ctypes.c_ulong(0)
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def check(hwnd):
    """May we semantically target the element at hwnd?
    Returns (allowed, reason). reason None on success, else typed code —
    callers must NOT use DOM/CDP when reason is set."""
    b = binding()
    if b is None:
        return False, "no_binding"
    pid = _hwnd_pid(hwnd)
    if not pid:
        return False, "unknown_owner"
    if pid != b["pid"]:
        return False, "foreign_process"
    return True, None


class _WSClient:
    """Thin JSON-RPC over one websocket. dialect: "cdp" (Chromium) or
    "bidi" (Firefox/Zen — WebDriver BiDi). suppress_origin avoids the
    remote-allow-origins handshake check on both engines.

    Event frames ({"method": ...}) are never discarded: they land in
    `self.events` (bounded deque) in both modes. `start_reader()` moves
    recv to a dedicated thread so events stream continuously instead of
    only between calls."""

    def __init__(self, url, dialect, timeout=10.0):
        import collections
        import queue as _q  # noqa: F401 (used by call in reader mode)
        import threading
        import websocket
        self.dialect = dialect
        self.timeout = timeout
        self.ws = websocket.create_connection(
            url, timeout=timeout, suppress_origin=True)
        self._id = 0
        self.context = None  # bidi browsingContext / cdp target page
        self.events = collections.deque(maxlen=2000)
        self._pending = {}
        self._reader_t = None
        self._send_lock = threading.Lock()
        self._eof = False

    def _result(self, msg):
        if self.dialect == "bidi":
            if msg.get("type") == "error":
                raise RuntimeError(
                    f"{msg.get('error')}: {msg.get('message')}")
            return msg.get("result")
        if "error" in msg:
            raise RuntimeError(str(msg["error"]))
        return msg.get("result")

    def call(self, method, params=None, timeout=None):
        import queue as _q
        if self._eof:
            raise RuntimeError("ws closed")
        self._id += 1
        mid = self._id
        if self._reader_t is None:
            self.ws.send(json.dumps(
                {"id": mid, "method": method, "params": params or {}}))
            while True:
                msg = json.loads(self.ws.recv())
                if msg.get("id") != mid:
                    if msg.get("method"):
                        self.events.append(msg)
                    continue
                return self._result(msg)
        q = _q.Queue()
        self._pending[mid] = q
        with self._send_lock:
            self.ws.send(json.dumps(
                {"id": mid, "method": method, "params": params or {}}))
        try:
            msg = q.get(timeout=timeout or self.timeout)
        except _q.Empty:
            self._pending.pop(mid, None)
            raise RuntimeError(f"ws call timeout: {method}")
        if msg is None or msg.get("__eof__"):
            raise RuntimeError("ws closed")
        return self._result(msg)

    def start_reader(self):
        """Dedicated recv thread: responses -> pending callers, events ->
        self.events. After this, call() never touches recv directly."""
        import threading
        if self._reader_t is not None:
            return
        self._reader_t = threading.Thread(
            target=self._recv_loop, daemon=True)
        self._reader_t.start()

    def _recv_loop(self):
        while True:
            try:
                msg = json.loads(self.ws.recv())
            except Exception:
                self._eof = True
                for q in list(self._pending.values()):
                    q.put({"__eof__": True})
                self._pending.clear()
                return
            mid = msg.get("id")
            if mid is not None and mid in self._pending:
                self._pending.pop(mid).put(msg)
            elif msg.get("method"):
                self.events.append(msg)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def _http_json(url, timeout=5.0):
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _bidi_value(v):
    """Unwrap a BiDi remote value to a plain Python value (recursive for
    arrays/objects)."""
    if not isinstance(v, dict):
        return v
    t = v.get("type")
    if t == "undefined":
        return None
    val = v.get("value")
    if t == "array" and isinstance(val, list):
        return [_bidi_value(x) for x in val]
    if t == "object" and isinstance(val, list):
        return {k: _bidi_value(x) for k, x in val}
    return val if "value" in v else v


class BrowserClient:
    """Bound-browser semantic client: evaluate / click / screenshot over
    CDP or BiDi. Coordinates are CSS px in viewport space — callers convert
    with viewport_to_desktop for physical input paths."""

    def __init__(self, ws, dialect, target):
        self._ws = ws
        self.dialect = dialect
        self.target = target  # page target id (cdp) | browsingContext (bidi)
        self.endpoint = None  # set by _cdp_client (tabs via /json/list)

    def evaluate(self, expression):
        if self.dialect == "cdp":
            r = self._ws.call("Runtime.evaluate", {
                "expression": expression, "returnByValue": True})
            return (r.get("result") or {}).get("value")
        r = self._ws.call("script.evaluate", {
            "expression": expression,
            "target": {"context": self.target},
            "awaitPromise": False})
        return _bidi_value((r or {}).get("result"))

    def click(self, x, y):
        """Semantic click at CSS-px viewport coords."""
        if self.dialect == "cdp":
            for t in ("mousePressed", "mouseReleased"):
                self._ws.call("Input.dispatchMouseEvent", {
                    "type": t, "x": x, "y": y,
                    "button": "left", "clickCount": 1})
            return
        self._ws.call("input.performActions", {
            "context": self.target,
            "actions": [{"type": "pointer", "id": "m",
                         "parameters": {"pointerType": "mouse"},
                         "actions": [
                             {"type": "pointerMove", "x": int(x),
                              "y": int(y), "origin": "viewport"},
                             {"type": "pointerDown", "button": 0},
                             {"type": "pointerUp", "button": 0}]}]})

    def navigate(self, url):
        if self.dialect == "cdp":
            return self._ws.call("Page.navigate", {"url": url})
        return self._ws.call("browsingContext.navigate",
                             {"context": self.target, "url": url,
                              "wait": "complete"})

    def screenshot(self):
        """Viewport PNG, base64."""
        if self.dialect == "cdp":
            return self._ws.call("Page.captureScreenshot",
                                 {"format": "png"}).get("data")
        return self._ws.call("browsingContext.captureScreenshot",
                             {"context": self.target}).get("data")

    def evaluate_in(self, expression, context=None):
        """evaluate scoped to a browsing context (BiDi). CDP evaluates on
        the attached page target only — nested frames need their own
        session; callers get an explicit error rather than silent bleed."""
        if context and context != self.target:
            if self.dialect == "cdp":
                raise RuntimeError(
                    "cdp_context: frame-scoped eval needs a frame session")
            r = self._ws.call("script.evaluate", {
                "expression": expression,
                "target": {"context": context},
                "awaitPromise": False})
            return _bidi_value((r or {}).get("result"))
        return self.evaluate(expression)

    def contexts(self):
        """Top-level + nested browsing contexts (BiDi). CDP: just the page."""
        if self.dialect == "cdp":
            return [self.target]
        tree = self._ws.call("browsingContext.getTree", {})
        return [c["context"] for c in (tree or {}).get("contexts", [])]

    def actionable_at(self, cx, cy, bounds_css=None):
        """Is a DOM element the real hit target at CSS point (cx,cy)?
        Returns dict ok/reason. bounds_css [l,t,w,h] = expected element
        rect — when given, a returned element not intersecting it means the
        target is COVERED."""
        # Deep hit-test: elementFromPoint then pierce same-origin iframes
        # (coords re-based to the frame viewport) and OPEN shadow roots —
        # closed roots stay opaque by design. When expected bounds are
        # known, the effective (deepest) hit must match them: a mismatch
        # means the target is covered.
        js = ("(()=>{let el=document.elementFromPoint(%f,%f);"
              "if(!el)return{ok:false,reason:'no_element'};"
              "let g=0;"
              "while(el.tagName==='IFRAME'&&el.contentDocument&&g++<8){"
              "const fr=el.getBoundingClientRect();"
              "el=el.contentDocument.elementFromPoint(%f-fr.left,%f-fr.top);"
              "if(!el)return{ok:false,reason:'no_element'}}"
              "g=0;"
              "while(el.shadowRoot&&g++<10){"
              "const n=el.shadowRoot.elementFromPoint(%f,%f);"
              "if(!n)break;el=n}"
              % (cx, cy, cx, cy, cx, cy))
        if bounds_css:
            l, t, w, h = bounds_css
            js += (
                "const B=[%f,%f,%f,%f];"
                "const r0=el.getBoundingClientRect();"
                "if(!(r0.right>B[0]+1&&r0.left<B[0]+B[2]-1&&"
                "r0.bottom>B[1]+1&&r0.top<B[1]+B[3]-1&&"
                "r0.width<=B[2]*1.6&&r0.height<=B[3]*1.6))"
                "return{ok:false,reason:'covered'};"
                % (l, t, w, h))
        js += (
            "const r=el.getBoundingClientRect();"
            "if(r.width<1||r.height<1)return{ok:false,reason:'zero_size'};"
            "if(el.disabled||el.getAttribute('aria-disabled')==='true')"
            "return{ok:false,reason:'disabled'};"
            "if(el.tagName==='CANVAS'||el.tagName==='VIDEO')"
            "return{ok:false,reason:'canvas',tag:el.tagName};"
            "return{ok:true,tag:el.tagName}})()")
        r = self.evaluate(js)
        return r or {"ok": False, "reason": "no_element"}

    def wait_actionable(self, cx, cy, bounds_css=None, timeout=3.0,
                        interval=0.15):
        """Poll actionable_at until ok or deadline — returns the last
        result (callers read .ok/.reason)."""
        import time as _t
        deadline = _t.monotonic() + timeout
        last = {"ok": False, "reason": "timeout"}
        while _t.monotonic() < deadline:
            last = self.actionable_at(cx, cy, bounds_css)
            if last.get("ok") or last.get("reason") in (
                    "disabled", "canvas", "zero_size"):
                return last
            _t.sleep(interval)
        return last

    def insert_text(self, text):
        """Insert text at the focused element (CDP) or send per-char key
        events (BiDi — no insertText equivalent)."""
        if self.dialect == "cdp":
            return self._ws.call("Input.insertText", {"text": text})
        actions = []
        for ch in text:
            actions.append({"type": "keyDown", "value": ch})
            actions.append({"type": "keyUp", "value": ch})
        return self._ws.call("input.performActions", {
            "context": self.target,
            "actions": [{"type": "key", "id": "kb", "actions": actions}]})

    # -- observation (agent-browser port, tier 1) ---------------------------

    def install_collector(self):
        """Inject the console/error/network JS collector. Preload-script on
        both dialects so the buffers survive navigation; live evaluate covers
        the already-loaded page."""
        if self.dialect == "cdp":
            self._ws.call("Page.addScriptToEvaluateOnNewDocument",
                          {"source": _COLLECTOR_JS})
        else:
            self._ws.call("script.addPreloadScript", {
                "functionDeclaration": _COLLECTOR_JS,
                "target": {"contexts": [self.target]}})
        r = self.evaluate(_COLLECTOR_JS)
        return {"ok": True, "installed": r}

    def collector(self, kind, clear=False):
        """Read (or drain) a collector buffer: log | errors | net."""
        name = "__cu_" + {"log": "log", "errors": "errors",
                          "net": "net"}.get(kind, kind)
        if clear:
            expr = (f"window.__cu_drain?window.__cu_drain('{name}')"
                    f":(window.{name}||[])")
        else:
            expr = f"(window.{name}||[])"
        return self.evaluate(expr) or []

    def wait(self, fn=None, text=None, url=None, selector=None,
             state="visible", timeout=10.0, interval=0.25):
        """Poll a page condition until met or deadline. The probe always
        answers 'target present/matched?' — hidden waits for falsy."""
        if fn:
            probe = f"!!({fn})"
        elif text:
            probe = ("!!(document.body&&document.body.innerText.includes("
                     + json.dumps(text) + "))")
        elif url:
            import re
            pat = "^" + re.escape(url).replace(r"\*", ".*") + "$"
            probe = ("new RegExp(" + json.dumps(pat)
                     + ").test(location.href)")
        elif selector:
            probe = "!!document.querySelector(" + json.dumps(selector) + ")"
        else:
            return {"ok": False, "reason": "no_condition"}
        want = (state != "hidden")
        import time as _t
        deadline = _t.monotonic() + timeout
        while True:
            try:
                v = bool(self.evaluate(probe))
            except Exception:
                v = False
            if v == want:
                return {"ok": True, "matched": probe[:80]}
            if _t.monotonic() >= deadline:
                return {"ok": False, "reason": "timeout"}
            _t.sleep(interval)

    def cookies(self):
        """Cookies for the attached context (CDP Network / BiDi storage)."""
        if self.dialect == "cdp":
            r = self._ws.call("Network.getCookies")
            return (r or {}).get("cookies", [])
        r = self._ws.call("storage.getCookies", {
            "partition": {"type": "context", "context": self.target}})
        return (r or {}).get("cookies", [])

    def storage(self, area, op="all", key=None, value=None):
        """localStorage/sessionStorage ops via evaluate."""
        store = "localStorage" if area == "local" else "sessionStorage"
        if op == "get":
            expr = store + ".getItem(" + json.dumps(key) + ")"
        elif op == "set":
            expr = ("(" + store + ".setItem(" + json.dumps(key) + ","
                    + json.dumps(value) + "),true)")
        elif op == "remove":
            expr = "(" + store + ".removeItem(" + json.dumps(key) + "),true)"
        elif op == "clear":
            expr = "(" + store + ".clear(),true)"
        elif op == "keys":
            expr = "Object.keys(" + store + ")"
        else:
            expr = "Object.entries(" + store + ")"
        return self.evaluate(expr)

    def find(self, kind, value, name=None):
        """Semantic DOM search: role|text|label|placeholder|alt|testid|title.
        role covers explicit + implicit ARIA roles for common tags; `name`
        filters by accessible-name approximation. Max 50 hits, CSS-px bounds."""
        js = _FIND_JS % (json.dumps(kind), json.dumps(value),
                         json.dumps(name))
        return self.evaluate(js) or []

    def tabs(self):
        """Page targets (CDP /json/list) or top-level contexts (BiDi)."""
        if self.dialect == "cdp":
            ep = (self.endpoint or "").rstrip("/")
            try:
                items = _http_json(ep + "/json/list") or []
            except Exception:
                return []
            return [{"id": t["id"], "title": t.get("title"),
                     "url": t.get("url")}
                    for t in items if t.get("type") == "page"]
        tree = self._ws.call("browsingContext.getTree", {})
        return [{"id": c["context"], "url": c.get("url")}
                for c in (tree or {}).get("contexts", [])
                if not c.get("parent")]

    def close(self):
        self._ws.close()


def _discover_cdp(endpoint, timeout, target_id=None):
    """Chromium: /json/list -> page target ws url. A pinned target_id wins;
    otherwise the first page."""
    try:
        pages = _http_json(endpoint.rstrip("/") + "/json/list", timeout)
    except Exception:
        return None
    for t in pages:
        if (t.get("type") == "page" and t.get("webSocketDebuggerUrl")
                and (target_id is None or t.get("id") == target_id)):
            return t["webSocketDebuggerUrl"], t.get("id")
    return None


def _connect_bidi(endpoint, timeout, target_id=None):
    """Gecko: ws endpoint at /session; session.new then getTree. Fresh
    profiles can expose stale 0x0 top-level contexts — probe innerWidth and
    pick the first painted one; fallback to the last context. A pinned
    target_id wins over all heuristics."""
    host = endpoint.rstrip("/").split("://", 1)[-1]
    ws = _WSClient(f"ws://{host}/session", "bidi", timeout)
    ws.call("session.new", {"capabilities": {}})
    tree = ws.call("browsingContext.getTree", {})
    ctxs = [c["context"] for c in (tree or {}).get("contexts", [])
            if not c.get("parent")]
    if not ctxs:
        ws.close()
        raise RuntimeError("bidi: no browsing context")
    if target_id in ctxs:
        return ws, target_id
    pick = ctxs[-1]
    for ctx in ctxs:
        try:
            r = ws.call("script.evaluate", {
                "expression": "innerWidth",
                "target": {"context": ctx}, "awaitPromise": False})
            if _bidi_value((r or {}).get("result")):
                pick = ctx
                break
        except Exception:
            continue
    return ws, pick


def _cdp_client(timeout=10.0):
    """Attach to the bound browser. Returns BrowserClient or None when
    unbound / driver missing / endpoint unreachable. Never raises."""
    b = binding()
    if b is None:
        return None
    try:
        import websocket  # noqa: F401
    except ImportError:
        return None
    ep = b["endpoint"]
    tid = b.get("target_id")
    try:
        found = _discover_cdp(ep, timeout, target_id=tid)
        if found:
            ws_url, tid = found
            ws = _WSClient(ws_url, "cdp", timeout)
            for dom in ("Page.enable", "Runtime.enable"):
                try:
                    ws.call(dom)
                except Exception:
                    pass
            cli = BrowserClient(ws, "cdp", tid)
            cli.endpoint = ep
            return cli
        ws, ctx = _connect_bidi(ep, timeout, target_id=tid)
        cli = BrowserClient(ws, "bidi", ctx)
        cli.endpoint = ep
        return cli
    except Exception:
        return None


def viewport_to_desktop(css_x, css_y, viewport_origin, dpr=1.0):
    """CSS px -> desktop physical px. Callers MUST supply the viewport's
    top-left corner in desktop px and the device pixel ratio; mixing the two
    spaces without conversion is the bug this signature exists to prevent."""
    ox, oy = viewport_origin
    return round(css_x * dpr + ox), round(css_y * dpr + oy)


def _client_origin(hwnd):
    """Desktop px of hwnd's client-area (viewport) top-left corner."""
    if os.name != "nt" or not hwnd:
        return (0, 0)
    import ctypes
    import ctypes.wintypes
    pt = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def desktop_to_viewport(dx, dy, hwnd, dpr=1.0):
    """Desktop physical px -> CSS px for the bound browser's viewport."""
    ox, oy = _client_origin(hwnd)
    return (dx - ox) / dpr, (dy - oy) / dpr


def dom_action(hwnd, x, y, op, text=None, timeout=10.0, enabled=True,
               wait=2.0, bounds_px=None):
    """Route a semantic browser action for the element at desktop (x, y)
    inside window hwnd. Returns (result, reason); reason None on success —
    callers must NOT fall back to physical input on browser_* rejections.
    Actionability gate: the element under the point must exist, be visible,
    enabled and uncovered; covered/no_element get a `wait` window."""
    ok, reason = check(hwnd)
    if not ok:
        return None, f"browser_{reason}"
    if not enabled:
        return None, "browser_disabled"
    cli = _cdp_client(timeout=timeout)
    if cli is None:
        return None, "browser_unavailable"
    try:
        dpr = cli.evaluate("devicePixelRatio") or 1.0
        cx, cy = desktop_to_viewport(x, y, hwnd, dpr)
        bcss = None
        if bounds_px:  # sidecar bounds are [l, t, w, h] in desktop px
            l, t = desktop_to_viewport(bounds_px[0], bounds_px[1], hwnd, dpr)
            bcss = [l, t, bounds_px[2] / dpr, bounds_px[3] / dpr]
        a = cli.wait_actionable(cx, cy, bounds_css=bcss, timeout=wait)
        if not a.get("ok"):
            return None, "browser_actionable_" + (a.get("reason") or
                                                  "unknown")
        if op == "click":
            cli.click(cx, cy)
            return {"backend": "dom", "dialect": cli.dialect,
                    "css": [round(cx, 1), round(cy, 1)]}, None
        if op == "type":
            cli.click(cx, cy)  # focus the field first
            cli.insert_text(text or "")
            return {"backend": "dom", "dialect": cli.dialect,
                    "typed": len(text or "")}, None
        return None, f"unknown_op:{op}"
    except Exception as e:
        return None, f"dom_{type(e).__name__}: {e}"
    finally:
        cli.close()
