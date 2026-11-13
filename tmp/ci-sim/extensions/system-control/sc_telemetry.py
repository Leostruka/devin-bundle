"""Bounded, resumable event streams.

`normalize` produces event envelopes with a module-global monotonic
cursor (never derived from event `ts`). `open_stream` registers a
bounded deque-backed stream; `drain` returns events after a cursor and
flags `resync_required` when the cursor fell behind the retained
window. Streams persist across CLI invocations by living inside the
sc_sessions daemon; the *_remote wrappers use its envelope auth.
"""

import itertools
import json
import math
import re
import threading
import time
import uuid
from collections import deque

_CURSOR = itertools.count(1)
_CURSOR_LOCK = threading.Lock()
_SECRET_RX = re.compile(
    r"password|passwd|token|secret|api[_-]?key|authorization|cookie|"
    r"credential|private[_-]?key", re.IGNORECASE)
_SEVERITIES = frozenset({"info", "warning", "error"})
_ATTR_KEYS_MAX = 32
_ATTR_VAL_MAX = 512
_CAPACITY_MAX = 65536
_REGISTRY = {}
_REGISTRY_LOCK = threading.Lock()


def _next_cursor():
    with _CURSOR_LOCK:
        return next(_CURSOR)


def _clean_attrs(attrs):
    """Untrusted attrs: redact secret-shaped keys, cap count/length."""
    if not isinstance(attrs, dict):
        return {}
    out = {}
    for k, v in attrs.items():
        if len(out) >= _ATTR_KEYS_MAX:
            break
        key = str(k)
        if _SECRET_RX.search(key):
            out[key] = "***"
            continue
        if isinstance(v, (dict, list, tuple, set)):
            # Never serialize nested structures — they can embed
            # secret values the key-shape regex cannot see.
            out[key] = "***"
            continue
        text = v if isinstance(v, str) else str(v)
        if len(text) > _ATTR_VAL_MAX:
            text = text[:_ATTR_VAL_MAX] + "...[truncated]"
        out[key] = text
    return out


def normalize(subject, *, source, kind, severity="info", ts=None,
              attrs=None):
    """Build an event envelope; cursor is global monotonic."""
    if severity not in _SEVERITIES:
        severity = "info"
    now = time.time()
    return {"ts": ts if ts is not None else now,
            "observed_ts": now,
            "source": source, "kind": kind,
            "subject": subject if isinstance(subject, dict) else {},
            "severity": severity,
            "attrs": _clean_attrs(attrs),
            "cursor": _next_cursor(),
            "dropped": 0}


class Stream:
    """Bounded event buffer; seq tracks retention, cursor resume."""

    def __init__(self, capacity, ttl_s, provider=None,
                 interval_s=5.0):
        self.id = uuid.uuid4().hex
        self.capacity = capacity
        self.ttl_s = ttl_s
        self.provider = provider
        self.interval_s = max(1.0, float(interval_s))
        self.created_at = time.time()
        self.dropped = 0
        self.next_seq = 0
        self.closed = False
        # Hosted streams (daemon-owned) are fed by the daemon poller;
        # drain must not poll them inline on the accept loop.
        self.hosted = False
        self._buf = deque(maxlen=capacity)
        self._lock = threading.Lock()

    @property
    def expired(self):
        return (self.ttl_s is not None
                and time.time() - self.created_at > self.ttl_s)

    @property
    def base_seq(self):
        return self._buf[0][0] if self._buf else 0

    def feed(self, events):
        """Append events; eviction increments dropped."""
        if self.closed:
            return
        with self._lock:
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                seq = ev.get("cursor")
                if not isinstance(seq, int) or isinstance(seq, bool):
                    seq = self.next_seq + 1
                if len(self._buf) == self._buf.maxlen:
                    self.dropped += 1
                self._buf.append((seq, ev))
                if seq > self.next_seq:
                    self.next_seq = seq

    def meta(self):
        return {"id": self.id, "capacity": self.capacity,
                "ttl_s": self.ttl_s, "interval_s": self.interval_s,
                "created_at": self.created_at,
                "buffered": len(self._buf), "dropped": self.dropped,
                "provider": bool(self.provider)}


def _bad_num(v):
    return (isinstance(v, bool) or not isinstance(v, (int, float))
            or not math.isfinite(v))


def provider_output(produced, *, source="provider"):
    """Coerce a provider return value into an event list.

    A dict/str/non-iterable return is a provider bug, not event data —
    emit one provider.error event instead of feeding its keys.
    """
    if produced is None:
        return []
    if isinstance(produced, (dict, str, bytes)):
        return [normalize({}, source=source, kind="provider.error",
                          severity="error",
                          attrs={"message": "provider returned "
                                            "non-event output"})]
    try:
        items = list(produced)
    except TypeError:
        return [normalize({}, source=source, kind="provider.error",
                          severity="error",
                          attrs={"message": "provider returned "
                                            "non-iterable output"})]
    return items


def open_stream(*, capacity=1024, ttl_s=300, provider=None,
                interval_s=5.0):
    """Create a stream in the module registry."""
    if (_bad_num(capacity)
            or not 1 <= int(capacity) <= _CAPACITY_MAX):
        return {"ok": False, "status": "rejected",
                "error": f"capacity must be in [1, {_CAPACITY_MAX}]"}
    if ttl_s is not None and (_bad_num(ttl_s) or ttl_s <= 0):
        return {"ok": False, "status": "rejected",
                "error": "ttl_s must be a positive finite number"}
    if _bad_num(interval_s) or interval_s <= 0:
        return {"ok": False, "status": "rejected",
                "error": "interval_s must be a positive finite number"}
    s = Stream(int(capacity), ttl_s, provider=provider,
               interval_s=interval_s)
    with _REGISTRY_LOCK:
        _REGISTRY[s.id] = s
    return {"ok": True, "stream": s}


def _resolve(stream):
    if isinstance(stream, Stream):
        s = stream
    else:
        with _REGISTRY_LOCK:
            s = _REGISTRY.get(stream)
    if s is None or s.closed or s.expired:
        return None
    return s


def drain(stream, *, cursor=None, limit=100):
    """Poll provider (if any), then return events after `cursor`."""
    s = _resolve(stream)
    if s is None:
        return {"ok": False, "status": "rejected",
                "error": "unknown or closed stream"}
    if s.provider is not None and not s.hosted:
        try:
            produced = s.provider()
        except Exception as exc:
            return {"ok": False, "status": "unknown",
                    "error": f"provider failed: {exc}"}
        s.feed(provider_output(produced))
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 100
    if cursor is not None:
        try:
            cursor = int(cursor)
        except (TypeError, ValueError):
            return {"ok": False, "status": "rejected",
                    "error": "cursor must be an integer"}
    with s._lock:
        items = list(s._buf)
        dropped = s.dropped
    base = items[0][0] if items else 0
    resync = bool(items) and cursor is not None and cursor < base
    if cursor is None:
        selected = items
    else:
        selected = [p for p in items if p[0] > cursor]
    selected = selected[:max(0, limit)]
    last = selected[-1][0] if selected else (cursor or 0)
    return {"ok": True, "status": "verified",
            "value": {"events": [ev for _, ev in selected],
                      "cursor": last,
                      "resync_required": resync},
            "evidence": {"dropped": dropped, "spill": None}}


def close_stream(stream):
    """Remove a stream from the registry; later ops are rejected."""
    sid = stream.id if isinstance(stream, Stream) else stream
    with _REGISTRY_LOCK:
        s = _REGISTRY.pop(sid, None)
    if isinstance(stream, Stream) and s is None:
        s = stream
    if s is None:
        return {"ok": False, "status": "rejected",
                "error": "unknown or closed stream"}
    s.closed = True
    return {"ok": True, "closed": sid}


def reduce_events(events, *, top_k=10):
    """Group by (kind, subject); preserve errors and drop counts."""
    groups = {}
    errors = []
    dropped = 0
    total = 0
    for ev in events or []:
        if not isinstance(ev, dict):
            continue
        total += 1
        try:
            dropped += int(ev.get("dropped") or 0)
        except (TypeError, ValueError):
            pass
        kind = ev.get("kind")
        if (ev.get("severity") == "error"
                or (isinstance(kind, str)
                    and ("error" in kind or "overflow" in kind))):
            errors.append(ev)
        key = (str(kind),
               json.dumps(ev.get("subject"), sort_keys=True,
                          default=str))
        g = groups.get(key)
        if g is None:
            groups[key] = {"kind": kind,
                           "subject": ev.get("subject"),
                           "count": 1,
                           "first_ts": ev.get("ts"),
                           "last_ts": ev.get("ts"),
                           "sample": ev}
        else:
            g["count"] += 1
            g["last_ts"] = ev.get("ts")
    ranked = sorted(groups.values(),
                    key=lambda g: (-g["count"], str(g["kind"])))
    return {"groups": ranked[:max(0, int(top_k))],
            "errors": errors, "dropped": dropped, "total": total}


# --- daemon-hosted remote surface (envelope auth via sc_sessions) ----

def _authed_op(op, arg):
    import sc_sessions
    st = sc_sessions.start_daemon()
    if not st.get("ok"):
        return st
    return sc_sessions._authed(op, arg)


def open_stream_remote(*, capacity=1024, ttl_s=300, provider=None,
                       interval_s=5.0):
    return _authed_op("stream.open",
                      {"capacity": capacity, "ttl_s": ttl_s,
                       "provider": provider,
                       "interval_s": interval_s})


def drain_remote(stream_id, *, cursor=None, limit=100):
    arg = {"id": stream_id, "limit": limit}
    if cursor is not None:
        arg["cursor"] = cursor
    return _authed_op("stream.drain", arg)


def close_stream_remote(stream_id):
    return _authed_op("stream.close", {"id": stream_id})


def list_streams_remote():
    return _authed_op("stream.list", {})
