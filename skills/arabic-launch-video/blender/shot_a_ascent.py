"""Shot A — «The Ascent». 0–7.15s (215 frames).

A rosegold line draws itself across the academy's blueprint grid, then —
on the music's lift at 2.75s — the 34 lessons rise as tiles along it and
wind upward into a spiral path, 11 units marked by rosegold milestones.
"""
import bpy, math, random, sys, os
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

S = reset()
S.frame_start, S.frame_end = 1, 215
world(PINE_900, 1.0)
# light atmospheric haze so the lights carve depth into the dark
vol = bpy.data.worlds["W"].node_tree
vs = vol.nodes.new("ShaderNodeVolumeScatter")
vs.inputs["Density"].default_value = 0.012
vs.inputs["Color"].default_value = lin(TEAL_400)
wo = next(n for n in vol.nodes if n.type == "OUTPUT_WORLD")
vol.links.new(vs.outputs[0], wo.inputs["Volume"])
S.render.use_motion_blur = True
S.render.motion_blur_shutter = 0.45

rng = random.Random(7)

# ───────── blueprint grid floor ─────────
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("Grid")
fm.use_nodes = True
nt = fm.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
N = nt.nodes.new
L = nt.links.new
out = N("ShaderNodeOutputMaterial")
tc = N("ShaderNodeTexCoord")
sep = N("ShaderNodeSeparateXYZ")
L(tc.outputs["Object"], sep.inputs[0])


def line_mask(axis_out, period, width):
    d = N("ShaderNodeMath"); d.operation = "DIVIDE"; d.inputs[1].default_value = period
    L(axis_out, d.inputs[0])
    a = N("ShaderNodeMath"); a.operation = "ADD"; a.inputs[1].default_value = 0.5
    L(d.outputs[0], a.inputs[0])
    f = N("ShaderNodeMath"); f.operation = "FRACT"
    L(a.outputs[0], f.inputs[0])
    s = N("ShaderNodeMath"); s.operation = "SUBTRACT"; s.inputs[1].default_value = 0.5
    L(f.outputs[0], s.inputs[0])
    ab = N("ShaderNodeMath"); ab.operation = "ABSOLUTE"
    L(s.outputs[0], ab.inputs[0])
    lt = N("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = width / period
    L(ab.outputs[0], lt.inputs[0])
    return lt.outputs[0]


def grid(period, width):
    mx = N("ShaderNodeMath"); mx.operation = "MAXIMUM"
    L(line_mask(sep.outputs[0], period, width), mx.inputs[0])
    L(line_mask(sep.outputs[1], period, width), mx.inputs[1])
    return mx.outputs[0]


minor = grid(1.0, 0.012)
major = grid(5.0, 0.03)
mm = N("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = 0.10
L(minor, mm.inputs[0])
mj = N("ShaderNodeMath"); mj.operation = "MULTIPLY"; mj.inputs[1].default_value = 0.24
L(major, mj.inputs[0])
lines = N("ShaderNodeMath"); lines.operation = "MAXIMUM"
L(mm.outputs[0], lines.inputs[0]); L(mj.outputs[0], lines.inputs[1])
# fade with distance from the spiral so the floor dissolves into the dark
vl = N("ShaderNodeVectorMath"); vl.operation = "LENGTH"
L(tc.outputs["Object"], vl.inputs[0])
mr = N("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 6
mr.inputs["From Max"].default_value = 30
mr.inputs["To Min"].default_value = 1
mr.inputs["To Max"].default_value = 0
L(vl.outputs["Value"], mr.inputs["Value"])
fade = N("ShaderNodeMath"); fade.operation = "MULTIPLY"
L(lines.outputs[0], fade.inputs[0]); L(mr.outputs["Result"], fade.inputs[1])
strength = N("ShaderNodeMath"); strength.operation = "MULTIPLY"; strength.inputs[1].default_value = 1.0
L(fade.outputs[0], strength.inputs[0])
em = N("ShaderNodeEmission"); em.inputs[0].default_value = lin(CREAM_200)
L(strength.outputs[0], em.inputs[1])
bs = N("ShaderNodeBsdfPrincipled")
bs.inputs["Base Color"].default_value = lin(PINE_900)
bs.inputs["Roughness"].default_value = 0.35
bs.inputs["Specular IOR Level"].default_value = 0.35
add = N("ShaderNodeAddShader")
L(bs.outputs[0], add.inputs[0]); L(em.outputs[0], add.inputs[1])
L(add.outputs[0], out.inputs[0])
floor.data.materials.append(fm)

# ───────── the path ─────────
R0, R1, H, TURNS = 3.4, 1.7, 10.5, 1.55
pts = []
LEAD = 70
for k in range(LEAD):
    u = k / LEAD
    y = -16 + (16 - R0) * u
    x = 0.9 * math.sin(math.pi * 1.5 * u) * (1 - u)
    pts.append(Vector((x, y, 0.0)))
HEL = 320
for k in range(HEL + 1):
    u = k / HEL
    th = -math.pi / 2 + u * TURNS * 2 * math.pi
    r = R0 + (R1 - R0) * u
    z = H * (u ** 1.08)
    pts.append(Vector((r * math.cos(th), r * math.sin(th), z)))

# arc length table
acc = [0.0]
for i in range(1, len(pts)):
    acc.append(acc[-1] + (pts[i] - pts[i - 1]).length)
TOTAL = acc[-1]
LEAD_LEN = acc[LEAD]


def at_len(s):
    s = max(0, min(TOTAL, s))
    lo, hi = 0, len(acc) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if acc[mid] < s:
            lo = mid
        else:
            hi = mid
    t = (s - acc[lo]) / max(1e-6, acc[hi] - acc[lo])
    p = pts[lo].lerp(pts[hi], t)
    tan = (pts[hi] - pts[lo]).normalized()
    return p, tan


TILE_T = 0.16
# glowing inlay line (runs on top of the tiles)
cd = bpy.data.curves.new("PathLine", "CURVE")
cd.dimensions = "3D"
sp = cd.splines.new("POLY")
sp.points.add(len(pts) - 1)
for i, p in enumerate(pts):
    zoff = 0.03 if i < LEAD else TILE_T + 0.02
    sp.points[i].co = (p.x, p.y, p.z + zoff, 1)
cd.bevel_depth = 0.028
cd.bevel_resolution = 3
cd.use_fill_caps = True
cd.bevel_factor_mapping_end = "SPLINE"
line = bpy.data.objects.new("PathLine", cd)
S.collection.objects.link(line)
line.data.materials.append(emission("LineGlow", ROSE_500, 3.2))

# line draw-on: lead-in during the hook, then races up ahead of the tiles
lead_frac = LEAD_LEN / TOTAL
key(line, "data.bevel_factor_end", sec(0.15), 0.0, "BEZIER")
key(line, "data.bevel_factor_end", sec(2.72), lead_frac, "BEZIER")
key(line, "data.bevel_factor_end", sec(5.35), 1.0, "BEZIER")

# ───────── 34 lesson tiles in 11 units ─────────
UNITS = [6, 4, 5, 5, 5, 3, 1, 2, 1, 1, 1]
slots = []
pos = 0.0
for ui, n in enumerate(UNITS):
    for j in range(n):
        slots.append((pos, ui, j == 0))
        pos += 1.0
    pos += 0.9  # gap between units
span = pos - 0.9
start_len = LEAD_LEN + 0.55
usable = TOTAL - start_len - 0.9
step = usable / span

paper = principled("Paper", CREAM_100, 0.0, 0.5, emit_hex=CREAM_200, emit=0.12, coat=0.2)
paper_edge = principled("PaperShade", CREAM_200, 0.0, 0.55, emit_hex=CREAM_200, emit=0.08)
rose = principled("Rose", ROSE_400, 1.0, 0.2, emit_hex=ROSE_500, emit=0.9)
teal = principled("Teal", TEAL_500, 0.0, 0.45)

tiles = []
for i, (p_slot, ui, first) in enumerate(slots):
    s_len = start_len + (p_slot + 0.5) * step
    p, tan = at_len(s_len)
    bpy.ops.mesh.primitive_cube_add(size=1)
    t = bpy.context.object
    t.name = f"Tile{i:02d}"
    t.dimensions = (step * 0.8, 1.7, TILE_T)
    bpy.ops.object.transform_apply(scale=True)
    bev = t.modifiers.new("b", "BEVEL")
    bev.width = 0.03
    bev.segments = 3
    # orient: local X along tangent, Z up
    x = Vector((tan.x, tan.y, tan.z)).normalized()
    zup = Vector((0, 0, 1))
    y = zup.cross(x).normalized()
    z = x.cross(y).normalized()
    M = Matrix((x, y, z)).transposed().to_4x4()
    t.matrix_world = Matrix.Translation(p + Vector((0, 0, TILE_T / 2))) @ M
    t.data.materials.append(rose if first else (paper if i % 2 == 0 else paper_edge))
    for poly in t.data.polygons:
        poly.use_smooth = True
    tiles.append(t)

# rise, one lesson at a time, from the lift (2.75s)
for i, t in enumerate(tiles):
    t0 = 2.75 + i * 0.072
    base = t.location.copy()
    key(t, "scale", sec(t0) - 1, (0.001, 0.001, 0.001), "CONSTANT")
    key(t, "location", sec(t0) - 1, base - Vector((0, 0, 0.9)), "CONSTANT")
    key(t, "scale", sec(t0), (0.2, 0.2, 0.2), "BACK", "EASE_OUT")
    key(t, "location", sec(t0), base - Vector((0, 0, 0.9)), "EXPO", "EASE_OUT")
    key(t, "scale", sec(t0 + 0.38), (1, 1, 1), "BEZIER")
    key(t, "location", sec(t0 + 0.42), base, "BEZIER")
    # before its moment the tile does not exist
    key(t, "scale", 1, (0.001, 0.001, 0.001), "CONSTANT")

# ───────── summit: the target the path climbs to ─────────
top, _ = at_len(TOTAL)
summit = top + Vector((0, 0, 1.25))
ring_mat = emission("RingGlow", ROSE_300, 4.0)
rings = []
for r, th in ((0.62, 0.035), (1.0, 0.02), (1.45, 0.012)):
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=th, location=summit)
    o = bpy.context.object
    o.rotation_euler = (math.radians(90), 0, math.radians(20))
    o.data.materials.append(ring_mat)
    rings.append(o)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.34, location=summit)
gem = bpy.context.object
gem.scale = (0.75, 0.75, 1.25)
gem.data.materials.append(rose)
for i, o in enumerate(rings + [gem]):
    t0 = 5.05 + i * 0.09
    key(o, "scale", 1, (0.001, 0.001, 0.001), "CONSTANT")
    key(o, "scale", sec(t0), (0.001, 0.001, 0.001), "BACK", "EASE_OUT")
    key(o, "scale", sec(t0 + 0.5), (0.75, 0.75, 1.25) if o is gem else (1, 1, 1), "BEZIER")
key(gem, "rotation_euler", 1, (0, 0, 0), "LINEAR")
key(gem, "rotation_euler", 215, (0, 0, math.radians(260)), "LINEAR")
for i, o in enumerate(rings):
    key(o, "rotation_euler", sec(5.0), (math.radians(90), 0, math.radians(20 + i * 30)), "LINEAR")
    key(o, "rotation_euler", 215, (math.radians(90 - 12 * (i - 1)), 0, math.radians(80 + i * 60)), "LINEAR")

# ───────── lab solids: wireframe geometry drifting around the climb ─────────
wire_a = emission("WireCream", CREAM_200, 1.6)
wire_b = emission("WireTeal", TEAL_400, 2.2)
solids = [
    ("cube", (-5.2, 1.5, 3.2), 1.3),
    ("ico", (5.4, 2.8, 6.3), 1.1),
    ("cone", (-4.6, 3.8, 8.8), 1.0),
    ("cyl", (4.9, -3.0, 2.2), 0.9),
    ("tet", (-3.8, -5.5, 1.6), 0.8),
    ("torus", (4.2, 4.5, 10.6), 0.9),
    ("cube2", (-6.5, 6.0, 12.0), 0.8),
]
for i, (kind, loc, s) in enumerate(solids):
    if kind.startswith("cube"):
        bpy.ops.mesh.primitive_cube_add(size=s, location=loc)
    elif kind == "ico":
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=s * 0.7, location=loc)
    elif kind == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=s * 0.6, depth=s * 1.3, location=loc)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=s * 0.5, depth=s, location=loc)
    elif kind == "tet":
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=s * 0.7, depth=s, location=loc)
    elif kind == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=s * 0.6, minor_radius=s * 0.18, major_segments=16, minor_segments=6, location=loc)
    o = bpy.context.object
    w = o.modifiers.new("w", "WIREFRAME")
    w.thickness = 0.022
    o.data.materials.append(wire_b if i % 2 else wire_a)
    r0 = (rng.uniform(0, 6), rng.uniform(0, 6), rng.uniform(0, 6))
    key(o, "rotation_euler", 1, r0, "LINEAR")
    key(o, "rotation_euler", 215, (r0[0] + 1.1, r0[1] + 0.7, r0[2] + 1.5), "LINEAR")
    key(o, "location", 1, loc, "LINEAR")
    key(o, "location", 215, (loc[0], loc[1], loc[2] + 0.9), "LINEAR")

# ───────── floating paper chips (the hero artwork's squares) ─────────
chip_mats = [principled("ChipCream", CREAM_200, 0, 0.6), principled("ChipRose", ROSE_500, 0.6, 0.35),
             principled("ChipTeal", TEAL_500, 0, 0.5), emission("ChipGlow", ROSE_300, 3.0)]
for i in range(90):
    ang = rng.uniform(0, 2 * math.pi)
    rad = rng.uniform(4.5, 11)
    z = rng.uniform(0.4, 15)
    loc = (rad * math.cos(ang), rad * math.sin(ang), z)
    s = rng.uniform(0.06, 0.32)
    bpy.ops.mesh.primitive_plane_add(size=s, location=loc)
    o = bpy.context.object
    o.data.materials.append(chip_mats[0 if i % 5 < 2 else (1 if i % 5 == 2 else (2 if i % 5 == 3 else 3))])
    r0 = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
    key(o, "rotation_euler", 1, r0, "LINEAR")
    key(o, "rotation_euler", 215, (r0[0] + rng.uniform(-1.5, 1.5), r0[1] + rng.uniform(-1.5, 1.5), r0[2]), "LINEAR")
    key(o, "location", 1, loc, "LINEAR")
    key(o, "location", 215, (loc[0], loc[1], loc[2] + rng.uniform(0.4, 1.4)), "LINEAR")

# ───────── light ─────────
def area(name, loc, rot, energy, color, size):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = lin(color)[:3]
    ld.size = size
    o = bpy.data.objects.new(name, ld)
    o.location = loc
    o.rotation_euler = rot
    S.collection.objects.link(o)
    return o

area("Key", (6, -8, 14), (math.radians(45), 0, math.radians(35)), 5200, ROSE_300, 6)
area("Rim", (-7, 9, 9), (math.radians(-60), 0, math.radians(200)), 1800, TEAL_400, 8)
area("Fill", (0, -14, 3), (math.radians(80), 0, 0), 500, CREAM_100, 10)

# ───────── camera ─────────
look = bpy.data.objects.new("Look", None)
S.collection.objects.link(look)
cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 26
cam_d.sensor_fit = "VERTICAL"
cam_d.sensor_height = 36
cam_d.dof.use_dof = True
cam_d.dof.focus_object = look
cam_d.dof.aperture_fstop = 3.2
cam = bpy.data.objects.new("Cam", cam_d)
S.collection.objects.link(cam)
S.camera = cam
c = cam.constraints.new("TRACK_TO")
c.target = look
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"


def polar(a_deg, r, z):
    a = math.radians(a_deg)
    return (r * math.cos(a), r * math.sin(a), z)

# hook: skim the floor behind the drawing line
key(cam, "location", 1, (0.9, -21.5, 0.55))
key(look, "location", 1, (0.0, -12.0, 0.35))
key(cam, "location", sec(2.75), (0.35, -15.2, 0.95))
key(look, "location", sec(2.75), (0.0, -4.0, 0.9))
# the lift: crane up and swing round the spiral as the lessons rise
key(cam, "location", sec(4.8), polar(-100, 12.0, 4.6))
key(look, "location", sec(4.8), (0.0, 0.0, 4.0))
key(cam, "location", 215, polar(-128, 15.5, 9.5))
key(look, "location", 215, (0.0, 0.0, 7.4))

glare(S, threshold=0.75, size=0.6, strength=0.7)
run(S, os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_a"))
