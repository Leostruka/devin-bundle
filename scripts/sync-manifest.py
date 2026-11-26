#!/usr/bin/env python3
"""Sync manifest.json counts and export hashes with disk state.

Reproduced failure (2026-11-26): 73 skill export_hash entries were stale
because audit validated script/agent hashes but never skill hashes, and no
tool repaired drift. This script is the repair path; audit checks are the
detection path.

Modes:
  (default)   apply: rewrite manifest.json with corrected counts/hashes
  --check     read-only: exit 1 when drift exists, 0 when clean

Never adds or removes skill/agent/script entries: unlisted-on-disk and
missing-on-disk are reported for a human decision, and --check fails on
them. Counts follow the audit canon: entries on disk.
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_envelope import bind

_stamp, _dumps = bind("sync-manifest")


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def hash_variants(path):
    """Same tolerance as audit text_hash_matches: raw, lf, crlf."""
    with open(path, "rb") as fh:
        raw = fh.read()
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {hashlib.sha256(d).hexdigest() for d in (raw, lf, crlf)}


def is_stale(path, expected):
    return expected.lower() not in hash_variants(path)


def collect():
    skills = sorted(
        d for d in os.listdir("skills")
        if os.path.isdir(os.path.join("skills", d))
        and os.path.isfile(os.path.join("skills", d, "SKILL.md")))
    agents = sorted(
        f[:-3] for f in os.listdir("agents") if f.endswith(".md"))
    # .js helpers (e.g. mermaid-parse-check.js) are listed in the
    # manifest but excluded from script_count, which counts .py only.
    scripts = sorted(
        f for f in os.listdir("scripts")
        if f.endswith((".py", ".js")))
    return skills, agents, scripts


def diff_state(manifest, skills, agents, scripts):
    changes, problems = [], []
    entries = {s["name"]: s for s in manifest.get("skills", [])}
    for name in skills:
        entry = entries.get(name)
        if entry is None:
            problems.append("unlisted skill on disk: " + name)
            continue
        path = os.path.join("skills", name, "SKILL.md")
        if is_stale(path, entry.get("export_hash", "")):
            changes.append(("skill", name, sha(path)))
    for name in entries:
        if name not in skills:
            problems.append("manifest skill missing on disk: " + name)
    if manifest.get("skill_count") != len(skills):
        changes.append(("count", "skill_count", len(skills)))
    agent_entries = {a["name"]: a for a in manifest.get("agents", [])}
    for name in agents:
        entry = agent_entries.get(name)
        if entry is None:
            problems.append("unlisted agent on disk: " + name)
            continue
        path = os.path.join("agents", name + ".md")
        if is_stale(path, entry.get("export_hash", "")):
            changes.append(("agent", name, sha(path)))
    for name in agent_entries:
        if name not in agents:
            problems.append("manifest agent missing on disk: " + name)
    if manifest.get("agent_count") != len(agents):
        changes.append(("count", "agent_count", len(agents)))
    script_entries = {s["name"]: s for s in manifest.get("scripts", [])}
    for name in scripts:
        entry = script_entries.get(name)
        if entry is None:
            problems.append("unlisted script on disk: " + name)
            continue
        spath = os.path.join("scripts", name)
        if is_stale(spath, entry.get("export_hash", "")):
            changes.append(("script", name, sha(spath)))
    for name in script_entries:
        if name not in scripts:
            problems.append("manifest script missing on disk: " + name)
    py_count = sum(1 for s in scripts if s.endswith(".py"))
    if manifest.get("script_count") != py_count:
        changes.append(("count", "script_count", py_count))
    return changes, problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not os.path.isfile("manifest.json"):
        print(_dumps({"ok": False, "error": "manifest.json not in cwd"}))
        return 2
    with open("manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    skills, agents, scripts = collect()
    changes, problems = diff_state(manifest, skills, agents, scripts)
    if args.check:
        ok = not changes and not problems
        print(_dumps({
            "ok": ok, "drift": len(changes),
            "items": [{"type": c, "name": n} for c, n, _ in changes],
            "problems": problems}))
        return 0 if ok else 1
    entries = {s["name"]: s for s in manifest.get("skills", [])}
    agent_entries = {a["name"]: a for a in manifest.get("agents", [])}
    script_entries = {s["name"]: s for s in manifest.get("scripts", [])}
    applied = []
    for kind, name, want in changes:
        if kind == "skill" and name in entries:
            entries[name]["export_hash"] = want
            applied.append(kind + ":" + name)
        elif kind == "agent" and name in agent_entries:
            agent_entries[name]["export_hash"] = want
            applied.append(kind + ":" + name)
        elif kind == "script" and name in script_entries:
            script_entries[name]["export_hash"] = want
            applied.append(kind + ":" + name)
        elif kind == "count":
            manifest[name] = want
            applied.append(kind + ":" + name)
    if applied:
        with open("manifest.json", "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    print(_dumps({
        "ok": True, "applied": applied, "count": len(applied),
        "problems": problems}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
