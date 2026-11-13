#!/usr/bin/env python3
"""changelog-refs — append missing merged-PR refs to [Unreleased] (#488).

audit.py already detects 'missing refs' from commit subjects matching
(#NNN) since the last tag; this script is the fixer half of the pair —
it appends one bullet per missing ref so the warning never needs a
hand cleanup.

  changelog-refs.py            dry-run: print the bullets it would add
  changelog-refs.py --write    append them under ## [Unreleased]

docs(changelog) PRs are skipped — they cannot cite their own number
pre-merge (same exclusion the audit check applies).
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bundle_envelope import bind  # noqa: E402

_stamp, _dumps = bind("changelog-refs")

TAG_RE = re.compile(r'\(#(\d+)\)\s*$')


def _subjects():
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    rng = f"{tag.stdout.strip()}..HEAD" if tag.returncode == 0 \
        and tag.stdout.strip() else "HEAD~60..HEAD"
    p = subprocess.run(["git", "log", rng, "--format=%s"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return [l.strip() for l in p.stdout.splitlines() if l.strip()]


def _unreleased(text):
    m = re.search(r'## \[Unreleased\](.*?)(?=\n## \[)', text, re.S)
    return m.group(1) if m else None


def missing_refs(chlog=None):
    subs = [s for s in _subjects() if TAG_RE.search(s)
            and not s.startswith("docs(changelog)")]
    if chlog is None:
        chlog = open("CHANGELOG.md", encoding="utf-8-sig").read()
    body = _unreleased(chlog)
    out = []
    for s in subs:
        num = TAG_RE.search(s).group(1)
        if body is not None and f"#{num}" not in body:
            out.append((num, s))
    return out


def main():
    write = "--write" in sys.argv
    try:
        todo = missing_refs()
    except OSError as e:
        print(_dumps({"ok": False, "error": f"io:{e}"}))
        return 1
    if not todo:
        print(_dumps({"ok": True, "missing": 0}))
        return
    bullets = [f"- {s}\n" for _n, s in todo]
    if not write:
        print(_dumps({"ok": True, "missing": len(todo)}))
        sys.stderr.writelines(bullets)
        return
    path = "CHANGELOG.md"
    try:
        text = open(path, encoding="utf-8-sig").read()
    except OSError as e:
        print(_dumps({"ok": False, "error": f"io:{e}"}))
        return 1
    i = text.find("## [Unreleased]")
    j = text.find("\n", i)
    text = text[:j + 1] + "".join(bullets) + text[j + 1:]
    open(path, "w", encoding="utf-8", newline="").write(text)
    print(_dumps({"ok": True, "appended": len(todo)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
