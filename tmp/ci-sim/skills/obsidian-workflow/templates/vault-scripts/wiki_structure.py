#!/usr/bin/env python3
"""Dump the wiki page tree (local equivalent of read_wiki_structure).

Usage:
    python wiki_structure.py

Reads frontmatter from all .md files in the vault and prints the hierarchical
page tree based on the `parent` field.
"""
import re
from pathlib import Path
from collections import defaultdict


def parse_frontmatter(text):
    fm = {}
    if not text.startswith("---"):
        return fm
    end = text.find("---", 3)
    if end == -1:
        return fm
    block = text[3:end]
    for line in block.strip().splitlines():
        m = re.match(r"^(\w+):\s*(.+)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm


def build_tree(vault_dir):
    pages = {}
    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        if not fm:
            continue
        title = fm.get("title", md_file.stem)
        parent = fm.get("parent", "null")
        if parent == "null":
            parent = None
        rel = str(md_file.relative_to(vault_dir)).replace("\\", "/")
        pages[rel] = {"title": title, "parent": parent, "path": rel}

    # Build children map
    children = defaultdict(list)
    roots = []
    for path, info in pages.items():
        if info["parent"] is None:
            roots.append(path)
        else:
            # Find parent by title or path stem
            parent_path = None
            for p, i in pages.items():
                if i["title"] == info["parent"] or p.endswith(info["parent"] + ".md") or Path(p).stem == info["parent"]:
                    parent_path = p
                    break
            if parent_path:
                children[parent_path].append(path)
            else:
                roots.append(path)

    return pages, children, roots


def print_tree(pages, children, roots, indent=0):
    for root in sorted(roots):
        info = pages[root]
        prefix = "  " * indent
        print(f"{prefix}- {info['title']}  ({info['path']})")
        print_tree(pages, children, children.get(root, []), indent + 1)


def main():
    vault_dir = Path(__file__).parent.resolve()
    pages, children, roots = build_tree(vault_dir)
    print(f"Wiki structure ({len(pages)} pages):")
    print()
    print_tree(pages, children, roots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
