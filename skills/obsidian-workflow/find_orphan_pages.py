#!/usr/bin/env python3
"""Find orphan pages in an obsidian-project-docs wiki.

An orphan page is a .md file that has NO inbound wikilinks AND NO outbound
wikilinks — it is disconnected from the wiki graph.

This script is referenced by the obsidian-workflow skill quality checklist:
    "Zero graph orphans — run find_orphan_pages.py --wiki <wiki-dir>"

Usage:
    python find_orphan_pages.py --wiki <wiki-dir> [--vault <vault-dir>]

Exit code 0 = no orphans found (or only whitelisted orphans)
Exit code 1 = orphans found
"""
import argparse
import re
import sys
from pathlib import Path


LINK_PATTERN = re.compile(r'\[\[([^\]]+?)\]\]')


def parse_target(raw: str) -> str:
    """Parse wikilink target, handling escaped pipes in markdown tables."""
    # Handle [[Target\|Alias]] → Target
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


def is_false_positive(tgt: str) -> bool:
    """Check if a wikilink target is a known false positive."""
    if tgt.startswith('#'):
        return True
    if tgt.startswith('...'):
        return True
    if tgt.startswith(':'):
        return True
    if tgt.startswith('byte,'):
        return True
    return False


def collect_wiki_files(wiki_dir: Path) -> dict:
    """Collect all .md files in the wiki directory.

    Returns dict mapping stem -> file path.
    Excludes Media/ templates (they have placeholder links).
    """
    files = {}
    for p in wiki_dir.rglob("*.md"):
        if "Media" in str(p):
            continue
        files[p.stem] = p
    return files


def build_link_graph(wiki_dir: Path) -> tuple:
    """Build inbound and outbound link graphs.

    Returns:
        outbound: dict mapping file stem -> set of target stems
        inbound: dict mapping target stem -> set of source stems
    """
    files = collect_wiki_files(wiki_dir)
    outbound = {stem: set() for stem in files}
    inbound = {stem: set() for stem in files}

    for stem, path in files.items():
        content = path.read_text(encoding="utf-8", errors="replace")
        for m in LINK_PATTERN.finditer(content):
            tgt = parse_target(m.group(1))
            if is_false_positive(tgt):
                continue
            tgt = tgt.rstrip("\\")
            # Resolve path-based links to stem
            tgt_stem = tgt.split("/")[-1]
            if tgt_stem in files:
                outbound[stem].add(tgt_stem)
                inbound[tgt_stem].add(stem)
            # Also check if full path matches
            elif tgt in files:
                outbound[stem].add(tgt)
                inbound[tgt].add(stem)

    return outbound, inbound, files


def find_orphans(wiki_dir: Path) -> list:
    """Find orphan pages (no inbound AND no outbound wikilinks)."""
    outbound, inbound, files = build_link_graph(wiki_dir)

    orphans = []
    for stem in sorted(files.keys()):
        if len(outbound[stem]) == 0 and len(inbound[stem]) == 0:
            orphans.append((stem, files[stem]))

    return orphans


def find_dead_ends(wiki_dir: Path) -> list:
    """Find dead-end pages (no outbound wikilinks but have inbound)."""
    outbound, inbound, files = build_link_graph(wiki_dir)

    dead_ends = []
    for stem in sorted(files.keys()):
        if len(outbound[stem]) == 0 and len(inbound[stem]) > 0:
            dead_ends.append((stem, files[stem], len(inbound[stem])))

    return dead_ends


def find_unreferenced(wiki_dir: Path) -> list:
    """Find unreferenced pages (no inbound wikilinks but have outbound)."""
    outbound, inbound, files = build_link_graph(wiki_dir)

    unreferenced = []
    for stem in sorted(files.keys()):
        if len(inbound[stem]) == 0 and len(outbound[stem]) > 0:
            unreferenced.append((stem, files[stem], len(outbound[stem])))

    return unreferenced


def main():
    parser = argparse.ArgumentParser(
        description="Find orphan pages in an obsidian-project-docs wiki"
    )
    parser.add_argument("--wiki", type=str, required=True,
                        help="Path to the _wiki directory")
    parser.add_argument("--vault", type=str, default=None,
                        help="Path to the vault root (for cross-vault link resolution)")
    parser.add_argument("--show-dead-ends", action="store_true",
                        help="Also show dead-end pages (no outbound links)")
    parser.add_argument("--show-unreferenced", action="store_true",
                        help="Also show unreferenced pages (no inbound links)")
    args = parser.parse_args()

    wiki_dir = Path(args.wiki)
    if not wiki_dir.is_dir():
        print(f"ERROR: {wiki_dir} is not a directory")
        sys.exit(1)

    print(f"Wiki directory: {wiki_dir}")
    print()

    # Build graph
    outbound, inbound, files = build_link_graph(wiki_dir)
    print(f"Total .md files: {len(files)}")
    total_links = sum(len(v) for v in outbound.values())
    print(f"Total wikilinks: {total_links}")
    print()

    # Find orphans
    orphans = find_orphans(wiki_dir)
    print("=== Orphan pages (no inbound AND no outbound) ===")
    if orphans:
        for stem, path in orphans:
            rel = path.relative_to(wiki_dir)
            print(f"  ORPHAN: {rel}")
        print(f"\nTotal orphans: {len(orphans)}")
    else:
        print("  OK — zero orphan pages")
    print()

    # Dead ends (optional)
    if args.show_dead_ends:
        dead_ends = find_dead_ends(wiki_dir)
        print("=== Dead-end pages (no outbound, has inbound) ===")
        if dead_ends:
            for stem, path, in_count in dead_ends:
                rel = path.relative_to(wiki_dir)
                print(f"  DEAD-END: {rel} ({in_count} inbound links)")
            print(f"\nTotal dead-ends: {len(dead_ends)}")
        else:
            print("  OK — zero dead-end pages")
        print()

    # Unreferenced (optional)
    if args.show_unreferenced:
        unreferenced = find_unreferenced(wiki_dir)
        print("=== Unreferenced pages (no inbound, has outbound) ===")
        if unreferenced:
            for stem, path, out_count in unreferenced:
                rel = path.relative_to(wiki_dir)
                print(f"  UNREF: {rel} ({out_count} outbound links)")
            print(f"\nTotal unreferenced: {len(unreferenced)}")
        else:
            print("  OK — zero unreferenced pages")
        print()

    # Summary
    print("=" * 60)
    if orphans:
        print(f"FOUND {len(orphans)} orphan page(s)")
        sys.exit(1)
    else:
        print("PASSED: zero orphan pages")
        sys.exit(0)


if __name__ == "__main__":
    main()
