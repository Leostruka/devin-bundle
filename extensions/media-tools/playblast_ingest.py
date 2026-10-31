"""playblast_ingest — validate a Blender playblast (MP4 + camera.json) and
emit a local handoff job descriptor for camera-preserving repaint
pipelines (Seedance/Katana-class). Stdlib only; no external calls.

Usage:
    playblast_ingest.py <playblast.mp4> [--camera camera.json]
                        [--out handoff.json] [--beats-per-second 1]
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from fractions import Fraction

DESC_VERSION = 1
FPS_TOL = 0.5
FRAME_TOL = 2
RES_TOL = 4
MAX_META_BYTES = 64 * 1024 * 1024
MAX_FRAMES = 200000
BPS_RANGE = (0.05, 60.0)


def find_ffprobe():
    exe = os.environ.get("FFPROBE_EXE")
    if exe and os.path.isfile(exe):
        return exe
    return shutil.which("ffprobe")


def probe(mp4, ffprobe=None):
    """Return ffprobe JSON dict for mp4, or raise ValueError."""
    exe = ffprobe or find_ffprobe()
    if not exe:
        raise FileNotFoundError("ffprobe not found (install ffmpeg)")
    try:
        out = subprocess.run(
            [exe, "-v", "error", "-print_format", "json",
             "-show_streams", "-show_format", mp4],
            capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise ValueError("ffprobe timed out after 60s")
    if out.returncode != 0:
        raise ValueError(f"ffprobe failed: {out.stderr.strip()[:300]}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"ffprobe bad output: {e}")


def _video_stream(info):
    for s in info.get("streams", []):
        if s.get("codec_type") == "video":
            return s
    return None


def _rate(stream):
    for key in ("avg_frame_rate", "r_frame_rate"):
        r = stream.get(key)
        if r and r != "0/0":
            try:
                return float(Fraction(r))
            except (ValueError, ZeroDivisionError):
                continue
    return None


def _finite(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))


def load_camera(path):
    try:
        size = os.path.getsize(path)
    except OSError as e:
        raise FileNotFoundError(f"cannot read camera.json: {e}")
    if size > MAX_META_BYTES:
        raise ValueError(f"camera.json too large: {size} bytes")
    try:
        with open(path, encoding="utf-8") as fh:
            meta = json.load(fh)
    except OSError as e:
        raise FileNotFoundError(f"cannot read camera.json: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"camera.json invalid JSON: {e}")
    for key in ("fps", "frame_start", "frame_end", "frames"):
        if key not in meta:
            raise ValueError(f"camera.json missing '{key}'")
    if not _finite(meta["fps"]) or meta["fps"] <= 0:
        raise ValueError("camera.json 'fps' must be finite > 0")
    for key in ("frame_start", "frame_end"):
        if (not isinstance(meta[key], int)
                or isinstance(meta[key], bool)):
            raise ValueError(f"camera.json '{key}' must be an int")
    if meta["frame_end"] < meta["frame_start"]:
        raise ValueError("camera.json frame_end < frame_start")
    span = meta["frame_end"] - meta["frame_start"] + 1
    if span > MAX_FRAMES:
        raise ValueError(f"camera.json span {span} exceeds {MAX_FRAMES}")
    if not isinstance(meta["frames"], list) or not meta["frames"]:
        raise ValueError("camera.json 'frames' must be a non-empty list")
    expected = meta["frame_start"]
    for fr in meta["frames"]:
        fid = fr.get("frame") if isinstance(fr, dict) else None
        if not isinstance(fid, int) or isinstance(fid, bool):
            raise ValueError("camera.json frame id must be an int")
        if fid != expected:
            raise ValueError(f"camera.json frames must cover "
                             f"frame_start..frame_end once each, in order: "
                             f"expected {expected}, got {fid}")
        expected += 1
    if expected - 1 != meta["frame_end"]:
        raise ValueError("camera.json frames do not cover "
                         "frame_start..frame_end")
    for fr in meta["frames"]:
        for key in ("frame", "matrix_world", "location",
                    "rotation_euler", "lens"):
            if key not in fr:
                raise ValueError(f"camera.json frame missing '{key}'")
        if (not isinstance(fr["location"], list)
                or not isinstance(fr["rotation_euler"], list)
                or len(fr["location"]) != 3
                or len(fr["rotation_euler"]) != 3):
            raise ValueError("camera.json location/rotation must be 3-vec")
        if (not isinstance(fr["matrix_world"], list)
                or len(fr["matrix_world"]) != 4
                or any(not isinstance(r, list) or len(r) != 4
                       for r in fr["matrix_world"])):
            raise ValueError("camera.json matrix_world must be 4x4")
        vec = (list(fr["location"]) + list(fr["rotation_euler"])
               + [fr["lens"]] + [x for r in fr["matrix_world"] for x in r])
        if not all(_finite(v) for v in vec):
            raise ValueError("camera.json frame has non-finite values")
    return meta


def validate_agreement(meta, stream):
    """Check camera.json metadata agrees with the probed MP4. Returns
    list of mismatch strings (empty = agree)."""
    bad = []
    fps_meta = float(meta["fps"])
    fps_vid = _rate(stream)
    if fps_vid is None or abs(fps_vid - fps_meta) > FPS_TOL:
        bad.append(f"fps: meta={fps_meta} probe={fps_vid}")
    n_meta = int(meta["frame_end"]) - int(meta["frame_start"]) + 1
    n_vid = stream.get("nb_frames")
    if n_vid and n_vid.isdigit():
        if abs(int(n_vid) - n_meta) > FRAME_TOL:
            bad.append(f"frame count: meta={n_meta} probe={n_vid}")
    elif stream.get("duration") and fps_vid:
        if abs(float(stream["duration"]) * fps_vid - n_meta) > FRAME_TOL + 1:
            bad.append(f"duration*fps vs meta frames: "
                       f"{float(stream['duration']) * fps_vid:.1f} vs {n_meta}")
    w_meta, h_meta = meta.get("width"), meta.get("height")
    if w_meta and abs(int(stream.get("width", 0)) - int(w_meta)) > RES_TOL:
        bad.append(f"width: meta={w_meta} probe={stream.get('width')}")
    if h_meta and abs(int(stream.get("height", 0)) - int(h_meta)) > RES_TOL:
        bad.append(f"height: meta={h_meta} probe={stream.get('height')}")
    return bad


def _beats(meta, per_second):
    fps = float(meta["fps"])
    interval = 1.0 / float(per_second)
    beats = []
    next_t = 0.0

    def _entry(fr):
        return {"t": round((fr["frame"] - meta["frame_start"]) / fps, 3),
                "frame": fr["frame"], "location": fr["location"],
                "rotation_euler": fr["rotation_euler"], "lens": fr["lens"]}

    for fr in meta["frames"]:
        t = (fr["frame"] - meta["frame_start"]) / fps
        if t + 1e-9 >= next_t:
            beats.append(_entry(fr))
            next_t += interval
    if beats[-1]["frame"] != meta["frames"][-1]["frame"]:
        beats.append(_entry(meta["frames"][-1]))
    return beats


def build_descriptor(mp4, meta, stream, info, preview=None,
                     beats_per_second=1):
    fps = float(meta["fps"])
    n_frames = int(meta["frame_end"]) - int(meta["frame_start"]) + 1
    dur = float(info.get("format", {}).get("duration") or 0.0)
    return {
        "version": DESC_VERSION,
        "kind": "camera-blocking-handoff",
        "source": {
            "mp4": os.path.abspath(mp4),
            "camera_json": None,
            "preview_png": os.path.abspath(preview) if preview else None,
        },
        "video": {
            "codec": stream.get("codec_name"),
            "width": stream.get("width"),
            "height": stream.get("height"),
            "fps": fps,
            "frames": n_frames,
            "duration_s": round(dur or n_frames / fps, 3),
        },
        "camera": {
            "name": meta.get("camera"),
            "frame_start": meta["frame_start"],
            "frame_end": meta["frame_end"],
            "lens": meta["frames"][0]["lens"],
        },
        "prompt_template": {
            "references": [],
            "hard_location_map": True,
            "instruction": ("Repaint preserving camera path and framing; "
                            "beats give per-timestamp camera pose."),
            "beats": _beats(meta, beats_per_second),
        },
        "target": {"engine": "seedance-class", "external_call": False},
    }


def ingest_playblast(mp4, camera_json=None, out=None, preview=None,
                     beats_per_second=1, ffprobe=None):
    """Validate mp4 + camera.json, write handoff descriptor, return it."""
    if not os.path.isfile(mp4):
        raise FileNotFoundError(f"mp4 not found: {mp4}")
    if not mp4.lower().endswith(".mp4"):
        raise ValueError("playblast must be .mp4")
    if (not _finite(beats_per_second)
            or not BPS_RANGE[0] <= beats_per_second <= BPS_RANGE[1]):
        raise ValueError(f"beats_per_second must be finite in "
                         f"{BPS_RANGE}, got {beats_per_second!r}")
    camera_json = camera_json or mp4[:-4] + ".camera.json"
    meta = load_camera(camera_json)
    info = probe(mp4, ffprobe=ffprobe)
    stream = _video_stream(info)
    if stream is None:
        raise ValueError("no video stream in mp4")
    bad = validate_agreement(meta, stream)
    if bad:
        raise ValueError("metadata/probe mismatch: " + "; ".join(bad))
    desc = build_descriptor(mp4, meta, stream, info, preview=preview,
                            beats_per_second=beats_per_second)
    desc["source"]["camera_json"] = os.path.abspath(camera_json)
    out = out or mp4[:-4] + ".handoff.json"
    if os.path.exists(out):
        raise FileExistsError(f"refusing to overwrite {out}")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(desc, fh, indent=1)
    return desc


def main(argv=None):
    ap = argparse.ArgumentParser(description="Playblast ingest/validation")
    ap.add_argument("mp4")
    ap.add_argument("--camera", default=None)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--beats-per-second", type=float, default=1)
    args = ap.parse_args(argv)
    try:
        desc = ingest_playblast(args.mp4, camera_json=args.camera,
                                out=args.out, preview=args.preview,
                                beats_per_second=args.beats_per_second)
    except (OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    print(json.dumps({"ok": True, "descriptor": desc}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
