"""Shot C — the قُدرة mark in 3D. Scene-local 0–5.6s (170 frames), alpha.

Cream ring swings in edge-on and lands on the beat (0.56s), the rosegold
diamond and page stamp down onto it on the next beat (1.09s), a strip of
light sweeps the metal, then the mark breathes in a slow drift.
"""
import bpy, math, sys, os
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

HERE = os.path.dirname(os.path.abspath(__file__))
S = reset()
S.render.resolution_x = 1080
S.render.resolution_y = 1080
S.frame_start, S.frame_end = 1, 170
world(ROSE_300, 0.55)  # never seen (alpha film) — it is what the metal reflects
S.eevee.use_raytracing = True
S.render.use_motion_blur = True
S.render.motion_blur_shutter = 0.5


def import_svg(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=path)
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    return o


base = import_svg(os.path.join(HERE, "mark_base.svg"), "Base")
gold = import_svg(os.path.join(HERE, "mark_gold.svg"), "Gold")

# SVG units → centre on origin, ~4.2 units tall
for o in (base, gold):
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
bb = [base.matrix_world @ Vector(c) for c in base.bound_box]
h = max(v.y for v in bb) - min(v.y for v in bb)
k = 4.2 / h
center = base.location.copy()
for o in (base, gold):
    o.location = (o.location - center) * k
    o.scale = (o.scale[0] * k, o.scale[1] * k, o.scale[2] * k)
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)

base.data.extrude = 0.16
base.data.bevel_depth = 0.022
base.data.bevel_resolution = 4
gold.data.extrude = 0.24
gold.data.bevel_depth = 0.026
gold.data.bevel_resolution = 4
base.data.materials.clear()
gold.data.materials.clear()
base.data.materials.append(principled("MarkCream", "#f3ecdd", 0.0, 0.32, coat=0.6))
gold.data.materials.append(principled("MarkGold", "#dabd9d", 1.0, 0.24))

# pivot for the whole mark
piv = bpy.data.objects.new("Pivot", None)
S.collection.objects.link(piv)
for o in (base, gold):
    o.parent = piv
# the SVG imports flat on XY; stand it up facing -Y (camera side)
piv.rotation_mode = "XYZ"

gold_home = gold.location.copy()

# ── motion ──
# ring swings in edge-on, lands on the beat at 0.56s
key(piv, "rotation_euler", 1, (math.radians(90), math.radians(-100), math.radians(-24)), "CUBIC", "EASE_OUT")
key(piv, "rotation_euler", sec(0.56), (math.radians(90), math.radians(4), math.radians(2)), "BEZIER")
key(piv, "rotation_euler", sec(1.4), (math.radians(90), 0, 0), "BEZIER")
key(piv, "rotation_euler", 170, (math.radians(90), math.radians(-9), math.radians(-3)), "BEZIER")
key(piv, "location", 1, (1.4, 9.0, -0.6), "CUBIC", "EASE_OUT")
key(piv, "location", sec(0.56), (0, 0, 0), "BEZIER")
key(piv, "location", 170, (0, -0.35, 0.05), "BEZIER")
key(piv, "scale", 1, (0.4, 0.4, 0.4), "CUBIC", "EASE_OUT")
key(piv, "scale", sec(0.56), (1, 1, 1), "BEZIER")

# gold stamps down onto the ring on the next beat (1.09s)
key(gold, "location", 1, gold_home + Vector((0, 0, 3.2)), "CONSTANT")
key(gold, "location", sec(0.7), gold_home + Vector((0, 0, 3.2)), "EXPO", "EASE_IN")
key(gold, "location", sec(1.09), gold_home, "BACK", "EASE_OUT")
key(gold, "location", sec(1.3), gold_home, "BEZIER")
key(gold, "scale", 1, (0.001, 0.001, 0.001), "CONSTANT")
key(gold, "scale", sec(0.7) - 1, (0.001, 0.001, 0.001), "CONSTANT")
key(gold, "scale", sec(0.7), (1, 1, 1), "CONSTANT")


def area(name, loc, rot, energy, color, size, shape="RECTANGLE", sy=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = lin(color)[:3]
    ld.shape = shape
    ld.size = size
    if sy:
        ld.size_y = sy
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = rot
    S.collection.objects.link(o)
    return o


area("Key", (4, -7, 5), (math.radians(60), 0, math.radians(30)), 650, CREAM_100, 5)
area("Rim", (-5, 4, 3), (math.radians(-70), 0, math.radians(-130)), 1400, TEAL_400, 4)
area("Warm", (-4, -6, -3), (math.radians(115), 0, math.radians(-35)), 500, ROSE_400, 4)
# the sweep: a tall strip light crossing in front, catching every facet once
sweep = area("Sweep", (-7, -5, 0), (math.radians(90), 0, 0), 2600, "#ffffff", 0.35, "RECTANGLE", 9)
key(sweep, "location", sec(1.1), (-7, -5, 0), "BEZIER")
key(sweep, "location", sec(2.6), (7, -5, 0), "BEZIER")

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 110
cam = bpy.data.objects.new("Cam", cam_d)
cam.location = (0, -22, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
S.collection.objects.link(cam)
S.camera = cam

glare(S, threshold=0.85, size=0.55, strength=0.6)
run(S, os.path.join(HERE, "out_c"), alpha=True)
