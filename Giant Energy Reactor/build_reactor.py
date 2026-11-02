"""
GIANT ENERGY REACTOR - THE CORE OF INFINITE POWER
Procedural Blender builder. Re-runnable: purges every object prefixed RE_
and rebuilds the whole scene deterministically.

Blender 5.2 / EEVEE.  Run inside Blender:
    exec(compile(open(r"<path>\\build_reactor.py").read(), "build_reactor.py", "exec"))
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector

BASE_DIR = r"D:\Tes Animasi-Motion-Blender\Giant Energy Reactor"
TAU = math.pi * 2.0
RND = random.Random(20261101)

PALETTE = {
    "GUNMETAL": "#252D36",
    "STEEL": "#687783",
    "TITANIUM": "#AAB8C2",
    "BRONZE": "#96633F",
    "COPPER": "#B96D48",
    "CYAN": "#28DFFF",
    "ELECTRIC": "#087DFF",
    "AMBER": "#FF9C32",
    "GLASS": "#101B28",
}

CORE_Z = 7.6
BASE_TOP = 1.25
PILLAR_R = 4.85
PILLAR_TOP = 11.2


# ---------------------------------------------------------------- materials
def _s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip("#")
    return tuple(_s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


def make_mat(name, hexv, metallic=1.0, rough=0.4, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    col = hexcol(hexv)
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*hexcol(emit), 1.0)
        bsdf.inputs["Emission Strength"].default_value = estr
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        try:
            m.use_transparent_shadow = False
        except Exception:
            pass
    return m


MAT = {}


def build_materials():
    MAT["gunmetal"] = make_mat("MAT_DARK_GUNMETAL", "#1E252D", 1.0, 0.55)
    MAT["steel"] = make_mat("MAT_INDUSTRIAL_STEEL", "#3A444E", 0.95, 0.38)
    MAT["titanium"] = make_mat("MAT_TITANIUM", "#7C8A96", 1.0, 0.26)
    MAT["bronze"] = make_mat("MAT_BRONZE", "#8A5A38", 1.0, 0.46)
    MAT["copper"] = make_mat("MAT_COPPER", "#B0673F", 1.0, 0.34)
    MAT["cyan"] = make_mat("MAT_REACTOR_CYAN", "#041A22", 0.0, 0.30, PALETTE["CYAN"], 3.0)
    MAT["electric"] = make_mat("MAT_ELECTRIC_BLUE", "#02101F", 0.0, 0.25, PALETTE["ELECTRIC"], 2.2, alpha=0.30)
    MAT["amber"] = make_mat("MAT_WARNING_AMBER", "#241102", 0.0, 0.35, PALETTE["AMBER"], 7.0)
    MAT["core"] = make_mat("MAT_CORE_WHITE", "#DDF6FF", 0.0, 0.20, "#BFEFFF", 14.0)
    MAT["halo"] = make_mat("MAT_CORE_HALO", "#0B3A4A", 0.0, 0.30, "#7FE8FF", 1.4, alpha=0.06)
    MAT["glass"] = make_mat("MAT_DARK_GLASS", PALETTE["GLASS"], 0.0, 0.06, "#0E3A55", 0.25, alpha=0.08)
    MAT["floor"] = make_mat("MAT_FLOOR_ALLOY", "#0C1116", 0.8, 0.42)
    MAT["bg"] = make_mat("MAT_BG_STRUCTURE", "#05080C", 0.0, 0.95)

    # core nucleus: facing-driven gradient so it reads as volumetric energy, not a white disc
    m = bpy.data.materials.get("MAT_CORE_NUCLEUS") or bpy.data.materials.new("MAT_CORE_NUCLEUS")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.01, 0.06, 0.10, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.25
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = (0.006, 0.16, 0.36, 1.0)
    els[1].position = 0.85
    els[1].color = (0.88, 1.0, 1.0, 1.0)
    nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 6.5
    MAT["core"] = m


# ---------------------------------------------------------------- collections
COLLS = {}
ROOT = None


def build_collections():
    global ROOT
    ROOT = bpy.data.collections.new("GIANT_ENERGY_REACTOR")
    bpy.context.scene.collection.children.link(ROOT)
    names = [
        "01_REACTOR_CORE",
        "02_CONTAINMENT_RINGS",
        "03_STRUCTURAL_FRAME",
        "04_GEAR_ASSEMBLIES",
        "05_HYDRAULIC_SYSTEMS",
        "06_ENERGY_NETWORK",
        "07_INDUSTRIAL_BASE",
        "08_ENVIRONMENT",
        "09_LIGHTING",
        "10_CAMERAS",
    ]
    for n in names:
        c = bpy.data.collections.new(n)
        ROOT.children.link(c)
        COLLS[n[3:]] = c


def C(key):
    return COLLS[key]


# ---------------------------------------------------------------- primitives
def _finish(ob, name, mat, coll):
    ob.name = name
    ob.data.name = name
    if mat is not None:
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    return ob


def bevel(ob, width=0.02, segments=2):
    b = ob.modifiers.new("Bevel", "BEVEL")
    b.width = width
    b.segments = segments
    b.limit_method = "ANGLE"
    b.angle_limit = math.radians(40)
    return ob


def box(name, size, loc, mat, coll, rot=(0, 0, 0), bev=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.scale = size
    _finish(ob, name, mat, coll)
    if bev:
        bevel(ob, bev, 2)
    return ob


def cyl(name, r, d, loc, mat, coll, rot=(0, 0, 0), verts=20, bev=0.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d, location=loc, rotation=rot)
    ob = bpy.context.object
    _finish(ob, name, mat, coll)
    if bev:
        bevel(ob, bev, 1)
    return ob


def cone(name, r1, r2, d, loc, mat, coll, rot=(0, 0, 0), verts=24, bev=0.012):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d, location=loc, rotation=rot)
    ob = bpy.context.object
    _finish(ob, name, mat, coll)
    if bev:
        bevel(ob, bev, 1)
    return ob


def torus(name, major, minor, loc, mat, coll, rot=(0, 0, 0), mseg=48, nseg=10):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor, major_segments=mseg,
        minor_segments=nseg, location=loc, rotation=rot,
    )
    ob = bpy.context.object
    return _finish(ob, name, mat, coll)


def sphere(name, r, loc, mat, coll, smooth=True, seg=32, rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    ob = bpy.context.object
    _finish(ob, name, mat, coll)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def align_z(ob, direction):
    ob.rotation_euler = Vector(direction).normalized().to_track_quat("Z", "Y").to_euler()


def pipe(name, points, radius, mat, coll, res=6):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_depth = radius
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = Vector(co)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def ring_points(radius, tilt_x, tilt_z, count, z=CORE_Z, phase=0.0):
    """Points on a circle whose plane is rotated by tilt_x (X) then tilt_z (Z)."""
    pts = []
    rx, rz = math.radians(tilt_x), math.radians(tilt_z)
    for i in range(count):
        a = phase + i * TAU / count
        p = Vector((math.cos(a) * radius, math.sin(a) * radius, 0.0))
        # rotate about X
        y = p.y * math.cos(rx) - p.z * math.sin(rx)
        zz = p.y * math.sin(rx) + p.z * math.cos(rx)
        p = Vector((p.x, y, zz))
        # rotate about Z
        x = p.x * math.cos(rz) - p.y * math.sin(rz)
        y = p.x * math.sin(rz) + p.y * math.cos(rz)
        pts.append(Vector((x, y, p.z + z)))
    return pts


# ---------------------------------------------------------------- gear
def gear(name, teeth, r_tip, tooth_h, thick, bore, mat, coll, loc,
         normal=(0, 0, 1), hub_r=None, hub_h=None, hub_mat=None):
    r_root = r_tip - tooth_h
    step = TAU / teeth
    bm = bmesh.new()
    n = teeth * 4
    outer, inner = [], []
    for i in range(teeth):
        a = i * step
        for frac, rad in ((0.0, r_root), (0.13, r_tip), (0.40, r_tip), (0.53, r_root)):
            ang = a + step * frac
            outer.append(bm.verts.new((math.cos(ang) * rad, math.sin(ang) * rad, thick * 0.5)))
    for i in range(n):
        ang = i * TAU / n
        inner.append(bm.verts.new((math.cos(ang) * bore, math.sin(ang) * bore, thick * 0.5)))
    bm.verts.ensure_lookup_table()
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((inner[i], inner[j], outer[j], outer[i])))
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=verts, vec=(0, 0, -thick))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    me.materials.append(mat)
    ob.location = loc
    align_z(ob, normal)

    hub_r = hub_r if hub_r else r_root * 0.40
    hub_h = hub_h if hub_h else thick * 2.2
    hub_mat = hub_mat or MAT["bronze"]
    hb = cyl(name + "_hub", hub_r, hub_h, loc, hub_mat, coll, verts=16)
    align_z(hb, normal)
    cap = cyl(name + "_cap", hub_r * 0.62, hub_h * 0.30,
              Vector(loc) + Vector(normal).normalized() * hub_h * 0.58,
              MAT["titanium"], coll, verts=12)
    align_z(cap, normal)
    return ob


# ---------------------------------------------------------------- build
def build_base():
    c = C("INDUSTRIAL_BASE")
    cyl("RE_Base_00", 6.9, 0.34, (0, 0, 0.17), MAT["gunmetal"], c, verts=32)
    cyl("RE_Base_01", 6.25, 0.30, (0, 0, 0.49), MAT["steel"], c, verts=32)
    cyl("RE_Base_02", 5.65, 0.42, (0, 0, 0.85), MAT["gunmetal"], c, verts=32)
    cyl("RE_Base_03", 4.95, 0.36, (0, 0, 1.21), MAT["steel"], c, verts=32)
    torus("RE_Base_Trim_Low", 6.05, 0.10, (0, 0, 0.66), MAT["bronze"], c)
    torus("RE_Base_Trim_High", 5.22, 0.08, (0, 0, 1.06), MAT["copper"], c)
    torus("RE_Base_Lip", 6.7, 0.07, (0, 0, 0.35), MAT["titanium"], c)

    # radial ribs on the base
    for i in range(12):
        a = i * TAU / 12
        box("RE_Base_Rib_%02d" % i, (2.1, 0.15, 0.13),
            (math.cos(a) * 5.3, math.sin(a) * 5.3, 1.07),
            MAT["bronze"], c, rot=(0, 0, a))

    # catwalk deck
    for i in range(24):
        a = i * TAU / 24
        box("RE_Catwalk_%02d" % i, (0.95, 0.62, 0.07),
            (math.cos(a) * 5.9, math.sin(a) * 5.9, 2.12),
            MAT["steel"], c, rot=(0, 0, a + math.pi / 2), bev=0.01)
    torus("RE_Catwalk_Rail", 6.28, 0.035, (0, 0, 3.05), MAT["titanium"], c, mseg=64, nseg=6)
    for i in range(16):
        a = i * TAU / 16
        cyl("RE_Catwalk_Post_%02d" % i, 0.035, 0.95,
            (math.cos(a) * 6.28, math.sin(a) * 6.28, 2.6), MAT["titanium"], c, verts=8)

    # vents + cooling units around the base
    for i in range(8):
        a = i * TAU / 8 + 0.2
        x, y = math.cos(a) * 5.55, math.sin(a) * 5.55
        box("RE_Vent_%02d" % i, (0.75, 0.95, 0.55), (x, y, 0.95),
            MAT["gunmetal"], c, rot=(0, 0, a))
        for k in range(4):
            tx, ty = -math.sin(a), math.cos(a)
            box("RE_Vent_Fin_%02d_%d" % (i, k), (0.62, 0.05, 0.06),
                (x + tx * (k - 1.5) * 0.17, y + ty * (k - 1.5) * 0.17, 1.26),
                MAT["steel"], c, rot=(0, 0, a), bev=0)

    # warning lights on the base rim
    for i in range(12):
        a = i * TAU / 12 + 0.13
        sphere("RE_Warn_%02d" % i, 0.075,
               (math.cos(a) * 6.62, math.sin(a) * 6.62, 0.62), MAT["amber"], c, seg=10, rings=6)


def build_pedestal():
    c = C("STRUCTURAL_FRAME")
    cone("RE_Pedestal_A", 4.9, 3.45, 2.85, (0, 0, 2.78), MAT["gunmetal"], c, verts=32)
    cone("RE_Pedestal_B", 3.45, 2.62, 1.28, (0, 0, 4.84), MAT["steel"], c, verts=32)
    torus("RE_Pedestal_Trim_A", 3.5, 0.11, (0, 0, 4.20), MAT["bronze"], c, mseg=40)
    torus("RE_Pedestal_Trim_B", 2.7, 0.09, (0, 0, 5.42), MAT["copper"], c, mseg=40)

    for i in range(8):
        a = i * TAU / 8
        x, y = math.cos(a) * 4.15, math.sin(a) * 4.15
        box("RE_Pedestal_Rib_%02d" % i, (0.30, 0.22, 3.2), (x, y, 2.9),
            MAT["steel"], c, rot=(0, 0, a), bev=0.015)
        box("RE_Pedestal_Brace_%02d" % i, (0.95, 0.16, 0.30),
            (math.cos(a) * 3.6, math.sin(a) * 3.6, 5.35), MAT["bronze"], c, rot=(0, 0, a))


def build_pillars():
    c = C("STRUCTURAL_FRAME")
    for i in range(8):
        a = i * TAU / 8 + math.pi / 8
        x, y = math.cos(a) * PILLAR_R, math.sin(a) * PILLAR_R
        box("RE_Pillar_%02d" % i, (0.58, 0.58, PILLAR_TOP - BASE_TOP),
            (x, y, (BASE_TOP + PILLAR_TOP) / 2), MAT["gunmetal"], c, rot=(0, 0, a), bev=0.025)
        box("RE_Pillar_Foot_%02d" % i, (0.95, 0.95, 0.55), (x, y, 1.5),
            MAT["steel"], c, rot=(0, 0, a), bev=0.02)
        box("RE_Pillar_Cap_%02d" % i, (0.9, 0.9, 0.55), (x, y, PILLAR_TOP - 0.2),
            MAT["steel"], c, rot=(0, 0, a), bev=0.02)
        # vertical copper pipe on the outer face
        cyl("RE_Pillar_Pipe_%02d" % i, 0.085, PILLAR_TOP - 2.2,
            (math.cos(a) * 5.18, math.sin(a) * 5.18, 6.2), MAT["copper"], c, verts=10)
        # bracket reaching toward the chamber
        box("RE_Pillar_Bracket_%02d" % i, (1.75, 0.22, 0.26),
            (math.cos(a) * 3.75, math.sin(a) * 3.75, CORE_Z), MAT["bronze"], c, rot=(0, 0, a))
        # stacked detail plates
        for k in range(3):
            box("RE_Pillar_Plate_%02d_%d" % (i, k), (0.72, 0.10, 0.14),
                (x, y, 2.6 + k * 0.42), MAT["titanium"], c, rot=(0, 0, a), bev=0.008)

    # diagonal cross-bracing between adjacent pillars
    def strut(name, p1, p2, w=0.13, mat=None):
        p1, p2 = Vector(p1), Vector(p2)
        d = p2 - p1
        ob = box(name, (w, w, d.length), (p1 + p2) * 0.5, mat or MAT["gunmetal"], c, bev=0.006)
        align_z(ob, d)
        return ob

    for i in range(8):
        a0 = i * TAU / 8 + math.pi / 8
        a1 = (i + 1) * TAU / 8 + math.pi / 8
        lo0 = (math.cos(a0) * 4.58, math.sin(a0) * 4.58, 2.35)
        lo1 = (math.cos(a1) * 4.58, math.sin(a1) * 4.58, 5.35)
        hi0 = (math.cos(a0) * 4.58, math.sin(a0) * 4.58, 9.15)
        hi1 = (math.cos(a1) * 4.58, math.sin(a1) * 4.58, 10.55)
        strut("RE_Brace_Lower_%02d" % i, lo0, lo1)
        strut("RE_Brace_Upper_%02d" % i, hi0, hi1)


def build_chamber():
    c = C("STRUCTURAL_FRAME")
    cyl("RE_Chamber_Ring_Low", 2.95, 0.55, (0, 0, 5.78), MAT["steel"], c, verts=32)
    cyl("RE_Chamber_Ring_High", 2.95, 0.55, (0, 0, 9.45), MAT["steel"], c, verts=32)
    torus("RE_Chamber_Trim_Low", 2.95, 0.10, (0, 0, 6.08), MAT["copper"], c, mseg=40)
    torus("RE_Chamber_Trim_High", 2.95, 0.10, (0, 0, 9.15), MAT["copper"], c, mseg=40)
    for i in range(12):
        a = i * TAU / 12
        x, y = math.cos(a) * 2.92, math.sin(a) * 2.92
        box("RE_Chamber_Strut_%02d" % i, (0.17, 0.17, 3.6), (x, y, CORE_Z),
            MAT["gunmetal"], c, rot=(0, 0, a), bev=0.01)
        sphere("RE_Chamber_Bolt_%02d" % i, 0.09, (x, y, 9.3), MAT["titanium"], c, seg=8, rings=5)


def build_core():
    c = C("REACTOR_CORE")
    sphere("RE_Core_Nucleus", 0.78, (0, 0, CORE_Z), MAT["core"], c, seg=32, rings=20)
    sphere("RE_Core_Energy", 1.55, (0, 0, CORE_Z), MAT["electric"], c, seg=28, rings=16)
    sphere("RE_Core_Halo", 1.92, (0, 0, CORE_Z), MAT["halo"], c, seg=24, rings=14)
    sphere("RE_Core_Shell", 2.30, (0, 0, CORE_Z), MAT["glass"], c, seg=28, rings=16)

    # floating energy fragments inside the containment
    for i in range(18):
        a = RND.uniform(0, TAU)
        el = RND.uniform(-1.0, 1.0)
        rad = RND.uniform(1.75, 2.15)
        x = math.cos(a) * math.sqrt(1 - el * el) * rad
        y = math.sin(a) * math.sqrt(1 - el * el) * rad
        z = CORE_Z + el * rad
        s = RND.uniform(0.045, 0.115)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=s, location=(x, y, z))
        ob = _finish(bpy.context.object, "RE_Core_Shard_%02d" % i, MAT["cyan"], c)
        ob.rotation_euler = (RND.uniform(0, 3), RND.uniform(0, 3), RND.uniform(0, 3))

    # radial stabilisers from shell to chamber wall
    for i in range(8):
        a = i * TAU / 8
        box("RE_Core_Stabiliser_%02d" % i, (0.85, 0.10, 0.16),
            (math.cos(a) * 2.35, math.sin(a) * 2.35, CORE_Z + RND.uniform(-0.5, 0.5)),
            MAT["titanium"], c, rot=(0, 0, a), bev=0.008)

    # energy nozzles at the top and bottom of the core
    cyl("RE_Core_Nozzle_Top", 0.28, 0.9, (0, 0, CORE_Z + 2.1), MAT["bronze"], c, verts=16)
    cyl("RE_Core_Nozzle_Bot", 0.28, 0.9, (0, 0, CORE_Z - 2.1), MAT["bronze"], c, verts=16)
    torus("RE_Core_Nozzle_Glow_T", 0.30, 0.05, (0, 0, CORE_Z + 2.5), MAT["cyan"], c, mseg=24, nseg=6)


def build_containment_rings():
    c = C("CONTAINMENT_RINGS")
    specs = [
        ("A", 4.55, 0.17, 0, 0, 20, 1.35),
        ("B", 4.05, 0.14, 35, 0, 18, 0.0),
        ("C", 3.55, 0.12, 35, 60, 16, -1.15),
    ]
    for tag, major, minor, tx, tz, segs, dz in specs:
        rot = (math.radians(tx), 0, math.radians(tz))
        zc = CORE_Z + dz
        torus("RE_Ring_%s" % tag, major, minor, (0, 0, zc), MAT["steel"], c, rot=rot, mseg=64, nseg=10)
        torus("RE_Ring_%s_Glow" % tag, major, minor * 0.42, (0, 0, zc), MAT["cyan"], c, rot=rot, mseg=64, nseg=6)
        for p in ring_points(major, tx, tz, segs, z=zc):
            ob = box("RE_Ring_%s_Seg_%02d" % (tag, len(c.objects)),
                     (0.42, 0.30, 0.30), p, MAT["bronze"], c, bev=0.012)
            ob.rotation_euler = (math.radians(tx), 0, math.atan2(p.y, p.x) + math.pi / 2)
        for i in range(6):
            a = i * TAU / 6
            p = ring_points(major, tx, tz, 6, z=zc, phase=a)[0]
            sphere("RE_Ring_%s_Joint_%d" % (tag, i), 0.19, p, MAT["titanium"], c, seg=12, rings=8)


def build_upper():
    c = C("STRUCTURAL_FRAME")
    cyl("RE_Upper_Base", 3.35, 0.45, (0, 0, 10.85), MAT["gunmetal"], c, verts=32)
    cone("RE_Upper_Cone", 3.35, 1.95, 1.45, (0, 0, 11.8), MAT["steel"], c, verts=32)
    cyl("RE_Upper_Collar", 2.0, 0.35, (0, 0, 12.62), MAT["bronze"], c, verts=28)
    torus("RE_Upper_Trim", 3.3, 0.08, (0, 0, 10.65), MAT["copper"], c, mseg=40)

    for i in range(4):
        a = i * TAU / 4 + math.pi / 4
        x, y = math.cos(a) * 2.15, math.sin(a) * 2.15
        cyl("RE_Stack_%d" % i, 0.30, 3.0, (x, y, 14.1), MAT["gunmetal"], c, verts=16)
        cyl("RE_Stack_Cap_%d" % i, 0.36, 0.22, (x, y, 15.68), MAT["steel"], c, verts=16)
        torus("RE_Stack_Glow_%d" % i, 0.31, 0.045, (x, y, 13.4), MAT["cyan"], c, mseg=24, nseg=6)
        torus("RE_Stack_Ring_%d" % i, 0.33, 0.05, (x, y, 14.9), MAT["bronze"], c, mseg=24, nseg=6)

    for i in range(4):
        a = i * TAU / 4
        cone("RE_Spire_%d" % i, 0.11, 0.02, 3.1, (math.cos(a) * 1.15, math.sin(a) * 1.15, 14.4),
             MAT["titanium"], c, verts=10, bev=0)

    cyl("RE_Antenna_Mast", 0.045, 3.4, (0, 0, 15.0), MAT["titanium"], c, verts=8, bev=0)
    for k in range(3):
        torus("RE_Antenna_Dish_%d" % k, 0.42 - k * 0.10, 0.035, (0, 0, 15.9 + k * 0.55),
              MAT["steel"], c, mseg=20, nseg=5)
    sphere("RE_Antenna_Tip", 0.09, (0, 0, 16.75), MAT["amber"], c, seg=10, rings=6)

    # vents around the upper base
    for i in range(8):
        a = i * TAU / 8 + 0.19
        box("RE_Upper_Vent_%02d" % i, (0.42, 0.24, 0.52),
            (math.cos(a) * 3.2, math.sin(a) * 3.2, 10.85), MAT["gunmetal"], c, rot=(0, 0, a), bev=0.01)


def build_gears():
    c = C("GEAR_ASSEMBLIES")
    specs = [
        (16, 1.05, 0.20, 0.26, 0.30),
        (20, 1.35, 0.22, 0.30, 0.34),
        (14, 0.85, 0.18, 0.24, 0.26),
        (24, 1.55, 0.24, 0.32, 0.40),
        (18, 1.15, 0.20, 0.28, 0.32),
        (12, 0.72, 0.16, 0.22, 0.24),
        (22, 1.45, 0.22, 0.30, 0.36),
        (16, 0.95, 0.18, 0.26, 0.28),
    ]
    for i, (teeth, r, th, thick, bore) in enumerate(specs):
        a = i * TAU / 8 + math.pi / 8
        normal = Vector((math.cos(a), math.sin(a), 0))
        loc = Vector((math.cos(a) * 4.52, math.sin(a) * 4.52, 3.0 + (i % 4) * 0.95))
        gear("RE_Gear_%02d" % i, teeth, r, th, thick, bore, MAT["bronze"], c,
             loc, normal=normal, hub_mat=MAT["titanium"])
        # mounting bracket behind the gear
        b = box("RE_Gear_Bracket_%02d" % i, (0.3, 0.3, r * 1.5), loc - normal * (thick * 1.5 + 0.12),
                MAT["gunmetal"], c, bev=0.01)
        align_z(b, normal)
        cyl("RE_Gear_Shaft_%02d" % i, 0.10, thick * 2.0 + 0.3,
            loc - normal * 0.10, MAT["titanium"], c, verts=10)

    # one meshing pair at the base front
    base_z = 1.80
    p1 = Vector((4.45, -4.30, base_z))
    n1 = Vector((0.62, -0.79, 0)).normalized()
    g1 = gear("RE_Gear_Pair_A", 30, 1.42, 0.15, 0.30, 0.30, MAT["steel"], c, p1, normal=n1,
              hub_r=0.46, hub_h=0.8)
    d = (1.42 + 0.96) * 0.965
    p2 = p1 + n1.cross(Vector((0, 0, 1))).normalized() * d
    g2 = gear("RE_Gear_Pair_B", 20, 0.96, 0.13, 0.26, 0.22, MAT["bronze"], c, p2, normal=n1,
              hub_r=0.32, hub_h=0.7)
    # radial spokes on the big pair
    for g, rr in ((g1, 1.42), (g2, 0.96)):
        for k in range(6):
            ang = k * math.pi / 3
            spoke = box("RE_Spoke_%s_%d" % (g.name[-1], k), (rr * 0.85, 0.08, 0.11),
                        Vector(g.location) + Vector(n1) * 0.18, MAT["copper"], c, bev=0)
            align_z(spoke, n1)
            spoke.rotation_euler.rotate_axis("Z", ang)


def build_hydraulics():
    c = C("HYDRAULIC_SYSTEMS")
    for i in range(8):
        a = i * TAU / 8 + math.pi / 8
        for side in (-1, 1):
            ang = a + side * 0.22
            base = Vector((math.cos(ang) * 5.55, math.sin(ang) * 5.55, 1.45))
            top = Vector((math.cos(a) * 4.95, math.sin(a) * 4.95, 4.4))
            mid = (base + top) * 0.5
            direction = (top - base).normalized()
            length = (top - base).length
            cy = cyl("RE_Hyd_Cyl_%02d_%d" % (i, side), 0.17, length * 0.55, mid, MAT["gunmetal"], c, verts=14)
            align_z(cy, direction)
            rod = cyl("RE_Hyd_Rod_%02d_%d" % (i, side), 0.075, length * 0.62,
                      mid + direction * length * 0.30, MAT["titanium"], c, verts=10)
            align_z(rod, direction)
            sphere("RE_Hyd_Joint_%02d_%d" % (i, side), 0.16, top, MAT["bronze"], c, seg=12, rings=8)
            sphere("RE_Hyd_Foot_%02d_%d" % (i, side), 0.19, base, MAT["steel"], c, seg=12, rings=8)


def build_energy_network():
    c = C("ENERGY_NETWORK")
    # main ring conduit around the pedestal
    torus("RE_Conduit_Ring", 5.05, 0.075, (0, 0, 4.55), MAT["cyan"], c, mseg=64, nseg=8)
    torus("RE_Conduit_Ring_Mount", 5.05, 0.035, (0, 0, 4.75), MAT["bronze"], c, mseg=64, nseg=5)

    # four large curved feeds from base to chamber
    for i in range(4):
        a = i * TAU / 4 + 0.4
        p0 = (math.cos(a) * 6.05, math.sin(a) * 6.05, 1.25)
        p1 = (math.cos(a) * 6.15, math.sin(a) * 6.15, 3.4)
        p2 = (math.cos(a) * 4.35, math.sin(a) * 4.35, 5.9)
        p3 = (math.cos(a) * 3.15, math.sin(a) * 3.15, 6.4)
        pipe("RE_Feed_%d" % i, [p0, p1, p2, p3], 0.13, MAT["copper"], c)

    # glowing lines climbing the pillars
    for i in range(8):
        a = i * TAU / 8 + math.pi / 8 + 0.10
        cyl("RE_Energy_Line_%02d" % i, 0.030, 9.2,
            (math.cos(a) * 4.72, math.sin(a) * 4.72, 6.0), MAT["cyan"], c, verts=8, bev=0)

    # branching small pipes from the ring to the gear positions
    for i in range(8):
        a = i * TAU / 8 + math.pi / 8
        p0 = (math.cos(a) * 5.05, math.sin(a) * 5.05, 4.55)
        p1 = (math.cos(a) * 4.75, math.sin(a) * 4.75, 3.9)
        pipe("RE_Branch_%02d" % i, [p0, p1], 0.05, MAT["cyan"], c)

    # distribution nodes on the base rim
    for i in range(10):
        a = i * TAU / 10 + 0.31
        x, y = math.cos(a) * 6.15, math.sin(a) * 6.15
        cyl("RE_Node_%02d" % i, 0.20, 0.30, (x, y, 1.52), MAT["bronze"], c, verts=12)
        sphere("RE_Node_Glow_%02d" % i, 0.10, (x, y, 1.70), MAT["cyan"], c, seg=10, rings=6)

    # amber secondary conduits
    for i in range(6):
        a = i * TAU / 6 + 0.9
        p0 = (math.cos(a) * 5.9, math.sin(a) * 5.9, 2.05)
        p1 = (math.cos(a) * 5.2, math.sin(a) * 5.2, 3.1)
        pipe("RE_Amber_%02d" % i, [p0, p1], 0.055, MAT["amber"], c)


def build_details():
    c = C("INDUSTRIAL_BASE")
    # valves
    for i in range(6):
        a = i * TAU / 6 + 0.55
        x, y = math.cos(a) * 5.35, math.sin(a) * 5.35
        cyl("RE_Valve_%02d" % i, 0.22, 0.34, (x, y, 1.62), MAT["bronze"], c, verts=14)
        torus("RE_Valve_Wheel_%02d" % i, 0.30, 0.045, (x, y, 1.84), MAT["copper"], c, mseg=20, nseg=6)
        for k in range(3):
            box("RE_Valve_Spoke_%02d_%d" % (i, k), (0.55, 0.05, 0.035), (x, y, 1.84),
                MAT["copper"], c, rot=(0, 0, k * math.pi / 3), bev=0)

    # control panels
    for i in range(4):
        a = i * TAU / 4 + 0.22
        x, y = math.cos(a) * 6.35, math.sin(a) * 6.35
        ob = box("RE_Panel_%02d" % i, (0.85, 0.30, 1.05), (x, y, 2.35),
                 MAT["gunmetal"], c, rot=(math.radians(18), 0, a), bev=0.012)
        scr = box("RE_Panel_Screen_%02d" % i, (0.62, 0.05, 0.42),
                  (x - math.cos(a) * 0.10, y - math.sin(a) * 0.10, 2.55),
                  MAT["cyan"], c, rot=(math.radians(18), 0, a), bev=0)

    # bolted collar rings on the pillars
    for i in range(8):
        a = i * TAU / 8 + math.pi / 8
        for k in range(6):
            ang = k * TAU / 6
            cyl("RE_Bolt_%02d_%d" % (i, k), 0.045, 0.10,
                (math.cos(a) * PILLAR_R + math.cos(ang) * 0.22,
                 math.sin(a) * PILLAR_R + math.sin(ang) * 0.22, 2.35),
                MAT["titanium"], c, verts=6, bev=0)

    # ladders
    for i in range(2):
        a = math.pi * 0.25 + i * math.pi
        x, y = math.cos(a) * 6.55, math.sin(a) * 6.55
        for side in (-1, 1):
            cyl("RE_Ladder_Rail_%d_%d" % (i, side), 0.035, 2.9,
                (x + math.cos(a + math.pi / 2) * side * 0.24,
                 y + math.sin(a + math.pi / 2) * side * 0.24, 1.45),
                MAT["titanium"], c, verts=8, bev=0)
        for k in range(6):
            box("RE_Ladder_Rung_%d_%d" % (i, k), (0.06, 0.44, 0.04),
                (x, y, 0.35 + k * 0.45), MAT["titanium"], c, rot=(0, 0, a), bev=0)

    # hanging sign / warning plate
    plate = box("RE_Warning_Plate", (0.55, 0.06, 0.20), (5.15, -4.9, 1.58),
                MAT["amber"], c, rot=(0, 0, math.radians(-40)), bev=0.006)


def build_environment():
    c = C("ENVIRONMENT")
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
    floor = _finish(bpy.context.object, "RE_Floor", MAT["floor"], c)
    for i, r in enumerate((8.6, 11.5, 14.8)):
        torus("RE_Floor_Ring_%d" % i, r, 0.035, (0, 0, 0.012), MAT["steel"], c, mseg=96, nseg=5)

    # industrial silhouette blocks behind the subject
    blocks = [
        (-46, 40, 10.0, 12, 20, 10),
        (-60, 52, 9.0, 14, 16, 12),
        (-28, 58, 12.0, 18, 22, 12),
        (8, 62, 10.0, 16, 18, 10),
    ]
    for i, (x, y, w, dx, dz, dy) in enumerate(blocks):
        box("RE_BG_Block_%02d" % i, (w, dy, dz), (x, y, dz * 0.5),
            MAT["bg"], c, bev=0)
        # a few lit windows
        for k in range(3):
            box("RE_BG_Win_%02d_%d" % (i, k), (0.35, 0.05, 0.26),
                (x - w * 0.28 + k * 1.15, y - dy * 0.52, 2.2 + (k % 2) * 3.6),
                MAT["amber"] if k % 2 == 0 else MAT["cyan"], c, bev=0)

    # distant mechanical gears, suspended
    gear("RE_BG_Gear_A", 28, 5.0, 0.45, 0.7, 1.1, MAT["gunmetal"], c,
         (-30, 32, 16), normal=(0, 1, 0))
    gear("RE_BG_Gear_B", 20, 3.4, 0.40, 0.6, 0.9, MAT["gunmetal"], c,
         (16, 40, 19), normal=(0.3, 1, 0.1))


def build_lights():
    c = C("LIGHTING")

    def add(name, kind, energy, color, loc, target=None, size=8.0, radius=1.0):
        li = bpy.data.lights.new(name, kind)
        li.energy = energy
        li.color = color
        if kind == "AREA":
            li.size = size
        if kind == "POINT":
            li.shadow_soft_size = radius
        ob = bpy.data.objects.new(name, li)
        c.objects.link(ob)
        ob.location = loc
        if target:
            d = Vector(target) - Vector(loc)
            ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return ob

    add("RE_Key", "AREA", 26000, (1.0, 0.86, 0.72), (-16, -13, 18), (0, 0, 8.0), size=16)
    add("RE_Rim_Cyan", "AREA", 9000, (0.24, 0.62, 1.0), (12, 16, 13), (0, 0, 8.5), size=10)
    add("RE_Fill_Blue", "AREA", 3500, (0.30, 0.50, 1.0), (14, -14, 4.5), (0, 0, 6.0), size=12)
    add("RE_Amber_Accent", "POINT", 4200, (1.0, 0.45, 0.10), (-7.5, -5.5, 2.2), radius=1.4)
    add("RE_Amber_Kick", "POINT", 2400, (1.0, 0.52, 0.16), (-9.5, -1.5, 6.8), radius=2.2)
    add("RE_Core_Light", "POINT", 1100, (0.16, 0.78, 1.0), (0, 0, CORE_Z), radius=2.0)
    add("RE_Ground_Bounce", "AREA", 1200, (0.20, 0.32, 0.55), (0, 0, 0.6), (0, 0, 8), size=18)
    add("RE_Ambient_Card", "AREA", 2600, (0.22, 0.32, 0.55), (0, -34, 16), (0, 0, 9), size=40)

    w = bpy.data.worlds.new("RE_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.012, 0.017, 0.026, 1.0)
    bg.inputs[1].default_value = 1.0


def build_cameras():
    c = C("CAMERAS")

    def cam(name, loc, target, lens):
        cd = bpy.data.cameras.new(name)
        cd.lens = lens
        ob = bpy.data.objects.new(name, cd)
        c.objects.link(ob)
        ob.location = loc
        d = Vector(target) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return ob

    hero = cam("CAMERA_REACTOR_HERO", (11.5, -16.0, 3.2), (0, 0, 7.6), 34)
    cam("CAMERA_REACTOR_DETAIL", (7.4, -8.6, 3.1), (3.2, -3.2, 2.0), 70)
    bpy.context.scene.camera = hero


# ---------------------------------------------------------------- scene
def setup_scene():
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    try:
        sc.eevee.taa_render_samples = 64
    except Exception:
        pass
    try:
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = 100
    sc.render.fps = 24
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "AgX"
    except Exception:
        pass
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.view_settings.exposure = 0.0
    sc.render.filepath = os.path.join(BASE_DIR, "renders", "reactor_render.png")

    # compositor bloom - Blender 5.x: parameters are input sockets on a node group
    try:
        old = bpy.data.node_groups.get("RE_Compositing")
        if old:
            bpy.data.node_groups.remove(old)
        ng = bpy.data.node_groups.new("RE_Compositing", "CompositorNodeTree")
        sc.compositing_node_group = ng
        sc.use_nodes = True
        rl = ng.nodes.new("CompositorNodeRLayers")
        glare = ng.nodes.new("CompositorNodeGlare")
        for value in ("Bloom", "Fog Glow"):
            try:
                glare.inputs["Type"].default_value = value
                break
            except Exception:
                continue
        try:
            glare.inputs["Quality"].default_value = "High"
        except Exception:
            pass
        glare.inputs["Threshold"].default_value = 0.95
        glare.inputs["Strength"].default_value = 0.75
        glare.inputs["Size"].default_value = 0.45
        comp = ng.nodes.new("NodeGroupOutput")
        try:
            ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        except Exception:
            pass
        ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
        ng.links.new(glare.outputs["Image"], comp.inputs[0])
        print("COMPOSITOR OK")
    except Exception as e:
        print("COMPOSITOR SKIPPED:", repr(e))


def purge():
    # Dedicated project file: clear every object and collection, not only RE_ prefixed ones.
    # Cameras/lights use spec-mandated names (CAMERA_REACTOR_HERO) and would otherwise accumulate.
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for cu in list(bpy.data.curves):
        if cu.users == 0:
            bpy.data.curves.remove(cu)


def main():
    stages = [
        ("purge", purge),
        ("materials", build_materials),
        ("collections", build_collections),
        ("scene", setup_scene),
        ("base", build_base),
        ("pedestal", build_pedestal),
        ("pillars", build_pillars),
        ("chamber", build_chamber),
        ("core", build_core),
        ("rings", build_containment_rings),
        ("upper", build_upper),
        ("gears", build_gears),
        ("hydraulics", build_hydraulics),
        ("energy", build_energy_network),
        ("details", build_details),
        ("environment", build_environment),
        ("lights", build_lights),
        ("cameras", build_cameras),
    ]
    failed = []
    for name, fn in stages:
        try:
            fn()
            print("  stage %-14s OK  (objects=%d)" % (name, len(bpy.data.objects)))
        except Exception as e:
            failed.append((name, repr(e)))
            print("  stage %-14s FAIL %r" % (name, e))

    objs = [o for o in bpy.data.objects if o.name.startswith("RE_")]
    tris = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
    print("REACTOR BUILD | objects=%d | collections=%d | tris=%d | engine=%s" % (
        len(objs), len(ROOT.children), tris, bpy.context.scene.render.engine))
    print("VIEW %s | LOOK %s | EXPOSURE %s" % (
        bpy.context.scene.view_settings.view_transform,
        bpy.context.scene.view_settings.look,
        bpy.context.scene.view_settings.exposure))
    print("FAILED_STAGES", failed)


main()
