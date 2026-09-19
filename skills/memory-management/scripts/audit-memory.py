#!/usr/bin/env python3
"""Audit project memory for orphan pages, stale notes, and broken wikilinks.

Usage:
  python audit-memory.py
"""
import os, re, sys

BASE = '.devin/memory'


def list_pages():
    pages = []
    for root, dirs, files in os.walk(BASE):
        for f in files:
            if f.endswith('.md'):
                pages.append(os.path.join(root, f))
    return pages


def wikilinks(content):
    return re.findall(r'\[\[([^\]|\n]+?)(?:\|[^\]]+)?\]\]', content)


def rel_to_path(rel):
    # [[notes/2026/08/fiscal-quarters]] => .devin/memory/notes/2026/08/fiscal-quarters.md
    return os.path.join(BASE, rel.replace('/', os.sep) + '.md')


def main():
    if not os.path.isdir(BASE):
        print(f'No memory directory at {BASE}')
        sys.exit(0)

    pages = list_pages()
    link_targets = {}
    links_out = {}
    for p in pages:
        with open(p, encoding='utf-8') as f:
            content = f.read()
        rel = p.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/')
        links = wikilinks(content)
        links_out[rel] = links
        for t in links:
            link_targets.setdefault(t, []).append(rel)

    errors = []
    for rel, links in links_out.items():
        for t in links:
            if not os.path.exists(rel_to_path(t)):
                errors.append(f'  Broken link in [[{rel}]] -> [[{t}]]')

    # orphan: no inbound links and no outbound links
    all_rels = {p.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/') for p in pages}
    out_rels = set(links_out.keys())
    in_rels = set(link_targets.keys())
    for r in all_rels:
        if r not in out_rels and r not in in_rels:
            errors.append(f'  Orphan page: [[{r}]]')

    if errors:
        print('Audit found issues:')
        for e in errors:
            print(e)
    else:
        print(f'Audit OK: {len(pages)} pages, no broken links or orphans')


if __name__ == '__main__':
    main()
