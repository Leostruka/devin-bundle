#!/usr/bin/env python3
"""Offline HTML parsing: CSS/XPath selection over a file or stdin.

Zero network. Parser core only — scrapling's Selector wraps lxml and ships
in the base install tier (no fetchers extra needed). Prints JSON to stdout:
{"ok": true, "source": ..., "count": N, "nodes": [{tag, text, attrib}]}.

Exit codes: 0 ok (0 matches is still ok), 1 selector/parse error,
2 usage/IO error.
"""
import argparse
import json
import sys


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def node_to_dict(el):
    """Selector -> plain dict. .text/.get_text_content varies by version;
    fall back honestly rather than guess."""
    text = ""
    for attr in ("text",):
        try:
            text = getattr(el, attr)
            if text is None:
                text = ""
            break
        except Exception:
            continue
    if hasattr(text, "strip"):
        text = text.strip()
    else:
        text = str(text)
    try:
        attrib = dict(el.attrib)
    except Exception:
        attrib = {}
    tag = getattr(el, "tag", None) or ""
    return {"tag": str(tag), "text": text, "attrib": attrib}


def main():
    ap = argparse.ArgumentParser(prog="parse.py")
    ap.add_argument("source", help="HTML file path, or '-' for stdin")
    sel = ap.add_mutually_exclusive_group(required=True)
    sel.add_argument("--css")
    sel.add_argument("--xpath")
    ap.add_argument("--first", action="store_true",
                    help="return only the first match")
    args = ap.parse_args()

    try:
        if args.source == "-":
            html = sys.stdin.read()
        else:
            html = open(args.source, encoding="utf-8").read()
    except OSError as exc:
        fail(f"read_error:{exc}", code=2)

    try:
        from scrapling import Selector
    except ImportError:
        fail("missing_dep:scrapling - install requirements.txt into the "
             "extension .venv", code=2)

    try:
        doc = Selector(html)
    except Exception as exc:
        fail(f"parse_error:{exc}")

    try:
        found = doc.css(args.css) if args.css else doc.xpath(args.xpath)
    except Exception as exc:
        fail(f"selector_error:{exc}")

    nodes = [node_to_dict(el) for el in found]
    if args.first:
        nodes = nodes[:1]
    print(json.dumps({"ok": True, "source": args.source,
                      "count": len(nodes), "nodes": nodes}))


if __name__ == "__main__":
    main()
