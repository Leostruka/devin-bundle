"""bootstrap — fetch whisper.cpp binary + ggml model into ./_cache.

Windows-x64 release zip from ggml-org/whisper.cpp releases; models from
huggingface ggerganov/whisper.cpp. Explicit fetch only — transcribe.py
never downloads silently.

  python bootstrap.py [--model base|small|tiny]

stdlib only. Prints {ok, steps, cache} JSON on stdout.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path(__file__).parent / "_cache"
RELEASE = ("https://github.com/ggml-org/whisper.cpp/releases/download/"
           "v1.7.6/whisper-bin-x64.zip")
RELEASE_SHA256 = ("0d2eca299c248f965bd0341bcb219db4b433c7f0c0ce2200d4df"
                  "85765e8156a9")
MODEL_URL = ("https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
             "{fname}")
# sha256 (HF LFS oid) per documented --model choice; unpinned models are
# refused rather than fetched unverified.
MODEL_SHA256 = {
    "tiny": "be07e048e1e599ad46341c8d2a135645097a538221678b7acdd1b1919c6e1b21",
    "base": "60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe",
    "small": "1be3a9b2063867b937e64e2ec7483364a79917e157fa98c5d94b5c1fffea987b",
}
_MODEL_RE = re.compile(r"[a-z0-9.-]+\Z")
BIN_MARKER = ".whisper-bin-x64.ok"


def _fail(msg):
    print(json.dumps({"ok": False, "error": msg}))
    return 2


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()
    except (urllib.error.URLError, OSError) as exc:
        raise _FetchError(f"fetch_error:{exc}")


class _FetchError(Exception):
    pass


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _safe_members(z):
    """Yield members, rejecting absolute paths and .. segments."""
    for info in z.infolist():
        name = info.filename
        parts = Path(name).parts
        if (name.startswith(("/", "\\")) or ":" in name
                or ".." in parts):
            raise _FetchError(f"bad_archive:unsafe_member:{name}")
        yield info


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base")
    ap.add_argument("--skip-binary", action="store_true")
    args = ap.parse_args(argv)
    if not _MODEL_RE.match(args.model):
        return _fail(f"bad_model:{args.model!r}")
    if args.model not in MODEL_SHA256:
        return _fail(f"unpinned_model:{args.model} "
                     f"(supported: {', '.join(sorted(MODEL_SHA256))})")
    steps = []
    try:
        CACHE.mkdir(exist_ok=True)
        if platform.system() == "Windows" and not args.skip_binary:
            marker = CACHE / BIN_MARKER
            if marker.exists():
                steps.append("whisper.cpp binary already extracted")
            else:
                data = _fetch(RELEASE)
                if _sha256(data) != RELEASE_SHA256:
                    raise _FetchError("checksum_mismatch:whisper-bin-x64.zip")
                try:
                    with zipfile.ZipFile(io.BytesIO(data)) as z:
                        z.extractall(CACHE, members=_safe_members(z))
                except zipfile.BadZipFile as exc:
                    raise _FetchError(f"bad_archive:{exc}")
                marker.write_text(RELEASE_SHA256, encoding="utf-8")
                steps.append("whisper.cpp binary extracted")
        elif not args.skip_binary:
            steps.append("non-windows: install whisper.cpp via package "
                         "manager, place binary on PATH or in _cache")
        fname = f"ggml-{args.model}.bin"
        expected = MODEL_SHA256[args.model]
        model_path = CACHE / fname
        if (model_path.exists()
                and _sha256(model_path.read_bytes()) == expected):
            steps.append(f"model {fname} already cached")
        else:
            data = _fetch(MODEL_URL.format(fname=fname))
            if _sha256(data) != expected:
                raise _FetchError(f"checksum_mismatch:{fname}")
            model_path.write_bytes(data)
            steps.append(f"model {fname} fetched")
    except _FetchError as exc:
        return _fail(str(exc))
    except OSError as exc:
        return _fail(f"write_error:{exc}")
    print(json.dumps({"ok": True, "steps": steps,
                      "cache": str(CACHE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
