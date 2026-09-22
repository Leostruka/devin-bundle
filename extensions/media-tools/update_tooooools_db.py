#!/usr/bin/env python3
"""Refresh the tooooools.app creative-tools catalog.

Scrapes https://www.tooooools.app/ (SSR — plain GET, no JS rendering) for the
tool links in the drawer nav, then fetches each tool page for its og:title and
meta description. Writes knowledge_bases/creative_tooooools.json.

Usage:
    update_tooooools_db.py [--out PATH] [--dry-run]
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://www.tooooools.app"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) devin-bundle-catalog"}
OUT_DEFAULT = os.path.join(os.path.dirname(__file__), "knowledge_bases",
                           "creative_tooooools.json")

LINK_RE = re.compile(r'href="(/(?:effects|animate)/[a-z0-9-]+)"')
TITLE_RE = re.compile(r'<meta property="og:title" content="([^"]+)"')
DESC_RE = re.compile(r'<meta name="description" content="([^"]+)"')
TAG_RE = re.compile(r'<[^>]+>')


def fetch(path):
    req = urllib.request.Request(BASE + path, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="replace")


def clean(html_text):
    return html.unescape(TAG_RE.sub("", html_text)).strip()


def scrape(dry_run=False):
    home = fetch("/")
    paths = sorted(set(LINK_RE.findall(home)))
    tools = []
    for path in paths:
        category = path.strip("/").split("/")[0]
        try:
            page = fetch(path)
            title_m = TITLE_RE.search(page)
            desc_m = DESC_RE.search(page)
            name = clean(title_m.group(1)) if title_m else path.rsplit("/", 1)[-1]
            desc = clean(desc_m.group(1)) if desc_m else ""
        except Exception as e:
            name, desc = path.rsplit("/", 1)[-1], f"scrape error: {e}"
        tools.append({
            "name": name,
            "url": BASE + path,
            "category": category,
            "description": desc,
        })
        if not dry_run:
            time.sleep(0.3)  # polite crawl
    return {
        "source": BASE,
        "note": "Curated browser-based creative tools catalog. Consult when the "
                "user asks for a visual effect not covered by local media-tools "
                "generators; suggest the tool or implement a local equivalent.",
        "tool_count": len(tools),
        "tools": tools,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--dry-run", action="store_true",
                    help="fetch and print, do not write")
    args = ap.parse_args()
    db = scrape(dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(db, indent=1, ensure_ascii=False))
        return
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(db, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(json.dumps({"ok": True, "out": args.out,
                      "tool_count": db["tool_count"]}))


if __name__ == "__main__":
    main()
