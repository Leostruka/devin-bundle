"""System Control request/response contract, schema v1.

Manual stdlib validation; schemas/v1.json documents the wire shape.
Requests fail closed: any deviation raises ValueError before dispatch.
"""

SCHEMA_VERSION = 1
STATUSES = frozenset({
    "dispatched", "verified", "rejected",
    "timeout", "unknown", "cancelled",
})
DEADLINE_MS_MAX = 300000
_REQUIRED_KEYS = ("version", "request_id", "capability", "args",
                  "deadline_ms")


class InvalidRequest(ValueError):
    """Request/argument validation failure — maps to CLI exit 2.

    Backend output parse failures stay plain errors and map to exit 1.
    """


def target(pid: int, start_time: int) -> dict:
    """Process identity is pid + start_time, never pid alone."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid < 0:
        raise InvalidRequest(
            "target.pid must be a non-negative integer")
    if (isinstance(start_time, bool) or not isinstance(start_time, int)
            or start_time < 0):
        raise InvalidRequest(
            "target.start_time must be a non-negative integer")
    return {"pid": pid, "start_time": start_time}


def validate_request(value: dict) -> dict:
    """Validate a v1 request; returns a normalized copy.

    Raises ValueError on any violation. Required keys: version,
    request_id, capability, args, deadline_ms. target.pid and
    target.start_time are required together when target is present.
    """
    if not isinstance(value, dict):
        raise InvalidRequest("request must be a JSON object")
    for key in _REQUIRED_KEYS:
        if key not in value:
            raise InvalidRequest(f"missing required key: {key}")
    version = value["version"]
    if isinstance(version, bool) or version != SCHEMA_VERSION:
        raise InvalidRequest(f"unsupported version: {version!r}")
    if not isinstance(value["request_id"], str) \
            or not value["request_id"]:
        raise InvalidRequest("request_id must be a non-empty string")
    if not isinstance(value["capability"], str) \
            or not value["capability"]:
        raise InvalidRequest("capability must be a non-empty string")
    if not isinstance(value["args"], dict):
        raise InvalidRequest("args must be an object")
    deadline = value["deadline_ms"]
    if (isinstance(deadline, bool) or not isinstance(deadline, int)
            or not 1 <= deadline <= DEADLINE_MS_MAX):
        raise InvalidRequest(
            f"deadline_ms must be an integer in [1, {DEADLINE_MS_MAX}]")
    req = dict(value)
    if req.get("target") is not None:
        t = req["target"]
        if not isinstance(t, dict):
            raise InvalidRequest("target must be an object")
        extra = set(t) - {"pid", "start_time"}
        if extra:
            raise InvalidRequest(
                f"unexpected target keys: {sorted(extra)}")
        if "pid" not in t:
            raise InvalidRequest(
                "target requires pid and start_time together: "
                "missing pid")
        if "start_time" not in t:
            raise InvalidRequest(
                "target requires pid and start_time together: "
                "missing start_time")
        req["target"] = target(t["pid"], t["start_time"])
    return req


def result(*, ok: bool, status: str, request_id: str, backend: str,
           privilege: str = "user", precondition=None, value=None,
           postcondition=None, cursor=None, spill=None,
           dropped: int = 0, error=None) -> dict:
    """Canonical response envelope; evidence fields always present."""
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status!r}")
    return {
        "ok": bool(ok),
        "status": status,
        "request_id": request_id,
        "backend": backend,
        "privilege": privilege,
        "precondition": precondition,
        "value": value,
        "postcondition": postcondition,
        "evidence": {"cursor": cursor, "spill": spill,
                     "dropped": dropped},
        "error": error,
    }


def untrusted(value) -> dict:
    """Wrap externally sourced data; it never grants authorization."""
    return {"untrusted": True, "value": value}
