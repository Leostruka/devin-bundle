#!/usr/bin/env python3
"""laya-shadow-report: summarize compact-gate shadow decisions.

Reads .devin/laya/shadow.jsonl (project then devin home) and prints the
observed firing distribution used to calibrate compact_gate thresholds
(.devin/docs/COMPACTION-POLICY.md): p quantiles, action/boundary counts,
abstain reasons, per-session max p, and inflation count (p > 1.0 means the
pressure marker outlived a compaction).
"""
import collections
import json
import os
import sys


def _devin_home():
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        return os.path.join(appdata, "devin")
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    if xdg:
        return os.path.join(xdg, "devin")
    return os.path.join(os.path.expanduser("~"), ".config", "devin")


def _find_log():
    for base in (os.environ.get("DEVIN_PROJECT_DIR"), os.getcwd(),
                 _devin_home()):
        if not base:
            continue
        p = os.path.join(base, ".devin", "laya", "shadow.jsonl")
        if os.path.isfile(p):
            return p
    return None


def _quantile(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * q))]


def main():
    log = _find_log()
    if not log:
        print("no shadow.jsonl found")
        return 1
    entries = []
    with open(log, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    cg = [e for e in entries if e.get("profile") == "compact-gate"]
    print(f"log: {log}")
    print(f"entries: {len(entries)}  compact-gate: {len(cg)}")
    if not cg:
        return 0
    ps = [e["p"] for e in cg if isinstance(e.get("p"), (int, float))]
    print(f"p min {_quantile(ps, 0):.3f}  p50 {_quantile(ps, 0.5):.3f}  "
          f"p75 {_quantile(ps, 0.75):.3f}  p90 {_quantile(ps, 0.9):.3f}  "
          f"max {max(ps):.3f}")
    print(f"inflated (p>1.0, post-compaction residue): "
          f"{sum(1 for x in ps if x > 1.0)}")
    for t in (0.6, 0.7, 0.8):
        print(f"p>={t}: {sum(1 for x in ps if x >= t)}")
    print("actions:", dict(collections.Counter(
        e.get("action") for e in cg)))
    print("boundary:", dict(collections.Counter(
        e.get("boundary") for e in cg)))
    print("action abstains:", dict(collections.Counter(
        e.get("a_reason") for e in cg if e.get("a_reason"))))
    sess = collections.defaultdict(float)
    for e in cg:
        if isinstance(e.get("p"), (int, float)):
            sess[e.get("session_id") or "?"] = max(
                sess[e.get("session_id") or "?"], e["p"])
    print("sessions:", len(sess))
    for s, m in sorted(sess.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {s}: max p {m:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
