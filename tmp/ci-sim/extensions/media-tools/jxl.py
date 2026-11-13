"""jxl — JPEG XL codec wrapper via cjxl/djxl (libjxl).

Explicit-bootstrap convention (same as extensions/asr): binaries live in
./_cache (JXL_CACHE env override), fetched only by jxl_bootstrap.py.
Missing binaries -> {"ok": false, "status": "missing", "hint": ...},
never a silent download.

Usage:
    jxl.py identify <file.jxl>
    jxl.py decode <in.jxl> <out.png>
    jxl.py encode <in.png> <out.jxl> [--quality 90] [--effort 7]

stdlib + subprocess only. Prints a typed JSON envelope on stdout.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from media_envelope import _stamp, _dumps



CACHE = Path(os.environ.get("JXL_CACHE",
                            Path(__file__).parent / "_cache"))
PATHS_FILE = CACHE / "jxl-paths.json"

DIM_RE = re.compile(r"(\d+)\s*x\s*(\d+)")
FRAMES_RE = re.compile(r"num_frames\D+(\d+)")
COLOR_RE = re.compile(r"[Cc]olor ?[Ss]pace[:\s]+([A-Za-z0-9_]+)")
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _cache_candidates(name):
    """Yield name variants under CACHE (zip may nest under a subdir)."""
    exes = [name + ".exe", name] if os.name == "nt" else [name, name + ".exe"]
    for exe in exes:
        for d in (CACHE, CACHE / "tools", CACHE / "bin"):
            p = d / exe
            if p.is_file():
                yield p
    if CACHE.is_dir():
        for exe in exes:
            yield from CACHE.glob(f"*/{exe}")


def find_tool(name):
    """Resolve a jxl tool: jxl-paths.json -> _cache -> PATH."""
    if PATHS_FILE.is_file():
        try:
            paths = json.loads(PATHS_FILE.read_text(encoding="utf-8"))
            p = Path(paths.get(name, ""))
            if p.is_file():
                return str(p)
        except (OSError, json.JSONDecodeError):
            pass
    for p in _cache_candidates(name):
        return str(p)
    return shutil.which(name)


def _tools():
    cjxl = find_tool("cjxl")
    djxl = find_tool("djxl")
    jxlinfo = find_tool("jxlinfo")
    return cjxl, djxl, jxlinfo


def _missing(what):
    return {"ok": False, "status": "missing",
            "error": f"{what}_missing",
            "hint": "run extensions/media-tools/jxl_bootstrap.py"}


def _run(argv, timeout=300):
    p = subprocess.run(argv, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=_NO_WINDOW)
    return p


def _png_ihdr(path):
    """Read PNG IHDR -> (width, height, bit_depth, color_type)."""
    data = Path(path).read_bytes()[:33]
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    w, h, depth, ctype = struct.unpack(">IIBB", data[16:26])
    return w, h, depth, ctype


_PNG_COLOR = {0: "gray", 2: "RGB", 3: "palette", 4: "gray+alpha", 6: "RGBA"}


def identify(path):
    """jxl file -> {width, height, colorspace, alpha, frames}."""
    _, djxl, jxlinfo = _tools()
    tool = jxlinfo or djxl
    if not tool:
        return _missing("djxl")
    if not Path(path).is_file():
        return {"ok": False, "error": f"input_missing:{path}"}
    if jxlinfo:
        p = _run([tool, str(path)])
        text = p.stdout + p.stderr
        if p.returncode != 0:
            return {"ok": False, "error": "jxlinfo_failed",
                    "stderr": p.stderr[-2000:]}
        m = DIM_RE.search(text)
        out = {"ok": True, "file": str(path)}
        if m:
            out["width"], out["height"] = int(m.group(1)), int(m.group(2))
        f = FRAMES_RE.search(text)
        out["frames"] = int(f.group(1)) if f else 1
        c = COLOR_RE.search(text)
        if c:
            out["colorspace"] = c.group(1)
        out["alpha"] = "alpha" in text.lower()
        return out
    # fallback: djxl decode to temp PNG, read IHDR + parse verbose stderr
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "probe.png"
        p = _run([tool, str(path), str(tmp), "-v"])
        text = p.stdout + p.stderr
        if p.returncode != 0 or not tmp.is_file():
            return {"ok": False, "error": "djxl_failed",
                    "stderr": p.stderr[-2000:]}
        w, h, _depth, ctype = _png_ihdr(tmp)
        f = FRAMES_RE.search(text)
        return {"ok": True, "file": str(path),
                "width": w, "height": h,
                "colorspace": _PNG_COLOR.get(ctype, f"ct{ctype}"),
                "alpha": ctype in (4, 6) or "alpha" in text.lower(),
                "frames": int(f.group(1)) if f else 1}


def decode(src, dst):
    """jxl -> png."""
    _, djxl, _ = _tools()
    if not djxl:
        return _missing("djxl")
    if not Path(src).is_file():
        return {"ok": False, "error": f"input_missing:{src}"}
    p = _run([djxl, str(src), str(dst)])
    if p.returncode != 0 or not Path(dst).is_file():
        return {"ok": False, "error": "djxl_failed",
                "stderr": p.stderr[-2000:]}
    return {"ok": True, "input": str(src), "output": str(dst)}


def encode(src, dst, quality=90, effort=7):
    """png -> jxl. quality 0-100 (-q), effort 1-9 (-e)."""
    cjxl, _, _ = _tools()
    if not cjxl:
        return _missing("cjxl")
    if not Path(src).is_file():
        return {"ok": False, "error": f"input_missing:{src}"}
    if not (0 <= quality <= 100):
        return {"ok": False, "error": f"bad_quality:{quality}"}
    if not (1 <= effort <= 9):
        return {"ok": False, "error": f"bad_effort:{effort}"}
    p = _run([cjxl, str(src), str(dst),
              "-q", str(quality), "-e", str(effort)])
    if p.returncode != 0 or not Path(dst).is_file():
        return {"ok": False, "error": "cjxl_failed",
                "stderr": p.stderr[-2000:]}
    return {"ok": True, "input": str(src), "output": str(dst),
            "quality": quality, "effort": effort}


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="JPEG XL via cjxl/djxl")
    sub = ap.add_subparsers(dest="action", required=True)
    sub.add_parser("identify").add_argument("file")
    d = sub.add_parser("decode")
    d.add_argument("input")
    d.add_argument("output")
    e = sub.add_parser("encode")
    e.add_argument("input")
    e.add_argument("output")
    e.add_argument("--quality", type=float, default=90)
    e.add_argument("--effort", type=int, default=7)
    args = ap.parse_args(argv)
    if args.action == "identify":
        res = identify(args.file)
    elif args.action == "decode":
        res = decode(args.input, args.output)
    else:
        res = encode(args.input, args.output, args.quality, args.effort)
    print(_dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
