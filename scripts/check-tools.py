#!/usr/bin/env python3
"""check-tools.py - validate tools.json + byte-identity of renders.

Golden rule (upstream agency-agents tools.json contract): two renders of
the same tool/format must produce byte-identical output. Drift means a
renderer is non-deterministic (timestamps, randomness, env leaks) and the
install ledger cannot trust rendered_hash.

Usage: python scripts/check-tools.py [--json]
Exit 0 = pass; 1 = schema or determinism failure.
"""
import json
import os
import subprocess
import sys

from bundle_envelope import bind


_stamp, _dumps = bind("check-tools")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED_KEYS = ("label", "format", "installKind", "dest", "enabled")


def _load():
    path = os.path.join(ROOT, "tools.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_schema(data):
    """Return list of schema problems (empty = valid)."""
    problems = []
    tools = data.get("tools")
    if not isinstance(tools, dict) or not tools:
        return ["tools.json: missing non-empty 'tools' object"]
    for name, tool in tools.items():
        if not isinstance(tool, dict):
            problems.append(f"{name}: not an object")
            continue
        for key in REQUIRED_KEYS:
            if key not in tool:
                problems.append(f"{name}: missing '{key}'")
        if tool.get("enabled") and not tool.get("renderer"):
            problems.append(f"{name}: enabled but no renderer")
    return problems


def _expand_dest(dest):
    """Expand %VAR%, $VAR and ~ in a dest template."""
    out = dest
    for key, val in os.environ.items():
        out = out.replace("%" + key + "%", val)
    return os.path.expandvars(os.path.expanduser(out))


def check_byte_identity(renderer, dest):
    """Run `renderer dest` twice; returns (identical, detail)."""
    argv = [sys.executable, os.path.join(ROOT, renderer)]
    if dest:
        argv.append(_expand_dest(dest))
    outputs = []
    for _ in range(2):
        try:
            proc = subprocess.run(argv, capture_output=True, cwd=ROOT,
                                  timeout=120)
        except subprocess.TimeoutExpired:
            return False, "renderer timeout after 120s"
        if proc.returncode != 0:
            return False, f"renderer exit {proc.returncode}"
        outputs.append(proc.stdout)
    if outputs[0] == outputs[1]:
        return True, f"{len(outputs[0])} bytes identical"
    diff = next((i for i, (a, b) in enumerate(
        zip(outputs[0], outputs[1])) if a != b), -1)
    return False, f"outputs diverge at byte {diff}"


def main():
    as_json = "--json" in sys.argv
    report = {"schema": [], "renders": {}}
    try:
        data = _load()
    except (OSError, ValueError) as e:
        report["schema"] = [f"tools.json unreadable: {e}"]
        print(_dumps(report, indent=2) if as_json else
              f"FAIL tools.json unreadable: {e}")
        return 1
    report["schema"] = validate_schema(data)
    ok = not report["schema"]
    for name, tool in data["tools"].items():
        if not tool.get("enabled"):
            report["renders"][name] = "skipped (disabled)"
            continue
        renderer = tool.get("renderer")
        if not renderer:
            continue
        identical, detail = check_byte_identity(
            renderer, tool.get("dest"))
        report["renders"][name] = ("PASS" if identical else "FAIL") \
            + " " + detail
        ok = ok and identical
    if as_json:
        print(_dumps(report, indent=2, sort_keys=True))
    else:
        for p in report["schema"]:
            print("FAIL schema: " + p)
        for name, res in report["renders"].items():
            tag = "OK  " if res.startswith("PASS") else \
                "SKIP" if res.startswith("skipped") else "FAIL "
            print(f"{tag} {name}: {res}")
        if ok:
            print("check-tools: all enabled renderers deterministic")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
