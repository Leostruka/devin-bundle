#!/usr/bin/env python3
"""agent-desktop perception/action backend (issue #427, eval #423).

Wraps the vercel-labs `agent-desktop` CLI (Apache-2.0) — OS
accessibility-tree (UIA/AX/AT-SPI) observe/act without screenshots.
Every command prints one JSON envelope {"ok","data"|"error"}; refs like
@snapshot_id:eN stay valid until the next snapshot of that app.

This module ships two layers:

- AgentDesktop: primitive CLI client (snapshot/find/click/...)
- DesktopBackend: cu_backend.Backend-shaped adapter (issue #429,
  option A - tree-native). observe() returns an observation dict
  {"tree", "meta"}, NOT the (img, meta) pixel-frame tuple the QMP/ADB
  backends return; frame-pipeline consumers (mouse.py, record.py,
  screenshot.py) must not receive a DesktopBackend target. Tree
  consumers branch on backend.kind == "agent-desktop". Canvas/Electron
  apps without AX coverage keep the screenshot() escape hatch.

The integration decision is documented in
.devin/research/2026-11-09-agent-desktop-eval.md.

Resolution order for the binary: $CU_AGENT_DESKTOP, PATH,
`npx -y agent-desktop` (downloads on first use - offline hosts should
set CU_AGENT_DESKTOP or preinstall).

Security: snapshots can contain private desktop content. Callers must
not upload tree JSON to public logs; --headed physical input stays
behind the caller's existing confirm gates.
"""
import json
import os
import shutil
import subprocess
import time


class AgentDesktopError(Exception):
    """CLI transport, protocol or policy failure."""


class AgentDesktopUnavailable(AgentDesktopError):
    """Binary not resolvable on this host."""


def _npx_prefix():
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    return [npx, "-y", "agent-desktop"] if npx else None


def resolve_binary():
    """Return argv prefix that invokes agent-desktop, or None."""
    env = os.environ.get("CU_AGENT_DESKTOP")
    if env:
        return [env]
    exe = (shutil.which("agent-desktop")
           or shutil.which("agent-desktop.cmd"))
    if exe:
        return [exe]
    return _npx_prefix()


class AgentDesktop:
    """Thin CLI client. `run` injectable for tests:
    run(argv_list, timeout_s) -> CompletedProcess-like."""

    def __init__(self, binary=None, run=None, timeout=30):
        self._bin = binary if binary is not None else resolve_binary()
        self._run = run or self._default_run
        self._timeout = timeout
        self._snapshot_id = None

    @staticmethod
    def _default_run(argv, timeout_s):
        return subprocess.run(argv, capture_output=True, text=True,
                              encoding="utf-8", errors="replace",
                              timeout=timeout_s,
                              creationflags=getattr(
                                  subprocess, "CREATE_NO_WINDOW", 0))

    # -- transport ---------------------------------------------------------

    def _call(self, *args, timeout=None):
        if self._bin is None:
            raise AgentDesktopUnavailable(
                "agent-desktop not found - set CU_AGENT_DESKTOP or "
                "install: npm i -g agent-desktop")
        argv = [str(a) for a in (*self._bin, *args)]
        try:
            p = self._run(argv, timeout or self._timeout)
        except subprocess.TimeoutExpired:
            raise AgentDesktopError(f"timeout:{' '.join(args[:2])}")
        out = (p.stdout or "").strip()
        # npm/npx noise precedes the JSON envelope - find first '{'
        i = out.find("{")
        if i < 0:
            raise AgentDesktopError(
                f"no_json_envelope:{(p.stderr or out)[:200]}")
        try:
            env = json.loads(out[i:])
        except json.JSONDecodeError as e:
            raise AgentDesktopError(f"bad_envelope:{e}")
        if not env.get("ok"):
            err = env.get("error") or {}
            raise AgentDesktopError(
                f"{err.get('code','?')}:{err.get('message','?')[:200]}")
        data = env.get("data")
        if isinstance(data, dict) and data.get("snapshot_id"):
            self._snapshot_id = data["snapshot_id"]
        return data if data is not None else {}

    # -- probes ------------------------------------------------------------

    def status(self):
        return self._call("status")

    def available(self):
        try:
            s = self.status()
            return s.get("platform") in ("windows", "macos", "linux")
        except AgentDesktopError:
            return False

    # -- observe -----------------------------------------------------------

    def list_apps(self, app=None):
        args = ["list-apps"] + (["--app", app] if app else [])
        return self._call(*args)

    def list_windows(self, app=None):
        args = ["list-windows"] + (["--app", app] if app else [])
        return self._call(*args)

    def snapshot(self, app=None, interactive=True, compact=True,
                 skeleton=False, root=None):
        args = ["snapshot"]
        if skeleton:
            args.append("--skeleton")
        if interactive and not skeleton:
            args.append("-i")
        if compact:
            args.append("--compact")
        if app:
            args += ["--app", app]
        if root:
            args += ["--root", root]
        return self._call(*args)

    def find(self, query, app=None):
        args = ["find", query]
        if app:
            args += ["--app", app]
        return self._call(*args)

    def get(self, ref, prop="text"):
        return self._call("get", ref, "--property", prop)

    def is_state(self, ref, state="visible"):
        return self._call("is", ref, "--property", state)

    # -- act ---------------------------------------------------------------

    def _act(self, verb, ref, *extra):
        return self._call(verb, ref, *extra)

    def click(self, ref):
        return self._act("click", ref)

    def double_click(self, ref, headed=False):
        args = ["double-click", ref] + (["--headed"] if headed else [])
        return self._call(*args)

    def right_click(self, ref, headed=False):
        args = ["right-click", ref] + (["--headed"] if headed else [])
        return self._call(*args)

    def type_text(self, ref, text):
        return self._call("type", ref, text)

    def set_value(self, ref, value):
        return self._call("set-value", ref, value)

    def clear(self, ref):
        return self._act("clear", ref)

    def focus(self, ref):
        return self._act("focus", ref)

    def select(self, ref, option):
        return self._call("select", ref, option)

    def toggle(self, ref):
        return self._act("toggle", ref)

    def check(self, ref):
        return self._act("check", ref)

    def uncheck(self, ref):
        return self._act("uncheck", ref)

    def expand(self, ref):
        return self._act("expand", ref)

    def collapse(self, ref):
        return self._act("collapse", ref)

    def scroll(self, ref, direction="down", amount=None):
        args = ["scroll", ref, "--direction", direction]
        if amount is not None:
            args += ["--amount", str(amount)]
        return self._call(*args)

    def scroll_to(self, ref):
        return self._act("scroll-to", ref)

    def press(self, combo):
        return self._call("press", combo)

    def hover(self, ref, headed=True):
        args = ["hover", ref] + (["--headed"] if headed else [])
        return self._call(*args)

    def launch(self, app, activate=False):
        args = ["launch", app]
        if activate:
            args.append("--activate")
        return self._call(*args)

    def focus_window(self, app):
        return self._call("focus-window", "--app", app)

    def screenshot(self, app=None, output=None):
        args = ["screenshot"]
        if app:
            args += ["--app", app]
        if output:
            args.append(output)
        return self._call(*args)

    # -- observe-act-verify loop -------------------------------------------

    def verify(self, predicate, attempts=3, delay=0.4, **snap_kw):
        """Re-snapshot until predicate(tree_data) is truthy.

        predicate receives the snapshot `data` dict (tree + refs).
        Returns (ok, last_data). Bounded retries; no infinite poll.
        """
        import time
        last = None
        for _ in range(max(1, attempts)):
            last = self.snapshot(**snap_kw)
            try:
                if predicate(last):
                    return True, last
            except Exception:
                pass  # fail-soft: probe fallback
            time.sleep(delay)
        return False, last


# -- Backend-contract adapter (issue #429, option A: tree-native) ---------


def _op_click(ad, a):
    return ad.click(a["ref"])


def _op_double_click(ad, a):
    return ad.double_click(a["ref"], headed=bool(a.get("headed")))


def _op_right_click(ad, a):
    return ad.right_click(a["ref"], headed=bool(a.get("headed")))


def _op_type(ad, a):
    return ad.type_text(a["ref"], a.get("text", ""))


def _op_set_value(ad, a):
    return ad.set_value(a["ref"], a.get("value", ""))


def _op_press(ad, a):
    return ad.press(a.get("combo", ""))


def _op_scroll(ad, a):
    return ad.scroll(a["ref"], a.get("direction", "down"),
                     a.get("amount"))


_DISPATCH_OPS = {
    "click": _op_click, "double_click": _op_double_click,
    "right_click": _op_right_click, "type": _op_type,
    "set_value": _op_set_value, "clear": lambda ad, a: ad.clear(a["ref"]),
    "focus": lambda ad, a: ad.focus(a["ref"]),
    "select": lambda ad, a: ad.select(a["ref"], a.get("option", "")),
    "toggle": lambda ad, a: ad.toggle(a["ref"]),
    "check": lambda ad, a: ad.check(a["ref"]),
    "uncheck": lambda ad, a: ad.uncheck(a["ref"]),
    "expand": lambda ad, a: ad.expand(a["ref"]),
    "collapse": lambda ad, a: ad.collapse(a["ref"]),
    "scroll": _op_scroll,
    "scroll_to": lambda ad, a: ad.scroll_to(a["ref"]),
    "press": _op_press,
    "hover": lambda ad, a: ad.hover(a["ref"],
                                    headed=bool(a.get("headed", True))),
    "launch": lambda ad, a: ad.launch(a.get("app", ""),
                                      activate=bool(a.get("activate"))),
    "focus_window": lambda ad, a: ad.focus_window(a.get("app", "")),
    "screenshot": lambda ad, a: ad.screenshot(
        a.get("app"), a.get("output")),
}


class DesktopBackend:
    """cu_backend.Backend-shaped adapter over AgentDesktop.

    Stateless CLI wrapper: no owned input state to release, close() is
    a no-op. observe() returns {"tree", "meta"} - the tree-native
    contract; meta carries monotonic_ns for ordering checks. Physical
    input stays behind the caller's --headed/confirm gates."""

    kind = "agent-desktop"

    def __init__(self, client=None):
        self._ad = client or AgentDesktop()

    def capabilities(self):
        try:
            s = self._ad.status()
        except AgentDesktopError as e:
            return {"backend": self.kind, "available": False,
                    "error": str(e)}
        return {"backend": self.kind, "available": True,
                "platform": s.get("platform"),
                "surfaces": s.get("surfaces", []),
                "observe": "tree", "verbs": sorted(_DISPATCH_OPS)}

    def observe(self, options=None):
        """Snapshot -> {"tree": data, "meta": {...}}.

        Divergence from QMP/ADB (img, meta): the primary observation is
        the AX element tree. `options.app` scopes the snapshot."""
        opts = options or {}
        data = self._ad.snapshot(app=opts.get("app"))
        return {"tree": data,
                "meta": {"backend": self.kind,
                         "snapshot_id": data.get("snapshot_id")
                         or self._ad._snapshot_id,
                         "instance_id": None,
                         "monotonic_ns": time.monotonic_ns()}}

    def dispatch(self, action):
        """action {"op": <verb>, ...params} -> normalized result dict.

        'dispatched' means the CLI accepted the action - verification
        is a separate observe()+predicate step, same as cu_backend's
        ack/verify split."""
        if not isinstance(action, dict):
            return {"ok": False, "status": "rejected",
                    "error": "action_not_dict"}
        op = action.get("op")
        fn = _DISPATCH_OPS.get(op)
        if fn is None:
            return {"ok": False, "status": "rejected",
                    "error": f"unknown_op:{op}"}
        try:
            result = fn(self._ad, action)
        except AgentDesktopError as e:
            return {"ok": False, "status": "error", "op": op,
                    "error": str(e)}
        return {"ok": True, "status": "dispatched", "op": op,
                "result": result}

    def status(self):
        return self._ad.status()

    def release_all(self, timeout_s=5):
        return {"released": [], "backend": self.kind}

    def release_owned(self):
        return self.release_all()

    def close(self):
        pass
