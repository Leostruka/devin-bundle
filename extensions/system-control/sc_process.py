"""Read-only process inventory on top of the selected backend."""

import uuid

import sc_backend
import sc_contract as contract


def snapshot(*, pid=None, limit=100, backend=None) -> dict:
    """Bounded process list wrapped in the result envelope."""
    b = backend if backend is not None else sc_backend.current()
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        raise contract.InvalidRequest("limit must be an integer")
    if lim < 0:
        raise contract.InvalidRequest("limit must be non-negative")
    items = list(b.process_list(pid))[:lim]
    return contract.result(
        ok=True, status="verified",
        request_id=uuid.uuid4().hex[:12],
        backend=sc_backend.backend_name(b), value=items)
