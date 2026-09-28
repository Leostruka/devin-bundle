#!/usr/bin/env python3
"""HTTP scraping via Scrapling Fetcher (curl_cffi): fetch a URL, select
nodes, print JSON. TLS impersonation + SSRF-safe redirects on.

--adaptive fingerprints matches into local SQLite so selectors survive
markup churn (class renames). --browser tiers are consent-gated: they
need `python -m scrapling.cli.install` (~300-600MB first-run download)
which is never run by this tool.

JSON out: {"ok": true, "status": int, "url": final_url, "count": N,
"nodes": [{tag, text, attrib}], "adaptive": {...} when used}.
Exit 0 ok / 1 fetch+select error / 2 usage error.
"""
import argparse
import json
import sys

import st_common


def main():
    ap = argparse.ArgumentParser(prog="scrape.py")
    ap.add_argument("url")
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--css")
    sel.add_argument("--xpath")
    ap.add_argument("--impersonate", default="chrome",
                    help="TLS fingerprint (chrome/edge/safari/firefox/tor "
                         "+ versions)")
    ap.add_argument("--adaptive", action="store_true",
                    help="auto_save + adaptive relocate via local SQLite")
    ap.add_argument("--identifier", default=None,
                    help="adaptive storage key name (default: selector)")
    ap.add_argument("--browser", choices=["dynamic", "stealthy"],
                    default=None,
                    help="opt-in browser tier; needs prior "
                         "`python -m scrapling.cli.install`")
    args = ap.parse_args()

    if args.browser and not st_common.browser_tier_installed():
        st_common.fail(
            "feature_off:browser_tier_not_installed - run "
            "`python -m scrapling.cli.install` in the extension venv "
            "first (~300-600MB download, explicit user consent)",
            code=2)

    try:
        from scrapling import Fetcher
    except ImportError:
        st_common.fail("missing_dep:scrapling - install requirements.txt "
                       "into the extension .venv", code=2)

    fetcher = Fetcher()
    cfg = st_common.selector_config(args.adaptive)
    try:
        page = fetcher.get(args.url, impersonate=args.impersonate,
                           follow_redirects="safe",
                           selector_config=cfg or {})
    except Exception as exc:
        st_common.fail(f"fetch_error:{exc}")

    selector = args.css or args.xpath
    use_css = bool(args.css)
    identifier = args.identifier or selector
    adaptive_meta = None
    try:
        if args.adaptive:
            pick = page.css if use_css else page.xpath
            found = pick(selector, identifier=identifier,
                         adaptive=True, auto_save=True)
            adaptive_meta = {"auto_save": True, "identifier": identifier,
                             "storage": str(st_common.storage_root())}
        else:
            found = page.css(selector) if use_css else page.xpath(selector)
    except Exception as exc:
        st_common.fail(f"selector_error:{exc}")

    nodes = [st_common.node_to_dict(el) for el in found]
    out = {"ok": True,
           "status": getattr(page, "status", None),
           "url": getattr(page, "url", args.url),
           "count": len(nodes), "nodes": nodes}
    if adaptive_meta:
        out["adaptive"] = adaptive_meta
    print(json.dumps(out))


if __name__ == "__main__":
    main()
