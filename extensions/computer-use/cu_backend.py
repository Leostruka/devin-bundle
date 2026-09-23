#!/usr/bin/env python3
"""Backend seam: one implementation per target kind.

open_backend(target) -> Backend
  Backend contract (C05+): capabilities(), observe(options),
  dispatch(action), release_owned(), close() — all dicts except close.

C01 implements no backend: every non-local provider raises
BackendUnavailable with a stable reason token, so a remote request is a
typed rejection rather than a silent local execution. `local` itself is
not a Backend — it keeps using the existing native code path.
"""


class BackendUnavailable(Exception):
    """Provider has no implemented/available backend for this target."""


def open_backend(target):
    kind = target.get("kind") if isinstance(target, dict) else None
    if kind == "local":
        raise BackendUnavailable("local_uses_native_dispatch")
    raise BackendUnavailable(f"backend_unavailable:{kind}")
