"""
NEON_RITUAL - architecture, stage, rings, props, chains, banners, atmosphere.
All dimensions in metres. Stage centre (0, 8, 0), camera enters from -Y.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Euler

from nr_core import (
    COLL, MAT, box, cyl, sphere, ico, torus, curve_tube, join_objects,
    origin_to_world, look_at, point_light, area_light,
)

TAU = math.tau
RNG = random.Random(20261102)


# ------------------------------------------------------------------ architecture

def build_floor():
    c = COLL["MAIN_HALL"]
    box("FLOOR_SLAB", (42, 68, 0.25), (0, 1, -0.125), MAT["floor"], c)
    # expansion seams, joined
    seams = []
    for x in range(-18, 19, 4):
        seams.append(box("SEAM_X_%d" % x, (0.035, 66, 0.012),
                         (x, 1, 0.006), MAT["black_metal"], c))
    for y in range(-30, 33, 4):
        seams.append(box("SEAM_Y_%d" % y, (40, 0.035, 0.012),
                         (0, y, 0.007), MAT["black_metal"], c))
    join_objects(seams, "FLOOR_SEAMS")

    # low kerb around the stage
    torus("STAGE_KERB", 8.35, 0.10, (0, 8, 0.10), MAT["gunmetal"], c, 96, 8)


def gothic_arch(name, span, spring_z, depth, y, mat, coll,
                thick=0.72, blocks=12, rot_z=0.0, loc=(0, 0, 0)):
    S = span
    c = 0.25 * S
    R = 0.75 * S
    th = math.acos(c / R)
    apex = R * math.sin(th)
    arc_len = R * th / blocks
    parts = []
    # left half: centre +c, angle pi -> pi-th
    for i in range(blocks):
        t = math.pi - th * (i + 0.5) / blocks
        px = c + R * math.cos(t)
        pz = spring_z + R * math.sin(t)
        ob = box("%s_L%d" % (name, i), (thick, depth, arc_len * 0.94),
                 (px, 0, pz), mat, coll, rot=(0, -t, 0))
        parts.append(ob)
    # right half: centre -c, angle 0 -> th
    for i in range(blocks):
        t = th * (i + 0.5) / blocks
        px = -c + R * math.cos(t)
        pz = spring_z + R * math.sin(t)
        ob = box("%s_R%d" % (name, i), (thick, depth, arc_len * 0.94),
                 (px, 0, pz), mat, coll, rot=(0, -t, 0))
        parts.append(ob)
    # keystone
    parts.append(box(name + "_KEY", (thick * 1.15, depth * 1.05, arc_len * 1.35),
                     (0, 0, spring_z + apex), mat, coll))
    ob = join_objects(parts, name)
    origin_to_world(ob)
    ob.location = (loc[0], y + loc[1], loc[2])
    ob.rotation_euler = (0, 0, rot_z)
    md = ob.modifiers.new("BEVEL", "BEVEL")
    md.width = 0.035
    md.segments = 1
    md.limit_method = "ANGLE"
    return ob


def build_pillars():
    c = COLL["PILLARS"]
    parts = []
    parts.append(cyl("PIL_SHAFT", 0.92, 14.0, (0, 0, 7.0), MAT["concrete"], c,
                     verts=20))
    parts.append(box("PIL_BASE", (2.7, 2.7, 1.25), (0, 0, 0.62),
                     MAT["concrete"], c))
    parts.append(box("PIL_BASE2", (2.15, 2.15, 0.5), (0, 0, 1.45),
                     MAT["concrete"], c))
    parts.append(box("PIL_CAP", (2.35, 2.35, 0.75), (0, 0, 13.75),
                     MAT["concrete"], c))
    parts.append(box("PIL_CAP2", (1.55, 1.55, 0.35), (0, 0, 14.25),
                     MAT["concrete"], c))
    for i, z in enumerate((4.2, 8.0, 11.8)):
        parts.append(cyl("PIL_BAND%d" % i, 1.02, 0.26, (0, 0, z),
                         MAT["gunmetal"], c, verts=20))
    parts.append(box("PIL_STRIP", (0.06, 0.18, 2.7), (0.94, 0, 5.1),
                     MAT["red"], c))
    parts.append(box("PIL_STRIP2", (0.06, 0.18, 2.2), (0.94, 0, 21.0),
                     MAT["red"], c))
    # upper colonette
    parts.append(cyl("PIL_UPPER", 0.34, 11.5, (0, 0, 20.0),
                     MAT["concrete"], c, verts=14))
    for i, z in enumerate((17.0, 22.5, 26.0)):
        parts.append(cyl("PIL_UR%d" % i, 0.44, 0.18, (0, 0, z),
                         MAT["gunmetal"], c, verts=14))
    master = join_objects(parts, "PILLAR_MASTER")
    origin_to_world(master)
    master.location = (-9, -28, 0)
    for side, x in ((-1, -9), (1, 9)):
        for j, y in enumerate((-28, -21, -14, -7, 0, 7, 14, 21)):
            if side == -1 and j == 0:
                ob = master
            else:
                ob = master.copy()
                ob.data = master.data
                bpy.context.scene.collection.objects.link(ob)
            ob.location = (x, y, 0)
            ob.rotation_euler = (0, 0, 0 if side == -1 else math.pi)
            ob.name = "PILLAR_%s_%02d" % ("W" if side == -1 else "E", j)
            for col in list(ob.users_collection):
                col.objects.unlink(ob)
            c.objects.link(ob)


def build_arches():
    c = COLL["ARCHITECTURE"]
    for i, y in enumerate((-24.5, -17.5, -10.5, -3.5, 3.5, 10.5, 17.5)):
        gothic_arch("ARCH_NAVE_%02d" % i, 18.0, 14.0, 1.15, y,
                    MAT["concrete"], c, thick=0.75, blocks=14)
    for side, x in ((-1, -14), (1, 14)):
        for i, y in enumerate((-21, -7, 7, 21)):
            gothic_arch("ARCH_AISLE_%s_%02d" % ("W" if side == -1 else "E", i),
                        9.5, 9.5, 0.9, 0,
                        MAT["concrete"], c, thick=0.55, blocks=10,
                        rot_z=math.pi * 0.5, loc=(x, y, 0))
    # south portal frame
    for side, x in ((-1, -4.0), (1, 4.0)):
        box("PORTAL_JAMB_%d" % side, (1.6, 3.0, 12.0), (x, -30, 6.0),
            MAT["concrete"], c, bevel=0.06)
    gothic_arch("PORTAL_ARCH", 8.0, 6.0, 1.2, -30.0, MAT["concrete"], c,
                thick=0.6, blocks=10)


def build_walls():
    c = COLL["ARCHITECTURE"]
    for side, x in ((-1, -19), (1, 19)):
        for i, y in enumerate((-28, -21, -14, -7, 0, 7, 14, 21)):
            box("WALL_%s_%02d" % ("W" if side == -1 else "E", i),
                (0.7, 6.6, 34.0), (x, y, 17.0), MAT["concrete"], c)
        # horizontal bands and vertical ribs
        for z in (2.2, 12.0, 18.0, 27.0, 32.0):
            box("WALLBAND_%s_%d" % ("W" if side == -1 else "E", int(z)),
                (0.9, 57.0, 0.25), (x, -2.0, z), MAT["gunmetal"], c)
        for i, y in enumerate((-28, -21, -14, -7, 0, 7, 14, 21)):
            box("WALLRIB_%s_%02d" % ("W" if side == -1 else "E", i),
                (1.0, 0.4, 34.0), (x - side * 0.55, y, 17.0),
                MAT["concrete_dark"], c)
        # buttresses
        for i, y in enumerate((-24.5, -10.5, 3.5, 17.5)):
            box("BUTTRESS_%s_%02d" % ("W" if side == -1 else "E", i),
                (1.4, 1.6, 22.0), (x - side * 1.0, y, 11.0),
                MAT["concrete"], c, bevel=0.05)
            box("BUTTRESS_CAP_%s_%02d" % ("W" if side == -1 else "E", i),
                (1.2, 1.2, 1.0), (x - side * 1.0, y, 22.5),
                MAT["concrete_dark"], c)

    # south wall, split around the 8 m portal
    for side, x in ((-1, -11.5), (1, 11.5)):
        box("SOUTH_WALL_%d" % side, (15.0, 1.2, 34.0), (x, -30, 17.0),
            MAT["concrete"], c, bevel=0.05)
    box("SOUTH_LINTEL", (10.0, 1.2, 22.0), (0, -30, 23.0),
        MAT["concrete"], c, bevel=0.05)
    box("SOUTH_TOPBAND", (38.0, 1.4, 0.6), (0, -30, 12.2),
        MAT["gunmetal"], c)

    # north wall
    box("NORTH_WALL", (40.0, 1.4, 34.0), (0, 32, 17.0),
        MAT["concrete"], c, bevel=0.05)

    # ceiling slab
    box("CEILING", (42, 68, 0.4), (0, 1, 34.2), MAT["concrete_dark"], c)


def build_trusses():
    c = COLL["BEAMS"]
    parts = []
    # one bay: 38 m span, top and bottom chords, verticals, diagonals
    parts.append(box("TR_CHORD_T", (38, 0.35, 0.35), (0, 0, 30.0),
                     MAT["gunmetal"], c))
    parts.append(box("TR_CHORD_B", (38, 0.35, 0.35), (0, 0, 28.6),
                     MAT["gunmetal"], c))
    for i in range(-18, 19, 3):
        parts.append(box("TR_V%d" % i, (0.16, 0.22, 1.4), (i, 0, 29.3),
                         MAT["gunmetal"], c))
        if i < 18:
            parts.append(box("TR_D%d" % i, (3.2, 0.2, 0.16),
                             (i + 1.5, 0, 29.3), MAT["gunmetal"], c,
                             rot=(0, math.radians(23), 0)))
    master = join_objects(parts, "TRUSS_MASTER")
    origin_to_world(master)
    master.location = (0, -28, 0)
    for j, y in enumerate((-28, -21, -14, -7, 0, 7, 14, 21, 28)):
        if j == 0:
            ob = master
        else:
            ob = master.copy()
            ob.data = master.data
            bpy.context.scene.collection.objects.link(ob)
        ob.location = (0, y, 0)
        ob.name = "TRUSS_%02d" % j
        for col in list(ob.users_collection):
            col.objects.unlink(ob)
        c.objects.link(ob)

    # longitudinal beams
    for x in (-18.5, -6, 6, 18.5):
        box("LONG_BEAM_%s" % x, (0.25, 64, 0.35), (x, 1, 29.3),
            MAT["gunmetal"], c)


def build_catwalks():
    c = COLL["ARCHITECTURE"]
    for side, x in ((-1, -13), (1, 13)):
        tag = "W" if side == -1 else "E"
        box("CATWALK_%s" % tag, (2.6, 56, 0.18), (x, -2, 12.0),
            MAT["gunmetal"], c)
        # grating slats
        slats = []
        for i in range(-27, 28):
            slats.append(box("SLAT_%s_%d" % (tag, i), (2.6, 0.05, 0.04),
                             (x, i, 12.12), MAT["black_metal"], c))
        join_objects(slats, "CATWALK_SLATS_" + tag)
        # railings
        rail = []
        for i in range(-27, 28, 2):
            rail.append(box("RAIL_POST_%s_%d" % (tag, i), (0.06, 0.06, 1.05),
                            (x + side * 1.2, i, 12.55), MAT["gunmetal"], c))
        for z in (12.5, 13.0):
            rail.append(box("RAIL_BAR_%s_%d" % (tag, int(z * 10)),
                            (0.05, 56, 0.05), (x + side * 1.2, -2, z),
                            MAT["gunmetal"], c))
        join_objects(rail, "CATWALK_RAIL_" + tag)
        # support columns
        for y in (-28, -14, 0, 14, 28):
            cyl("CAT_SUP_%s_%d" % (tag, y), 0.22, 12.0, (x, y, 6.0),
                MAT["gunmetal"], c, verts=10)
    # stairs from floor to catwalk at y=-20 and y=10
    for side, x in ((-1, -13), (1, 13)):
        for j, y0 in enumerate((-20, 10)):
            steps = []
            for i in range(12):
                h = (i + 1) * 1.0
                steps.append(box("CAT_STEP_%s_%d_%d" % (side, j, i),
                                 (1.6, 0.55, h),
                                 (x - side * 0.9, y0 + i * 0.55,
                                  h * 0.5), MAT["gunmetal"], c))
            join_objects(steps, "CAT_STAIRS_%s_%d" % (side, j))


def build_corridor():
    c = COLL["MAIN_HALL"]
    box("COR_FLOOR", (4.5, 18, 0.2), (0, -39, -0.1), MAT["floor"], c)
    box("COR_CEIL", (4.5, 18, 0.3), (0, -39, 6.15), MAT["concrete_dark"], c)
    for side, x in ((-1, -2.25), (1, 2.25)):
        box("COR_WALL_%d" % side, (0.4, 18, 6.0), (x, -39, 3.0),
            MAT["concrete"], c)
        box("COR_STRIP_%d" % side, (0.05, 17.4, 0.08), (x - side * 0.24, -39, 2.5),
            MAT["red"], c)
        box("COR_PIPE_%d" % side, (0.18, 18, 0.18), (x * 0.72, -39, 5.3),
            MAT["gunmetal"], c)
    for i, y in enumerate(range(-47, -29, 2)):
        box("COR_RIB_%d" % i, (4.9, 0.35, 0.45), (0, y, 6.0),
            MAT["concrete_dark"], c)
        box("COR_RIBV_%dL" % i, (0.35, 0.35, 6.0), (-2.1, y, 3.0),
            MAT["concrete_dark"], c)
        box("COR_RIBV_%dR" % i, (0.35, 0.35, 6.0), (2.1, y, 3.0),
            MAT["concrete_dark"], c)
    # pipes and cable bundles
    for x, z, r in ((-1.6, 5.55, 0.11), (1.6, 5.6, 0.08)):
        curve_tube("COR_CABLE_%s" % x,
                   [(x, -48, z), (x, -42, z - 0.05), (x, -36, z), (x, -30, z + 0.05)],
                   r, MAT["black_metal"], c, res=6, bevel_res=2)
    # far-end dark cap with one red practical
    box("COR_END", (4.6, 0.4, 6.2), (0, -48.2, 3.0), MAT["concrete_dark"], c)
    point_light("COR_END_LIGHT", (0, -47.2, 3.2), 180, (1, 0.02, 0.02), 0.5,
                COLL["RED_NEON"])
    area_light("COR_PORTAL_LIGHT", (0, -31.6, 4.4), (0, -39, 2.0),
               450, 4.0, (1, 0.95, 0.9), COLL["WHITE_SPOT"])


def build_apse():
    c = COLL["ARCHITECTURE"]
    box("APSE_PLATFORM", (24, 8, 0.6), (0, 28, 0.3), MAT["concrete"], c)
    for i, x in enumerate((-7, 0, 7)):
        for side in (-1, 1):
            box("APSE_JAMB_%d_%d" % (i, side), (0.65, 0.9, 4.4),
                (x + side * 2.75, 29.0, 2.8), MAT["concrete"], c)
        gothic_arch("APSE_ARCH_%d" % i, 5.5, 5.0, 0.8, 29.0,
                    MAT["concrete"], c, thick=0.45, blocks=9)
        box("APSE_NICHE_%d" % i, (4.2, 0.3, 8.0), (x, 31.4, 4.0),
            MAT["concrete_dark"], c)
        point_light("APSE_LIGHT_%d" % i, (x, 30.2, 4.0), 120,
                    (1, 0.01, 0.01), 0.4, COLL["RED_NEON"])
    # steps up to apse
    for i in range(4):
        box("APSE_STEP_%d" % i, (22, 1.0, 0.15),
            (0, 23.5 - i * 0.9, 0.075 + i * 0.15),
            MAT["concrete"], c)


def build_ruins():
    c = COLL["RUINS"]
    spots = [(-8.0, -24.0), (8.2, -18.0), (-8.5, -8.0), (8.6, 2.0),
             (-8.2, 15.0), (8.4, 19.0), (-15.0, -3.0), (15.2, 8.0)]
    for i, (x, y) in enumerate(spots):
        n = 4 + (i % 3)
        for k in range(n):
            sx = RNG.uniform(0.4, 1.6)
            sy = RNG.uniform(0.4, 1.5)
            sz = RNG.uniform(0.15, 0.65)
            px = x + RNG.uniform(-1.0, 1.0)
            py = y + RNG.uniform(-1.0, 1.0)
            ob = box("RUBBLE_%02d_%d" % (i, k), (sx, sy, sz),
                     (px, py, sz * 0.5), MAT["concrete_dark"], c,
                     rot=(0, 0, RNG.uniform(0, TAU)))
        # rebar
        for k in range(3):
            curve_tube("REBAR_%02d_%d" % (i, k),
                       [(x + RNG.uniform(-1, 1), y + RNG.uniform(-1, 1), 0.0),
                        (x + RNG.uniform(-1, 1), y + RNG.uniform(-1, 1),
                         RNG.uniform(0.6, 1.6))],
                       0.025, MAT["gunmetal"], c, res=4, bevel_res=1)


def build_banners():
    c = COLL["DECOR"]
    positions = [(-8.45, -17.5), (8.45, -17.5), (-8.45, 3.5),
                 (8.45, 3.5), (-8.45, 17.5), (8.45, 17.5)]
    for i, (x, y) in enumerate(positions):
        side = -1 if x < 0 else 1
        w, h = 2.6, 6.2
        bm = bmesh.new()
        nu, nv = 14, 26
        verts = []
        for iu in range(nu + 1):
            u = (iu / nu - 0.5) * w
            for iv in range(nv + 1):
                v = (iv / nv) * h
                fold = (math.sin(iu / nu * math.pi * 4.0) * 0.11 +
                        math.sin(iv / nv * math.pi * 3.0 + 1.0) * 0.045)
                verts.append(bm.verts.new((fold, u, -v)))
        bm.verts.ensure_lookup_table()
        for iu in range(nu):
            for iv in range(nv):
                a = verts[iu * (nv + 1) + iv]
                b = verts[(iu + 1) * (nv + 1) + iv]
                cc = verts[(iu + 1) * (nv + 1) + iv + 1]
                d = verts[iu * (nv + 1) + iv + 1]
                bm.faces.new((a, b, cc, d))
        me = bpy.data.meshes.new("BANNER_%d_M" % i)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new("BANNER_%02d" % i, me)
        ob.location = (x, y, 16.5)
        ob.rotation_euler = (0, 0, 0)
        me.materials.append(MAT["fabric"])
        c.objects.link(ob)
        md = ob.modifiers.new("SOLIDIFY", "SOLIDIFY")
        md.thickness = 0.035
        md.offset = 0
        # top pole
        cyl("BANNER_POLE_%02d" % i, 0.055, w + 0.4,
            (x, y, 16.55), MAT["gunmetal"], c, verts=8,
            rot=(math.radians(90), 0, 0))
        # sigil
        sig = _star_mesh("SIGIL_%02d" % i, 0.52, 0.20, 8)
        sig.location = (x + side * 0.11, y, 13.2)
        sig.rotation_euler = (0, 0, math.radians(90))
        sig.data.materials.append(MAT["sigil"])
        c.objects.link(sig)


def _star_mesh(name, outer, inner, points):
    bm = bmesh.new()
    center = bm.verts.new((0, 0, 0))
    verts = []
    for i in range(points * 2):
        a = i * math.pi / points
        r = outer if i % 2 == 0 else inner
        verts.append(bm.verts.new((math.cos(a) * r, 0, math.sin(a) * r)))
    for i in range(len(verts)):
        bm.faces.new((center, verts[i], verts[(i + 1) % len(verts)]))
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


# ------------------------------------------------------------------ stage

def build_stage():
    c = COLL["STAGE_PLATFORM"]
    for i, (r, h, z) in enumerate(((8.0, 0.80, 0.40), (6.0, 0.45, 1.025),
                                    (4.0, 0.40, 1.45))):
        cyl("STAGE_TIER_%d" % i, r, h, (0, 8, z), MAT["concrete_dark"], c,
            verts=64)
        torus("STAGE_TRIM_%d" % i, r - 0.04, 0.09, (0, 8, z + h * 0.5),
              MAT["gunmetal"], c, 80, 8)
        torus("STAGE_RED_%d" % i, r - 0.12, 0.04, (0, 8, z + h * 0.5 + 0.01),
              MAT["red"], c, 80, 6)
    # front stairs to the base tier: a real run in front of the stage
    for i in range(5):
        yc = -4.0 + i * 0.8 + 0.4
        zc = 0.08 + i * 0.16
        box("STAGE_STEP_%d" % i, (8.0, 0.8, 0.16),
            (0, yc, zc), MAT["concrete_dark"], COLL["STAIRCASE"])
        box("STAGE_STEP_RED_%d" % i, (7.9, 0.04, 0.025),
            (0, yc - 0.38, zc + 0.07), MAT["red"], COLL["STAIRCASE"])
    # understructure
    for i in range(8):
        a = i * TAU / 8.0
        x, y = math.cos(a) * 7.1, 8 + math.sin(a) * 7.1
        cyl("STAGE_SUP_%d" % i, 0.18, 0.8, (x, y, 0.4),
            MAT["gunmetal"], c, verts=8)
        box("STAGE_BEAM_%d" % i, (0.3, 3.0, 0.25),
            (x * 0.6, 8 + (y - 8) * 0.6, 0.25), MAT["gunmetal"], c,
            rot=(0, 0, a))
    # cable trays
    for side in (-1, 1):
        curve_tube("STAGE_CABLE_%d" % side,
                   [(side * 2.0, 1.0, 1.5), (side * 5.0, 6.0, 1.5),
                    (side * 6.0, 12.0, 1.5), (side * 4.0, 15.0, 1.5)],
                   0.06, MAT["black_metal"], c, res=6, bevel_res=1)


def build_dj_booth():
    c = COLL["DJ_BOOTH"]
    box("DJ_BASE", (4.8, 1.35, 1.05), (0, 10.2, 2.15),
        MAT["gunmetal"], c, bevel=0.03)
    box("DJ_FRONT", (4.9, 0.12, 0.9), (0, 9.48, 2.10),
        MAT["black_metal"], c)
    box("DJ_RED", (4.7, 0.05, 0.04), (0, 9.40, 2.55),
        MAT["red"], c)
    for side in (-1, 1):
        cyl("DJ_TT_%d" % side, 0.42, 0.08, (side * 1.2, 10.2, 2.71),
            MAT["black_metal"], c, verts=24)
        cyl("DJ_TT2_%d" % side, 0.22, 0.09, (side * 1.2, 10.2, 2.75),
            MAT["gunmetal"], c, verts=18)
    for side in (-1, 1):
        box("DJ_SCREEN_%d" % side, (0.75, 0.05, 0.48),
            (side * 1.75, 9.65, 2.82), MAT["led"], c,
            rot=(math.radians(-12), 0, 0))
    box("DJ_MONITOR", (0.9, 0.05, 0.55), (0, 9.55, 2.81),
        MAT["led"], c, rot=(math.radians(-12), 0, 0))
    # monitor wedges
    for side in (-1, 1):
        box("STAGE_WEDGE_%d" % side, (0.8, 0.55, 0.45),
            (side * 2.7, 2.0, 1.87), MAT["black_metal"], c,
            rot=(math.radians(-18), 0, 0))


def build_speakers():
    c = COLL["SPEAKERS"]
    for side in (-1, 1):
        x = side * 8.6
        y = 7.5
        box("SPK_PLINTH_%d" % side, (1.9, 1.5, 0.2), (x, y, 0.1),
            MAT["gunmetal"], c)
        for k in range(3):
            z = 0.75 + k * 1.28
            box("SPK_%d_%d" % (side, k), (1.7, 1.35, 1.2),
                (x, y, z), MAT["black_metal"], c, bevel=0.02)
            for j in range(2):
                cyl("SPK_CONE_%d_%d_%d" % (side, k, j), 0.36, 0.10,
                    (x, y - 0.70, z - 0.25 + j * 0.5),
                    MAT["gunmetal"], c, verts=20, rot=(math.radians(90), 0, 0))
            box("SPK_RED_%d_%d" % (side, k), (1.75, 0.03, 0.035),
                (x, y - 0.69, z + 0.58), MAT["red"], c)


def build_led():
    c = COLL["LED"]
    # side screens
    for side in (-1, 1):
        x = side * 8.2
        box("LED_FRAME_%d" % side, (3.8, 0.5, 5.2), (x, 14.5, 5.0),
            MAT["black_metal"], c)
        box("LED_SCREEN_%d" % side, (3.4, 0.06, 4.8), (x, 14.24, 5.0),
            MAT["led"], c)
        for z in (2.6, 7.4):
            box("LED_TRUSS_%d_%d" % (side, int(z * 10)), (4.2, 0.25, 0.25),
                (x, 14.5, z), MAT["gunmetal"], c)
        for dz in (-1.5, 1.5):
            box("LED_LEG_%d_%d" % (side, int(dz * 10)), (0.22, 0.22, 2.4),
                (x + dz, 14.5, 1.2), MAT["gunmetal"], c)
    # back screen
    box("LED_BACK_FRAME", (8.6, 0.5, 4.5), (0, 17.5, 5.5),
        MAT["black_metal"], c)
    box("LED_BACK", (8.0, 0.06, 4.0), (0, 17.24, 5.5), MAT["led"], c)
    for side in (-1, 1):
        box("LED_BACK_LEG_%d" % side, (0.3, 0.3, 3.3),
            (side * 3.8, 17.5, 1.65), MAT["gunmetal"], c)


def build_stage_truss():
    c = COLL["BEAMS"]
    for side in (-1, 1):
        for y in (2.0, 14.0):
            box("TOWER_%d_%d" % (side, int(y)), (0.35, 0.35, 11.0),
                (side * 6.5, y, 5.5), MAT["gunmetal"], c)
    # no front horizontal beam: it would cut a black bar across the title
    for side in (-1, 1):
        box("TRUSS_SIDE_%d" % side, (0.35, 12.0, 0.35),
            (side * 6.5, 8.0, 11.0), MAT["gunmetal"], c)
    # spotlights on the truss
    for i, x in enumerate((-5.0, -2.5, 0.0, 2.5, 5.0)):
        cyl("TRUSS_LAMP_%d" % i, 0.18, 0.45, (x, 2.0, 10.5),
            MAT["black_metal"], c, verts=12)
        sphere("TRUSS_BULB_%d" % i, 0.10, (x, 1.78, 10.45),
               MAT["white_emit"], c, seg=10, rings=6)


def build_rings():
    c = COLL["RINGS"]
    radii = (5.0, 6.5, 8.0)
    for i, r in enumerate(radii):
        parts = []
        parts.append(torus("RING_%d_BODY" % i, r, 0.34, (0, 0, 0),
                           MAT["gunmetal"], c, 72, 10))
        parts.append(torus("RING_%d_RED" % i, r - 0.30, 0.045, (0, 0, 0),
                           MAT["red"], c, 72, 6))
        # segmentation brackets
        for k in range(12):
            a = k * TAU / 12.0
            parts.append(box("RING_%d_BRK_%d" % (i, k), (0.55, 0.72, 0.85),
                             (math.cos(a) * r, math.sin(a) * r, 0),
                             MAT["black_metal"], c, rot=(0, 0, a)))
        ob = join_objects(parts, "ORBITAL_RING_%02d" % i)
        ob.location = (0, 4, 22)
        ob.rotation_euler = (math.radians(2.0 - i * 2.0), 0, 0)
    # support struts
    for k in range(4):
        a = k * TAU / 4.0 + math.pi / 4
        x, y = math.cos(a) * 8.2, 4 + math.sin(a) * 8.2
        curve_tube("RING_STRUT_%d" % k,
                   [(x, y, 30.0), (x * 0.72, 4 + (y - 4) * 0.72, 24.0),
                    (x * 0.62, 4 + (y - 4) * 0.62, 22.0)],
                   0.10, MAT["gunmetal"], c, res=4, bevel_res=2)


def build_chains():
    c = COLL["CHAINS"]
    specs = [(-16, -26, 28), (16, -23, 27), (-17, -10, 29), (17, -5, 26),
             (-16, 8, 28), (16, 12, 27), (-17, 22, 30), (17, 20, 29),
             (-5.5, -9.0, 20), (5.5, -9.0, 20), (-4.0, -14, 23), (4.0, -14, 23)]
    for i, (x, y, top) in enumerate(specs):
        bottom = 1.0 if top < 22 else 8.0
        n = max(8, int((top - bottom) / 0.55))
        parts = []
        for k in range(n):
            z = top - k * 0.55
            rot = (math.radians(90), 0, 0) if k % 2 == 0 else (0, 0, math.radians(90))
            parts.append(torus("CH_%d_L%d" % (i, k), 0.18, 0.055,
                               (x, y, z), MAT["gunmetal"], c, 16, 6, rot))
        join_objects(parts, "CHAIN_%02d" % i)


def build_props():
    c = COLL["MACHINERY"]
    # barrels
    for i, (x, y) in enumerate(((-15.5, -24), (-15.0, -22.6), (15.6, -20),
                                 (15.2, 18.5), (-15.4, 14), (14.8, -27))):
        cyl("BARREL_%02d" % i, 0.45, 1.2, (x, y, 0.6), MAT["gunmetal"], c,
            verts=16)
        for z in (0.25, 0.95):
            torus("BARREL_R_%02d_%d" % (i, int(z * 10)), 0.47, 0.045,
                  (x, y, z), MAT["black_metal"], c, 18, 5)
        box("BARREL_BAND_%02d" % i, (0.9, 0.9, 0.12), (x, y, 0.75),
            MAT["red"], c)
    # crates
    for i, (x, y, z, s) in enumerate(((-14.5, -18, 0.5, 1.0), (-14.3, -16.6, 0.5, 0.9),
                                       (15.0, 6.0, 0.5, 1.1), (14.6, 7.1, 0.45, 0.9),
                                       (-15.0, 21.0, 0.55, 1.0))):
        box("CRATE_%02d" % i, (s, s, s), (x, y, z), MAT["black_metal"], c,
            bevel=0.02)
        for ex in (-1, 1):
            for ey in (-1, 1):
                box("CRATE_EDGE_%02d_%d_%d" % (i, ex, ey), (0.06, 0.06, s),
                    (x + ex * s * 0.48, y + ey * s * 0.48, z),
                    MAT["gunmetal"], c)
    # pipes along side walls
    for side in (-1, 1):
        for k, z in enumerate((7.0, 8.0, 9.0)):
            pts = [(side * 18.4, -28, z), (side * 18.4, -10, z),
                   (side * 18.4, 8, z), (side * 18.4, 26, z)]
            curve_tube("PIPE_%d_%d" % (side, k), pts, 0.09 + k * 0.02,
                       MAT["gunmetal"], c, res=4, bevel_res=2)
            for y in (-24, -14, -4, 6, 16, 24):
                cyl("PIPE_FLANGE_%d_%d_%d" % (side, k, y), 0.16, 0.10,
                    (side * 18.4, y, z), MAT["black_metal"], c,
                    verts=10, rot=(math.radians(90), 0, 0))
    # fans
    for side, y in ((-1, -7), (1, 14)):
        x = side * 18.3
        cyl("FAN_HOUSING_%d" % side, 0.9, 0.25, (x, y, 5.0),
            MAT["gunmetal"], c, verts=24, rot=(0, math.radians(90), 0))
        for k in range(4):
            box("FAN_BLADE_%d_%d" % (side, k), (0.06, 0.75, 0.16),
                (x - side * 0.14, y, 5.0), MAT["black_metal"], c,
                rot=(math.radians(45 * k), 0, 0))
    # tanks
    for side, y in ((-1, 18), (1, 22)):
        x = side * 15.5
        cyl("TANK_%d" % side, 1.0, 2.6, (x, y, 1.3), MAT["gunmetal"], c,
            verts=20)
        sphere("TANK_DOME_%d" % side, 1.0, (x, y, 2.6), MAT["gunmetal"], c,
               seg=20, rings=8, scale=(1, 1, 0.45))
        for k in range(3):
            torus("TANK_R_%d_%d" % (side, k), 1.02, 0.035,
                  (x, y, 0.5 + k * 0.8), MAT["black_metal"], c, 24, 5)
    # generators
    for side in (-1, 1):
        x = side * 15.5
        box("GEN_%d" % side, (2.0, 1.2, 1.2), (x, -26, 0.6),
            MAT["gunmetal"], c, bevel=0.02)
        for k in range(2):
            cyl("GEN_CYL_%d_%d" % (side, k), 0.25, 1.0,
                (x + (k - 0.5) * 0.6, -26, 1.6), MAT["black_metal"], c,
                verts=14)
    # fences
    for side, y in ((-1, 23), (1, 24)):
        x = side * 16.5
        for k in range(5):
            cyl("FENCE_POST_%d_%d" % (side, k), 0.04, 2.0,
                (x, y - 2 + k, 1.0), MAT["gunmetal"], c, verts=6)
        for z in (0.6, 1.4):
            box("FENCE_BAR_%d_%d" % (side, int(z * 10)), (0.05, 4.2, 0.05),
                (x, y, z), MAT["gunmetal"], c)
    # security cameras
    for side, y in ((-1, -14), (1, 7)):
        x = side * 18.2
        box("SEC_BRACKET_%d" % side, (0.5, 0.15, 0.15), (x, y, 13.0),
            MAT["gunmetal"], c)
        cyl("SEC_BODY_%d" % side, 0.25, 0.6, (x - side * 0.35, y, 12.85),
            MAT["black_metal"], c, verts=12, rot=(0, math.radians(90), 0))
        cyl("SEC_LENS_%d" % side, 0.12, 0.06, (x - side * 0.68, y, 12.85),
            MAT["red"], c, verts=12, rot=(0, math.radians(90), 0))
    # control panels
    for side, y in ((-1, 12), (1, 2)):
        x = side * 16.8
        box("PANEL_%d" % side, (1.4, 0.5, 2.0), (x, y, 1.0),
            MAT["gunmetal"], c, bevel=0.02)
        box("PANEL_SCR_%d" % side, (1.0, 0.04, 0.6), (x, y - 0.27, 1.45),
            MAT["led"], c)
        for k in range(3):
            cyl("PANEL_KNOB_%d_%d" % (side, k), 0.07, 0.06,
                (x - 0.4 + k * 0.4, y - 0.28, 0.75), MAT["red"], c,
                verts=10, rot=(math.radians(90), 0, 0))
    # cable coils
    for i, (x, y) in enumerate(((-12.5, -12), (12.8, -2), (-12.0, 7))):
        for k in range(4):
            torus("COIL_%02d_%d" % (i, k), 0.65, 0.06, (x, y, 0.06 + k * 0.11),
                  MAT["black_metal"], c, 24, 5)
    # barriers
    for i, x in enumerate((-4.5, 4.5)):
        box("BARRIER_%02d" % i, (2.4, 0.5, 1.0), (x, 0.0, 0.5),
            MAT["concrete"], c, bevel=0.03)
        box("BARRIER_STRIPE_%02d" % i, (2.2, 0.52, 0.12), (x, 0.0, 0.6),
            MAT["red"], c)
    # light rods on pillars
    for side, x in ((-1, -8.65), (1, 8.65)):
        for y in (-21, -7, 7, 21):
            for z in (4.0, 20.0):
                cyl("LIGHT_ROD_%s_%d_%d" % (side, y, int(z)), 0.035, 2.7,
                    (x, y, z), MAT["red_hot"], COLL["RED_NEON"], verts=6)
                point_light("ROD_L_%s_%d_%d" % (side, y, int(z)),
                            (x, y, z), 35, (1, 0.01, 0.01), 0.25,
                            COLL["RED_NEON"])


# ------------------------------------------------------------------ atmosphere

def build_atmosphere():
    c = COLL["FOG"]
    # world volume
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("NEON_WORLD")
        bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (250, 120)
    bg.inputs["Color"].default_value = (0.010, 0.008, 0.009, 1)
    bg.inputs["Strength"].default_value = 0.35
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.location = (250, -180)
    vol.inputs["Color"].default_value = (0.10, 0.035, 0.040, 1)
    vol.inputs["Density"].default_value = 0.0022
    vol.inputs["Anisotropy"].default_value = 0.40
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])

    # ground fog volume
    _volume_box("GROUND_FOG", (38, 62, 2.4), (0, 1, 1.2), c, 0.008,
                (0.12, 0.04, 0.045), 6.0, animate=True)
    # smoke plumes
    for i, (x, y, z, s) in enumerate(((-6.0, 6.0, 3.0, 5.0),
                                       (6.0, 7.0, 3.5, 5.5),
                                       (0.0, 18.0, 2.5, 6.0))):
        _volume_box("SMOKE_%02d" % i, (s, s, s * 0.8), (x, y, z), COLL["SMOKE"],
                    0.032, (0.14, 0.055, 0.06), 3.0, animate=True)

    # dust field, one mesh, slow drift
    parts = []
    for i in range(180):
        x = RNG.uniform(-17, 17)
        y = RNG.uniform(-29, 29)
        z = RNG.uniform(0.5, 24)
        r = RNG.uniform(0.012, 0.03)
        parts.append(ico("DUST_%03d" % i, r, (x, y, z), MAT["dust"],
                         COLL["PARTICLES"], sub=1))
    join_objects(parts, "DUST_FIELD")


def _volume_box(name, size, loc, coll, density, color, noise_scale,
                animate=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    coll.objects.link(ob)
    m = bpy.data.materials.new(name + "_MAT")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.location = (250, 0)
    vol.inputs["Color"].default_value = (*color, 1)
    vol.inputs["Density"].default_value = density
    vol.inputs["Anisotropy"].default_value = 0.4
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.location = (-450, 0)
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = noise_scale
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.6
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-150, 0)
    mr.inputs["From Min"].default_value = 0.35
    mr.inputs["From Max"].default_value = 0.75
    mr.inputs["To Min"].default_value = 0.2
    mr.inputs["To Max"].default_value = 1.6
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    mult = nt.nodes.new("ShaderNodeMath")
    mult.location = (50, 0)
    mult.operation = "MULTIPLY"
    mult.inputs[1].default_value = density
    nt.links.new(mr.outputs["Result"], mult.inputs[0])
    nt.links.new(mult.outputs["Value"], vol.inputs["Density"])
    nt.links.new(vol.outputs["Volume"], out.inputs["Volume"])
    ob.data.materials.append(m)
    if animate:
        noise.inputs["W"].default_value = 0.0
        noise.inputs["W"].keyframe_insert("default_value", frame=1)
        noise.inputs["W"].default_value = 3.0
        noise.inputs["W"].keyframe_insert("default_value", frame=450)


def build_world():
    build_floor()
    build_walls()
    build_pillars()
    build_arches()
    build_trusses()
    build_catwalks()
    build_corridor()
    build_apse()
    build_ruins()
    build_banners()
    build_stage()
    build_dj_booth()
    build_speakers()
    build_led()
    build_stage_truss()
    build_rings()
    build_chains()
    build_props()
    build_atmosphere()
    print("WORLD BUILT objects=%d" % len(bpy.data.objects))
