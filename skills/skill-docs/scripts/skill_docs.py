#!/usr/bin/env python3
"""skill-docs - deterministic search/get/manifest over skills/*/SKILL.md.

Stdlib only, no network. Envelope v2 (api_version 2 + meta.answered_by).
Corpus root: BUNDLE_SKILLS_DIR -> skills/ walking up from this script ->
~/.config/devin/skills -> %APPDATA%/devin/skills.

Usage:
    python skill_docs.py search <query>
    python skill_docs.py get <name> [--meta]
    python skill_docs.py manifest
    python skill_docs.py doctor
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

WRAPPER = "skill-docs"
_FM_RE = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_FIELD_RE = re.compile(r"^(name|description):\s*(.*)", re.MULTILINE)
# Skill dir names only - no separators, no leading dot: path-traversal proof.
_SAFE_NAME = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]*\Z")


_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _stamp(payload):
    if isinstance(payload, dict):
        meta = payload.get("meta")
        if not isinstance(meta, dict):
            meta = {}
            payload["meta"] = meta
        payload["api_version"] = 2
        meta.setdefault("answered_by",
                        {"bundle": _bundle_version(), "wrapper": WRAPPER})
    return payload


def _emit(payload, code=0):
    text = json.dumps(_stamp(payload), sort_keys=True, indent=2,
                      ensure_ascii=False)
    sys.stdout.buffer.write((text + "\n").encode("utf-8"))
    return code


def _corpus_root():
    env = os.environ.get("BUNDLE_SKILLS_DIR")
    if env:
        return Path(env)
    for parent in Path(__file__).resolve().parents:
        cand = parent / "skills"
        if cand.is_dir() and (cand / "skill-docs").is_dir():
            return cand
    for cand in (Path.home() / ".config" / "devin" / "skills",):
        if cand.is_dir():
            return cand
    appdata = os.environ.get("APPDATA")
    if appdata:
        cand = Path(appdata) / "devin" / "skills"
        if cand.is_dir():
            return cand
    return None


def _parse_skill(skill_md):
    """Return (meta_dict, body, error). utf-8-sig so a stray BOM cannot
    silently hide the frontmatter block."""
    try:
        raw = skill_md.read_text(encoding="utf-8-sig")
    except OSError as e:
        return {}, "", str(e)
    meta = {}
    body = raw
    m = _FM_RE.match(raw)
    if m:
        for fm in _FIELD_RE.finditer(m.group(1)):
            meta[fm.group(1)] = fm.group(2).strip()
        body = raw[m.end():]
    meta.setdefault("name", skill_md.parent.name)
    meta.setdefault("description", "")
    return meta, body, None


def _corpus(root):
    items = []
    for entry in sorted(root.iterdir()):
        skill_md = entry / "SKILL.md"
        if entry.is_dir() and skill_md.is_file():
            meta, body, err = _parse_skill(skill_md)
            items.append({"name": entry.name, "meta": meta, "body": body,
                          "files": sorted(p.name for p in entry.iterdir()
                                          if p.is_file()),
                          "error": err})
    return items


def _tokens(text):
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if t}


def cmd_search(args):
    root = _corpus_root()
    if root is None or not root.is_dir():
        return _emit({"ok": False, "error": "no skills corpus found"}, 1)
    q = _tokens(args.query)
    if not q:
        return _emit({"ok": False, "error": "empty query"}, 1)
    hits = []
    for it in _corpus(root):
        name_l = it["name"].lower()
        desc = it["meta"].get("description", "")
        score = 0
        name_tok = _tokens(name_l)
        desc_tok = _tokens(desc)
        body_tok = _tokens(it["body"])
        score += 10 * len(q & {name_l})
        score += 6 * len(q & name_tok)
        score += 3 * len(q & desc_tok)
        score += 1 * len(q & body_tok)
        if args.query.strip().lower() == name_l:
            score += 50
        if score > 0:
            hit = {"name": it["name"], "score": score,
                   "description": desc}
            hit["tier"] = ("name" if (q & name_tok or args.query.strip().lower() == name_l)
                           else "description" if q & desc_tok else "body")
            hits.append(hit)
    hits.sort(key=lambda h: (-h["score"], h["name"]))
    hits = hits[:max(0, args.limit)]
    return _emit({"ok": True, "query": args.query, "root": str(root),
                  "count": len(hits), "results": hits})


def cmd_get(args):
    if not _SAFE_NAME.match(args.name):
        return _emit({"ok": False,
                      "error": f"invalid skill name: {args.name!r}"}, 1)
    root = _corpus_root()
    if root is None or not root.is_dir():
        return _emit({"ok": False, "error": "no skills corpus found"}, 1)
    skill_md = (root / args.name / "SKILL.md").resolve()
    if root.resolve() not in skill_md.parents:
        return _emit({"ok": False,
                      "error": f"invalid skill name: {args.name!r}"}, 1)
    if not skill_md.is_file():
        return _emit({"ok": False, "error": f"skill not found: {args.name}"}, 1)
    meta, body, err = _parse_skill(skill_md)
    if err:
        return _emit({"ok": False, "error": err}, 1)
    out = {"ok": True, "name": args.name, "meta": meta,
           "files": sorted(p.name for p in skill_md.parent.iterdir()
                           if p.is_file())}
    if not args.meta:
        out["body"] = body.strip()
    out["sha256"] = hashlib.sha256(
        skill_md.read_bytes()).hexdigest()
    return _emit(out)


def cmd_manifest(args):
    root = _corpus_root()
    if root is None or not root.is_dir():
        return _emit({"ok": False, "error": "no skills corpus found"}, 1)
    items = _corpus(root)
    return _emit({"ok": True, "root": str(root), "count": len(items),
                  "skills": [{"name": it["name"],
                              "description": it["meta"].get("description", ""),
                              "files": it["files"]} for it in items]})


def cmd_doctor(args):
    root = _corpus_root()
    if root is None or not root.is_dir():
        return _emit({"ok": False, "error": "no skills corpus found",
                      "root": str(root) if root else None}, 1)
    items = _corpus(root)
    bad = [{"name": it["name"], "error": it["error"]}
           for it in items if it["error"] or not it["meta"].get("description")]
    return _emit({"ok": not bad, "root": str(root),
                  "skill_count": len(items),
                  "unreadable_or_missing_description": bad}, 1 if bad else 0)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(fn=cmd_search)
    g = sub.add_parser("get")
    g.add_argument("name")
    g.add_argument("--meta", action="store_true")
    g.set_defaults(fn=cmd_get)
    m = sub.add_parser("manifest")
    m.set_defaults(fn=cmd_manifest)
    d = sub.add_parser("doctor")
    d.set_defaults(fn=cmd_doctor)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except Exception as e:  # fail loud, never a bare traceback to agents
        return _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, 1)


if __name__ == "__main__":
    sys.exit(main())
