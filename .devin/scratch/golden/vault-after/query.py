#!/usr/bin/env python3
"""Keyword search across the wiki (local equivalent of ask_question).

Usage:
    python query.py --query "authentication flow"
    python query.py --query "database schema" --max-results 10

Searches all .md files for the query terms, returns matching pages with
context snippets and source citations.
"""
import argparse
import re
from pathlib import Path


def search(vault_dir, query, max_results=5):
    terms = [t.lower() for t in query.split() if t]
    results = []

    for md_file in vault_dir.rglob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        text_lower = text.lower()
        score = sum(1 for term in terms if term in text_lower)
        if score == 0:
            continue

        # Extract context snippets around matches
        snippets = []
        for term in terms:
            for m in re.finditer(re.escape(term), text_lower):
                start = max(0, m.start() - 80)
                end = min(len(text), m.end() + 80)
                snippet = text[start:end].replace("\n", " ").strip()
                snippets.append(f"...{snippet}...")
                if len(snippets) >= 3:
                    break
            if len(snippets) >= 3:
                break

        # Extract source citations
        sources = set()
        for m in re.finditer(r"source:\s*[`]?([^\s`]+)[`]?", text):
            sources.add(m.group(1).strip())

        rel = str(md_file.relative_to(vault_dir)).replace("\\", "/")
        results.append({
            "page": rel,
            "score": score,
            "snippets": snippets,
            "sources": sorted(sources)[:5],
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def main():
    parser = argparse.ArgumentParser(description="Search the wiki by keyword.")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=5, help="Max results to return")
    args = parser.parse_args()

    vault_dir = Path(__file__).parent.resolve()
    results = search(vault_dir, args.query, args.max_results)

    if not results:
        print(f"No results for: {args.query}")
        return 0

    print(f"Search results for '{args.query}' ({len(results)} pages):")
    print()
    for r in results:
        print(f"## {r['page']}  (score: {r['score']})")
        for s in r["snippets"]:
            print(f"  {s}")
        if r["sources"]:
            print(f"  Sources: {', '.join(r['sources'])}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
