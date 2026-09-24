#!/usr/bin/env python3
"""Capture the screen to a PNG file. Prints a JSON result to stdout.

Overlays:
  --grid [PX]   coordinate grid with physical-pixel labels (legacy fallback)
  --hints       Vimium-style letter badges over real interactive elements
                (Windows UI Automation; falls back to --grid 100 on failure)

Requires mss (+ pillow for overlays; uiautomation for --hints on Windows).
"""
import argparse
import json
import os
import sys
import tempfile
import time

import cu_actions
import cu_capture
import cu_hints
import cu_motion as cm
import cu_target


def set_dpi_awareness():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def fail(msg, code=1):
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(code)


def _load_pil():
    try:
        from PIL import Image, ImageDraw, ImageFont
        return Image, ImageDraw, ImageFont
    except ImportError:
        fail("pillow required for overlays — run: "
             "<venv-python> -m pip install -r requirements.txt", 2)


def _font(ImageFont, size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _to_image(img):
    from PIL import Image
    return Image.frombytes("RGB", (img.width, img.height), img.rgb).convert("RGBA")


_STATE_PATH = os.path.join(tempfile.gettempdir(), "devin-cu-shotstate.json")


def _shot_state_path(scope=None):
    """scope=(env_id, instance_id, session_id) -> per-env private dir;
    None -> _STATE_PATH (legacy tempdir seam; tests monkeypatch it)."""
    if scope is None:
        return _STATE_PATH
    return str(cu_target.state_path(cu_target.runtime_root(), *scope,
                                    "devin-cu-shotstate.json"))


def _shot_state(scope=None):
    try:
        with open(_shot_state_path(scope), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_shot_state(sha, path, scope=None):
    p = _shot_state_path(scope)
    try:
        with open(p + ".tmp", "w", encoding="utf-8") as f:
            json.dump({"sha256": sha, "path": path}, f)
        os.replace(p + ".tmp", p)
    except Exception:
        pass


def _img_hash(img):
    import hashlib
    return hashlib.sha256(img.rgb).hexdigest()


def _diff_file(img, path):
    """Changed-pixel ratio of the fresh grab vs an image file. Any channel
    shift >8 levels counts; size mismatch means everything changed."""
    from PIL import Image, ImageChops
    a = _to_image(img).convert("L")
    b = Image.open(path).convert("L")
    if a.size != b.size:
        return 1.0
    d = ImageChops.difference(a, b)
    hist = d.histogram()
    return sum(hist[9:]) / (a.width * a.height)


def _save_diff(img, path, out):
    """Write the pixel-difference image for a --diff comparison."""
    from PIL import Image, ImageChops
    a = _to_image(img).convert("RGB")
    b = Image.open(path).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    ImageChops.difference(a, b).save(out, "PNG")


def _write_png_raw(img, out):
    """Minimal PNG encoder (stdlib zlib, no PIL) — remote path must not
    require the host image stack."""
    import struct
    import zlib
    w, h = img.width, img.height
    stride = w * 3
    raw = b"".join(b"\x00" + img.rgb[y * stride:(y + 1) * stride]
                   for y in range(h))
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I",
                            zlib.crc32(tag + data) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    with open(out, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                + chunk(b"IDAT", zlib.compress(raw))
                + chunk(b"IEND", b""))


def _save_image(im, out, fmt="png", quality=80):
    """Format-aware save. Accepts a PIL Image or a raw frame
    (.rgb/.width/.height). JPEG ~5x cheaper to encode than PNG — the
    fast profile's pixel path when pixels are still required."""
    if fmt == "jpeg":
        if not hasattr(im, "save"):
            im = _to_image(im)
        im.convert("RGB").save(out, "JPEG", quality=int(quality))
    elif hasattr(im, "save"):
        im.convert("RGB").save(out, "PNG")
    else:
        _write_png_raw(im, out)


def _save_with_grid(img, spacing, out, ox=0, oy=0, fmt="png", quality=80):
    """Grid labels are GLOBAL physical pixels (ox/oy = image top-left in
    desktop space) so they read true on secondary/negative-origin monitors."""
    Image, ImageDraw, ImageFont = _load_pil()
    if spacing < 20:
        fail("--grid spacing must be >= 20 px", 2)
    im = _to_image(img)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    font = _font(ImageFont, 18)
    line = (255, 255, 0, 110)
    for x in range(0, img.width, spacing):
        d.line([(x, 0), (x, img.height)], fill=line)
        d.text((x + 2, 2), str(ox + x), font=font, fill=(255, 255, 0, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for y in range(0, img.height, spacing):
        d.line([(0, y), (img.width, y)], fill=line)
        d.text((2, y + 2), str(oy + y), font=font, fill=(255, 255, 0, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 255))
    _save_image(Image.alpha_composite(im, ov), out, fmt, quality)


def _save_with_hints(img, elements, out, ox, oy, fmt="png", quality=80):
    """Draw Vimium-style badges. elements carry screen-px bounds; (ox, oy) is
    the captured image's top-left corner in screen space."""
    Image, ImageDraw, ImageFont = _load_pil()
    im = _to_image(img)
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    font = _font(ImageFont, 15)
    els_in = [e for e in elements
              if 0 <= e["x"] - ox < img.width and 0 <= e["y"] - oy < img.height]
    hints = []
    for el, hid in zip(els_in, cu_hints.hint_ids(len(els_in))):
        bx = min(max(el["bounds"][0] - ox, 0), img.width - 30)
        by = min(max(el["bounds"][1] - oy, 0), img.height - 18)
        label = hid.upper()
        tb = d.textbbox((0, 0), label, font=font)
        pw, ph = tb[2] - tb[0] + 10, tb[3] - tb[1] + 7
        d.rounded_rectangle([bx, by, bx + pw, by + ph], radius=4,
                            fill=(255, 223, 0, 235), outline=(20, 20, 20, 255),
                            width=1)
        d.text((bx + 5, by + 3), label, font=font, fill=(15, 15, 15, 255))
        hints.append({"id": hid, "x": el["x"], "y": el["y"],
                      "name": el["name"], "type": el["type"],
                      "bounds": el["bounds"], "hwnd": el.get("hwnd"),
                      "enabled": el.get("enabled", True)})
    _save_image(Image.alpha_composite(im, ov), out, fmt, quality)
    return hints


def _remote_main(target):
    """Capture inside an isolated env via its backend — no mss, no UIA,
    no host pixels anywhere on this path."""
    p = cm.JsonParser(description="Capture env framebuffer to PNG")
    p.add_argument("--out", default=None)
    p.add_argument("--grid", type=int, nargs="?", const=100, default=None)
    p.add_argument("--hints", action="store_true",
                   help="no guest UIA yet (C10) — returns hints: null")
    p.add_argument("--format", choices=["png", "jpeg"], default="png")
    p.add_argument("--quality", type=int, default=80)
    p.add_argument("--if-changed", action="store_true")
    p.add_argument("--threshold", type=float, default=None)
    p.add_argument("--env", default=None)
    args = p.parse_args()
    backend = target["backend"]
    try:
        img, meta = backend.observe()
    except Exception as exc:
        cu_target.reject_remote(f"{type(exc).__name__}: {exc}")
    scope = (target["env_id"], meta.get("instance_id") or "boot",
             "default")
    env_dir = backend.env_dir
    ext = "jpg" if args.format == "jpeg" else "png"
    out = args.out or str(env_dir /
                        f"screenshot-{int(time.time())}.{ext}")
    if args.if_changed:
        shot_hash = _img_hash(img)
        st = _shot_state(scope)
        if st.get("sha256") == shot_hash:
            print(json.dumps({"ok": True, "changed": False,
                              "path": st.get("path")}))
            return
    result = {"ok": True, "path": out, "width": img.width,
              "height": img.height, "env_id": target["env_id"],
              "instance_id": meta.get("instance_id"),
              "frame_sha256": meta.get("frame_sha256"),
              "backend": meta.get("backend"),
              "origin_px": meta.get("origin_px"),
              "captured_at": round(time.time(), 3)}
    if args.hints:
        result["hints"] = None
        result["note"] = ("no guest element enumeration yet (C10) — "
                          "use --grid and click pixel coords")
    if args.grid or args.hints:
        _save_with_grid(img, args.grid or 100, out, 0, 0,
                        fmt=args.format, quality=args.quality)
        result["grid_px"] = args.grid or 100
    else:
        _save_image(img, out, args.format, args.quality)
    if args.if_changed:
        _write_shot_state(shot_hash, out, scope=scope)
    print(json.dumps(result))


def main():
    target = cu_target.cli_guard(sys.argv[1:])
    if target is not None:
        _remote_main(target)
        return
    if os.environ.get("CU_SESSION") == "1":
        import cu_session_dispatch
        cu_session_dispatch.run_via_daemon("screenshot", sys.argv[1:])
        return
    p = cm.JsonParser(description="Capture screen to PNG")
    p.add_argument("--out", default=None,
                   help="Output PNG path (default: screenshot-<ts>.png in the "
                        "system temp dir; use a .devin/ path to keep it as "
                        "project documentation)")
    p.add_argument("--monitor", type=int, default=0,
                   help="Monitor index: 0 = all monitors combined (default), 1..N = specific")
    p.add_argument("--region", default=None,
                   help="Crop region as 'x,y,w,h' (pixels)")
    ov = p.add_mutually_exclusive_group()
    ov.add_argument("--grid", type=int, nargs="?", const=100, default=None,
                    metavar="PX",
                    help="Overlay a coordinate grid with physical-pixel labels "
                         "every PX px (default 100). Use when picking click "
                         "targets — the labels survive image rescaling.")
    ov.add_argument("--hints", action="store_true",
                    help="Vimium-style letter badges on interactive elements "
                         "(UIA). stdout lists {id,x,y,name,type}; click via "
                         "mouse.py click --hint <id>. Falls back to --grid 100.")
    p.add_argument("--window", choices=["focused", "all"], default="focused",
                   help="--hints scope: focused window (default) or all windows")
    p.add_argument("--format", choices=["png", "jpeg"], default=None,
                   help="image encoding (jpeg ~5x faster; default: profile "
                        "fast -> jpeg, others -> png)")
    p.add_argument("--quality", type=int, default=80,
                   help="jpeg quality (default 80)")
    p.add_argument("--no-image", action="store_true",
                   help="with --hints: enumerate + sidecar only, skip pixel "
                        "capture entirely (visual bypass)")
    p.add_argument("--image", action="store_true",
                   help="with --hints under profile fast: still capture "
                        "pixels (fast skips them by default)")
    p.add_argument("--if-changed", action="store_true",
                   help="skip writing when the capture is unchanged vs the "
                        "last shot — token saver for verify loops")
    p.add_argument("--threshold", type=float, default=None,
                   help="change ratio tolerated by --if-changed/--diff "
                        "(0.01 = ignore <=1%% of pixels)")
    p.add_argument("--diff", default=None, metavar="BASELINE.png",
                   help="compare the capture vs a baseline image and print "
                        "changed_ratio instead of saving normally")
    p.add_argument("--diff-out", default=None,
                   help="with --diff: also save the pixel-difference image")
    p.add_argument("--env", default=None,
                   help="isolated environment id "
                        "(.devin/computer-use/envs); absent = local host")
    args = p.parse_args()

    set_dpi_awareness()
    profile = cm.get_profile()
    fmt = args.format or ("jpeg" if profile == "fast" else "png")
    ext = "jpg" if fmt == "jpeg" else "png"
    out = args.out or os.path.join(tempfile.gettempdir(),
                                   f"screenshot-{int(time.time())}.{ext}")

    # Visual bypass: --hints under fast (or --no-image) needs element
    # targets, not pixels — skip grab+encode entirely (~120ms saved).
    if args.hints and (args.no_image or (profile == "fast" and not args.image)):
        obs = cu_hints.enum_clickables(scope=args.window)
        els = obs["elements"] if obs else None
        if els:
            hints = [{"id": hid, "x": e["x"], "y": e["y"], "name": e["name"],
                      "type": e["type"], "bounds": e["bounds"],
                      "hwnd": e.get("hwnd"),
                      "enabled": e.get("enabled", True)}
                     for e, hid in zip(els, cu_hints.hint_ids(len(els)))]
            data = cu_hints.write_sidecar(
                hints, window=obs["window"], capture={"skipped": True})
            print(json.dumps(
                {"ok": True, "path": None, "capture": "skipped",
                 "profile": profile, "hints": hints,
                 "truncated": obs["truncated"],
                 "session_id": data["session_id"],
                 "observation_id": data["observation_id"],
                 "generation": data["generation"],
                 "window": obs["window"],
                 "note": "visual bypass — no image; click via "
                         "mouse.py click --hint <id>"}))
            return
        if args.no_image:
            # explicit bypass with nothing to target: fail honestly — the
            # caller asked for no pixels and there's nothing to offer
            cu_hints.invalidate_sidecar()
            fail("no elements enumerated and pixels skipped — "
                 "rerun with --image for a visual capture")
        # fast-profile default: bypass is an optimization, not a mode —
        # UIA yielded nothing, so fall through to the pixel path below

    try:
        import mss.tools
    except ImportError:
        fail("mss not installed — run: <venv-python> -m pip install -r requirements.txt", 2)

    try:
        mons = cu_capture.monitors()
        if args.region:
            try:
                x, y, w, h = [int(v) for v in args.region.split(",")]
            except ValueError:
                fail("--region must be 'x,y,w,h' integers", 2)
            bbox = {"left": x, "top": y, "width": w, "height": h}
        else:
            if args.monitor < 0 or args.monitor >= len(mons):
                fail(f"monitor {args.monitor} out of range (0..{len(mons)-1})", 2)
            bbox = mons[args.monitor]
        img, _meta = cu_capture.grab(bbox)
        origin = [bbox["left"], bbox["top"]]
        if args.diff:
            ratio = _diff_file(img, args.diff)
            res = {"ok": True, "changed_ratio": round(ratio, 6),
                   "changed": ratio > (args.threshold or 0.0),
                   "baseline": args.diff, "width": img.width,
                   "height": img.height}
            if args.diff_out:
                _save_diff(img, args.diff, args.diff_out)
                res["diff_path"] = args.diff_out
            print(json.dumps(res))
            return
        shot_hash = None
        if args.if_changed:
            shot_hash = _img_hash(img)
            st = _shot_state()
            if st.get("sha256") == shot_hash:
                print(json.dumps({"ok": True, "changed": False,
                                  "path": st.get("path")}))
                return
            if (args.threshold is not None and st.get("path")
                    and os.path.isfile(st["path"])):
                try:
                    if _diff_file(img, st["path"]) <= args.threshold:
                        print(json.dumps({"ok": True, "changed": False,
                                          "path": st["path"]}))
                        return
                except Exception:
                    pass
        result = {"ok": True, "path": out, "width": img.width,
                  "height": img.height, "monitor": args.monitor,
                  "origin_px": origin,
                  "captured_at": round(time.time(), 3)}
        if args.hints:
            obs = cu_hints.enum_clickables(scope=args.window)
            els = obs["elements"] if obs else None
            if els:
                hints = _save_with_hints(img, els, out, *origin,
                                          fmt=fmt, quality=args.quality)
                if hints:
                    data = cu_hints.write_sidecar(
                        hints, window=obs["window"],
                        capture={"origin_px": origin,
                                 "size_px": [img.width, img.height]})
                    result.update(
                        hints=hints, truncated=obs["truncated"],
                        session_id=data["session_id"],
                        observation_id=data["observation_id"],
                        generation=data["generation"],
                        window=obs["window"],
                        note=("hint labels over real elements — click via "
                              "mouse.py click --hint <id> or click the "
                              "x,y coords"))
                else:
                    cu_hints.invalidate_sidecar()
                    _save_with_grid(img, 100, out, *origin,
                                  fmt=fmt, quality=args.quality)
                    result.update(hints=None, fallback="grid",
                                  grid_px=100, truncated=False)
            else:
                cu_hints.invalidate_sidecar()
                _save_with_grid(img, 100, out, *origin,
                                  fmt=fmt, quality=args.quality)
                result.update(hints=None, fallback="grid",
                              grid_px=100, truncated=False)
        elif args.grid:
            _save_with_grid(img, args.grid, out, *origin,
                                  fmt=fmt, quality=args.quality)
            result["grid_px"] = args.grid
            result["note"] = ("grid labels are physical pixels — "
                              "read click coords directly")
        else:
            if fmt == "jpeg":
                _save_image(_to_image(img), out, "jpeg", args.quality)
            else:
                mss.tools.to_png(img.rgb, img.size, output=out)
        if shot_hash:
            _write_shot_state(shot_hash, out)
        print(json.dumps(result))
    except Exception as e:
        fail(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    cu_actions.run_cli(main)
