#!/usr/bin/env python3
"""S1 probe harness - CU real-time research (Phase 2).

Standardized task: spawned cmd PTY emits a marker after a deterministic
delay; measures perception strategies against the SAME task.

Marker is assembled at runtime (set "M=CU_READY_" & echo %M%MARK42) so the
literal pattern never appears in the command string - no input-echo
false positives.

Each variant records: calls (CLI invocations), per-call wall ms,
detect_s (time from fire to marker observed), total_s.
Results printed as one JSON object + written to %TEMP%.
"""
import json
import os
import subprocess
import tempfile
import time

PY = os.path.expandvars(
    r"%APPDATA%/devin/extensions/computer-use/.venv/Scripts/python.exe")
EXT = os.path.expandvars(r"%APPDATA%/devin/extensions/computer-use")
TERM = os.path.join(EXT, "terminal.py")
MARKER = "CU_READY_MARK42"


def call(args, timeout=60, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    t0 = time.time()
    r = subprocess.run([PY, TERM] + args, capture_output=True, text=True,
                       timeout=timeout, env=env)
    return (time.time() - t0) * 1000, r.stdout.strip()


def fire_text(delay_s):
    """One send payload, two lines. ConPTY submits on \\r, not \\n
    (measured: \\n echoes the line without executing; the link pump at
    cu_terminal.py:1133 appends \\r for the same reason). `set` must be
    its own line: cmd expands %M% at parse time per line."""
    n = max(2, int(delay_s) + 1)
    return ('set "M=CU_READY_"\r'
            f'ping -n {n} 127.0.0.1 >nul & echo %M%MARK42\r')


def v_poll(delay_s, interval=0.5, cap=20):
    """Baseline: agent-poll loop - send, then recv --tail until match."""
    res = {"variant": "poll", "delay": delay_s, "calls": []}
    ms, out = call(["spawn", "--shell", "cmd"])
    sid = json.loads(out)["session"]
    res["calls"].append(round(ms, 1))
    try:
        ms, _ = call(["send-to", sid, fire_text(delay_s)])
        res["calls"].append(round(ms, 1))
        t0 = time.time()
        while time.time() - t0 < cap:
            ms, out = call(["recv", sid, "--tail", "8"])
            res["calls"].append(round(ms, 1))
            if MARKER in out:
                break
            time.sleep(interval)
        res["total_s"] = round(time.time() - t0, 3)
        res["found"] = MARKER in out
    finally:
        call(["close", sid])
    res["n_calls"] = len(res["calls"])
    return res


def v_wait(delay_s):
    """H3: single blocking recv --wait."""
    res = {"variant": "wait", "delay": delay_s, "calls": []}
    ms, out = call(["spawn", "--shell", "cmd"])
    sid = json.loads(out)["session"]
    res["calls"].append(round(ms, 1))
    try:
        ms, _ = call(["send-to", sid, fire_text(delay_s)])
        res["calls"].append(round(ms, 1))
        t0 = time.time()
        ms, out = call(["recv", sid, "--wait", MARKER, "--timeout", "15"])
        res["calls"].append(round(ms, 1))
        res["total_s"] = round(time.time() - t0, 3)
        res["found"] = MARKER in out
    finally:
        call(["close", sid])
    res["n_calls"] = len(res["calls"])
    return res


def v_batch(delay_s):
    """H4: terminal.py exec - spawn+send+wait+close inside ONE CLI call
    (terminal.py:233-240). `call echo %M%` re-expands after `set` ran,
    so the marker is assembled at runtime within a single line."""
    res = {"variant": "batch", "delay": delay_s, "calls": []}
    n = max(2, int(delay_s) + 1)
    cmd = (f'set "M=CU_READY_" & ping -n {n} 127.0.0.1 >nul '
           f'& call echo %M%MARK42')
    t0 = time.time()
    ms, out = call(["exec", cmd, "--wait", MARKER, "--timeout", "15"])
    res["calls"].append(round(ms, 1))
    res["total_s"] = round(time.time() - t0, 3)
    res["found"] = MARKER in out
    res["n_calls"] = len(res["calls"])
    return res


def main():
    delays = [1, 2, 3, 2, 4]
    variants = {"poll": [], "wait": [], "batch": []}
    for d in delays:
        variants["poll"].append(v_poll(d))
        variants["wait"].append(v_wait(d))
        variants["batch"].append(v_batch(d))
    for name, runs in variants.items():
        det = [r["total_s"] for r in runs]
        nc = [r["n_calls"] for r in runs]
        found = sum(1 for r in runs if r.get("found"))
        print(f"== {name}: total_s={det} n_calls={nc} "
              f"found={found}/{len(runs)}")
    out_path = os.path.join(tempfile.gettempdir(), "cu-rt-s1-results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(variants, f, indent=1)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
