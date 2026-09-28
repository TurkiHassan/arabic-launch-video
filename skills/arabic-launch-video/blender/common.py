"""Shared helpers for the Qudrah Academy launch shots (Blender 5.2, EEVEE)."""
import bpy, math, os, sys

FPS = 30

# Academy palette (tailwind.config.ts) — sRGB hex
PINE_950 = "#0e1b14"
PINE_900 = "#16281e"
PINE_800 = "#1f3428"
PINE_700 = "#2a4536"
TEAL_500 = "#336261"
TEAL_400 = "#4a7d7b"
CREAM_100 = "#f2f1ec"
CREAM_200 = "#ece3d0"
CREAM_300 = "#e0d5bd"
ROSE_300 = "#eacbb2"
ROSE_400 = "#d9b498"
ROSE_500 = "#d4a98c"
ROSE_600 = "#b9896c"
ROSE_700 = "#9a6b52"


def lin(hexstr, a=1.0):
    h = hexstr.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, a)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.fps = FPS
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 100
    s.eevee.taa_render_samples = 32
    s.view_settings.view_transform = "AgX"
    try:
        s.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    s.render.film_transparent = False
    return s


def world(color_hex, strength=1.0):
    w = bpy.data.worlds.new("W")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = lin(color_hex)
    bg.inputs[1].default_value = strength
    return w


def principled(name, base_hex, metallic=0.0, rough=0.5, emit_hex=None, emit=0.0, coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(base_hex)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if emit_hex:
        b.inputs["Emission Color"].default_value = lin(emit_hex)
        b.inputs["Emission Strength"].default_value = emit
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
    return m


def emission(name, hexstr, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = lin(hexstr)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m


def key(obj, path, frame, value, interp="BEZIER", easing="AUTO", index=-1):
    """Keyframe obj.path at frame (float seconds allowed via sec())."""
    target = obj
    if path.startswith("data."):
        target = obj.data
        path = path[5:]
    setattr(target, path, value) if not isinstance(value, (tuple, list)) else setattr(target, path, value)
    target.keyframe_insert(data_path=path, frame=frame, index=index)
    ad = target.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad):
            if fc.data_path == path:
                for kp in fc.keyframe_points:
                    if abs(kp.co[0] - frame) < 1e-4:
                        kp.interpolation = interp
                        kp.easing = easing


def _fcurves(ad):
    act = ad.action
    if hasattr(act, "fcurves") and len(getattr(act, "fcurves", [])):
        return list(act.fcurves)
    # Blender 4.4+/5.x layered actions
    out = []
    try:
        slot = ad.action_slot
        for layer in act.layers:
            for strip in layer.strips:
                cb = strip.channelbag(slot)
                if cb:
                    out.extend(cb.fcurves)
    except Exception:
        pass
    return out


def sec(t):
    return 1 + t * FPS


def glare(scene, threshold=0.8, size=7, mix=0.0, strength=1.0):
    """Fog-glow bloom via the compositor (5.x node-group compositor)."""
    try:
        ng = bpy.data.node_groups.new("Comp", "CompositorNodeTree")
        scene.compositing_node_group = ng
        rl = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        out = ng.nodes.new("NodeGroupOutput")
        ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        # glare inputs in 5.x are sockets
        def setin(node, names, val):
            for nm in names:
                if nm in node.inputs:
                    node.inputs[nm].default_value = val
                    return True
            return False
        try:
            gl.glare_type = "FOG_GLOW"
        except Exception:
            pass
        for v in ("Bloom", "BLOOM", "Fog Glow", "FOG_GLOW"):
            try:
                gl.inputs["Type"].default_value = v
                print("GLARE TYPE", v)
                break
            except Exception:
                continue
        setin(gl, ["Threshold"], threshold)
        setin(gl, ["Strength"], strength)
        setin(gl, ["Size"], size)
        setin(gl, ["Quality"], "High")
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], out.inputs[0])
        return True
    except Exception as e:
        print("GLARE FAILED", e)
        return False


def render_settings_png(scene, outdir, alpha=False):
    os.makedirs(outdir, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if alpha else "RGB"
    scene.render.film_transparent = alpha
    scene.render.filepath = os.path.join(outdir, "f_")


def args():
    """Parse args after '--': still=<frame> scale=<pct> out=<dir> start= end="""
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    d = {}
    for x in a:
        k, _, v = x.partition("=")
        d[k] = v
    return d


def run(scene, outdir, alpha=False):
    a = args()
    if "scale" in a:
        scene.render.resolution_percentage = int(a["scale"])
    if "samples" in a:
        scene.eevee.taa_render_samples = int(a["samples"])
    if "save" in a:
        bpy.ops.wm.save_as_mainfile(filepath=a["save"])
    if "still" in a:
        for f in a["still"].split(","):
            scene.frame_set(int(f))
            scene.render.image_settings.file_format = "PNG"
            scene.render.film_transparent = alpha
            scene.render.image_settings.color_mode = "RGBA" if alpha else "RGB"
            scene.render.filepath = os.path.join(a.get("out", outdir), f"still_{int(f):04d}.png")
            bpy.ops.render.render(write_still=True)
    elif "anim" in a:
        render_settings_png(scene, a.get("out", outdir), alpha)
        if "start" in a:
            scene.frame_start = int(a["start"])
        if "end" in a:
            scene.frame_end = int(a["end"])
        bpy.ops.render.render(animation=True)
