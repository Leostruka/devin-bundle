#!/usr/bin/env python3
"""QMP client: newline-delimited JSON over an injected reader/writer pair.

call(command, args) -> dict — the {"return": ...} payload.
  - Correlates on "id": async {"event": ...} messages and foreign ids
    never satisfy a pending call.
  - {"return": {}} is transport success ONLY — never evidence of a UI
    effect (QMP cannot confirm what the guest did with input).
  - Commands are checked against an internal allowlist split into
    query/observe/input/lifecycle; anything else raises before a byte is
    written. There is no public passthrough — see public_operation_allowed.

Transport errors are typed: QmpError (protocol/not_allowed), QmpRefused
({"error": ...} response), QmpEOF (stream closed), QmpTimeout (deadline).
Deadline is checked between reads; a blocking reader can exceed it —
the supervisor wraps the transport, this layer keeps the contract.
"""
import itertools
import json
import time

_QUERY = frozenset({
    "query-status", "query-name", "query-version", "query-commands",
    "query-schema", "query-mice", "query-displays", "query-block",
    "query-vcpus",
})
_OBSERVE = frozenset({"screendump"})
_INPUT = frozenset({"input-send-event"})
_LIFECYCLE = frozenset({"quit", "stop", "cont", "system_powerdown",
                        "system_reset"})
_CONTROL = frozenset({"qmp_capabilities"})

ALLOWED_COMMANDS = _QUERY | _OBSERVE | _INPUT | _LIFECYCLE | _CONTROL

# Typed operations the supervisor may publish to the agent layer — raw
# QMP command names are never public operations.
PUBLIC_OPS = frozenset({
    "env.status", "env.capture", "env.input", "env.stop", "env.reset",
})


def public_operation_allowed(name):
    return name in PUBLIC_OPS


class QmpError(Exception):
    """Protocol violation or not-allowed command."""


class QmpRefused(QmpError):
    """QEMU answered {"error": {"class", "desc"}} — carries .cls/.desc."""

    def __init__(self, cls, desc):
        super().__init__(f"{cls}: {desc}")
        self.cls, self.desc = cls, desc


class QmpEOF(QmpError):
    """Stream ended mid-conversation."""


class QmpTimeout(QmpError):
    """Deadline exceeded waiting for a complete message/response."""


class QmpClient:
    def __init__(self, reader, writer, deadline_s=30.0):
        self._reader = reader
        self._writer = writer
        self.deadline_s = deadline_s
        self._buf = ""
        self._ids = itertools.count(1)
        self.events = []

    # -- framing --------------------------------------------------------------

    def _deadline(self):
        return time.monotonic() + self.deadline_s

    def _read_message(self, deadline):
        """One complete JSON value; raises QmpTimeout/QmpEOF/QmpError."""
        while True:
            nl = self._buf.find("\n")
            if nl >= 0:
                line, self._buf = self._buf[:nl], self._buf[nl + 1:]
                line = line.strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError as exc:
                    raise QmpError(f"protocol: invalid JSON: {exc}")
            if time.monotonic() >= deadline:
                raise QmpTimeout("deadline exceeded waiting for message")
            readline = getattr(self._reader, "readline", None)
            chunk = readline() if readline is not None \
                else self._reader.read(4096)
            if chunk == "" or chunk == b"":
                raise QmpEOF("stream closed")
            self._buf += (chunk.decode("utf-8", "replace")
                          if isinstance(chunk, bytes) else chunk)

    def _send(self, obj):
        data = json.dumps(obj) + "\r\n"
        self._writer.write(data)
        flush = getattr(self._writer, "flush", None)
        if flush:
            flush()

    def _await_response(self, rid, deadline):
        """Return the response dict for rid; skips events/stray ids."""
        while True:
            msg = self._read_message(deadline)
            if not isinstance(msg, dict):
                raise QmpError("protocol: non-object message")
            if "event" in msg:
                self.events.append(msg)
                continue
            if msg.get("id") != rid:
                continue  # stray id — not our answer
            return msg

    # -- public ---------------------------------------------------------------

    def negotiate(self):
        """Consume the QMP greeting and leave capability mode.
        qmp_capabilities carries no id — responses are in-order, so the
        first non-event message is its answer."""
        msg = self._read_message(self._deadline())
        if not isinstance(msg, dict) or "QMP" not in msg:
            raise QmpError("protocol: expected greeting")
        self._send({"execute": "qmp_capabilities"})
        resp = self._read_message(self._deadline())
        while isinstance(resp, dict) and "event" in resp:
            self.events.append(resp)
            resp = self._read_message(self._deadline())
        if not isinstance(resp, dict):
            raise QmpError("protocol: non-object message")
        if "error" in resp:
            raise QmpRefused(resp["error"].get("class", "?"),
                             resp["error"].get("desc", ""))
        return msg["QMP"]

    def _next_id(self):
        return f"qmp-{next(self._ids)}"

    def call(self, command, arguments=None):
        """Execute an allowlisted command; return its "return" payload."""
        if command not in ALLOWED_COMMANDS:
            raise QmpError(f"not_allowed:{command}")
        rid = self._next_id()
        msg = {"execute": command, "id": rid}
        if arguments is not None:
            msg["arguments"] = arguments
        self._send(msg)
        resp = self._await_response(rid, self._deadline())
        if "error" in resp:
            err = resp["error"]
            raise QmpRefused(err.get("class", "?"), err.get("desc", ""))
        return resp.get("return", {})
