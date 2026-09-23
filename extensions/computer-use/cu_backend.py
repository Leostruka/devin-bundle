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
    never run on a remote path."""
    kind = target.get("kind") if isinstance(target, dict) else None
    if kind == "local" or kind is None:
        import cu_actions
        cu_actions.emergency_release()
        return {"released": "host"}
    return open_backend(target).release_all()
