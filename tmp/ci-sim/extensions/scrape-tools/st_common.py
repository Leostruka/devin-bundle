#!/usr/bin/env python3
"""Shared helpers for scrape-tools: JSON contract, node extraction,
storage root. Stdlib only — scrapling is imported by callers lazily."""
import json
import os
import sys
from pathlib import Path

STATE_ROOT_ENV = "SCRAPE_STATE_ROOT"

_BUNDLE_VERSION = None


def _bundle_version():
    """Bundle version from the nearest manifest.json ancestor, cached.

    manifest.json sits at the install root in both the repo layout
    (extensions/<name>/ -> repo root) and the live install
    (%APPDATA%/devin/extensions/<name>/ -> %APPDATA%/devin). Only a
    JSON object with a "name" key counts as the bundle manifest;
    malformed or unrelated JSON yields "" rather than a guess.
    """
    global _BUNDLE_VERSION
    if _BUNDLE_VERSION is None:
        _BUNDLE_VERSION = ""
        for parent in Path(__file__).absolute().parents:
            mf = parent / "manifest.json"
            if mf.is_file():
                try:
                    data = json.loads(mf.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    break
                if isinstance(data, dict) and data.get("name"):
                    _BUNDLE_VERSION = str(data.get("version") or "")
                break
    return _BUNDLE_VERSION


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "scrape-tools"}


def _stamp(payload):
    """Assert envelope contract v2 on a response dict (in place)."""
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def emit(payload):
    """Stamp contract v2 fields and print payload as JSON."""
    _stamp(payload)
    print(json.dumps(payload))


def fail(msg, code=1):
    emit({"ok": False, "error": msg})
    sys.exit(code)


def node_to_dict(el):
    """Selector element -> plain dict."""
    text = getattr(el, "text", "") or ""
    text = text.strip() if hasattr(text, "strip") else str(text)
    try:
        attrib = dict(el.attrib)
    except Exception:
        attrib = {}
    tag = getattr(el, "tag", None) or ""
    return {"tag": str(tag), "text": text, "attrib": attrib}


def storage_root(root=None):
    """Adaptive-storage root: $SCRAPE_STATE_ROOT or .devin/scrape-tools/
    storage under cwd. Own dir - deliberately not CU_STATE_ROOT."""
    base = root or os.environ.get(STATE_ROOT_ENV)
    if base:
        return Path(base)
    return Path.cwd() / ".devin" / "scrape-tools" / "storage"


def selector_config(adaptive):
    """Selector kwargs for Fetcher.get(selector_config=...): enable the
    adaptive engine and pin its SQLite file under storage_root()."""
    if not adaptive:
        return None
    root = storage_root()
    root.mkdir(parents=True, exist_ok=True)
    return {"adaptive": True,
            "storage_args": {"storage_file": str(root / "adaptive.db")}}


def browser_tier_installed():
    """Browser binaries exist? Fetcher tier needs none; Dynamic/Stealthy
    need `scrapling install` (Playwright Chromium + patchright browsers)."""
    local = os.environ.get("LOCALAPPDATA")
    candidates = [
        Path.home() / ".local-browsers",                       # patchright
        Path(local) / "ms-playwright" if local else
        Path.home() / ".cache" / "ms-playwright",              # playwright
    ]
    return any(p.is_dir() and any(p.iterdir()) for p in candidates)
