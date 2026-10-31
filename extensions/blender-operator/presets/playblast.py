"""playblast preset — fast headless animation render to MP4 + camera.json.

Executed inside blender_server's bpy namespace. PARAMS dict:

    {"out_dir": "...", "name": "shot", "width": 640, "height": 360,
     "engine": "BLENDER_WORKBENCH"|"BLENDER_EEVEE_NEXT",
     "preview_frame": null}

Renders scene.frame_start..frame_end at scene.render.fps to
<out_dir>/<name>.mp4 via Blender's FFMPEG output, writes
<out_dir>/<name>.camera.json with fps/frame range and per-frame
matrix_world/location/rotation_euler/lens, and renders
<out_dir>/<name>.preview.png of one frame. Refuses to overwrite existing
files unless PARAMS["force"] is true. Sets `_result` with artifact paths.
"""
import json
import os

import bpy

P = globals().get("PARAMS") or {}
OUT_DIR = P["out_dir"]
NAME = P.get("name", "playblast")
WIDTH = int(P.get("width", 640))
HEIGHT = int(P.get("height", 360))
ENGINE = P.get("engine", "BLENDER_WORKBENCH")
FORCE = bool(P.get("force", False))

scene = bpy.context.scene
cam = scene.camera
if cam is None:
    raise RuntimeError("no scene camera — run camera_rig first")

os.makedirs(OUT_DIR, exist_ok=True)
mp4 = os.path.join(OUT_DIR, f"{NAME}.mp4")
cam_json = os.path.join(OUT_DIR, f"{NAME}.camera.json")
preview = os.path.join(OUT_DIR, f"{NAME}.preview.png")
for p in (mp4, cam_json, preview):
    if os.path.exists(p) and not FORCE:
        raise FileExistsError(f"refusing to overwrite {p}")

f0, f1 = scene.frame_start, scene.frame_end
fps = scene.render.fps / scene.render.fps_base

scene.render.engine = ENGINE
scene.render.resolution_x = WIDTH
scene.render.resolution_y = HEIGHT
scene.render.resolution_percentage = 100
if ENGINE == "BLENDER_WORKBENCH":
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.ffmpeg_preset = "GOOD"
scene.render.filepath = mp4

frames = []
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    mw = cam.matrix_world
    frames.append({
        "frame": f,
        "matrix_world": [[round(mw[r][c], 6) for c in range(4)]
                         for r in range(4)],
        "location": [round(v, 6) for v in cam.matrix_world.translation],
        "rotation_euler": [round(v, 6)
                           for v in cam.matrix_world.to_euler()],
        "lens": round(cam.data.lens, 4),
    })

with open(cam_json, "w", encoding="utf-8") as fh:
    json.dump({"fps": fps, "frame_start": f0, "frame_end": f1,
               "camera": cam.name, "width": WIDTH, "height": HEIGHT,
               "frames": frames}, fh, indent=1)

pf = P.get("preview_frame")
pf = int(pf) if pf is not None else (f0 + f1) // 2

bpy.ops.render.render(animation=True)  # writes mp4

scene.render.image_settings.file_format = "PNG"
scene.frame_set(pf)
scene.render.filepath = preview
bpy.ops.render.render(write_still=True)

_result = {"ok": True, "mp4": mp4, "camera_json": cam_json,
           "preview": preview, "engine": ENGINE,
           "fps": fps, "frames": f1 - f0 + 1,
           "preview_frame": pf}
