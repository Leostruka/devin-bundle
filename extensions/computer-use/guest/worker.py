#!/usr/bin/env python3
"""Guest-side worker — runs INSIDE the approved image, opens
/dev/virtio-ports/devin.cu, answers host requests on the pipe.

Opt-in: profiles without it keep working over QMP with reduced,
explicit capabilities. Everything here produces untrusted data — the
host side (cu_guest) size-caps and schema-checks every reply.

Pure parts (build_handshake, handle_request) are unit-testable on the
host; serve() only runs in the guest.
"""
import json
import sys

PROTOCOL_VERSION = 1

METHODS = frozenset({"ping", "text.insert", "clipboard.get",
                     "clipboard.set", "probe.state", "exec.run",
                     "dom.navigate", "dom.eval", "uia.snapshot"})


def _boot_id():
    try:
        with open("/proc/sys/kernel/random/boot_id") as f:
            return f.read().strip()
    except OSError:
        return "unknown"


def build_handshake(session):
    """Announce protocol + session reality. `interactive` False (locked
    desktop, session 0, VT without a compositor) means interactive caps
    must be reported False — the host strips them anyway."""
    return {"version": PROTOCOL_VERSION,
            "boot_id": _boot_id(),
            "interactive": bool(session.get("interactive")),
            "session_id": session.get("session_id"),
            "capabilities": dict(session.get("capabilities") or {})}


def handle_request(req, caps):
    """One request -> one reply dict. Unknown methods and calls without
    the capability are refused — the worker is a service, not a shell."""
    rid = req.get("id")
    method = req.get("method")
    if method not in METHODS:
        return {"id": rid, "ok": False,
                "error": f"method:{method}"}
    cap_for = {"text.insert": "text_insert",
               "clipboard.get": "clipboard",
               "clipboard.set": "clipboard",
               "probe.state": "probe", "exec.run": "exec",
               "dom.navigate": "dom", "dom.eval": "dom",
               "uia.snapshot": "uia"}
    cap = cap_for.get(method)
    if cap and not (caps or {}).get(cap):
        return {"id": rid, "ok": False,
                "error": f"capability:{cap}"}
    if method == "ping":
        return {"id": rid, "ok": True, "pong": True,
                "boot_id": _boot_id()}
    # Real effectors (text/clipboard/probe) are guest-platform code —
    # dispatched here in later slices.
    return {"id": rid, "ok": False,
            "error": f"not_implemented:{method}"}


def serve(port_path):
    """Line-oriented loop on the virtio-serial port. Handshake first —
    a host that doesn't like our session closes the pipe."""
    import os
    fd = os.open(port_path, os.O_RDWR | os.O_NOCTTY)
    r, w = os.fdopen(fd, "rb"), os.fdopen(os.dup(fd), "wb")
    session = {"interactive": os.environ.get("DISPLAY") is not None,
               "session_id": None,
               "capabilities": {}}
    w.write(json.dumps({"hello": build_handshake(session)}).encode()
            + b"\n")
    w.flush()
    caps = session["capabilities"]
    for raw in r:
        try:
            req = json.loads(raw)
            resp = handle_request(req, caps)
        except Exception as exc:
            resp = {"ok": False, "error": f"{type(exc).__name__}:{exc}"}
        w.write(json.dumps(resp).encode() + b"\n")
        w.flush()


if __name__ == "__main__":
    serve(sys.argv[1] if len(sys.argv) > 1
          else "/dev/virtio-ports/devin.cu")
