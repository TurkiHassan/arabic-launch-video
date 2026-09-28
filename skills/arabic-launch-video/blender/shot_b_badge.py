"""Shot B — the unit badge (◆ وسام). Scene-local 0–4.5s (135 frames), alpha.

A rosegold medallion spins in from depth like a flipped coin, decelerates and
lands face-on on the strong beat (1.09s local = 17.47s global), a cream
diamond glyph at its heart. Six lesson pips — the unit's six lessons — click
into orbit around it one per beat, then the medal floats.
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

HERE = os.path.dirname(os.path.abspath(__file__))
S = reset()
S.render.resolution_x = 1080
S.render.resolution_y = 1080
S.frame_start, S.frame_end = 1, 135
world(ROSE_300, 0.5)  # reflections only; film is transparent
S.eevee.use_raytracing = True
S.render.use_motion_blur = True
S.render.motion_blur_shutter = 0.5

rose = principled("Rose", ROSE_500, 1.0, 0.22)
rose_dark = principled("RoseDark", ROSE_700, 1.0, 0.35)
cream = principled("Cream", CREAM_100, 0.0, 0.3, coat=0.8)
pine = principled("Pine", PINE_800, 0.0, 0.4, coat=0.5)

piv = bpy.data.objects.new("Medal", None)
S.collection.objects.link(piv)

# disc (faces the camera along -Y)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.55, depth=0.22, rotation=(math.radians(90), 0, 0))
disc = bpy.context.object
b = disc.modifiers.new("b", "BEVEL"); b.width = 0.05; b.segments = 4
disc.data.materials.append(rose)
disc.parent = piv
for p in disc.data.polygons:
    p.use_smooth = True

# inner pine field
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.25, depth=0.23, rotation=(math.radians(90), 0, 0))
field = bpy.context.object
field.data.materials.append(pine)
field.parent = piv

# raised rim ring
bpy.ops.mesh.primitive_torus_add(major_radius=1.33, minor_radius=0.045, major_segments=96, minor_segments=12,
                                 rotation=(math.radians(90), 0, 0), location=(0, -0.12, 0))
ring = bpy.context.object
ring.data.materials.append(rose)
ring.parent = piv

# notches around the rim: 11 — one per unit
for i in range(11):
    a = i / 11 * 2 * math.pi + math.pi / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(1.44 * math.cos(a), -0.12, 1.44 * math.sin(a)))
    n = bpy.context.object
    n.dimensions = (0.06, 0.05, 0.16)
    n.rotation_euler = (0, -a + math.pi / 2, 0)
    n.data.materials.append(rose_dark)
    n.parent = piv

# the ◆ glyph: a faceted diamond
bm = bmesh.new()
v = [bm.verts.new(c) for c in [(0.72, 0, 0), (0, 0, 0.95), (-0.72, 0, 0), (0, 0, -0.95), (0, -0.34, 0)]]
for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
    bm.faces.new((v[a_], v[b_], v[4]))
me = bpy.data.meshes.new("Gem")
bm.to_mesh(me)
gem = bpy.data.objects.new("Gem", me)
S.collection.objects.link(gem)
gem.location = (0, -0.12, 0)
gem.data.materials.append(cream)
gem.parent = piv

# ── motion: coin spin from depth, landing on the beat ──
LAND = 1.09
key(piv, "location", 1, (0.0, 14.0, 1.2), "QUART", "EASE_OUT")
key(piv, "location", sec(LAND), (0, 0, 0), "BEZIER")
key(piv, "location", 135, (0, -0.4, 0.12), "BEZIER")
key(piv, "rotation_euler", 1, (math.radians(-20), 0, math.radians(-3 * 360 - 40)), "QUART", "EASE_OUT")
key(piv, "rotation_euler", sec(LAND), (0, 0, math.radians(6)), "BACK", "EASE_OUT")
key(piv, "rotation_euler", sec(LAND + 0.4), (0, 0, 0), "BEZIER")
key(piv, "rotation_euler", 135, (math.radians(-5), 0, math.radians(-12)), "BEZIER")

# ── six lesson pips click into orbit, one per beat after the landing ──
BEAT = 0.546
for i in range(6):
    a = math.pi / 2 - i * (2 * math.pi / 6) - math.pi / 6
    home = (2.15 * math.cos(a), -0.05, 2.15 * math.sin(a))
    bpy.ops.mesh.primitive_cube_add(size=0.28, location=home)
    pip = bpy.context.object
    pip.rotation_euler = (0, math.radians(45), 0)
    bv = pip.modifiers.new("b", "BEVEL"); bv.width = 0.03; bv.segments = 3
    pip.data.materials.append(cream if i % 2 == 0 else rose)
    t0 = LAND + 0.1 + i * BEAT / 2
    key(pip, "scale", 1, (0.001, 0.001, 0.001), "CONSTANT")
    key(pip, "scale", sec(t0), (0.001, 0.001, 0.001), "BACK", "EASE_OUT")
    key(pip, "scale", sec(t0 + 0.3), (1, 1, 1), "BEZIER")
    out = (home[0] * 1.35, -0.6, home[2] * 1.35)
    key(pip, "location", sec(t0), out, "EXPO", "EASE_OUT")
    key(pip, "location", sec(t0 + 0.35), home, "BEZIER")
    key(pip, "location", 135, (home[0], home[1] - 0.2, home[2] + 0.1), "BEZIER")


def area(name, loc, rot, energy, color, size, sy=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy; ld.color = lin(color)[:3]; ld.size = size
    if sy:
        ld.shape = "RECTANGLE"; ld.size_y = sy
    o = bpy.data.objects.new(name, ld)
    o.location = loc; o.rotation_euler = rot
    S.collection.objects.link(o)
    return o


area("Key", (4, -7, 5), (math.radians(60), 0, math.radians(30)), 700, CREAM_100, 5)
area("Rim", (-5, 4, 3), (math.radians(-70), 0, math.radians(-130)), 1400, TEAL_400, 4)
sweep = area("Sweep", (-7, -5, 0), (math.radians(90), 0, 0), 2400, "#ffffff", 0.35, 9)
key(sweep, "location", sec(LAND), (-7, -5, 0), "BEZIER")
key(sweep, "location", sec(LAND + 1.3), (7, -5, 0), "BEZIER")

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 135
cam = bpy.data.objects.new("Cam", cam_d)
cam.location = (0, -22, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
S.collection.objects.link(cam)
S.camera = cam

glare(S, threshold=0.85, size=0.55, strength=0.6)
run(S, os.path.join(HERE, "out_b"), alpha=True)
