"""bootstrap — fetch whisper.cpp binary + ggml model into ./_cache.

Windows-x64 release zip from ggml-org/whisper.cpp releases; models from
huggingface ggerganov/whisper.cpp. Explicit fetch only — transcribe.py
never downloads silently.

  python bootstrap.py [--model base|small|tiny]

stdlib only. Prints {ok, steps, cache} JSON on stdout.
"""
from __future__ import annotations

import argparse
import io
import json
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

CACHE = Path(__file__).parent / "_cache"
RELEASE = ("https://github.com/ggml-org/whisper.cpp/releases/download/"
           "v1.7.6/whisper-bin-x64.zip")
MODEL_URL = ("https://huggingface.co/ggerganov/whisper.cpp/resolve/main/"
             "{fname}")


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="base")
    ap.add_argument("--skip-binary", action="store_true")
    args = ap.parse_args(argv)
    steps = []
    CACHE.mkdir(exist_ok=True)
    if platform.system() == "Windows" and not args.skip_binary:
        data = _fetch(RELEASE)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(CACHE)
        steps.append("whisper.cpp binary extracted")
    elif not args.skip_binary:
        steps.append("non-windows: install whisper.cpp via package "
                     "manager, place binary on PATH or in _cache")
    fname = f"ggml-{args.model}.bin"
    (CACHE / fname).write_bytes(_fetch(MODEL_URL.format(fname=fname)))
    steps.append(f"model {fname} fetched")
    print(json.dumps({"ok": True, "steps": steps,
                      "cache": str(CACHE)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
