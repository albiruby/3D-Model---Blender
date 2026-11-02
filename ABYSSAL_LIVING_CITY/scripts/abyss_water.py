"""
abyss_water.py : the medium.

Two independent depth cues, deliberately separable so they can be A/B tested:

  fog    - compositor depth fog driven by the Z pass.  Cheap, exact, controllable.
  volume - a world volume that scatters the key light and produces real god rays.

Both are used in the final look; the M1 test decides the balance between them.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector

ATMO = {"mode": "both", "fog_near": 120.0, "fog_far": 620.0,
        "fog_color": "#1A5573", "fog_strength": 1.0,
        "dens": 0.0026, "aniso": 0.62, "abs_dens": 0.0030}


def _comp_group():
    return bpy.data.node_groups.get("AB_Compositing")


def _find(ng, ntype):
    for n in ng.nodes:
        if n.type == ntype:
            return n
    return None


def set_fog(near=None, far=None, color=None, strength=None):
    g = _comp_group()
    if g is None:
        return
    if near is not None:
        ATMO["fog_near"] = near
    if far is not None:
        ATMO["fog_far"] = far
    if color is not None:
        ATMO["fog_color"] = color
    if strength is not None:
        ATMO["fog_strength"] = strength
    # Mist pass: start/depth are world units, falloff is shaped by mist_settings.
    w = MAT.get("world")
    if w is not None:
        ms = w.mist_settings
        ms.start = ATMO["fog_near"]
        ms.depth = max(1.0, ATMO["fog_far"] - ATMO["fog_near"])
        try:
            ms.falloff = "QUADRATIC"
        except Exception:
            pass
    mr = _find(g, "MAP_RANGE")
    if mr is not None:
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = ATMO["fog_strength"]
    for n in g.nodes:
        if n.type == "MIX_RGB" and n.blend_type == "MIX":
            n.inputs["Color2"].default_value = (*hexcol(ATMO["fog_color"]), 1.0)
    print("FOG mist start=%.0f depth=%.0f strength=%.2f colour=%s" % (
        ATMO["fog_near"], ATMO["fog_far"] - ATMO["fog_near"],
        ATMO["fog_strength"], ATMO["fog_color"]))


def _world_volume(enabled, dens=None, aniso=None, abs_dens=None):
    w = MAT.get("world")
    if w is None:
        return
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type in ("VOLUME_SCATTER", "VOLUME_ABSORPTION", "ADD_SHADER"):
            nt.nodes.remove(n)
    out = next((n for n in nt.nodes if n.type == "OUTPUT_WORLD"), None)
    if out is None:
        return
    for l in list(out.inputs["Volume"].links):
        nt.links.remove(l)
    if not enabled:
        return
    dens = ATMO["dens"] if dens is None else dens
    aniso = ATMO["aniso"] if aniso is None else aniso
    abs_dens = ATMO["abs_dens"] if abs_dens is None else abs_dens
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (*hexcol("#2C7FA6"), 1.0)
    sc.inputs["Density"].default_value = dens
    sc.inputs["Anisotropy"].default_value = aniso
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (*hexcol("#5A2A3E"), 1.0)
    ab.inputs["Density"].default_value = abs_dens
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(sc.outputs["Volume"], add.inputs[0])
    nt.links.new(ab.outputs["Volume"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Volume"])


def set_atmosphere(mode="both", **kw):
    """mode: 'fog' | 'volume' | 'both' | 'none'"""
    ATMO["mode"] = mode
    for k, v in kw.items():
        if k in ATMO:
            ATMO[k] = v
    sc = bpy.context.scene
    use_vol = mode in ("volume", "both")
    _world_volume(use_vol)
    if mode == "fog":
        set_fog(strength=1.0)
    elif mode == "volume":
        set_fog(strength=0.25)
    elif mode == "both":
        set_fog(strength=0.94)
    else:
        set_fog(strength=0.0)
    for attr, val in (("volumetric_samples", 64), ("volumetric_end", 420.0),
                      ("volumetric_start", 2.0),
                      ("volumetric_sample_distribution", 0.94),
                      ("use_volumetric_shadows", use_vol),
                      ("volumetric_shadow_samples", 16)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
    print("ATMOSPHERE mode=%s dens=%.4f fog=%.2f" % (mode, ATMO["dens"],
                                                     ATMO["fog_strength"]))


# ---------------------------------------------------------------- marine snow
def build_marine_snow(count=1500, seed=7, coll="OCEAN"):
    """Static drifting particulate: one merged mesh of tiny octahedra.

    No particle system, no animation. Reads as water only because it is sparse
    and the specks are at the edge of visibility.
    """
    rng = random.Random(seed)
    bm = bmesh.new()
    placed = 0
    for i in range(count):
        x = rng.uniform(-96.0, 96.0)
        y = rng.uniform(-82.0, 82.0)
        z = rng.uniform(-25.0, 28.0)
        if z < seabed_h(x, y) + 0.8:
            continue
        # denser over the city, thinning outward
        keep = 0.30 + 0.62 * smoothstep(80.0, 18.0, math.hypot(x, y))
        if rng.random() > keep:
            continue
        r = rng.uniform(0.022, 0.058)
        rz = r * rng.uniform(1.1, 2.0)
        ca = rng.uniform(0, TAU)
        sa = math.sqrt(max(0.0, 1.0 - ca * ca))
        c = Vector((x, y, z))
        ex = Vector((ca * r, sa * r, 0.0))
        ey = Vector((-sa * r, ca * r, 0.0))
        ez = Vector((0.0, 0.0, rz))
        v = [bm.verts.new(c + ez), bm.verts.new(c + ex), bm.verts.new(c + ey),
             bm.verts.new(c - ex), bm.verts.new(c - ey), bm.verts.new(c - ez)]
        for a, b in ((0, 1), (0, 2), (0, 3), (0, 4)):
            bm.faces.new((v[a], v[b], v[5]))
        for a, b in ((1, 2), (2, 3), (3, 4), (4, 1)):
            bm.faces.new((v[a], v[5], v[b]))
        placed += 1
    me = bpy.data.meshes.new("MARINE_SNOW")
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(MAT["snow"])
    ob = bpy.data.objects.new("MARINE_SNOW", me)
    C(coll).objects.link(ob)
    try:
        ob.visible_shadow = False
    except Exception:
        pass
    print("MARINE SNOW specks=%d verts=%d" % (placed, len(me.vertices)))
    return ob


def build_water():
    set_atmosphere("both")
    build_marine_snow()
