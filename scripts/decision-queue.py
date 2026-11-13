#!/usr/bin/env python3
"""decision-queue - record human-blocking stops into .devin/decisions.jsonl.

Near-loop contract: the agent should interrupt only at real decisions.
When a Stop fires and the last assistant message carries decision/blocker
markers, append a record so `pulse.py`/roadmap-board can surface the
pending queue.

Hook mode (stdin payload): reads last_assistant_message/message, appends
{"id","ts","excerpt","resolved":false,"source":"stop"} on match.

CLI modes:
  --pending     print unresolved records (JSON array)
  --resolve ID  mark record resolved
Fail-open everywhere: any error -> exit 0 silent (hook path).
"""
import json
import os
import re
import sys
import time

from bundle_envelope import bind


_stamp, _dumps = bind("decision-queue")


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DECISION_MARKERS = (
    re.compile(r"\bblocked\b|\bblocker\b", re.I),
    re.compile(r"\bdecision required\b|\bneed(?:s)? (?:a |your )?decision\b",
               re.I),
    re.compile(r"\bapprove|\bapproval required|\bconfirm\b", re.I),
    re.compile(r"\bwaiting (?:for|on) (?:you|your|input)\b", re.I),
    re.compile(r"\?\s*$", re.M),  # turn ends on a question to the user
)


def _queue_path():
    root = os.environ.get("DEVIN_PROJECT_DIR") or os.getcwd()
    return os.path.join(root, ".devin", "decisions.jsonl")


def _load(path):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return out


def _hook(payload):
    msg = (payload.get("last_assistant_message")
           or payload.get("message") or "")
    if not any(p.search(msg) for p in DECISION_MARKERS):
        return
    path = _queue_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    excerpt = " ".join(msg.split())[-400:]
    rec = {"id": f"d{int(time.time() * 1000)}", "ts": int(time.time()),
           "excerpt": excerpt, "resolved": False, "source": "stop"}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main(argv=None):
    argv = argv or []
    path = _queue_path()
    if "--pending" in argv:
        recs = [r for r in _load(path) if not r.get("resolved")]
        print(_dumps({"ok": True, "pending": len(recs),
                          "records": recs}, indent=1))
        return 0
    if "--resolve" in argv:
        i = argv.index("--resolve")
        if i + 1 >= len(argv):
            print(_dumps({"ok": False, "error": "--resolve <id>"}))
            return 2
        rid = argv[i + 1]
        recs = _load(path)
        found = False
        for r in recs:
            if r.get("id") == rid:
                r["resolved"] = True
                r["resolved_at"] = int(time.time())
                found = True
        if found:
            with open(path, "w", encoding="utf-8") as f:
                for r in recs:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(_dumps({"ok": found, "id": rid}))
        return 0 if found else 1
    try:
        _recfg = getattr(sys.stdin, "reconfigure", None)
        if _recfg:
            try:
                _recfg(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    try:
        _hook(payload)
    except Exception:
        pass  # fail-soft: cleanup; preserve primary error
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
