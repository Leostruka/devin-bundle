#!/usr/bin/env python3
"""Backend seam: one implementation per target kind.

open_backend(target) -> Backend
  Backend contract (C05+): capabilities(), observe(options),
  dispatch(action), release_owned(), close() — all dicts except close.

provider "qemu" -> cu_qmp_backend.QmpBackend bound to the env's private
dir; other providers remain typed rejections. `local` itself is not a
Backend — it keeps using the existing native code path.
"""


class BackendUnavailable(Exception):
    """Provider has no implemented/available backend for this target."""


def open_backend(target):
    kind = target.get("kind") if isinstance(target, dict) else None
    if kind == "local":
        raise BackendUnavailable("local_uses_native_dispatch")
    if kind == "qemu":
        import cu_qmp_backend
        return cu_qmp_backend.QmpBackend(target["env_id"])
    raise BackendUnavailable(f"backend_unavailable:{kind}")


# Results provably free of side effects — the only retryable kind.
_RETRYABLE_STATUSES = frozenset({"rejected", "dry_run", "planned"})


def may_retry(result):
    """True only when the result PROVES nothing was dispatched:
    pre-send rejections/dry-runs, or ops explicitly marked read_only.
    'unknown' after a send is never retryable — replay could double
    the effect."""
    if not isinstance(result, dict):
        return False
    if result.get("read_only") is True:
        return True
    return result.get("status") in _RETRYABLE_STATUSES


def cleanup(target):
    """Release input state for the target. Remote envs release through
    their backend — cu_actions.emergency_release is HOST state and must
    never run on a remote path. Host release requires an EXPLICIT
    kind=local; an unknown/absent kind never defaults to host."""
    kind = target.get("kind") if isinstance(target, dict) else None
    if kind == "local":
        import cu_actions
        cu_actions.emergency_release()
        return {"released": "host"}
    backend = target.get("backend") or open_backend(target)
    return backend.release_all()


def result_from_ack(ack, request_id=None):
    """Normalize a transport ACK. 'dispatched' — an ack proves the
    daemon accepted bytes, never that the guest reacted. Verification
    is a separate step (verify_effect)."""
    r = {"ok": True, "status": "dispatched"}
    if request_id is not None:
        r["request_id"] = request_id
    if isinstance(ack, dict) and "return" in ack:
        r["ack"] = ack["return"]
    return r


# Closed predicate set — anything else is rejected, not evaluated.
_PREDICATE_KINDS = frozenset(
    {"frame_changed", "region_changed", "field_equals", "probe"})


def _region_differs(fa, fb, x, y, w, h):
    """True iff any pixel inside rect (x,y,w,h) differs between frames.
    Geometry mismatch counts as 'cannot compare' -> False, never True."""
    if fa is None or fb is None:
        return False
    if (fa.width, fa.height) != (fb.width, fb.height):
        return False
    for py in range(y, min(y + h, fa.height)):
        for px in range(x, min(x + w, fa.width)):
            i = (py * fa.width + px) * 3
            if fa.rgb[i:i + 3] != fb.rgb[i:i + 3]:
                return True
    return False


def verify_effect(action, before, after, predicate):
    """Compare a pre-action observation with a post-action one under a
    closed predicate. Requires the SAME env instance and a LATER
    observation. A satisfied visual predicate yields 'evidence' —
    never 'verified'/'done'; intent-level proof needs a semantic
    predicate (field/probe), which reports source_unavailable until a
    guest agent exists."""
    b, a = (before or {}), (after or {})
    bm, am = b.get("meta") or {}, a.get("meta") or {}
    if bm.get("instance_id") != am.get("instance_id"):
        return {"verified": False, "reason": "instance_mismatch"}
    if not (am.get("monotonic_ns") or 0) > (bm.get("monotonic_ns") or 0):
        return {"verified": False, "reason": "stale_observation_order"}
    if not isinstance(predicate, dict):
        return {"verified": False, "reason": "predicate_required"}
    kind = predicate.get("kind")
    if kind not in _PREDICATE_KINDS:
        return {"verified": False, "reason": f"predicate:{kind}"}
    if kind == "frame_changed":
        ok = bm.get("frame_sha256") != am.get("frame_sha256")
    elif kind == "region_changed":
        ok = _region_differs(b.get("frame"), a.get("frame"),
                             int(predicate.get("x", 0)),
                             int(predicate.get("y", 0)),
                             int(predicate.get("w", 0)),
                             int(predicate.get("h", 0)))
    else:  # field_equals / probe — need a guest-side source (C10+)
        return {"verified": False,
                "reason": f"source_unavailable:{kind}"}
    return {"verified": False, "status": "evidence",
            "predicate": kind, "predicate_satisfied": ok,
            "note": "visual change is evidence, not task completion"}
