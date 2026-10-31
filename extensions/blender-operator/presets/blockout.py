"""blockout preset — build a low-poly greybox set for camera blocking.

Executed inside blender_server's bpy namespace via wrapper exec. Reads an
optional `PARAMS` dict from globals (injected by the orchestrator):

    PARAMS = {"collection": "BLOCKOUT", "seed": 7}

Adds a ground plane plus deterministic boxes/cylinders/cones with flat grey
materials, one sun light and a neutral world. Creates its own collection
only; never deletes existing objects or scenes. Sets `_result` to a summary.
"""
import math
import random

import bpy

P = globals().get("PARAMS") or {}
COLL = P.get("collection", "BLOCKOUT")
SEED = int(P.get("seed", 7))

coll = bpy.data.collections.get(COLL) or bpy.data.collections.new(COLL)
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)

mat = bpy.data.materials.get("BLOCKOUT_GREY") or bpy.data.materials.new(
    "BLOCKOUT_GREY")
mat.diffuse_color = (0.55, 0.55, 0.58, 1.0)


def _link(obj):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    if obj.type == "MESH":
        obj.data.materials.append(mat)
    return obj


def _box(name, loc, scale):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(scale=True)
    return _link(o)


def _cyl(name, loc, radius, depth):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    return _link(o)


def _cone(name, loc, r1, depth):
    bpy.ops.mesh.primitive_cone_add(
        vertices=8, radius1=r1, radius2=0.0, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    return _link(o)


rng = random.Random(SEED)

bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
ground = bpy.context.object
ground.name = "BLOCKOUT_ground"
_link(ground)

spots = [(-4, -3, 1.0), (3.5, -3.5, 1.4), (-3, 3, 0.8), (4, 3, 1.1),
         (0, -0.5, 0.6), (-1.5, 1.5, 1.8)]
created = []
for i, (x, y, h) in enumerate(spots):
    jx = x + rng.uniform(-0.4, 0.4)
    jy = y + rng.uniform(-0.4, 0.4)
    created.append(_box(f"BLOCKOUT_box{i}", (jx, jy, h / 2),
                        (1.0, 1.0, h / 2)).name)

created.append(_cyl("BLOCKOUT_tower", (0, 4.5, 1.6), 0.7, 3.2).name)
created.append(_cone("BLOCKOUT_spire", (-5, 0.5, 1.2), 1.0, 2.4).name)

# lighting: one sun + neutral grey world
if not bpy.data.objects.get("BLOCKOUT_sun"):
    ld = bpy.data.lights.new("BLOCKOUT_sun", type="SUN")
    ld.energy = 3.0
    ld.angle = math.radians(30)
    sun = bpy.data.objects.new("BLOCKOUT_sun", ld)
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    coll.objects.link(sun)

world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.08, 0.09, 0.11, 1.0)
    bg.inputs[1].default_value = 0.6

_result = {"ok": True, "collection": COLL, "objects": sorted(
    o.name for o in coll.objects), "created": created}
