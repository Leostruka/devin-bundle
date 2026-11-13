#!/usr/bin/env python3
"""look_ledger.py - visual-structure ledger; detects reskins of the same
layout family by hashing fonts + palette + grid skeleton.

Usage:
  look_ledger.py record <file> --ledger ledger.jsonl
  look_ledger.py compare <fileA> <fileB>
  look_ledger.py check <file> --ledger ledger.jsonl
"""
import hashlib
import json
import re
import sys
from pathlib import Path

from design_envelope import _stamp, _dumps




def visual_signature(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    fonts = sorted(set(f.strip().strip("'\"").lower()
                       for m in re.finditer(r"font-family\s*:\s*([^;}]+)",
                                            text)
                       for f in m.group(1).split(",")))
    colors = sorted(set(re.findall(r"#[0-9a-fA-F]{6}\b", text)))
    grid = re.findall(r"(grid|flex)\b[^;}]*?(gap|columns?|template)",
                      text)
    classes = re.findall(r"class=\"([^\"]+)\"", text)
    skel = hashlib.sha256("\n".join(classes).encode()).hexdigest()[:16]
    return {"fonts": fonts, "colors": colors,
            "grid_signals": len(grid), "skeleton": skel}


def record(path, ledger):
    sig = visual_signature(path)
    entry = {"file": str(path), **sig}
    with open(ledger, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def compare(a, b):
    sa, sb = visual_signature(a), visual_signature(b)
    same_fonts = sa["fonts"] == sb["fonts"]
    shared_colors = len(set(sa["colors"]) & set(sb["colors"]))
    same_skel = sa["skeleton"] == sb["skeleton"]
    reskin = same_skel and (not same_fonts or shared_colors < 2)
    return {"same_skeleton": same_skel, "same_fonts": same_fonts,
            "shared_colors": shared_colors, "reskin": reskin}


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(argv) < 3:
        print(__doc__.strip())
        return 1
    cmd = argv[1]
    try:
        if cmd == "record":
            ledger = argv[argv.index("--ledger") + 1]
            print(_dumps(record(argv[2], ledger), ensure_ascii=False))
            return 0
        if cmd == "compare" and len(argv) >= 4:
            print(_dumps(compare(argv[2], argv[3]), ensure_ascii=False))
            return 0
        if cmd == "check":
            ledger = argv[argv.index("--ledger") + 1]
            sig = visual_signature(argv[2])
            hits = []
            try:
                for line in Path(ledger).read_text(
                        encoding="utf-8").splitlines():
                    e = json.loads(line)
                    if e["skeleton"] == sig["skeleton"] \
                            and e["file"] != str(argv[2]):
                        hits.append(e["file"])
            except OSError:
                pass
            print(_dumps({"matches": hits,
                              "reskin_family": bool(hits)}))
            return 1 if hits else 0
    except (OSError, ValueError, IndexError) as exc:
        print(_dumps({"ok": False, "error": str(exc)},
                         ensure_ascii=False))
        return 1
    print(__doc__.strip())
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
