#!/usr/bin/env python3
"""PlantUML renderer — serverless, zero-dependency, stdlib only.

Compresses a PlantUML DSL file (UTF-8 → raw Deflate → PlantUML's modified
Base64) and fetches the rendered artifact from the public PlantUML server.
No Java, no .jar, no third-party packages.

  plantuml_renderer.py diagram.puml                 # → diagram.svg
  plantuml_renderer.py diagram.puml --format png    # → diagram.png
  plantuml_renderer.py diagram.puml -o out/arch.svg
  plantuml_renderer.py --check diagram.puml         # syntax sanity only, no network
  plantuml_renderer.py --self-test                  # offline asserts + JSON

PlantUML text encoding (plantuml.com/plantuml/txt):
  UTF-8 bytes → zlib deflate with raw stream (wbits=-15) → 6-bit groups →
  alphabet "0-9A-Za-z-_". Reference: plantuml source TranscoderUtil.
"""
import argparse
import json
import re
import sys
import urllib.request
import zlib
from pathlib import Path

SERVER = "http://www.plantuml.com/plantuml"
_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"

START_RE = re.compile(r"@start\w+", re.IGNORECASE)
END_RE = re.compile(r"@end\w*", re.IGNORECASE)


def emit(obj, code=0):
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    sys.exit(code)


def encode6bit(b):
    return _ALPHABET[b & 0x3F] if 0 <= b < 64 else "?"


def append3bytes(b1, b2, b3):
    c1, c2, c3 = b1 >> 2, ((b1 & 0x3) << 4) | (b2 >> 4), ((b2 & 0xF) << 2) | (b3 >> 6)
    return encode6bit(c1) + encode6bit(c2) + encode6bit(c3) + encode6bit(b3 & 0x3F)


def plantuml_encode(text):
    """UTF-8 → raw deflate → modified base64 (PlantUML URL-safe alphabet)."""
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = comp.compress(text.encode("utf-8")) + comp.flush()
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i:i + 3]
        b1, b2, b3 = (list(chunk) + [0, 0])[:3]
        out.append(append3bytes(b1, b2, b3))
    return "".join(out)


def check_source(text):
    """Cheap structural sanity before hitting the network."""
    errors = []
    starts, ends = START_RE.findall(text), END_RE.findall(text)
    if not starts:
        errors.append("missing @start<diagram> directive")
    if not ends:
        errors.append("missing @end directive")
    if len(starts) != len(ends):
        errors.append(f"unbalanced blocks: {len(starts)} @start vs {len(ends)} @end")
    if len(text.strip()) < 10:
        errors.append("source suspiciously short")
    return errors


def render(src_path, fmt, out_path=None, server=SERVER):
    text = Path(src_path).read_text(encoding="utf-8")
    errors = check_source(text)
    if errors:
        emit({"ok": False, "error": "syntax check failed", "details": errors}, 2)
    url = f"{server}/{fmt}/{plantuml_encode(text)}"
    req = urllib.request.Request(url, headers={"User-Agent": "devin-bundle-plantuml/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
    except Exception as e:
        emit({"ok": False, "error": f"render request failed: {e}"}, 1)
    if fmt == "svg" and b"<svg" not in body[:2000]:
        emit({"ok": False, "error": "server returned non-SVG (syntax error in source?)",
              "preview": body[:300].decode("utf-8", "replace")}, 1)
    out = Path(out_path) if out_path else Path(src_path).with_suffix(f".{fmt}")
    out.write_bytes(body)
    return out


def self_test():
    # Known-vector: "@startuml\n@enduml" must encode to a non-empty URL-safe string
    enc = plantuml_encode("@startuml\nAlice -> Bob: hi\n@enduml")
    assert enc and re.fullmatch(r"[0-9A-Za-z\-_]+", enc), "encode produced unsafe chars"
    # Empty/deflate path
    assert plantuml_encode("@startuml\n@enduml"), "minimal diagram failed"
    # check_source catches the three failure shapes
    assert check_source("Alice -> Bob")  # no @start
    assert check_source("@startuml\nfoo")  # no @end
    assert not check_source("@startuml\nAlice -> Bob\n@enduml")
    emit({"ok": True, "self_test": "passed", "sample_encode": enc[:40] + "..."})


def main():
    p = argparse.ArgumentParser(description="Render PlantUML DSL via the public server (no Java).")
    p.add_argument("source", nargs="?", help="PlantUML source file (.puml/.txt)")
    p.add_argument("--format", choices=["svg", "png"], default="svg")
    p.add_argument("-o", "--out", help="Output file (default: <source>.<format>)")
    p.add_argument("--check", action="store_true", help="Syntax sanity only; no network")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        self_test()
    if not args.source:
        p.error("source file required")
    if not Path(args.source).exists():
        emit({"ok": False, "error": f"source not found: {args.source}"}, 2)

    if args.check:
        text = Path(args.source).read_text(encoding="utf-8")
        errors = check_source(text)
        emit({"ok": not errors, "source": args.source, "errors": errors}, 0 if not errors else 2)

    out = render(args.source, args.format, args.out)
    emit({"ok": True, "path": str(out.resolve()), "bytes": out.stat().st_size})


if __name__ == "__main__":
    main()
