#!/usr/bin/env python3
"""Shared helpers for scrape-tools: JSON contract, node extraction,
storage root. Stdlib only — scrapling is imported by callers lazily."""
import json
import os
import sys
from pathlib import Path

STATE_ROOT_ENV = "SCRAPE_STATE_ROOT"


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
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
