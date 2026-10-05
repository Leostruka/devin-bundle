#!/usr/bin/env python3
"""Record the screen to a video file plus an agent-readable contact sheet.

Encoders (picked by output extension):
  .mp4/.webm/.mkv/.mov  - ffmpeg fed over a rawvideo pipe; frames stream,
                          never buffer. Rejects when ffmpeg is not on PATH.
  .webp/.gif            - Pillow animated image; frames buffer downscaled to
                          --max-width, capped at --max-frames.
  (no extension)        - .mp4 when ffmpeg exists, else .webp.

The sheet (--sheet, default <temp>/record-<ts>-sheet.png) is a tile grid of
--tiles reservoir-sampled frames; it is the artifact the agent reads, since
video files cannot be viewed directly. --no-sheet disables it.

--env records an isolated guest by polling backend.observe(); fps there is
best-effort (QEMU screendump is slow). fps_actual reports the truth.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time

import cu_actions
import cu_capture
import cu_motion as cm
import cu_target

FFMPEG_EXTS = {".mp4", ".webm", ".mkv", ".mov"}
PIL_EXTS = {".webp", ".gif"}
PIL_MAX_WIDTH = 1280  # fallback-encoder frame cap when --max-width unset
TILE_W = 480


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def _load_pil():
    try:
        from PIL import Image
        return Image
    except ImportError:
        fail("pillow required; run "
             "<venv-python> -m pip install -r requirements.txt", 2)


def set_dpi_awareness():
    import cu_dpi
    cu_dpi.set_dpi_awareness()


def _pick_encoder(out):
    """Extension decides the encoder; nothing silently downgrades."""
    ext = os.path.splitext(out)[1].lower()
    if ext in FFMPEG_EXTS:
        if not shutil.which("ffmpeg"):
            fail(f"ffmpeg not on PATH (required for '{ext}'); "
                 "use .webp/.gif or install ffmpeg", 2)
        return "ffmpeg"
    if ext in PIL_EXTS:
        return "pillow"
    if ext:
        fail(f"unknown recording extension '{ext}'; supported: "
             f"{sorted(FFMPEG_EXTS | PIL_EXTS)}", 2)
    return "ffmpeg" if shutil.which("ffmpeg") else "pillow"


def _ffmpeg_cmd(w, h, fps, out):
    """rawvideo rgb24 on stdin; scale pads odd dims for yuv420p codecs."""
    ext = os.path.splitext(out)[1].lower()
    cmd = [shutil.which("ffmpeg"), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{w}x{h}", "-r", f"{fps:g}", "-i", "-", "-an",
           "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"]
    if ext == ".webm":
        cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-crf", "34",
                "-b:v", "0", "-deadline", "realtime", "-cpu-used", "8",
                "-row-mt", "1"]
    else:
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "26",
                "-preset", "veryfast", "-movflags", "+faststart"]
    return cmd + [out]


class _Sheet:
    """Reservoir sample (Algorithm R) of up to `tiles` thumbnails: uniform
    over whatever was captured, no total count needed, bounded memory."""

    def __init__(self, Image, tiles, cols):
        self.Image = Image
        self.tiles = tiles
        self.cols = cols
        self.thumbs = []
        self.seen = 0

    def feed(self, img):
        self.seen += 1
        im = self.Image.frombytes("RGB", (img.width, img.height), img.rgb)
        if im.width > TILE_W:
            im = im.resize(
                (TILE_W, max(1, round(im.height * TILE_W / im.width))))
        if len(self.thumbs) < self.tiles:
            self.thumbs.append(im)
        else:
            j = random.randrange(self.seen)
            if j < self.tiles:
                self.thumbs[j] = im

    def save(self, out):
        if not self.thumbs:
            return None
        w = max(t.width for t in self.thumbs)
        h = max(t.height for t in self.thumbs)
        cols = min(self.cols, len(self.thumbs))
        rows = math.ceil(len(self.thumbs) / cols)
        sheet = self.Image.new("RGB", (w * cols, h * rows), (10, 10, 10))
        for i, t in enumerate(self.thumbs):
            sheet.paste(t, ((i % cols) * w, (i // cols) * h))
        sheet.save(out, "PNG")
        return {"path": out, "tiles": len(self.thumbs), "cols": cols,
                "tile_px": [w, h]}


class _CapReached(Exception):
    """Pillow buffer hit --max-frames: stop capturing, encode what we have."""


def _record(grab, seconds, fps, consume, stats):
    """Absolute-deadline pacing (per-step sleep drift cannot accumulate).
    consume(img) receives every captured frame; stats tracks
    captured/dropped across early exits."""
    interval = 1.0 / fps
    end = time.monotonic() + seconds
    deadline = time.monotonic()
    while True:
        img, _meta = grab()
        consume(img)
        stats["captured"] += 1
        deadline += interval
        delay = deadline - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        else:
            missed = int(-delay // interval)
            stats["dropped"] += missed
            deadline += interval * missed
        if time.monotonic() >= end:
            break


def _local_grab(args):
    try:
        import mss  # noqa: F401
    except ImportError:
        fail("mss not installed; run "
             "<venv-python> -m pip install -r requirements.txt", 2)
    mons = cu_capture.monitors()
    if args.region:
        try:
            x, y, w, h = [int(v) for v in args.region.split(",")]
        except ValueError:
            fail("--region must be 'x,y,w,h' integers", 2)
        bbox = {"left": x, "top": y, "width": w, "height": h}
    else:
        if args.monitor < 0 or args.monitor >= len(mons):
            fail(f"monitor {args.monitor} out of range "
                 f"(0..{len(mons) - 1})", 2)
        bbox = mons[args.monitor]

    def grab():
        return cu_capture.grab(bbox)
    return grab


def _remote_grab(target, args):
    if args.region or args.monitor:
        cu_target.reject_remote(
            "--region/--monitor unsupported for --env; "
            "the guest framebuffer is recorded whole")
    backend = target["backend"]

    def grab():
        try:
            return backend.observe()
        except Exception as exc:
            cu_target.reject_remote(f"{type(exc).__name__}: {exc}")
    return grab


def main():
    target = cu_target.cli_guard(sys.argv[1:])
    if os.environ.get("CU_SESSION") == "1" and target is None:
        import cu_session_dispatch
        cu_session_dispatch.run_via_daemon("record", sys.argv[1:])
        return
    p = cm.JsonParser(description="Record the screen to video + contact sheet")
    p.add_argument("--seconds", type=float, default=5.0,
                   help="capture duration (default 5)")
    p.add_argument("--fps", type=float, default=8.0,
                   help="target frames/s (default 8; best-effort, missed "
                        "slots count as dropped and fps_actual reports the "
                        "truth)")
    p.add_argument("--monitor", type=int, default=0,
                   help="monitor index: 0 = all combined (default), 1..N")
    p.add_argument("--region", default=None,
                   help="crop region 'x,y,w,h' (local capture only)")
    p.add_argument("--out", default=None,
                   help="output path; .mp4/.webm/.mkv/.mov need ffmpeg on "
                        "PATH, .webp/.gif use Pillow. Default: "
                        "record-<ts>.mp4|webp in the OS temp dir")
    p.add_argument("--sheet", default=None,
                   help="contact-sheet PNG path (default "
                        "record-<ts>-sheet.png in temp); --no-sheet disables")
    p.add_argument("--no-sheet", action="store_true")
    p.add_argument("--tiles", type=int, default=6,
                   help="frames sampled into the sheet (default 6)")
    p.add_argument("--cols", type=int, default=3,
                   help="sheet columns (default 3)")
    p.add_argument("--max-width", type=int, default=0,
                   help="downscale video frames to this width (Pillow "
                        "encoder only; default 1280 there, native under "
                        "ffmpeg)")
    p.add_argument("--max-frames", type=int, default=300,
                   help="Pillow encoder frame cap (default 300, bounds "
                        "memory; ffmpeg streams unbounded)")
    p.add_argument("--env", default=None,
                   help="isolated environment id; records the guest "
                        "framebuffer via observe() polling")
    args = p.parse_args()

    if args.seconds <= 0:
        fail("--seconds must be > 0", 2)
    if not 0 < args.fps <= 60:
        fail("--fps must be in (0, 60]", 2)
    if args.tiles < 1 or args.cols < 1:
        fail("--tiles/--cols must be >= 1", 2)

    set_dpi_awareness()
    Image = _load_pil()

    ts = int(time.time())
    out = args.out or os.path.join(tempfile.gettempdir(), f"record-{ts}")
    enc = _pick_encoder(out)
    if not os.path.splitext(out)[1]:
        out += ".mp4" if enc == "ffmpeg" else ".webp"
    sheet_path = None if args.no_sheet else (
        args.sheet or os.path.join(tempfile.gettempdir(),
                                   f"record-{ts}-sheet.png"))
    sheet = _Sheet(Image, args.tiles, args.cols) if sheet_path else None

    grab = _remote_grab(target, args) if target is not None \
        else _local_grab(args)

    # First frame fixes geometry (the ffmpeg command needs WxH up front).
    img0, _m0 = grab()

    buf = []           # pillow path: buffered PIL frames
    proc = None        # ffmpeg path: encoder subprocess
    if enc == "pillow":
        mw = args.max_width or PIL_MAX_WIDTH

        def consume(img):
            im = Image.frombytes("RGB", (img.width, img.height), img.rgb)
            if im.width > mw:
                im = im.resize(
                    (mw, max(1, round(im.height * mw / im.width))))
            buf.append(im)
            if len(buf) >= args.max_frames:
                raise _CapReached()
    else:
        proc = subprocess.Popen(
            _ffmpeg_cmd(img0.width, img0.height, args.fps, out),
            stdin=subprocess.PIPE)

        def consume(img):
            try:
                proc.stdin.write(img.rgb)
            except (BrokenPipeError, OSError) as exc:
                proc.kill()
                fail(f"ffmpeg pipe died mid-capture: {exc}")

    def feed(img):
        consume(img)
        if sheet is not None:
            sheet.feed(img)

    stats = {"captured": 0, "dropped": 0}
    truncated = None
    t0 = time.monotonic()
    try:
        feed(img0)
        stats["captured"] += 1
        remaining = args.seconds - (time.monotonic() - t0)
        if remaining > 0:
            _record(grab, remaining, args.fps, feed, stats)
    except _CapReached:
        truncated = "max_frames"
    elapsed = time.monotonic() - t0

    if enc == "pillow":
        if not buf:
            fail("no frames captured")
        try:
            buf[0].save(out, save_all=True, append_images=buf[1:],
                        duration=int(1000 / args.fps), loop=0)
        except Exception as exc:
            fail(f"encode failed: {type(exc).__name__}: {exc}")
        frames_in_video = len(buf)
    else:
        try:
            proc.stdin.close()
            rc = proc.wait(timeout=120)
        except Exception as exc:
            proc.kill()
            fail(f"ffmpeg finalize failed: {type(exc).__name__}: {exc}")
        if rc != 0:
            fail(f"ffmpeg exited {rc}; output may be corrupt")
        frames_in_video = stats["captured"]

    sheet_info = sheet.save(sheet_path) if sheet is not None else None

    result = {"ok": True, "path": out, "encoder": enc,
              "sheet": sheet_info,
              "width": img0.width, "height": img0.height,
              "frames": frames_in_video, "dropped": stats["dropped"],
              "fps_target": args.fps,
              "fps_actual": round(stats["captured"] / elapsed, 2)
              if elapsed > 0 else 0,
              "seconds": round(elapsed, 2),
              "size_bytes": os.path.getsize(out)}
    if truncated:
        result["truncated"] = truncated
    if target is not None:
        result["env_id"] = target["env_id"]
    print(json.dumps(result))


if __name__ == "__main__":
    cu_actions.run_cli(main)
