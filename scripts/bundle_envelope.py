"""Envelope v2 helpers shared by scripts/ CLIs.

Same-dir shared-module carve-out (CLI-CONTRACT.md, cu_envelope
precedent): the `_stamp`/`_dumps` funnel lives here once instead of
per-file copies. Unlike extension dirs, scripts/ files stamp with a
per-file wrapper name, so callers bind:

    from bundle_envelope import bind
    _stamp, _dumps = bind("my-script")
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


def _stamp(payload, wrapper):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault(
        "answered_by", {"bundle": _bundle_version(), "wrapper": wrapper})
    return payload


def bind(wrapper):
    """Return (_stamp, _dumps) bound to this file's wrapper name."""
    def stamp(payload):
        return _stamp(payload, wrapper)

    def dumps(payload, **kw):
        return json.dumps(stamp(payload), **kw)

    return stamp, dumps


if __name__ == "__main__":
    import sys
    print(json.dumps(_stamp({"ok": True, "module": "bundle_envelope"},
                            sys.argv[1] if len(sys.argv) > 1
                            else "bundle_envelope"), indent=1))
