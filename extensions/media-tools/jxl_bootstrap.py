"""jxl_bootstrap — fetch pinned libjxl cjxl/djxl binaries into ./_cache.

libjxl v0.11.2 static release zips from github.com/libjxl/libjxl,
sha256-verified. Explicit fetch only — jxl.py never downloads at call
time. Writes resolved tool paths to _cache/jxl-paths.json.

  python jxl_bootstrap.py

stdlib only. Prints {ok, steps, cache} JSON on stdout.
"""
from __future__ import annotations

import hashlib
import io
import json
import platform
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from media_envelope import _stamp, _dumps


CACHE = Path(__file__).parent / "_cache"
VERSION = "v0.11.2"
BASE = f"https://github.com/libjxl/libjxl/releases/download/{VERSION}"

ASSETS = {
    ("Windows", "AMD64"): (
        "jxl-x64-windows-static.zip",
        "97dc815bdd99ba243d8502050357342cf649251a5df069f8c3daee6828cbe0ce"),
    ("Windows", "x86"): (
        "jxl-x86-windows-static.zip",
        "39f53943143468bb27f653dcfa7f6d2cf71a8b9fa14269de21d475a821002957"),
    ("Linux", "x86_64"): (
        "jxl-linux-x86_64-static.zip",
        "f8f8c031881d4a76845d3b3482a4e0138bb017568dc76d33abd79d24856a4dec"),
}


class _FetchError(Exception):
    pass


def _fail(msg):
    print(_dumps({"ok": False, "error": msg}))
    return 2


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except (urllib.error.URLError, OSError) as exc:
        raise _FetchError(f"fetch_error:{exc}")


def _safe_members(z):
    """Yield members, rejecting absolute paths and .. segments."""
    for info in z.infolist():
        name = info.filename
        parts = Path(name).parts
        if name.startswith(("/", "\\")) or ":" in name or ".." in parts:
            raise _FetchError(f"bad_archive:unsafe_member:{name}")
        yield info


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def main(argv=None):
    key = (platform.system(), platform.machine())
    asset = ASSETS.get(key)
    if not asset:
        return _fail("unsupported_platform:"
                     f"{key[0]}/{key[1]} — install cjxl/djxl via a "
                     "package manager and place them on PATH or in "
                     "_cache")
    fname, expected = asset
    try:
        CACHE.mkdir(exist_ok=True)
        data = _fetch(f"{BASE}/{fname}")
        digest = _sha256(data)
        if digest != expected:
            raise _FetchError(
                f"checksum_mismatch:{digest[:16]}!={expected[:16]}")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                z.extractall(CACHE, members=_safe_members(z))
        except zipfile.BadZipFile as exc:
            raise _FetchError(f"bad_archive:{exc}")
        exes = (["cjxl.exe", "djxl.exe", "jxlinfo.exe"]
                if key[0] == "Windows" else ["cjxl", "djxl", "jxlinfo"])
        found = {p.stem: str(p)
                 for exe in exes for p in CACHE.rglob(exe)}
        for stem in ("cjxl", "djxl"):
            if stem not in found:
                raise _FetchError(f"tool_not_in_archive:{stem}")
        paths_file = CACHE / "jxl-paths.json"
        paths_file.write_text(json.dumps(found, indent=1),
                              encoding="utf-8")
        steps = [f"{fname} extracted (sha256 verified)",
                 f"paths written to {paths_file.name}"]
    except _FetchError as exc:
        return _fail(str(exc))
    except OSError as exc:
        return _fail(f"write_error:{exc}")
    print(_dumps({"ok": True, "steps": steps, "cache": str(CACHE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
