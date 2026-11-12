"""transcribe — local ASR wrapper: yt-dlp fetch + whisper.cpp inference.

Deterministic, offline, no paid APIs. Pipeline proven in recon:
yt-dlp -> wav -> whisper.cpp (win-x64) + ggml model -> segments.

  python transcribe.py <url|audio-or-video-file> [--model base] [--lang auto]
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CACHE = Path(os.environ.get("ASR_CACHE",
                            Path(__file__).parent / "_cache"))
MODELS = {"base": "ggml-base.bin", "small": "ggml-small.bin",
          "tiny": "ggml-tiny.bin", "medium": "ggml-medium.bin",
          "large": "ggml-large-v3-turbo.bin"}
# issue #430: PT-BR and other non-EN speech garbles on `base` - prefer
# small+ and an explicit --lang when the source language is known.
SEG_RE = re.compile(
    r"\[(\d+):(\d+):(\d+)[.,](\d+)\s*-->\s*(\d+):(\d+):(\d+)[.,](\d+)\]"
    r"\s*(.*)")
# whisper.cpp stderr reports auto-detection, e.g.
# "whisper_full_with_state: ... lang pt (p = 0.98)" / "detected language: Portuguese"
_LANG_RE = re.compile(
    r"(?:detected language|lang(?:uage)?)\s*[:=]?\s*"
    r"(?:([A-Za-z]+)\s*\(p\s*=\s*([\d.]+)\)|([a-z]{2}))",
    re.IGNORECASE)


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
    # bundle layout puts binaries under _cache/Release/; check there and
    # _cache/ directly. "main" is only trusted inside CACHE -- on Windows
    # PATH lookup resolves main.CPL from system32 (WinError 193).
    for name in ("whisper-cli.exe", "whisper-cli", "main.exe", "main"):
        for d in (CACHE / "Release", CACHE):
            p = d / name
            if p.is_file():
                return str(p)
    for name in ("whisper-cli", "whisper.cpp"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _model_path(model):
    # accept "base", "ggml-base.bin" and bare filenames
    key = str(model).removeprefix("ggml-").removesuffix(".bin")
    fname = MODELS.get(key, model if str(model).endswith(".bin")
                       else f"ggml-{key}.bin")
    f = CACHE / fname
    return str(f) if f.exists() else None


def parse_lang_detection(stderr):
    """whisper.cpp stderr -> (lang, prob) from auto-detection lines."""
    best, code_only = None, None
    for m in _LANG_RE.finditer(stderr or ""):
        name, prob, code = m.groups()
        if name and prob:
            p = float(prob)
            if best is None or p > best[1]:
                best = (name.lower(), p)
        elif code:
            code_only = code.lower()
    if best:
        return best
    return (code_only, None) if code_only else (None, None)


def _ffmpeg():
    exe = os.environ.get("FFMPEG_EXE")
    if exe and os.path.isfile(exe):
        return exe
    return shutil.which("ffmpeg")


def fetch_audio(source, workdir):
    """URL -> wav via yt-dlp; local file -> wav path for whisper.cpp.

    whisper.cpp demuxes wav/mp3 only - video containers (mp4/mov/mkv)
    and other audio formats are silently empty, so anything outside
    {wav,mp3} is extracted to 16kHz mono wav via ffmpeg first.
    """
    src = Path(source)
    if not src.exists():
        if not shutil.which("yt-dlp"):
            raise RuntimeError("yt-dlp not on PATH")
        out = Path(workdir) / "audio.wav"
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "wav", "-o", str(out),
             source], check=True, capture_output=True, timeout=600,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return out
    if src.suffix.lower() in (".wav", ".mp3"):
        return src
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            f"{src.suffix or 'file'} input needs ffmpeg to extract "
            "audio (install ffmpeg or pass .wav/.mp3)")
    out = Path(workdir) / "audio.wav"
    subprocess.run(
        [ffmpeg, "-y", "-v", "error", "-i", str(src),
         "-vn", "-ac", "1", "-ar", "16000", str(out)],
        check=True, capture_output=True, timeout=600,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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
                           encoding="utf-8", errors="replace",
                           timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if p.returncode != 0:
        return {"ok": False, "error": "whisper_failed",
                "stderr": p.stderr[-2000:]}
    segs = parse_segments(p.stdout)
    out = {"ok": True, "text": " ".join(s["text"] for s in segs),
           "segments": segs, "model": model, "source": source}
    det_lang, det_prob = parse_lang_detection(p.stderr)
    if det_lang:
        out["detected_lang"] = det_lang
        if det_prob is not None:
            out["lang_confidence"] = det_prob
        warnings = []
        if lang != "auto" and det_lang != lang:
            warnings.append(
                f"lang_mismatch: --lang {lang} but detected {det_lang}")
        if det_prob is not None and det_prob < 0.5:
            warnings.append(
                f"low_lang_confidence:{det_prob:.2f} - pass --lang "
                "explicitly or use a larger model")
        if warnings:
            out["warnings"] = warnings
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="local ASR (whisper.cpp)")
    ap.add_argument("source")
    ap.add_argument("--model", default="base")
    ap.add_argument("--lang", default="auto")
    args = ap.parse_args(argv)
    res = transcribe(args.source, args.model, args.lang)
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
