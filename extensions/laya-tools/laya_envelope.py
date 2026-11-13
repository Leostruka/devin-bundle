"""Envelope v2 helpers shared by laya-tools CLIs.

Same-extension shared-module carve-out (CLI-CONTRACT.md, cu_envelope
precedent): the `_stamp`/`_dumps` funnel lives here once instead of
per-file copies. Every laya-tools JSON stdout emitter routes through
`_dumps` so all responses carry `api_version: 2` and
`meta.answered_by`.
"""

import json
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "laya-tools"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)
