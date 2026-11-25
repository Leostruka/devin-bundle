"""Dead-link tripwire: markdown links to relative paths inside
skills/**/*.md must resolve to files on disk.

Found 2026-11-25: 19 dead links across 11 files - mostly mode/reference
files pointing at siblings one dir up or in reference/ (mode files
ported without path adjustment). Skips fenced code blocks (example
content) and template placeholders like ](link)."""
import os
import re
import urllib.parse

FENCE = re.compile(r"^```")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
PLACEHOLDERS = {"link"}


def _strip_fences(src):
    out, fenced = [], False
    for line in src.splitlines():
        if FENCE.match(line):
            fenced = not fenced
        if not fenced:
            out.append(line)
    return "\n".join(out)


def _dead_links(root="skills"):
    dead = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            src = _strip_fences(open(p, encoding="utf-8").read())
            for m in LINK.finditer(src):
                link = urllib.parse.unquote(m.group(1))
                if link.startswith(("http://", "https://", "mailto:",
                                    "file:")) or link in PLACEHOLDERS:
                    continue
                tgt = os.path.normpath(os.path.join(dirpath, link))
                if not os.path.exists(tgt):
                    dead.append(p + " -> " + link)
    return dead


def test_no_dead_relative_links_in_skills():
    dead = _dead_links()
    assert dead == [], "\n".join(dead)
