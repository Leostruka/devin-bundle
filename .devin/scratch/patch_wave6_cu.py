"""Wave-6: stamp envelope v2 on the 8 computer-use agent-facing CLIs.

Inserts the canonical helper trio + _dumps() after the top-level import
block, then rewrites `print(json.dumps(` -> `print(_dumps(` so every JSON
emit funnels through _stamp.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CU = ROOT / "extensions" / "computer-use"

FILES = ["terminal.py", "screenshot.py", "mouse.py", "type_text.py",
         "record.py", "profile.py", "env.py", "browser.py",
         "cu_motion.py",
         "cu_target.py", "cu_actions.py", "cu_scope.py", "cu_session_dispatch.py", "cu_bench.py", "cu_dom_picker.py",
         "cu_events.py", "cu_notify.py", "cu_ocr.py", "cu_overlay.py",
         "cu_probe.py", "cu_session.py", "cu_taskrunner.py", "cu_wgc.py"]

TRIO = '''
_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
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
    return {"bundle": _bundle_version(), "wrapper": "computer-use"}


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

'''


def _paren_delta(ln):
    # crude balance of ()[]{} outside strings/comments — enough for import
    # continuations which contain no string literals
    code = ln.split("#", 1)[0]
    return (sum(code.count(c) for c in "([{")
            - sum(code.count(c) for c in ")]}"))


def insert_trio(text):
    # trio needs Path; ensure `from pathlib import Path` present
    if "from pathlib import" not in text:
        # add after the last top-level import *statement* (handles
        # multi-line `from x import (` continuations)
        lines = text.split("\n")
        last_imp = None
        depth = 0
        for i, ln in enumerate(lines[:80]):
            if depth == 0 and ln.startswith(("import ", "from ")):
                last_imp = i
            depth += _paren_delta(ln)
            if depth < 0:
                depth = 0
        if last_imp is None:
            raise RuntimeError("no import found")
        # advance past continuation lines of that import
        j = last_imp
        d = _paren_delta(lines[j])
        while d > 0:
            j += 1
            d += _paren_delta(lines[j])
        lines.insert(j + 1, "from pathlib import Path")
        text = "\n".join(lines)
    # insert trio right after the contiguous top import block
    lines = text.split("\n")
    # find first top-level statement that is not import/from/blank/docstring
    depth_end = None
    in_doc = False
    depth = 0
    for i, ln in enumerate(lines):
        s = ln.strip()
        if depth > 0:
            depth += _paren_delta(ln)
            if depth < 0:
                depth = 0
            continue
        if in_doc:
            if s.endswith('"""'):
                in_doc = False
            continue
        if s.startswith('"""') and i < 12:
            if not (s.endswith('"""') and len(s) > 3):
                in_doc = True
            continue
        if s.startswith(("import ", "from ", "#")) or not s:
            depth += _paren_delta(ln)
            if depth < 0:
                depth = 0
            continue
        depth_end = i
        break
    if depth_end is None:
        raise RuntimeError("no insertion point")
    lines.insert(depth_end, TRIO.rstrip("\n") + "\n")
    return "\n".join(lines)


changed = []
for name in FILES:
    p = CU / name
    text = p.read_text(encoding="utf-8")
    if "_BUNDLE_VERSION_CACHE" in text:
        print(f"{name}: already stamped, skipping")
        continue
    orig = text
    n = len(re.findall(r"print\(json\.dumps\(", text))
    text = text.replace("print(json.dumps(", "print(_dumps(")
    text = insert_trio(text)
    p.write_text(text, encoding="utf-8")
    changed.append((name, n))

for name, n in changed:
    print(f"{name}: {n} emit sites stamped")
