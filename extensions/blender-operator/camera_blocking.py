"""camera_blocking — orchestrate a low-poly blockout + keyframed camera
playblast into MP4/camera.json/PNG, then validate and ingest via
media-tools into a local handoff job descriptor.

Spawns its own isolated `blender -b --factory-startup` server process on a
dedicated port (default 19713), drives it through the presets via the
existing JSONL exec protocol, then shuts down ONLY the process it spawned.
User scenes and other blender servers are never touched: factory startup,
no --blend, kills restricted to the owned PID + its own port.

Usage:
    camera_blocking.py --out DIR [--name shot] [--fps 24] [--frames 48]
        [--width 640 --height 360] [--path orbit|dolly] [--radius 12]
        [--cam-height 5] [--lens 35] [--engine BLENDER_WORKBENCH]
        [--port 19713] [--exe PATH] [--force] [--keep-server]
"""
import argparse
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PRESETS = os.path.join(HERE, "presets")
SERVER = os.path.join(HERE, "blender_server.py")
MEDIA_TOOLS = os.path.join(HERE, os.pardir, "media-tools")
DEFAULT_PORT = 19713

LIMITS = {
    "fps": (1, 120),
    "frames": (2, 480),
    "width": (16, 4096),
    "height": (16, 4096),
    "radius": (0.5, 500.0),
    "cam_height": (0.1, 500.0),
    "lens": (1.0, 300.0),
    "port": (1024, 65535),
}
BPS_RANGE = (0.05, 60.0)
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PATHS = ("orbit", "dolly")
ENGINES = ("BLENDER_WORKBENCH", "BLENDER_EEVEE_NEXT")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


wrapper = _load("blender_operator_wrapper", os.path.join(HERE, "wrapper.py"))
ingest = _load("playblast_ingest",
               os.path.join(MEDIA_TOOLS, "playblast_ingest.py"))


def _num_ok(v):
    return (isinstance(v, (int, float)) and not isinstance(v, bool)
            and math.isfinite(v))


def validate_params(p):
    """Return list of problems (empty = ok)."""
    bad = []
    if not isinstance(p, dict):
        return ["params must be a dict"]
    for key, (lo, hi) in LIMITS.items():
        v = p.get(key)
        if not _num_ok(v):
            bad.append(f"{key}: expected finite number in [{lo}, {hi}], "
                       f"got {v!r}")
        elif not lo <= v <= hi:
            bad.append(f"{key}={v} outside [{lo}, {hi}]")
    name = p.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        bad.append(f"name {name!r} must match {NAME_RE.pattern}")
    if p.get("path") not in PATHS:
        bad.append(f"path must be one of {PATHS}")
    if p.get("engine") not in ENGINES:
        bad.append(f"engine must be one of {ENGINES}")
    out = p.get("out")
    if not isinstance(out, str) or not out \
            or os.path.abspath(out) == os.path.abspath(os.sep):
        bad.append("out dir missing, not a string, or filesystem root")
    bps = p.get("beats_per_second")
    if bps is not None and (not _num_ok(bps)
                            or not BPS_RANGE[0] <= bps <= BPS_RANGE[1]):
        bad.append(f"beats_per_second: expected finite number in "
                   f"{BPS_RANGE}, got {bps!r}")
    return bad


def artifacts(out, name):
    return (os.path.join(out, f"{name}.mp4"),
            os.path.join(out, f"{name}.camera.json"),
            os.path.join(out, f"{name}.preview.png"),
            os.path.join(out, f"{name}.handoff.json"))


def check_clobber(out, name, force):
    existing = [p for p in artifacts(out, name) if os.path.exists(p)]
    if existing and not force:
        return existing
    return []


class OwnershipError(RuntimeError):
    pass


def _owned_request(port, proc, nonce_box, payload, timeout=30):
    """Send payload only to the responder proven to be our spawned proc.

    Identity = pid match on the Popen object plus a stable server nonce
    pinned at first verified contact. Any request carries the pinned nonce
    so a foreign server that races onto the port rejects exec/shutdown.
    """
    if nonce_box[0] is not None:
        payload = dict(payload, nonce=nonce_box[0])
    resp = wrapper._request(port, payload, timeout=timeout)
    pid = (resp or {}).get("pid")
    if pid is None:
        raise OwnershipError("responder lacks identity fields")
    if pid != proc.pid:
        raise OwnershipError(
            f"foreign responder pid {pid} != owned pid {proc.pid}")
    nonce = (resp or {}).get("nonce")
    if nonce_box[0] is None:
        nonce_box[0] = nonce
    elif nonce != nonce_box[0]:
        raise OwnershipError("responder nonce changed mid-session")
    if proc.poll() is not None:
        raise OwnershipError("owned blender process exited")
    return resp


def _exec_preset(port, proc, nonce_box, preset, params, timeout=900):
    path = os.path.join(PRESETS, preset)
    code = (f"PARAMS = {params!r}\n"
            f"exec(compile(open({json.dumps(path)}, encoding='utf-8')"
            f".read(), {json.dumps(path)}, 'exec'))")
    return _owned_request(port, proc, nonce_box,
                          {"id": preset, "op": "exec", "code": code},
                          timeout=timeout)


def _shutdown_owned(port, proc, nonce_box):
    """Shut down only the process we spawned (its own port + proc)."""
    try:
        _owned_request(port, proc, nonce_box,
                       {"id": "id", "op": "ping"}, timeout=3)
        _owned_request(port, proc, nonce_box,
                       {"id": "bye", "op": "shutdown"}, timeout=5)
    except (OSError, OwnershipError):
        pass
    try:
        proc.wait(timeout=10)
        return True
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           capture_output=True, timeout=10)
        else:
            proc.kill()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return False


def run(p):
    """Full orchestration. Returns result dict (raises nothing; 'ok' key)."""
    problems = validate_params(p)
    if problems:
        return {"ok": False, "stage": "validate", "errors": problems}
    out, name = p["out"], p["name"]
    force = bool(p.get("force"))
    clobber = check_clobber(out, name, force)
    if clobber:
        return {"ok": False, "stage": "clobber",
                "errors": ["exists: " + c for c in clobber],
                "hint": "pass force=true / --force to overwrite"}

    blender = wrapper.find_blender(p.get("exe"))
    if not blender:
        return {"ok": False, "stage": "launch",
                "errors": ["blender executable not found; set BLENDER_EXE "
                           "or --exe"]}
    alive, _ = wrapper._alive(p["port"])
    if alive:
        return {"ok": False, "stage": "launch",
                "errors": [f"port {p['port']} already serves a blender; "
                           "refusing to share — pick another --port"]}

    argv = [blender, "-b", "--factory-startup", "--python", SERVER,
            "--", "--port", str(p["port"])]
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
          "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        kw["creationflags"] = (subprocess.CREATE_NEW_PROCESS_GROUP
                               | subprocess.DETACHED_PROCESS)
    else:
        kw["start_new_session"] = True
    proc = subprocess.Popen(argv, **kw)
    owned_pid = proc.pid
    nonce_box = [None]

    try:
        deadline = time.time() + 90
        ready = False
        while time.time() < deadline:
            try:
                _owned_request(p["port"], proc, nonce_box,
                               {"id": "hb", "op": "ping"}, timeout=3)
                ready = True
                break
            except OwnershipError as e:
                return {"ok": False, "stage": "launch",
                        "errors": [f"port responder is not our spawned "
                                   f"process: {e}"]}
            except OSError:
                pass
            if proc.poll() is not None:
                return {"ok": False, "stage": "launch",
                        "errors": ["blender exited during startup"],
                        "exit_code": proc.returncode}
            time.sleep(0.3)
        if not ready:
            return {"ok": False, "stage": "launch",
                    "errors": ["server not ready within 90s"]}

        steps = [
            ("blockout.py", {"seed": 7}),
            ("camera_rig.py", {
                "frame_start": 1, "frame_end": p["frames"], "fps": p["fps"],
                "path": p["path"], "radius": p["radius"],
                "height": p["cam_height"], "lens": p["lens"]}),
            ("playblast.py", {
                "out_dir": os.path.abspath(out), "name": name,
                "width": p["width"], "height": p["height"],
                "engine": p["engine"], "force": force}),
        ]
        for preset, params in steps:
            try:
                r = _exec_preset(p["port"], proc, nonce_box, preset, params)
            except OwnershipError as e:
                return {"ok": False, "stage": preset,
                        "errors": [f"ownership lost: {e}"]}
            if not r.get("ok"):
                return {"ok": False, "stage": preset,
                        "errors": [r.get("error") or "exec failed"],
                        "stderr": r.get("stderr")}
            if preset == "playblast.py":
                try:
                    last = json.loads(r["result_json"])
                except (TypeError, json.JSONDecodeError):
                    return {"ok": False, "stage": "playblast",
                            "errors": ["no result_json from playblast"]}
        mp4, cam_json, preview, handoff = artifacts(out, name)
        if force and os.path.exists(handoff):
            os.remove(handoff)
        try:
            desc = ingest.ingest_playblast(
                mp4, camera_json=cam_json, preview=preview,
                beats_per_second=p.get("beats_per_second", 1))
        except (OSError, ValueError) as e:
            return {"ok": False, "stage": "ingest", "errors": [str(e)],
                    "mp4": mp4, "camera_json": cam_json, "preview": preview}
        return {"ok": True, "mp4": mp4, "camera_json": cam_json,
                "preview": preview,
                "handoff": mp4[:-4] + ".handoff.json",
                "video": desc["video"], "beats": len(
                    desc["prompt_template"]["beats"]),
                "pid": owned_pid, "port": p["port"]}
    finally:
        if not p.get("keep_server"):
            _shutdown_owned(p["port"], proc, nonce_box)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Camera blocking playblast")
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="shot")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=360)
    ap.add_argument("--path", default="orbit", choices=PATHS)
    ap.add_argument("--radius", type=float, default=12.0)
    ap.add_argument("--cam-height", type=float, default=5.0)
    ap.add_argument("--lens", type=float, default=35.0)
    ap.add_argument("--engine", default="BLENDER_WORKBENCH",
                    choices=ENGINES)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--exe", default=None)
    ap.add_argument("--beats-per-second", type=float, default=1)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--keep-server", action="store_true")
    args = ap.parse_args(argv)
    p = {"out": args.out, "name": args.name, "fps": args.fps,
         "frames": args.frames, "width": args.width,
         "height": args.height, "path": args.path, "radius": args.radius,
         "cam_height": args.cam_height, "lens": args.lens,
         "engine": args.engine, "port": args.port, "exe": args.exe,
         "beats_per_second": args.beats_per_second,
         "force": args.force, "keep_server": args.keep_server}
    result = run(p)
    print(json.dumps(result, indent=1))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
