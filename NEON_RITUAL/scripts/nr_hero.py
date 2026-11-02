"""
NEON_RITUAL - hero chrome sculpture, orbital rings already in world,
custom 3D typography, event information, suspended sign rig.
"""

import bpy
import bmesh
import math
import os

from mathutils import Vector, Euler, Matrix

from nr_core import (
    COLL, MAT, box, cyl, sphere, ico, torus, curve_tube, join_objects,
    origin_to_world, apply_modifiers, text_obj, text_to_mesh, load_font,
    look_at, point_light, area_light,
)

TAU = math.tau


# ------------------------------------------------------------------ sculpture

def _bezier(name, points, radius, coll, cyclic=True, res=18, bevel_res=4):
    cu = bpy.data.curves.new(name + "_C", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.fill_mode = "FULL"
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    return ob


def _plane_loop(center, u, v, w, ru, rv, wobble=0.0, n=16):
    """A 3D ellipse in an arbitrary plane, with a small out-of-plane wobble."""
    cx, cy, cz = center
    ux, uy, uz = u
    vx, vy, vz = v
    wx, wy, wz = w
    pts = []
    for i in range(n):
        a = i * TAU / n
        ca, sa = math.cos(a), math.sin(a)
        off = math.sin(2 * a) * wobble
        pts.append((cx + ux * ca * ru + vx * sa * rv + wx * off,
                    cy + uy * ca * ru + vy * sa * rv + wy * off,
                    cz + uz * ca * ru + vz * sa * rv + wz * off))
    return pts


def _profile_curve(name, half_w, half_t, coll, seg=10):
    cu = bpy.data.curves.new(name + "_P", "CURVE")
    cu.dimensions = "2D"
    sp = cu.splines.new("POLY")
    sp.points.add(seg - 1)
    for i in range(seg):
        a = TAU * i / seg
        sp.points[i].co = (math.cos(a) * half_w, math.sin(a) * half_t, 0, 1)
    sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    ob.hide_render = True
    return ob


def _ribbon(name, points, width, thick, coll, cyclic=True, res=20):
    """A flat, wide ribbon rather than a round tube."""
    cu = bpy.data.curves.new(name + "_C", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_mode = "OBJECT"
    cu.bevel_object = _profile_curve(name + "_PROF", width * 0.5,
                                     thick * 0.5, coll)
    cu.twist_mode = "MINIMUM"
    cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    return ob


def build_sculpture():
    c = COLL["SCULPTURE"]
    curves = []

    # five large, open ribbon loops.  Thin tubes + big radii keep the negative
    # spaces open; no voxel remesh, so the silhouette stays a tangle, not a ball.
    curves.append(_bezier("SC_L1", _plane_loop(
        (0, 0, 0.5), (1, 0, 0), (0, 0, 1), (0, 1, 0),
        3.55, 3.95, 0.55, 18), 0.16, c))
    curves.append(_bezier("SC_L2", _plane_loop(
        (0, 0, 0.2), (0, 1, 0), (0, 0, 1), (1, 0, 0),
        3.00, 3.55, 0.65, 18), 0.14, c))
    curves.append(_bezier("SC_L3", _plane_loop(
        (0, 0, 1.65), (1, 0, 0), (0, 1, 0), (0, 0, 1),
        3.25, 2.65, 0.40, 18), 0.13, c))
    # wide liquid-metal ribbons: these carry the silhouette
    curves.append(_ribbon("SC_R1", _plane_loop(
        (0, 0, 0.4), (1, 0, 0), (0, 0, 1), (0, 1, 0),
        3.85, 4.15, 0.95, 22), 0.46, 0.10, c))
    curves.append(_ribbon("SC_R2", [
        (-4.8, -0.8, -3.2), (-5.2, 1.2, -1.0), (-3.2, 2.0, 1.6),
        (-0.6, 1.2, 3.6), (2.6, 0.0, 4.4), (4.8, -0.8, 3.4),
    ], 0.55, 0.12, c, cyclic=False))
    curves.append(_ribbon("SC_R3", _plane_loop(
        (0, 0, 0.8), (1, 0, 0), (0, 1, 0), (0, 0, 1),
        3.35, 2.75, 0.55, 20), 0.40, 0.09, c))

    # open tendrils that break the symmetry and connect the loops
    curves.append(_bezier("SC_T1", [
        (-3.4, -0.5, -3.9), (-4.2, 0.9, -2.1), (-2.5, 1.7, -0.1),
        (-0.5, 0.5, 2.3), (1.2, -0.7, 4.0),
    ], 0.10, c, cyclic=False))
    curves.append(_bezier("SC_T2", [
        (3.0, 0.9, -4.0), (4.3, -0.5, -1.7), (2.6, -1.9, 0.7),
        (0.9, -0.9, 3.0), (-0.4, 0.7, 4.2),
    ], 0.09, c, cyclic=False))
    curves.append(_bezier("SC_T3", [
        (-2.0, 1.6, -3.0), (-0.3, 2.8, -1.3), (1.6, 2.4, 0.9),
        (2.2, 0.9, 2.8), (1.1, -0.5, 3.9),
    ], 0.08, c, cyclic=False))

    # convert + join
    parts = []
    for cu in curves:
        ob = text_to_mesh(cu)
        parts.append(ob)
    body = join_objects(parts, "HERO_SCULPTURE_BODY")
    origin_to_world(body)

    # gentle smoothing only - never fuse the openings shut
    sm = body.modifiers.new("SMOOTH", "SMOOTH")
    sm.factor = 0.35
    sm.iterations = 2
    apply_modifiers(body)

    # organic micro-displacement
    tex = bpy.data.textures.new("SC_NOISE", type="CLOUDS")
    tex.noise_scale = 0.45
    tex.noise_depth = 3
    disp = body.modifiers.new("DISP", "DISPLACE")
    disp.texture = tex
    disp.strength = 0.020
    disp.mid_level = 0.5
    apply_modifiers(body)

    for p in body.data.polygons:
        p.use_smooth = True
    body.data.materials.append(MAT["chrome"])
    body.location = (0, 8, 14.8)
    body.name = "HERO_SCULPTURE"

    # red crystal core, parented so it moves with the sculpture
    core_mat = MAT["red_hot"].copy()
    core_mat.name = "CORE_CRYSTAL"
    beam_mat = MAT["red_hot"].copy()
    beam_mat.name = "HERO_BEAM_MAT"
    for m, strength in ((core_mat, 8.0), (beam_mat, 5.0)):
        m.use_fake_user = True
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
                n.inputs["Emission Strength"].default_value = strength
    crystal = ico("HERO_SCULPTURE_CORE", 0.62, (0, 8, 14.2), core_mat,
                  COLL["FRAGMENTS"], sub=2, scale=(0.9, 0.9, 2.2))
    crystal.parent = body
    crystal.matrix_parent_inverse = body.matrix_world.inverted()
    crystal.location = (0, 0, 0.2)

    core_light = point_light("HERO_CORE_LIGHT", (0, 8, 14.2), 45,
                             (1, 0.01, 0.01), 0.5, COLL["RED_NEON"])
    core_light.parent = body
    core_light.matrix_parent_inverse = body.matrix_world.inverted()
    core_light.location = (0, 0, 0.2)

    # floating chrome fragments
    frags = []
    specs = [(-4.6, 0.8, 10.4, 0.38, 1.2), (4.2, -1.2, 11.0, 0.30, 1.0),
             (-3.8, -2.8, 15.0, 0.26, 0.8), (4.6, 2.0, 16.0, 0.34, 1.1),
             (-1.8, 3.0, 17.8, 0.22, 0.7), (2.6, -3.0, 18.0, 0.20, 0.8)]
    for i, (x, y, z, r, h) in enumerate(specs):
        ob = ico("HERO_FRAG_%02d" % i, r, (x, y, z), MAT["chrome"],
                 COLL["FRAGMENTS"], sub=2, scale=(1.0, 0.7, h),
                 rot=(0.4 * i, 0.7 * i, 0.2 * i))
        frags.append(ob)

    # support beam + pedestal
    cyl("HERO_PEDESTAL", 1.35, 0.55, (0, 8, 1.925), MAT["gunmetal"],
        COLL["STAGE_PLATFORM"], verts=32)
    torus("HERO_PED_RED", 1.15, 0.05, (0, 8, 2.20), MAT["red"],
          COLL["STAGE_PLATFORM"], 48, 6)
    cyl("HERO_BEAM", 0.06, 8.10, (0, 8, 6.25), beam_mat,
        COLL["FRAGMENTS"], verts=10)

    # one rig for the floating fragments
    rig = bpy.data.objects.new("RIG_FRAGMENTS", None)
    rig.location = (0, 8, 14.4)
    COLL["CTRL"].objects.link(rig)
    for ob in frags:
        ob.parent = rig
        ob.matrix_parent_inverse = rig.matrix_world.inverted()

    body.data.calc_loop_triangles()
    print("SCULPTURE verts=%d tris=%d" % (len(body.data.vertices),
                                          len(body.data.loop_triangles)))


# ------------------------------------------------------------------ typography

def _star_xy(name, outer, inner, points):
    bm = bmesh.new()
    center = bm.verts.new((0, 0, 0))
    vs = []
    for i in range(points * 2):
        a = i * math.pi / points
        r = outer if i % 2 == 0 else inner
        vs.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, 0)))
    for i in range(len(vs)):
        bm.faces.new((center, vs[i], vs[(i + 1) % len(vs)]))
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def _spike(name, loc, length, radius, rot, mat, coll):
    return cyl(name, radius, length, loc, mat, coll, verts=8,
               rot=rot, r2=0.0)


def build_typography():
    c = COLL["LOGO"]
    font = load_font("Canterbury.ttf")
    chrome = MAT["chrome"]

    ne = text_obj("TYPO_NEON", "NEON", font, 1.02, (0, 1.52, 0),
                  (0, 0, 0), chrome, c, extrude=0.26, bevel=0.022,
                  offset=0.018)
    ri = text_obj("TYPO_RITUAL", "RITUAL", font, 1.42, (0, 0, 0),
                  (0, 0, 0), chrome, c, extrude=0.26, bevel=0.022,
                  offset=0.018)
    ne = text_to_mesh(ne)
    ri = text_to_mesh(ri)

    parts = [ri]
    # custom blade terminals
    parts.append(_spike("TYPO_SPK_L", (-3.55, -0.05, 0.0), 1.15, 0.075,
                        (0, math.radians(-90), 0), chrome, c))
    parts.append(_spike("TYPO_SPK_R", (3.55, -0.05, 0.0), 1.15, 0.075,
                        (0, math.radians(90), 0), chrome, c))
    parts.append(_spike("TYPO_SPK_TL", (-2.55, 1.72, 0.0), 0.85, 0.055,
                        (0, math.radians(-18), 0), chrome, c))
    parts.append(_spike("TYPO_SPK_TR", (2.55, 1.72, 0.0), 0.85, 0.055,
                        (0, math.radians(18), 0), chrome, c))
    parts.append(_spike("TYPO_SPK_BL", (-3.1, -0.42, 0.0), 0.75, 0.05,
                        (0, math.radians(-135), 0), chrome, c))
    parts.append(_spike("TYPO_SPK_BR", (3.1, -0.42, 0.0), 0.75, 0.05,
                        (0, math.radians(135), 0), chrome, c))
    # central sigil between the two lines, below the wordmark
    sig = _star_xy("TYPO_SIGIL", 0.34, 0.13, 8)
    sig.location = (0, -0.62, 0.08)
    sig.data.materials.append(chrome)
    c.objects.link(sig)
    parts.append(sig)

    logo = join_objects(parts, "TYPO_NEON_RITUAL")
    logo.location = (0, -2.0, 8.15)
    logo.rotation_euler = (math.radians(90), 0, 0)

    # The top line is kept separate so it can carry a slightly brighter
    # brushed-chrome material.  In the cathedral lighting a pure mirror
    # top line reflects the dark upper vault and disappears.
    top = MAT["chrome"].copy()
    top.name = "CHROME_TITLE_TOP"
    for n in top.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (0.95, 0.96, 1.0, 1)
            n.inputs["Metallic"].default_value = 0.95
            n.inputs["Roughness"].default_value = 0.18
            n.inputs["Emission Color"].default_value = (1.0, 0.92, 0.82, 1)
            n.inputs["Emission Strength"].default_value = 0.12
    top.use_fake_user = True
    MAT["chrome_top"] = top
    ne.data.materials.clear()
    ne.data.materials.append(top)
    ne.name = "TYPO_NEON"
    ne.location = (0.0, -2.0, 8.15 + 1.52)
    ne.rotation_euler = (math.radians(90), 0, 0)
    ne.scale = (1, 1, 1)
    for c in list(ne.users_collection):
        if c != COLL["LOGO"]:
            c.objects.unlink(ne)

    # suspension rods sit behind the sign, not through the letters
    for i, x in enumerate((-3.15, -1.05, 1.05, 3.15)):
        cyl("TYPO_ROD_%d" % i, 0.035, 20.0, (x, -1.45, 20.2),
            MAT["gunmetal"], COLL["DECOR"], verts=6)
        torus("TYPO_ROD_RING_%d" % i, 0.10, 0.025, (x, -1.45, 10.3),
              MAT["gunmetal"], COLL["DECOR"], 12, 5, (math.radians(90), 0, 0))

    # secondary line under the logo
    sec_mat = MAT["white_emit"].copy()
    sec_mat.name = "SECONDARY_EMIT"
    for n in sec_mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
            n.inputs["Emission Strength"].default_value = 0.0
    sec_mat.use_fake_user = True
    MAT["secondary_emit"] = sec_mat
    sec = text_obj("TYPO_SECONDARY", "UNDERGROUND ELECTRONIC EXPERIENCE",
                   load_font("LeagueSpartan-Bold.otf"), 0.20,
                   (0, -2.0, 6.75), (math.radians(90), 0, 0),
                   sec_mat, COLL["SECONDARY"], extrude=0.018,
                   bevel=0.004)
    sec.data.space_character = 1.25

    return logo, sec


def build_event_info():
    c = COLL["INFO"]
    font = load_font("LeagueSpartan-Bold.otf")
    info_mat = MAT["white_emit"].copy()
    info_mat.name = "INFO_EMIT"
    tag_mat = MAT["white_emit"].copy()
    tag_mat.name = "TAG_EMIT"
    for m in (info_mat, tag_mat):
        m.use_fake_user = True
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
                n.inputs["Emission Strength"].default_value = 0.0
    MAT["info_emit"] = info_mat
    MAT["tag_emit"] = tag_mat
    info = []
    lines = [
        ("SAT, 24 MAY 2025   ·   THE VOID", 0.27, 5.30),
        ("JAKARTA", 0.36, 4.85),
        ("TICKETS AT NEONRITUAL.COM", 0.26, 4.42),
    ]
    for i, (body, size, z) in enumerate(lines):
        ob = text_obj("INFO_LINE_%d" % i, body, font, size,
                      (0, -2.0, z), (math.radians(90), 0, 0),
                      info_mat, c, extrude=0.012, bevel=0.003)
        ob.data.space_character = 1.08
        info.append(ob)
    tag = text_obj("TAGLINE", "ENTER THE RITUAL.  FEEL THE BEAT.", font, 0.22,
                   (0, -2.0, 5.15), (math.radians(90), 0, 0),
                   tag_mat, COLL["SECONDARY"], extrude=0.010,
                   bevel=0.002)
    tag.data.space_character = 1.20
    # thin holographic frame
    frame_mat = MAT["red"].copy()
    frame_mat.name = "INFO_FRAME"
    for n in frame_mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
            n.inputs["Emission Strength"].default_value = 0.0
    frame_mat.use_fake_user = True
    MAT["info_frame"] = frame_mat
    for i, z in enumerate((5.62, 4.12)):
        box("INFO_FRAME_%d" % i, (4.8, 0.025, 0.018), (0, -2.02, z),
            frame_mat, c)
    for i, x in enumerate((-2.4, 2.4)):
        box("INFO_FRAME_V_%d" % i, (0.018, 0.025, 1.5), (x, -2.02, 4.87),
            frame_mat, c)
    return info, tag
