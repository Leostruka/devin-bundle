"""transcribe — local ASR wrapper: yt-dlp fetch + whisper.cpp inference.

Deterministic, offline, no paid APIs. Pipeline proven in recon:
yt-dlp -> wav -> whisper.cpp (win-x64) + ggml model -> segments.

  python transcribe.py <url|audio-file> [--model base] [--lang auto]
    -> {"ok": true, "text": "...", "segments": [{start, end, text}],
        "model": "base", "source": "..."}

Binaries/models live in a cache dir (ASR_CACHE env or ./_cache);
bootstrap.py fetches them. Missing binaries -> ok:false + hint,
never a silent download.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CACHE = Path(os.environ.get("ASR_CACHE",
                            Path(__file__).parent / "_cache"))
MODELS = {"base": "ggml-base.bin", "small": "ggml-small.bin",
          "tiny": "ggml-tiny.bin"}
SEG_RE = re.compile(
    r"\[(\d+):(\d+):(\d+)[.,](\d+)\s*-->\s*(\d+):(\d+):(\d+)[.,](\d+)\]"
    r"\s*(.*)")


def parse_segments(text):
    """whisper.cpp stdout -> [{start, end, text}] in seconds."""
    segs = []
    for m in SEG_RE.finditer(text):
        h, m_, s, ms, h2, m2, s2, ms2, txt = m.groups()
        segs.append({
            "start": int(h) * 3600 + int(m_) * 60 + int(s) + int(ms) / 1000,
            "end": int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2) / 1000,
            "text": txt.strip()})
    return segs


def _find_binary():
    for name in ("whisper-cli", "whisper-cli.exe", "main", "main.exe",
                 "whisper.cpp"):
        p = shutil.which(name) or (CACHE / name)
        if isinstance(p, Path) and p.exists():
            return str(p)
        if isinstance(p, str):
            return p
    return None


def _model_path(model):
    f = CACHE / MODELS.get(model, model)
    return str(f) if f.exists() else None


def fetch_audio(source, workdir):
    """URL -> wav via yt-dlp; local file -> pass through."""
    if Path(source).exists():
        return Path(source)
    if not shutil.which("yt-dlp"):
        raise RuntimeError("yt-dlp not on PATH")
    out = Path(workdir) / "audio.wav"
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "wav", "-o", str(out),
         source], check=True, capture_output=True, timeout=600)
    return out


def transcribe(source, model="base", lang="auto", timeout=600):
    if not shutil.which("yt-dlp") and not Path(source).exists():
        return {"ok": False, "error": "yt-dlp_missing",
                "hint": "pip install yt-dlp or pass a local audio file"}
    binary = _find_binary()
    if not binary:
        return {"ok": False, "error": "whisper_binary_missing",
                "hint": "run extensions/asr/bootstrap.py"}
    mpath = _model_path(model)
    if not mpath:
        return {"ok": False, "error": "model_missing",
                "hint": f"run extensions/asr/bootstrap.py ({model})"}
    with tempfile.TemporaryDirectory() as td:
        try:
            wav = fetch_audio(source, td)
        except (RuntimeError, subprocess.CalledProcessError) as e:
            return {"ok": False, "error": f"fetch_failed:{e}"}
        argv = [binary, "-m", mpath, "-f", str(wav)]
        if lang != "auto":
            argv += ["-l", lang]
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout)
    if p.returncode != 0:
        return {"ok": False, "error": "whisper_failed",
                "stderr": p.stderr[-2000:]}
    segs = parse_segments(p.stdout)
    return {"ok": True, "text": " ".join(s["text"] for s in segs),
            "segments": segs, "model": model, "source": source}


def main(argv=None):
    ap = argparse.ArgumentParser(description="local ASR (whisper.cpp)")
    ap.add_argument("source")
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default="auto")
    args = ap.parse_args(argv)
    print(json.dumps(transcribe(args.source, args.model, args.lang),
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
