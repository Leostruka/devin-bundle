#!/usr/bin/env python3
"""Guest worker channel — virtio-serial port `devin.cu`, owned by the
env supervisor, SEPARATE from QMP. The guest worker is opt-in code
inside the approved image; everything it sends is untrusted data:
size-capped, schema-checked, and capability-consistent with session
state.

- validate_handshake(reply) -> caps dict: claimed caps incompatible
  with the declared session (locked / session 0 / non-interactive) are
  stripped, never trusted.
- GuestChannel: JSON-line request/reply with reply-size cap, method
  allowlist, deadline, and boot_id continuity checks.
"""
import json
import threading

PROTOCOL_VERSION = 1

# Capabilities the catalog knows about; anything a guest claims outside
# this set is dropped silently.
CAP_CATALOG = frozenset(
    {"text_insert", "clipboard", "uia", "dom", "exec", "probe"})

# Caps that are meaningless without an interactive graphical session.
INTERACTIVE_REQUIRED = frozenset({"text_insert", "clipboard", "uia",
                                  "dom"})

METHODS = frozenset({"ping", "text.insert", "clipboard.get",
                     "clipboard.set", "probe.state"})


class GuestProtocolError(Exception):
    """Malformed/oversized/untrusted reply from the guest worker."""


class GuestTimeout(Exception):
    """Worker did not answer within the deadline."""


def validate_handshake(reply):
    """Handshake reply -> effective capability dict. A guest may claim
    anything; we keep only catalog caps AND drop interactive-only caps
    when the session is not interactive."""
    if not isinstance(reply, dict):
        raise GuestProtocolError("handshake:not_a_mapping")
    if reply.get("version") != PROTOCOL_VERSION:
        raise GuestProtocolError(
            f"handshake:version:{reply.get('version')}")
    claimed = reply.get("capabilities") or {}
    if not isinstance(claimed, dict):
        raise GuestProtocolError("handshake:capabilities")
    interactive = bool(reply.get("interactive"))
    caps = {}
    for name in CAP_CATALOG:
        ok = bool(claimed.get(name))
        if ok and name in INTERACTIVE_REQUIRED and not interactive:
            ok = False
        caps[name] = ok
    return caps


def check_operation(op, capabilities):
    """Pure gate: is `op` allowed under this capability set?
    Returns {"allowed": bool, "reason"?: str}."""
    _CAP_FOR = {"text.insert": "text_insert",
                "clipboard.get": "clipboard",
                "clipboard.set": "clipboard",
                "uia.snapshot": "uia",
                "dom.eval": "dom",
                "exec.run": "exec",
                "probe.state": "probe"}
    cap = _CAP_FOR.get(op)
    if cap is None:
        return {"allowed": False, "reason": "unknown_operation"}
    if not (capabilities or {}).get(cap):
        return {"allowed": False, "reason": "capability_unavailable"}
    return {"allowed": True}


class GuestChannel:
    """One request -> one reply over the supervisor-owned pipe pair.
    reader/writer are file-like (BytesIO in tests, real pipe ends in
    the supervisor)."""

    def __init__(self, reader, writer, timeout_s=5.0, max_reply=65536,
                 methods=None, boot_id=None):
        self._r = reader
        self._w = writer
        self.timeout_s = timeout_s
        self.max_reply = max_reply
        self.methods = METHODS if methods is None else methods
        self.boot_id = boot_id
        self._seq = 0

    def call(self, method, params=None):
        if method not in self.methods:
            raise GuestProtocolError(f"method:{method}")
        self._seq += 1
        rid = f"gw-{self._seq}"
        line = json.dumps({"id": rid, "method": method,
                           "params": params or {}}).encode() + b"\n"
        self._w.write(line)
        if hasattr(self._w, "flush"):
            self._w.flush()
        raw = self._read_line()
        if len(raw) > self.max_reply:
            raise GuestProtocolError(
                f"size:{len(raw)}>{self.max_reply}")
        try:
            reply = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GuestProtocolError(f"json:{exc}") from exc
        if not isinstance(reply, dict):
            raise GuestProtocolError("reply:not_a_mapping")
        if self.boot_id is not None and \
                reply.get("boot_id") is not None and \
                reply["boot_id"] != self.boot_id:
            raise GuestProtocolError(
                f"boot:{reply['boot_id']}!={self.boot_id}")
        return reply

    def _read_line(self):
        out = {}

        def _rd():
            try:
                out["line"] = self._r.readline()
            except Exception:
                out["line"] = b""

        t = threading.Thread(target=_rd, daemon=True)
        t.start()
        t.join(self.timeout_s)
        if t.is_alive():
            raise GuestTimeout(f"no reply within {self.timeout_s}s")
        line = out.get("line") or b""
        if not line:
            raise GuestProtocolError("eof")
        return line
