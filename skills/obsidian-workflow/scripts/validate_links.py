#!/usr/bin/env python3
"""Validate wikilinks in an Obsidian wiki directory."""

import argparse
import os
import re
import sys

LINK_PATTERN = re.compile(r'\[\[([^\]]+?)\]\]')


def parse_target(raw):
    parts = []
    current = ''
    i = 0
    while i < len(raw):
        if i < len(raw) - 1 and raw[i] == '\\' and raw[i + 1] == '|':
            parts.append(current)
            current = ''
            i += 2
        elif raw[i] == '|':
            parts.append(current)
            current = ''
            i += 1
        else:
            current += raw[i]
            i += 1
    parts.append(current)
    return parts[0].strip()


def is_false_positive(tgt):
    if tgt.startswith('#') or tgt.startswith('...') or tgt.startswith(':') or tgt.startswith('byte,'):
        return True
    return False


def validate_links(wiki_dir):
    if not os.path.isdir(wiki_dir):
        print(f"MISSING: {wiki_dir}")
        return 1

    md_files = []
    for root, dirs, files in os.walk(wiki_dir):
        for f in files:
            if f.endswith('.md'):
                md_files.append(os.path.join(root, f))

    all_basenames = set()
    all_links = {}
    for fp in md_files:
        with open(fp, 'r', encoding='utf-8') as fh:
            for i, line in enumerate(fh, 1):
                for m in LINK_PATTERN.finditer(line):
                    tgt = parse_target(m.group(1))
                    all_links.setdefault(tgt, []).append((os.path.relpath(fp, wiki_dir), i))
        all_basenames.add(os.path.splitext(os.path.basename(fp))[0])

    broken = []
    for tgt, refs in sorted(all_links.items()):
        if is_false_positive(tgt):
            continue
        tgt_clean = tgt.replace('\\', '/')
        tgt_base = tgt_clean.split('/')[-1]
        found = tgt_base in all_basenames
        if not found:
            for b in all_basenames:
                if tgt_clean == b or tgt_clean.endswith('/' + b):
                    found = True
                    break
        if not found:
            broken.append((tgt, refs))

    print(f"Total .md files: {len(md_files)}")
    print(f"Unique wikilink targets: {len(all_links)}")
    print(f"Broken links: {len(broken)}")

    if broken:
        print("\n=== BROKEN WIKILINKS ===")
        for tgt, refs in broken:
            print(f"\n  [[{tgt}]] referenced from:")
            for src, line in refs:
                print(f"    - {src}:{line}")
    else:
        print("\nAll wikilinks resolve. 0 broken.")

    return 0 if not broken else 1


def main():
    parser = argparse.ArgumentParser(description='Validate wikilinks in a wiki directory')
    parser.add_argument('--wiki', required=True, help='Path to _wiki directory')
    args = parser.parse_args()
    sys.exit(validate_links(args.wiki))


if __name__ == '__main__':
    main()
