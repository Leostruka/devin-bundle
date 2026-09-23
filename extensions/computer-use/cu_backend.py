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
