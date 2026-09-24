#!/usr/bin/env python3
"""Target resolution: which environment an action goes to.

--env ID selects an environment declared in the registry
(.devin/computer-use/envs/*.json, overridable via $CU_ENV_ROOT).
Absent --env is the existing local path — unchanged. An unknown env_id
raises TargetError; it never silently means local.

cli_guard(argv) runs BEFORE controllers, UIA, mss or cleanup registration
in each CLI: remote envs get a typed `rejected` JSON result while no
backend exists; local requests return None and proceed untouched.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ENV_ROOT_ENV = "CU_ENV_ROOT"
STATE_ROOT_ENV = "CU_STATE_ROOT"

_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_RESERVED = {"con", "prn", "aux", "nul",
             *(f"com{i}" for i in range(1, 10)),
             *(f"lpt{i}" for i in range(1, 10))}


class TargetError(Exception):
    """Unknown or malformed target — carries a stable reason token."""


def runtime_root():
    """Private root for per-env runtime state (outside the repo)."""
    return Path(os.environ.get(STATE_ROOT_ENV)
                or Path(tempfile.gettempdir()) / "devin-cu-envs")


def _check_component(value, what):
    if not isinstance(value, str) or not _COMPONENT_RE.match(value):
        raise ValueError(f"bad_{what}:{value!r}")
    return value


def _check_name(name):
    if not isinstance(name, str) or not _NAME_RE.match(name) \
            or ".." in name \
            or name.split(".")[0].lower() in _RESERVED:
        raise ValueError(f"bad_name:{name!r}")
    return name


def state_dir(root, env_id, instance_id, session_id, require_within=True):
    """root/env/instance/session — every component validated; when
    require_within the resolved dir must stay under the resolved root
    (catches symlink/reparse escapes on existing parents)."""
    root = Path(root)
    d = root / _check_component(env_id, "env_id") \
             / _check_component(instance_id, "instance_id") \
             / _check_component(session_id, "session_id")
    if require_within:
        rr, rp = root.resolve(), d.resolve()
        if os.path.commonpath([str(rr), str(rp)]) != str(rr):
            raise ValueError(f"escape:{d}")
    return d


def state_path(root, env_id, instance_id, session_id, name,
               require_within=True):
    return state_dir(root, env_id, instance_id, session_id,
                     require_within) / _check_name(name)


def ensure_private_dir(path):
    """makedirs + 0700 on POSIX (Windows temp dirs are already per-user)."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        os.chmod(path, 0o700)
    return path


def default_registry_root():
    return Path.cwd() / ".devin" / "computer-use" / "envs"


def load_registry(root=None):
    """{env_id: spec} from *.json under root. Malformed specs raise
    TargetError(invalid_spec) — a silent skip would hide config errors."""
    root = Path(root or os.environ.get(ENV_ROOT_ENV)
                or default_registry_root())
    registry = {}
    if not root.is_dir():
        return registry
    for f in sorted(root.glob("*.json")):
        try:
            spec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TargetError(f"invalid_spec:{f.name}: {exc}")
        if not isinstance(spec, dict) \
                or not isinstance(spec.get("env_id"), str) \
                or not isinstance(spec.get("provider"), str):
            raise TargetError(f"invalid_spec:{f.name}")
        registry[spec["env_id"]] = spec
    return registry


def resolve_target(env_id, registry):
    """env_id None -> local target. Unknown id -> TargetError, never local."""
    if env_id is None:
        return {"kind": "local"}
    spec = registry.get(env_id)
    if spec is None:
        raise TargetError(f"unknown_environment:{env_id}")
    return {"kind": spec["provider"], "env_id": env_id, "spec": spec}


def _emit_rejection(error, code):
    print(json.dumps({"ok": False, "status": "rejected",
                      "dispatch": {"backend": "none"},
                      "error": error}))
    raise SystemExit(code)


def reject_remote(error, code=1, backend="qmp"):
    """Typed rejection for a remote request this CLI cannot serve —
    same shape as cli_guard's own rejections."""
    print(json.dumps({"ok": False, "status": "rejected",
                      "dispatch": {"backend": backend},
                      "error": error}))
    raise SystemExit(code)


def cli_guard(argv):
    """Resolve --env before host resources exist.

    None -> local path proceeds. Remote env -> typed `rejected` SystemExit
    while open_backend has no implementation for its provider; when a
    backend lands (C06+), returns the target dict and the CLI branches on
    it — unreachable code today, so remote can never fall through to
    local dispatch.
    """
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--env", default=None)
    ns, _ = pre.parse_known_args(argv)
    if ns.env is None:
        return None
    try:
        target = resolve_target(ns.env, load_registry())
    except TargetError as exc:
        _emit_rejection(str(exc), code=2)
    if target["kind"] == "local":
        return None
    import cu_backend
    try:
        backend = cu_backend.open_backend(target)
    except cu_backend.BackendUnavailable as exc:
        _emit_rejection(str(exc), code=1)
    target["backend"] = backend
    return target
