"""Opt-in privileged broker seam.

Fail-closed dispatch to an operator-provisioned OS broker. The only
capability a broker may ever declare is ``service.restart`` — there is
no generic command execution and no wildcard. Every request is checked
before the broker is touched:

1. broker provisioned (not None, readable ``capabilities()``);
2. capability in the broker's declared list AND in the hardcoded
   allowlist ``BROKER_CAPABILITIES``;
3. ``request["subject"]["uid"]`` bound to the broker's subject set
   (real transports compare the OS peer identity; the seam exposes
   ``broker.subjects``);
4. deadline not expired (``issued_at_ms + deadline_ms >= now`` with an
   injectable clock).

Successful dispatch surfaces the broker's ``audit_id`` — sanitized to
a bounded safe charset, never echoing request args. ``broker.dispatch``
is a CONFIRM capability: callers consume a one-shot token via
``sc_policy`` before reaching this module.
"""

import math
import re
import time

import sc_contract as contract

# Only this capability may ever be broker-declared. Adding entries
# requires a design review — no wildcards, no generic execution.
BROKER_CAPABILITIES = frozenset({"service.restart"})

_AUDIT_ID_RE = re.compile(r"[A-Za-z0-9_.:-]{1,128}")
_AUDIT_ID_FULL = _AUDIT_ID_RE.fullmatch


def _rejected(error):
    return {"ok": False, "status": "rejected", "error": error}


def _declared_capabilities(broker):
    """Broker-declared capability list, or None if unreadable.

    Fail closed: any exception or malformed return means the broker
    metadata cannot be trusted and nothing may dispatch.
    """
    try:
        caps = broker.capabilities()
    except Exception:
        return None
    if (not isinstance(caps, (list, tuple))
            or any(not isinstance(c, str) or not c for c in caps)):
        return None
    return list(caps)


def _supported_capabilities(broker):
    declared = _declared_capabilities(broker)
    if declared is None:
        return None
    return [c for c in declared if c in BROKER_CAPABILITIES]


def _bound_subjects(broker):
    subjects = getattr(broker, "subjects", None)
    if not isinstance(subjects, (list, tuple, set, frozenset)):
        return None
    if any(not isinstance(s, str) or not s for s in subjects):
        return None
    return subjects


def _valid_issued_at(value):
    return (isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


def _sanitize_audit_id(value):
    """audit_id is surfaced verbatim only if it is a bounded,
    printable identifier — never an echo of request args."""
    if isinstance(value, str) and _AUDIT_ID_FULL(value):
        return value
    return None


def _sanitize_error(value):
    """Broker-supplied error strings get the same bounded charset as
    audit_id — a broker must not echo request args through errors."""
    if isinstance(value, str) and _AUDIT_ID_FULL(value):
        return value
    return None


def dispatch(request, *, broker, now_ms=None):
    """Validate and dispatch a v1 envelope to a provisioned broker.

    Returns a status dict; the broker is invoked only after every gate
    passes. ``now_ms`` is an injectable clock for deadline checks.
    """
    req = contract.validate_request(request)
    if broker is None:
        return _rejected("broker_not_provisioned")
    declared = _supported_capabilities(broker)
    if declared is None:
        return _rejected("broker_metadata_unreadable")
    capability = req["capability"]
    if (capability not in BROKER_CAPABILITIES
            or capability not in declared):
        return _rejected("capability_not_declared")
    subjects = _bound_subjects(broker)
    subject = req.get("subject")
    uid = subject.get("uid") if isinstance(subject, dict) else None
    if subjects is None or not isinstance(uid, str) \
            or uid not in subjects:
        return _rejected("subject_not_bound")
    if now_ms is None:
        now_ms = time.time() * 1000
    issued = req.get("issued_at_ms")
    # issued_at_ms is optional in v1; when absent the deadline gate is
    # deliberately skipped — deadline_ms is already contract-bounded
    # and subject binding + one-shot confirmations bound replay.
    if issued is not None:
        if not _valid_issued_at(issued):
            return _rejected("invalid_issued_at_ms")
        if issued + req["deadline_ms"] < now_ms:
            return _rejected("deadline_expired")
    try:
        result = broker.dispatch(req)
    except Exception:
        return {"ok": False, "status": "unknown",
                "error": "broker_dispatch_failed"}
    if not isinstance(result, dict) or not result.get("ok"):
        error = (_sanitize_error(result.get("error"))
                 if isinstance(result, dict) else None)
        return {"ok": False, "status": "rejected",
                "error": error or "broker_rejected"}
    audit_id = _sanitize_audit_id(result.get("audit_id"))
    if audit_id is None and isinstance(result.get("value"), dict):
        audit_id = _sanitize_audit_id(result["value"].get("audit_id"))
    if audit_id is None:
        return {"ok": False, "status": "unknown",
                "error": "missing_audit_id"}
    return {"ok": True, "status": "dispatched", "audit_id": audit_id}


def _probe(broker):
    """Shared fail-closed probe for preflight/status."""
    if broker is None:
        return {"ok": False, "provisioned": False, "capabilities": [],
                "unsupported": []}
    declared = _declared_capabilities(broker)
    if declared is None:
        return {"ok": False, "provisioned": False, "capabilities": [],
                "unsupported": []}
    return {"ok": True, "provisioned": True,
            "capabilities": [c for c in declared
                             if c in BROKER_CAPABILITIES],
            "unsupported": [c for c in declared
                            if c not in BROKER_CAPABILITIES]}


def preflight(broker=None):
    """Report provisioning state and the declared capability list.

    No broker is contacted beyond reading its declared metadata; an
    unreadable broker reports unprovisioned (fail closed).
    """
    return _probe(broker)


def status(broker=None):
    """Report provisioning state, declared capabilities, and the count
    of bound subjects (never the subject values themselves)."""
    res = _probe(broker)
    if res["ok"]:
        subjects = _bound_subjects(broker)
        res["subjects"] = len(subjects) if subjects is not None else 0
    return res
