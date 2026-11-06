#!/usr/bin/env python3
"""design_lint.py - deterministic static linter for AI-UI antipatterns.

Usage: design_lint.py <dir|file> [--json] [--list-rules] [--ignore FILE]
exit 0 = clean, 1 = usage/error, 2 = findings.

Ignores: a JSON file {"files": [...], "rules": [...]} persisted via
--ignore FILE (default .designlintignore in linted dir).
"""
import json
import os
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rules_registry import ANTIPATTERNS  # noqa: E402
import checks  # noqa: E402

TEXT_EXTS = {".html", ".htm", ".css", ".tsx", ".jsx", ".vue", ".svelte"}
_STYLE_RE = None


def _style_blocks(text):
    import re
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", text or "",
                                re.S | re.I))


def lint_file(path):
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    css = _style_blocks(text)
    if path.endswith(".css"):
        css = text + "\n" + css
    findings = []
    for rid, fn in checks.CHECKS.items():
        try:
            findings.extend(fn(text, css, path))
        except Exception:
            continue
    return findings


def _load_ignores(ignore_file):
    try:
        d = json.loads(Path(ignore_file).read_text(encoding="utf-8"))
        return set(d.get("files", [])), set(d.get("rules", []))
    except (OSError, json.JSONDecodeError):
        return set(), set()


def run(target, ignore_file=None):
    target = Path(target)
    if ignore_file is None:
        ignore_file = (target if target.is_dir()
                       else target.parent) / ".designlintignore"
    ig_files, ig_rules = _load_ignores(ignore_file)

    files = []
    if target.is_dir():
        for p in sorted(target.rglob("*")):
            if p.is_file() and p.suffix in TEXT_EXTS \
                    and "__pycache__" not in p.parts:
                files.append(str(p))
    elif target.is_file():
        files.append(str(target))

    findings = []
    for f in files:
        rel = os.path.relpath(f)
        if rel in ig_files or f in ig_files:
            continue
        findings.extend(f for f in lint_file(f) if f["rule"] not in ig_rules)

    skipped = {"browser": sum(1 for r in ANTIPATTERNS
                              if r["scope"] == "browser"),
                   "designsys": sum(1 for r in ANTIPATTERNS
                                    if r["scope"] == "designsys"),
                   "unported": sum(1 for r in ANTIPATTERNS
                                   if r["scope"] == "static"
                                   and r["id"] not in checks.CHECKS)}
    return findings, skipped


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if "--list-rules" in flags:
        for r in ANTIPATTERNS:
            impl = "yes" if r["id"] in checks.CHECKS else r["scope"]
            print(f"{r['id']}\t{r['category']}\t{impl}\t{r['name']}")
        print(f"{len(ANTIPATTERNS)} rules "
              f"({len(checks.CHECKS)} implemented static)")
        return 0
    if not args:
        print(__doc__.strip())
        return 1
    ignore = None
    if "--ignore" in flags:
        i = argv.index("--ignore")
        ignore = Path(argv[i + 1])
    findings, skipped = run(args[0], ignore)
    if "--json" in flags:
        print(json.dumps({"findings": findings, "skipped": skipped,
                          "count": len(findings)}, indent=1,
                         ensure_ascii=False))
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']}: {f['rule']}: {f['evidence']}")
        print(f"{len(findings)} finding(s); skipped: {skipped}")
    return 2 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
