#!/usr/bin/env python3
"""Sync manifest.json counts and export hashes with disk state.

Reproduced failure (2026-11-26): 73 skill export_hash entries were stale
because audit validated script/agent hashes but never skill hashes, and no
tool repaired drift. This script is the repair path; audit checks are the
detection path.

Modes:
  (default)   apply: rewrite manifest.json with corrected counts/hashes
  --check     read-only: exit 1 when drift exists, 0 when clean

Never adds or removes skill/agent entries: unlisted-on-disk and
missing-on-disk are reported for a human decision. Counts always reflect
the entries actually present in the manifest.
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
    return skills, agents


def diff_state(manifest, skills, agents):
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
    if manifest.get("skill_count") != len(manifest.get("skills", [])):
        changes.append(("count", "skill_count", len(manifest.get("skills", []))))
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
    if manifest.get("agent_count") != len(manifest.get("agents", [])):
        changes.append(("count", "agent_count", len(manifest.get("agents", []))))
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
    skills, agents = collect()
    changes, problems = diff_state(manifest, skills, agents)
    if args.check:
        ok = not changes
        print(_dumps({
            "ok": ok, "drift": len(changes),
            "items": [{"type": c, "name": n} for c, n, _ in changes],
            "problems": problems}))
        return 0 if ok else 1
    entries = {s["name"]: s for s in manifest.get("skills", [])}
    agent_entries = {a["name"]: a for a in manifest.get("agents", [])}
    applied = []
    for kind, name, want in changes:
        if kind == "skill" and name in entries:
            entries[name]["export_hash"] = want
            applied.append(kind + ":" + name)
        elif kind == "agent" and name in agent_entries:
            agent_entries[name]["export_hash"] = want
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
