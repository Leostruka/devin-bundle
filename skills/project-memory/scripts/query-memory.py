#!/usr/bin/env python3
"""Simple keyword RAG over .devin/memory/.

Usage:
  python query-memory.py "fiscal quarters"
  python query-memory.py "fiscal quarters" --top 5
"""
import argparse, os, re, sys

BASE = '.devin/memory'


def score(lines, terms):
    s = '\n'.join(lines).lower()
    return sum(s.count(t.lower()) for t in terms)


def search(query, top=5):
    terms = query.lower().split()
    results = []
    for root, dirs, files in os.walk(BASE):
        for f in files:
            if not f.endswith('.md'):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding='utf-8') as fp:
                    lines = fp.readlines()
            except Exception:
                continue
            sc = score(lines, terms)
            if sc == 0:
                continue
            # find best snippet
            best_i = 0
            best_score = 0
            for i in range(len(lines)):
                window = ''.join(lines[max(0, i-2):i+3]).lower()
                ws = sum(window.count(t) for t in terms)
                if ws > best_score:
                    best_score = ws
                    best_i = i
            snippet = ''.join(lines[max(0, best_i-2):best_i+3]).strip()
            rel = path.replace(BASE + os.sep, '').replace('.md', '').replace(os.sep, '/')
            results.append((sc, rel, snippet))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top]


def main():
    p = argparse.ArgumentParser(description='Query project memory')
    p.add_argument('query', help='Search query')
    p.add_argument('--top', type=int, default=5)
    p.add_argument('--json', action='store_true', help='Output as JSON')
    args = p.parse_args()

    if not os.path.isdir(BASE):
        print(f'No memory directory at {BASE}')
        sys.exit(0)

    hits = search(args.query, args.top)
    if not hits:
        print('No matches')
        return

    if args.json:
        import json
        print(json.dumps([{'score': s, 'page': r, 'snippet': n} for s, r, n in hits], indent=2))
    else:
        for s, r, n in hits:
            print(f"\n[[{r}]] (score {s})\n{n}\n")


if __name__ == '__main__':
    main()
