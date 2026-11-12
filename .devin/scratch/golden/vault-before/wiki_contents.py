#!/usr/bin/env python3
"""Dump the full content of a wiki page (local equivalent of read_wiki_contents).

Usage:
    python wiki_contents.py --page "02-Architecture"
    python wiki_contents.py --page "Modules/Auth"
"""
import argparse
from pathlib import Path


def find_page(vault_dir, name):
    # Try exact file match
    candidates = [
        vault_dir / f"{name}.md",
        vault_dir / f"{name}",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    # Try by stem
    for md in vault_dir.rglob("*.md"):
        if md.stem == name or md.name == name or str(md.relative_to(vault_dir)).replace("\\", "/") == name:
            return md
    # Try by title in frontmatter
    import re
    for md in vault_dir.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1 and f'title: "{name}"' in text[3:end]:
                return md
    return None


def main():
    parser = argparse.ArgumentParser(description="Dump wiki page content.")
    parser.add_argument("--page", required=True, help="Page name, path, or title")
    args = parser.parse_args()

    vault_dir = Path(__file__).parent.resolve()
    page = find_page(vault_dir, args.page)
    if page is None:
        print(f"Page not found: {args.page}")
        return 1

    print(page.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
