"""camera_rig preset — keyframed camera path for blocking shots.

Executed inside blender_server's bpy namespace. PARAMS dict:

    {"frame_start": 1, "frame_end": 48, "fps": 24,
     "path": "orbit"|"dolly", "radius": 12.0, "height": 5.0,
     "target": [0, 0, 1.0], "lens": 35.0, "name": "CAM"}

orbit: full circle around `target` at radius/height over the frame range.
dolly: straight line from (-radius, -radius, height) to
(radius, -radius*0.6, height*0.7), tracking the target.

Creates a camera + empty target, adds a TRACK_TO constraint, sets scene
camera, fps and frame range. Adds objects only; never removes user data.
Sets `_result` with the camera name and keyed frame count.
"""
import math

import bpy
from mathutils import Vector

P = globals().get("PARAMS") or {}
F0 = int(P.get("frame_start", 1))
F1 = int(P.get("frame_end", 48))
FPS = int(P.get("fps", 24))
PATH = P.get("path", "orbit")
RADIUS = float(P.get("radius", 12.0))
HEIGHT = float(P.get("height", 5.0))
TARGET = Vector(P.get("target", (0.0, 0.0, 1.0)))
LENS = float(P.get("lens", 35.0))
NAME = P.get("name", "BLOCKOUT_CAM")

if PATH not in ("orbit", "dolly"):
    raise ValueError(f"unsupported path '{PATH}'")
if F1 <= F0:
    raise ValueError("frame_end must exceed frame_start")

scene = bpy.context.scene

tgt = bpy.data.objects.get(f"{NAME}_target") or bpy.data.objects.new(
    f"{NAME}_target", None)
tgt.empty_display_size = 0.5
tgt.location = TARGET
if tgt.name not in scene.collection.objects:
    scene.collection.objects.link(tgt)

cam_data = bpy.data.cameras.new(NAME) if not bpy.data.cameras.get(NAME) \
    else bpy.data.cameras[NAME]
cam = bpy.data.objects.get(NAME) or bpy.data.objects.new(NAME, cam_data)
if cam.name not in scene.collection.objects:
    scene.collection.objects.link(cam)
cam_data.lens = LENS

for c in list(cam.constraints):
    if c.type == "TRACK_TO":
        cam.constraints.remove(c)
con = cam.constraints.new("TRACK_TO")
con.target = tgt
con.track_axis = "TRACK_NEGATIVE_Z"
con.up_axis = "UP_Y"


def _pos(t):
    if PATH == "orbit":
        a = 2.0 * math.pi * t
        return Vector((RADIUS * math.cos(a), RADIUS * math.sin(a), HEIGHT))
    x0, y0, z0 = -RADIUS, -RADIUS, HEIGHT
    x1, y1, z1 = RADIUS, -RADIUS * 0.6, HEIGHT * 0.7
    return Vector((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t,
                   z0 + (z1 - z0) * t))


step = max(1, (F1 - F0) // 12)
keyed = 0
for f in range(F0, F1 + 1, step):
    t = (f - F0) / (F1 - F0)
    cam.location = _pos(t)
    cam.keyframe_insert("location", frame=f)
    keyed += 1
if (F1 - F0) % step:
    cam.location = _pos(1.0)
    cam.keyframe_insert("location", frame=F1)
    keyed += 1
if cam.animation_data and cam.animation_data.action:
    for fc in cam.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"

scene.camera = cam
scene.render.fps = FPS
scene.render.fps_base = 1.0
scene.frame_start = F0
scene.frame_end = F1

_result = {"ok": True, "camera": cam.name, "target": tgt.name,
           "path": PATH, "fps": FPS, "frame_start": F0, "frame_end": F1,
           "keyed": keyed, "lens": LENS}
