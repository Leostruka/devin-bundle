#!/usr/bin/env python3
"""Append-only action audit for computer-use (OpenDots parity).

One JSONL record per dispatched action: {ts, tool, cmd, status, backend,
timings_ms}. Deliberately excludes typed values, file contents, and full
command strings, matching OpenDots' computer audit exclusion rule
(docs/COMPUTERS.md). Audit failure is swallowed: it must never break or
block the action it describes.
"""
import json
import os
import tempfile
import time

_MAX_BYTES = int(os.environ.get("CU_AUDIT_MAX_BYTES", str(256 * 1024)))
_KEEP_LINES = 1000


def enabled():
    return os.environ.get("CU_AUDIT", "").lower() not in (
        "0", "off", "false")


def audit_path():
    return os.environ.get(
        "CU_AUDIT_PATH",
        os.path.join(tempfile.gettempdir(), "devin-cu-audit.jsonl"))


def _rotate(path):
    try:
        if os.path.getsize(path) <= _MAX_BYTES:
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.writelines(lines[-_KEEP_LINES:])
        os.replace(tmp, path)
    except OSError:
        pass


def record(entry):
    if not enabled():
        return
    try:
        path = audit_path()
        _rotate(path)
        entry = dict(entry)
        entry["ts"] = entry.get("ts", round(time.time(), 3))
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    except Exception:
        pass
