#!/usr/bin/env python3
"""dom_elements — adapt scrape/parse node JSON into DOM-picker
elements (stdlib only, zero network).

Reads {"nodes": [{tag, text, attrib}]} (parse.py/scrape.py output)
from a file or stdin and prints {"elements": [...]} in the shape
extensions/computer-use/cu_dom_picker.py consumes. The conversion is
the canonical cu_dom_picker.nodes_to_elements — this module adds no
filtering of its own: disabled, hidden and unsafe nodes are emitted
as flagged evidence (enabled=False / hidden=True / unsafe=True) and
the picker's shortlist is the single authority that excludes them
from candidacy.

CLI:
  python dom_elements.py nodes.json   (or '-' for stdin)
Exit 0 ok / 2 usage-IO error.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                    / "computer-use"))
import cu_dom_picker as _dp

nodes_to_elements = _dp.nodes_to_elements
MAX_INPUT_BYTES = _dp.MAX_SNAPSHOT_BYTES


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="scrape nodes -> DOM-picker elements JSON")
    ap.add_argument("source", help="nodes JSON file ('-' = stdin)")
    args = ap.parse_args(argv)
    try:
        raw = _dp.read_bounded(args.source, MAX_INPUT_BYTES)
    except OSError as e:
        print(json.dumps({"ok": False, "error": f"read_error:{e}"}))
        return 2
    if raw is None:
        print(json.dumps({"ok": False, "error": "input_too_large"}))
        return 2
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"read_error:{e}"}))
        return 2
    nodes = data.get("nodes") if isinstance(data, dict) else data
    els = nodes_to_elements(nodes)
    print(json.dumps({"ok": True, "count": len(els),
                      "elements": els}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
