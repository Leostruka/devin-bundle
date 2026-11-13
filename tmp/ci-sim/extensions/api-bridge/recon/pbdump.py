"""Generic protobuf wire dump (no schema). Usage:

  python recon/pbdump.py <jsonl> <rid|all> [path-filter]

Prints field-number tree; strings shown when printable.
"""

import base64
import json
import sys


def varint(b: bytes, i: int):
    v = 0
    s = 0
    while True:
        x = b[i]
        i += 1
        v |= (x & 0x7F) << s
        if not (x & 0x80):
            return v, i
        s += 7


def dump(b: bytes, depth: int = 0, limit: int = 80):
    i = 0
    out = []
    while i < len(b):
        try:
            key, i = varint(b, i)
        except IndexError:
            break
        fn, wt = key >> 3, key & 7
        pad = "  " * depth
        if wt == 0:
            v, i = varint(b, i)
            out.append(f"{pad}f{fn} varint {v}")
        elif wt == 1:
            out.append(f"{pad}f{fn} i64 {b[i:i+8].hex()}")
            i += 8
        elif wt == 5:
            out.append(f"{pad}f{fn} i32 {b[i:i+4].hex()}")
            i += 4
        elif wt == 2:
            ln, i = varint(b, i)
            raw = b[i:i + ln]
            i += ln
            txt = None
            if 0 < ln <= 400:
                try:
                    t = raw.decode("utf-8")
                    if all(c.isprintable() or c in "\n\t" for c in t):
                        txt = t
                except UnicodeDecodeError:
                    pass
            if txt is not None and len(txt) > 2:
                out.append(f"{pad}f{fn} len {ln} str {txt[:limit]!r}")
            else:
                sub = None
                if ln > 0:
                    try:
                        sub = dump(raw, depth + 1, limit)
                    except Exception:
                        sub = None
                if sub and len(sub) > 1:
                    out.append(f"{pad}f{fn} len {ln} msg:")
                    out.extend(sub)
                else:
                    out.append(f"{pad}f{fn} len {ln} bytes {raw[:limit].hex()}")
        else:
            out.append(f"{pad}f{fn} wt{wt} <unsupported>")
            break
    return out


def frames(b: bytes):
    """Split Connect streaming frames (1B flags + 4B len); gunzip flag&1."""
    import gzip
    i = 0
    out = []
    while i + 5 <= len(b):
        flags = b[i]
        ln = int.from_bytes(b[i + 1:i + 5], "big")
        payload = b[i + 5:i + 5 + ln]
        if flags & 1:
            try:
                payload = gzip.decompress(payload)
            except Exception:
                pass
        out.append((flags, payload))
        i += 5 + ln
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: pbdump.py <proto.binlog> [want_path]",
              file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    want_path = sys.argv[2] if len(sys.argv) > 2 else None
    reqs = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r["dir"] == "req":
            if want_path and want_path not in r.get("path", ""):
                continue
            reqs[r["rid"]] = r
        elif r["dir"] == "resp" and r["rid"] not in reqs:
            continue
        body = base64.b64decode(r["body_b64"])
        if r["dir"] == "req":
            reqs[r["rid"]] = r
            print(f"=== REQ {r['path']} ({r['body_len']}B) ct={r['headers'].get('content-type')}")
            if "connect+" in r["headers"].get("content-type", ""):
                for flags, fr in frames(body):
                    print(f"  -- frame flags={flags} len={len(fr)}")
                    for x in dump(fr):
                        print("   ", x)
            else:
                for x in dump(body):
                    print(" ", x)
        elif r["dir"] == "resp":
            print(f"=== RESP #{r['rid']} status={r['status']} ({r['body_len']}B) ct={r['headers'].get('Content-Type')}")
            ct = r["headers"].get("Content-Type", "")
            if "connect+" in ct:
                for flags, fr in frames(body):
                    print(f"  -- frame flags={flags} len={len(fr)}")
                    if flags == 0:
                        for x in dump(fr):
                            print("   ", x)
                    else:
                        print("    trailer:", fr[:200])
            else:
                for x in dump(body):
                    print(" ", x)


if __name__ == "__main__":
    main()
