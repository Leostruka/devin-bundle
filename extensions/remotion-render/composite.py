"""composite - overlay a rendered plan video onto a source video via ffmpeg.

Pipeline step 6 of animation-direction: the source keeps its audio
(narration); the Remotion render sits on top - full-frame when the
render carries alpha (.mov ProRes/qtrle), or contained PiP/lower-third
for mp4 renders without alpha.

  python composite.py source.mp4 overlay.mov -o out.mp4
      [--fit frame|contain] [--pos x:y] [--mix] [--crf 20] [--dry]

-> {"ok": bool, "output": ..., "cmd": [...], "warnings": [...]}

Per-beat timing (sync_range) is a plan/render concern: render each
beat's clip separately and concat, or render one full-length plan.
This tool composites whole inputs only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

_BUNDLE_VERSION_CACHE = None


def _bundle_version():
    """Nearest ancestor manifest.json with a "name" marker, else ""."""
    global _BUNDLE_VERSION_CACHE
    if _BUNDLE_VERSION_CACHE is not None:
        return _BUNDLE_VERSION_CACHE
    import json as _json
    for parent in Path(__file__).absolute().parents:
        manifest = parent / "manifest.json"
        if manifest.is_file():
            try:
                data = _json.loads(
                    manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                break
            if isinstance(data, dict) and data.get("name"):
                _BUNDLE_VERSION_CACHE = str(data.get("version") or "")
            else:
                _BUNDLE_VERSION_CACHE = ""
            return _BUNDLE_VERSION_CACHE
    _BUNDLE_VERSION_CACHE = ""
    return _BUNDLE_VERSION_CACHE


def _answered_by():
    return {"bundle": _bundle_version(), "wrapper": "remotion-render"}


def _stamp(payload):
    if not isinstance(payload, dict):
        return payload
    payload["api_version"] = 2
    if not isinstance(payload.get("meta"), dict):
        payload["meta"] = {}
    payload["meta"].setdefault("answered_by", _answered_by())
    return payload


def _dumps(payload, **kw):
    return json.dumps(_stamp(payload), **kw)


POS_RE = re.compile(r"^-?\d+:-?\d+$")


def find_ffmpeg():
    exe = os.environ.get("FFMPEG_EXE")
    if exe and os.path.isfile(exe):
        return exe
    return shutil.which("ffmpeg")


def find_ffprobe():
    exe = os.environ.get("FFPROBE_EXE")
    if exe and os.path.isfile(exe):
        return exe
    return shutil.which("ffprobe")


def probe(path, ffprobe=None):
    """ffprobe JSON for path; raises ValueError on any failure."""
    exe = ffprobe or find_ffprobe()
    if not exe:
        raise FileNotFoundError("ffprobe not found (install ffmpeg)")
    try:
        out = subprocess.run(
            [exe, "-v", "error", "-print_format", "json",
             "-show_streams", "-show_format", str(path)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60)
    except subprocess.TimeoutExpired:
        raise ValueError("ffprobe timed out after 60s")
    if out.returncode != 0:
        raise ValueError(f"ffprobe failed: {out.stderr.strip()[:300]}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"ffprobe bad output: {e}")


def _streams(info, kind):
    return [s for s in info.get("streams", [])
            if s.get("codec_type") == kind]


def _video(info):
    vs = _streams(info, "video")
    return vs[0] if vs else None


def _has_audio(info):
    return bool(_streams(info, "audio"))


def _dims(stream):
    try:
        return int(stream["width"]), int(stream["height"])
    except (KeyError, TypeError, ValueError):
        return None, None


def _parse_pos(pos):
    """'x:y' -> (x, y); None -> (0, 0). Raises ValueError."""
    if pos is None:
        return 0, 0
    if not POS_RE.match(pos):
        raise ValueError(f"pos must be 'x:y' integers, got {pos!r}")
    x, y = pos.split(":", 1)
    return int(x), int(y)


def build_filter(src_w, src_h, ov_w, ov_h, fit="frame", pos=(0, 0)):
    """Return (filter_complex, out_label) for the video chain.

    frame:   overlay scaled to exact source dims at 0:0.
    contain: overlay AR-fit inside source frame (no pad - source shows
             through around it), centered plus pos offset.
    """
    if fit == "frame":
        return (f"[1:v]scale={src_w}:{src_h}[ov];"
                f"[0:v][ov]overlay=0:0[v]"), "[v]"
    if fit != "contain":
        raise ValueError(f"fit must be frame|contain, got {fit!r}")
    x, y = pos
    return (f"[1:v]scale={src_w}:{src_h}"
            f":force_original_aspect_ratio=decrease[ov];"
            f"[0:v][ov]overlay=(W-w)/2+{x}:(H-h)/2+{y}[v]"), "[v]"


def audio_mode(src_info, ov_info, mix=False):
    """-> 'source' | 'overlay' | 'mix' | 'none'.

    Narration-first: source audio wins; --mix amixes overlay audio in.
    Source silent + overlay audible -> overlay audio becomes the track.
    """
    src_a, ov_a = _has_audio(src_info), _has_audio(ov_info)
    if src_a and ov_a and mix:
        return "mix"
    if src_a:
        return "source"
    if ov_a:
        return "overlay"
    return "none"


def composite(source, overlay, out, fit="frame", pos=None, mix=False,
              crf=20, preset="veryfast", dry=False, ffmpeg=None,
              ffprobe=None):
    source, overlay, out = Path(source), Path(overlay), Path(out)
    warnings = []
    for p, name in ((source, "source"), (overlay, "overlay")):
        if not p.is_file():
            return {"ok": False, "error": f"{name}_missing",
                    "path": str(p)}
    if out.exists():
        return {"ok": False,
                "error": f"out_exists:{out} (refusing to overwrite; "
                         "pick another -o or delete it first)"}
    try:
        src_i, ov_i = probe(source, ffprobe), probe(overlay, ffprobe)
    except (ValueError, FileNotFoundError) as e:
        return {"ok": False, "error": str(e)}
    sv, ov = _video(src_i), _video(ov_i)
    if sv is None or ov is None:
        return {"ok": False, "error": "video_stream_missing",
                "hint": "both inputs need a video stream"}
    src_w, src_h = _dims(sv)
    ov_w, ov_h = _dims(ov)
    if not all((src_w, src_h, ov_w, ov_h)):
        return {"ok": False, "error": "video_dims_unreadable"}

    try:
        dx, dy = _parse_pos(pos)
        fchain, vlabel = build_filter(src_w, src_h, ov_w, ov_h, fit,
                                      (dx, dy))
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if fit == "frame" and pos:
        warnings.append("pos_ignored:fit=frame_covers_full_frame")

    # duration sanity: overlay shorter -> last frame holds (eof_action
    # repeat is ffmpeg default); source shorter -> -shortest trims.
    try:
        src_d = float(src_i.get("format", {}).get("duration", 0) or 0)
        ov_d = float(ov_i.get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        src_d = ov_d = 0.0
    if ov_d and src_d and ov_d < src_d - 0.5:
        warnings.append(f"overlay_shorter:{ov_d:.1f}s<{src_d:.1f}s"
                        "_last_frame_holds")
    if ov_d and src_d and ov_d > src_d + 0.5:
        warnings.append(f"overlay_longer:{ov_d:.1f}s>{src_d:.1f}s"
                        "_trimmed_by_shortest")

    mode = audio_mode(src_i, ov_i, mix=mix)
    exe = ffmpeg or find_ffmpeg() or "ffmpeg"
    cmd = [exe, "-y", "-i", str(source), "-i", str(overlay)]
    if mode == "mix":
        fchain += ";[0:a:0][1:a:0]amix=inputs=2:duration=first[a]"
        cmd += ["-filter_complex", fchain, "-map", "[v]",
                "-map", "[a]"]
    else:
        cmd += ["-filter_complex", fchain, "-map", vlabel]
        if mode == "source":
            cmd += ["-map", "0:a:0"]
        elif mode == "overlay":
            cmd += ["-map", "1:a:0"]
    cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", preset]
    if mode != "none":
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += ["-shortest", "-movflags", "+faststart", str(out)]
    result = {"ok": True, "output": str(out), "cmd": cmd,
              "warnings": warnings}
    if dry:
        result["note"] = "dry_run:cmd_built"
        return result
    exe = ffmpeg or find_ffmpeg()
    if not exe:
        return {"ok": False, "error": "ffmpeg_missing",
                "hint": "install ffmpeg", "cmd": cmd}
    cmd[0] = exe
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=1800,
                           creationflags=getattr(
                               subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "ffmpeg_timeout", "cmd": cmd}
    result.update({"ok": p.returncode == 0,
                   "stderr": p.stderr[-2000:]})
    if p.returncode != 0:
        result["error"] = "ffmpeg_failed"
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="overlay rendered plan onto source video (ffmpeg)")
    ap.add_argument("source")
    ap.add_argument("overlay")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--fit", choices=["frame", "contain"],
                    default="frame")
    ap.add_argument("--pos", default=None, help="x:y offset (contain)")
    ap.add_argument("--mix", action="store_true",
                    help="amix overlay audio with source audio")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv)
    result = composite(
        args.source, args.overlay, args.out, fit=args.fit,
        pos=args.pos, mix=args.mix, crf=args.crf, preset=args.preset,
        dry=args.dry)
    print(_dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
