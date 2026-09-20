"""Backend discovery: platform.system() selects the OS adapter module.

Import failure or an unknown platform yields a typed unsupported
backend — never a fallback shell command.
"""

import importlib
import platform

_MODULE_BY_SYSTEM = {
    "Windows": "backends.windows",
    "Linux": "backends.linux",
    "Darwin": "backends.macos",
}

KNOWN_CAPABILITIES = ("process.observe", "service.observe")


class BackendUnavailable(RuntimeError):
    """Raised when an operation needs a capability the host lacks."""


class UnsupportedBackend:
    """Typed stand-in when the OS adapter is absent or unimportable."""

    def __init__(self, name, reason):
        self.name = name
        self._reason = reason

    def capabilities(self):
        return [
            {"name": n, "supported": False, "reason": self._reason,
             "mode": "none"}
            for n in KNOWN_CAPABILITIES
        ]

    def process_list(self, pid=None):
        raise BackendUnavailable(self._reason)

    def process_get(self, pid, start_time=None):
        raise BackendUnavailable(self._reason)

    def service_status(self, name):
        raise BackendUnavailable(self._reason)


def current():
    """Return the backend module for this host, or UnsupportedBackend."""
    system = platform.system()
    modname = _MODULE_BY_SYSTEM.get(system)
    if modname is None:
        return UnsupportedBackend(
            (system or "unknown").lower(),
            f"unsupported platform: {system!r}")
    try:
        return importlib.import_module(modname)
    except Exception as exc:
        return UnsupportedBackend(
            system.lower(), f"backend import failed: {exc}")


def capabilities(backend=None) -> list:
    """Capability entries as {name, supported, reason, mode} dicts."""
    return list((backend or current()).capabilities())


def backend_name(backend) -> str:
    return (getattr(backend, "name", None)
            or getattr(backend, "__name__", "unknown"))
