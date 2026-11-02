"""
PARADISE AFTER DARK — architecture, stage, pool, canopy, festival set.
"""

import bpy
import bmesh
import math
import os

from mathutils import Vector, Euler

import tf_core as C

TAU = math.tau


# ------------------------------------------------------------------ pool outline

def _superellipse(a, rx, ry, cy, power=0.72):
    c, s = math.cos(a), math.sin(a)
    x = rx * math.copysign(abs(c) ** power, c)
    y = cy + ry * math.copysign(abs(s) ** power, s)
    return x, y


def pool_outline(n=96):
    """Long organic lagoon, 13.4 x 4.7 m, front edge at y=-6.8."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        x, y = _superellipse(a, 6.70, 2.35, -4.45, 0.72)
        x += 0.11 * math.sin(3.0 * a + 0.4)
        y += 0.06 * math.sin(2.0 * a + 0.9)
        pts.append((x, y))
    return pts


def deck_outline(n=96):
    """White stone deck around the pool and stage forecourt."""
    pts = []
    for i in range(n):
        a = TAU * i / n
        x, y = _superellipse(a, 8.35, 5.05, -2.10, 0.55)
        pts.append((x, y))
    return pts


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


# ------------------------------------------------------------------ ground

def _grid_faces(xs, ys, include):
    verts = []
    vmap = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            vmap[(i, j)] = len(verts)
            verts.append((x, y, 0.0))
    faces = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            cx = (xs[i] + xs[i + 1]) * 0.5
            cy = (ys[j] + ys[j + 1]) * 0.5
            if not include(cx, cy):
                continue
            faces.append((vmap[(i, j)], vmap[(i + 1, j)],
                          vmap[(i + 1, j + 1)], vmap[(i, j + 1)]))
    return verts, faces


def build_ground():
    coll = C.COLL["SETUP"]
    poly = pool_outline(96)
    # sand ground with a real hole for the pool
    step = 0.35
    xs = [(-20.0 + i * step) for i in range(int(40.0 / step) + 1)]
    ys = [(-18.0 + j * step) for j in range(int(30.0 / step) + 1)]
    verts, faces = _grid_faces(xs, ys,
                               lambda x, y: not point_in_poly(x, y, poly))
    C.mesh_obj("GROUND_SAND", verts, faces, C.MAT["sand"], coll,
               smooth=False)

    # white stone deck around the pool and under the stage
    deck = deck_outline(96)
    xs = [(-8.6 + i * 0.28) for i in range(int(17.2 / 0.28) + 1)]
    ys = [(-7.5 + j * 0.28) for j in range(int(10.7 / 0.28) + 1)]
    verts, faces = _grid_faces(
        xs, ys,
        lambda x, y: (point_in_poly(x, y, deck)
                      and not point_in_poly(x, y, poly)))
    ob = C.mesh_obj("COURT_DECK", verts, faces, C.MAT["stone"],
                    C.COLL["LANDSCAPE"], smooth=False)
    ob.location = (0, 0, 0.012)

    # deck edge kerb
    C.curve_tube("DECK_KERB", [(x, y, 0.075) for x, y in deck],
                 0.10, C.MAT["stone"], C.COLL["LANDSCAPE"], cyclic=True,
                 res=6, bevel_res=3)


# ------------------------------------------------------------------ pool & water

def build_pool():
    poly = pool_outline(96)
    wcoll = C.COLL["POOL"]
    water_z = -0.16
    floor_z = -0.95

    # water surface
    wverts = [(x, y, water_z) for x, y in poly]
    C.mesh_obj("POOL_WATER", wverts, [tuple(range(len(wverts)))],
               C.MAT["water"], wcoll, smooth=True)

    # pool floor, inset from the coping
    fverts = [(x * 0.955, -4.45 + (y + 4.45) * 0.940, floor_z)
              for x, y in poly]
    C.mesh_obj("POOL_FLOOR", fverts, [tuple(range(len(fverts)))],
               C.MAT["pool_floor"], wcoll, smooth=False)

    # one continuous wall mesh
    n = len(poly)
    wall_v = []
    for i in range(n):
        wall_v.append((poly[i][0], poly[i][1], water_z))
    for i in range(n):
        wall_v.append((fverts[i][0], fverts[i][1], floor_z))
    wall_f = []
    for i in range(n):
        j = (i + 1) % n
        wall_f.append((i, j, n + j, n + i))
    C.mesh_obj("POOL_WALL", wall_v, wall_f, C.MAT["stone"], wcoll,
               smooth=False)

    # shallow ledge just under the surface, catches light
    sverts = [(x * 0.92, -4.45 + (y + 4.45) * 0.90, -0.40)
              for x, y in poly]
    ledge_v = [(poly[i][0], poly[i][1], water_z) for i in range(n)]
    ledge_v += [(sverts[i][0], sverts[i][1], -0.40) for i in range(n)]
    ledge_f = []
    for i in range(n):
        j = (i + 1) % n
        ledge_f.append((i, j, n + j, n + i))
    C.mesh_obj("POOL_LEDGE", ledge_v, ledge_f, C.MAT["pool_floor"], wcoll,
               smooth=False)

    # rounded coping
    C.curve_tube("POOL_COPING", [(x, y, 0.02) for x, y in poly],
                 0.06, C.MAT["stone"], wcoll, cyclic=True, res=8,
                 bevel_res=4)

    # stepping stones: a curving path from the front deck to the stage
    stones = [(-3.55, -6.10, 0.52), (-2.35, -5.35, 0.58),
              (-1.05, -4.65, 0.54), (0.35, -4.05, 0.56),
              (1.75, -3.50, 0.50), (3.05, -3.05, 0.46)]
    for i, (x, y, r) in enumerate(stones):
        ob = C.cyl("STEP_STONE_%02d" % i, r, 0.11, (x, y, 0.015),
                   C.MAT["stone"], wcoll, verts=40)
        md = ob.modifiers.new("BEVEL", "BEVEL")
        md.width = 0.06
        md.segments = 4
        md.limit_method = "ANGLE"
        for p in ob.data.polygons:
            p.use_smooth = True

    # lily pads along the quiet back edge
    for i in range(10):
        a = C.RNG.uniform(0, TAU)
        rr = C.RNG.uniform(0.25, 0.80)
        x = math.cos(a) * 5.4 * rr
        y = -3.3 + math.sin(a) * 1.1 * rr
        r = C.RNG.uniform(0.18, 0.34)
        C.cyl("LILY_PAD_%02d" % i, r, 0.014, (x, y, water_z + 0.01),
              C.MAT["leaf_mid"], C.COLL["WATER"], verts=24)
        # notch
        C.box("LILY_NOTCH_%02d" % i, (r * 0.55, r * 0.16, 0.02),
              (x + r * 0.55, y, water_z + 0.012),
              C.MAT["water"], C.COLL["WATER"], rot=(0, 0, a))

    # lotus clusters
    for k in range(3):
        x, y = (-2.2 + k * 2.3, -3.1 + 0.5 * k)
        for i in range(6):
            a = i * TAU / 6
            C.sphere("LOTUS_%d_%d" % (k, i), 0.075,
                     (x + math.cos(a) * 0.09, y + math.sin(a) * 0.09,
                      water_z + 0.03),
                     C.MAT["flower_pink"] if i % 2 else C.MAT["flower_coral"],
                     C.COLL["WATER"], seg=8, rings=4, scale=(0.55, 0.30, 0.55))

    # waterfall: a stack of dark rocks with a white water sheet
    for i in range(9):
        bx = 6.25 + C.RNG.uniform(-1.05, 1.05)
        by = -1.95 + C.RNG.uniform(-0.45, 0.30)
        bz = C.RNG.uniform(0.28, 1.45)
        br = C.RNG.uniform(0.30, 0.62)
        C.ico("WF_BOULDER_%02d" % i, br, (bx, by, bz),
              C.MAT["rock"], C.COLL["ROCKS"], sub=2,
              scale=(1.25, 0.95, 0.85))
    # three falling streams read better than a flat sheet
    for i, dx in enumerate((-0.34, 0.0, 0.34)):
        x = 6.25 + dx
        pts = [(x, -2.28, 1.30),
               (x + 0.05, -2.38, 1.00),
               (x - 0.03, -2.47, 0.55),
               (x + 0.02, -2.52, 0.02),
               (x, -2.55, water_z)]
        C.curve_tube("WF_STREAM_%d" % i, pts, 0.055, C.MAT["foam"],
                     C.COLL["WATERFALL"], res=8, bevel_res=3)
    C.box("WF_BASIN", (1.55, 0.42, 0.10), (6.25, -2.60, 0.04),
          C.MAT["stone"], C.COLL["WATERFALL"], bevel=0.05, smooth=True)
    for i in range(10):
        C.sphere("WF_FOAM_%02d" % i, 0.10,
                 (6.25 + C.RNG.uniform(-0.95, 0.95),
                  -2.50 + C.RNG.uniform(-0.30, 0.08),
                  water_z + 0.03 + C.RNG.uniform(0, 0.08)),
                 C.MAT["foam"], C.COLL["WATERFALL"], seg=8, rings=4,
                 scale=(1.7, 0.9, 0.35))


# ------------------------------------------------------------------ planters

def build_planters():
    coll = C.COLL["PLANTERS"]
    beds = [(-8.4, -3.2, 4.4, 4.2), (8.4, -3.2, 4.4, 4.2),
            (-8.4, 4.4, 4.4, 4.4), (8.4, 4.4, 4.4, 4.4)]
    for i, (x, y, w, d) in enumerate(beds):
        C.box("PLANTER_WALL_%d" % i, (w, d, 0.55), (x, y, 0.275),
              C.MAT["white"], coll, bevel=0.12, smooth=True, bevel_seg=3)
        C.box("PLANTER_SOIL_%d" % i, (w - 0.35, d - 0.35, 0.10),
              (x, y, 0.56), C.MAT["soil"], coll)
        for k in range(3):
            ico_x = x + C.RNG.uniform(-w * 0.28, w * 0.28)
            ico_y = y + C.RNG.uniform(-d * 0.28, d * 0.28)
            C.ico("PLANTER_ROCK_%d_%d" % (i, k), C.RNG.uniform(0.2, 0.45),
                  (ico_x, ico_y, 0.62), C.MAT["lava"], C.COLL["ROCKS"],
                  sub=1, scale=(1.0, 0.8, 0.6))
    # low white garden kerb at the front corners
    for side in (-1, 1):
        C.curve_tube("GARDEN_KERB_%d" % side,
                     [(side * 6.0, -5.5, 0.12), (side * 6.3, -2.5, 0.12),
                      (side * 7.0, 0.5, 0.12), (side * 7.3, 3.5, 0.12)],
                     0.10, C.MAT["stone"], C.COLL["LANDSCAPE"], res=6)


# ------------------------------------------------------------------ pavilion

def petal_surface(name, loc, L, W, H, rot_z, tilt_y=0.0, mat=None,
                  coll=None):
    """A broad vertical petal facing the camera.

    Local X runs outward, local Z is the width/height of the leaf; the sheet
    therefore faces -Y and reads as a petal, not as a thin blade edge-on.
    """
    mat = mat or C.MAT["pearl"]
    coll = coll or C.COLL["PETALS"]

    def width(u):
        return W * (math.sin(math.pi * u) ** 0.62) * (1.0 - 0.12 * u)

    def f(u, v):
        w = width(u)
        x = L * u
        z = H * (u ** 1.36) + 0.5 * w * v
        y = 0.52 * (1.0 - 0.75 * v * v) * math.sin(math.pi * u)
        return (x, y, z)

    ob = C.parametric_surface(name, f, (0, 1), (-1, 1), 40, 26,
                              mat, coll, loc=loc, rot=(0, tilt_y, rot_z))
    md = ob.modifiers.new("SOLIDIFY", "SOLIDIFY")
    md.thickness = 0.085
    md.offset = 0
    md.use_even_offset = True
    for p in ob.data.polygons:
        p.use_smooth = True

    # large pearlescent glass insert in front of the white shell
    face_offset = -0.075 if math.cos(rot_z) >= 0 else 0.075

    def fp(u, v):
        uu = 0.12 + 0.80 * u
        vv = -0.70 + 1.40 * v
        w = width(uu)
        x = L * uu
        z = H * (uu ** 1.36) + 0.5 * w * vv
        y = 0.52 * (1.0 - 0.75 * vv * vv) * math.sin(math.pi * uu) + face_offset
        return (x, y, z)

    C.parametric_surface(name + "_GLASS", fp, (0, 1), (0, 1), 34, 20,
                         C.MAT["irid"], coll, loc=loc,
                         rot=(0, tilt_y, rot_z))

    # white structural ribs: centreline and both leaf edges
    def rib(points, nm, radius=0.10):
        C.curve_tube(nm, points, radius, C.MAT["white"], coll,
                     res=5, bevel_res=3, location=loc,
                     rotation=(0, tilt_y, rot_z))

    centre = []
    for i in range(19):
        u = i / 18
        centre.append((L * u, 0.52 * math.sin(math.pi * u),
                       H * (u ** 1.36)))
    rib(centre, name + "_RIB_C", 0.13)
    for s in (-1, 1):
        edge = []
        for i in range(19):
            u = i / 18
            w = width(u)
            edge.append((L * u, 0.0,
                         H * (u ** 1.36) + 0.5 * w * s))
        rib(edge, name + "_RIB_%d" % s, 0.155)
    # fine veins fanning from the base
    for s in (-1, 1):
        for vv in (0.28, 0.52, 0.76):
            vein = []
            for i in range(13):
                u = 0.10 + 0.84 * i / 12
                w = width(u)
                x = L * u
                z = H * (u ** 1.36) + 0.5 * w * vv * s
                y = 0.52 * (1.0 - 0.75 * (vv * s) ** 2) * math.sin(math.pi * u) + 0.02
                vein.append((x, y, z))
            C.curve_tube(name + "_VEIN_%d_%d" % (s, int(vv * 100)), vein,
                         0.017, C.MAT["white"], coll, res=4, bevel_res=1,
                         location=loc, rotation=(0, tilt_y, rot_z))
    # a white base band where the petal meets the architecture
    base = []
    for i in range(9):
        v = -1 + 2 * i / 8
        base.append((L * 0.06, 0.0,
                     H * (0.06 ** 1.36) + 0.5 * width(0.06) * v))
    C.curve_tube(name + "_BASE_BAND", base, 0.09, C.MAT["white"], coll,
                 res=4, bevel_res=2, location=loc,
                 rotation=(0, tilt_y, rot_z))
    return ob


def build_petals():
    # outer layer: broad leaves framing the dome, opening upward
    petal_surface("PETAL_UPPER_L", (-2.0, 5.6, 4.2), 6.9, 4.9, 5.0,
                  math.radians(181), math.radians(-3))
    petal_surface("PETAL_UPPER_R", (2.0, 5.6, 4.2), 6.9, 4.9, 5.0,
                  0.0, math.radians(3))
    # lower wings, flaring out beside the stage
    petal_surface("PETAL_LOWER_L", (-3.2, 4.9, 1.7), 5.7, 3.5, 3.3,
                  math.radians(176), math.radians(-6))
    petal_surface("PETAL_LOWER_R", (3.2, 4.9, 1.7), 5.7, 3.5, 3.3,
                  0.0, math.radians(6))
    # inner crown petals hugging the dome
    petal_surface("PETAL_CROWN_L", (-1.0, 6.1, 5.9), 3.9, 2.5, 2.7,
                  math.radians(207), math.radians(-9))
    petal_surface("PETAL_CROWN_R", (1.0, 6.1, 5.9), 3.9, 2.5, 2.7,
                  math.radians(-27), math.radians(9))
    # two small back petals peeking between the upper pair
    petal_surface("PETAL_BACK_L", (-0.7, 7.2, 6.4), 3.0, 1.9, 1.9,
                  math.radians(200), math.radians(-4))
    petal_surface("PETAL_BACK_R", (0.7, 7.2, 6.4), 3.0, 1.9, 1.9,
                  math.radians(-20), math.radians(4))


def build_dome():
    coll = C.COLL["DOME"]
    centre = (0.0, 6.5, 5.35)
    R = 3.25
    H = 4.75

    def f(u, v):
        a = TAU * u
        z = H * v
        r = R * (math.cos(v * math.pi * 0.5) ** 0.70)
        return (r * math.cos(a), r * math.sin(a), z)

    ob = C.parametric_surface("CENTRAL_DOME", f, (0, 1), (0, 0.985),
                              56, 24, C.MAT["pearl"], coll, loc=centre)
    md = ob.modifiers.new("SOLIDIFY", "SOLIDIFY")
    md.thickness = 0.12
    md.offset = 0
    for p in ob.data.polygons:
        p.use_smooth = True

    # pearlescent glass panels between the six ribs
    for k in range(6):
        u0 = TAU * k / 6 + 0.10
        u1 = TAU * (k + 1) / 6 - 0.10

        def fp(u, v, u0=u0, u1=u1):
            uu = u0 + (u1 - u0) * u
            vv = 0.12 + 0.74 * v
            r = R * (math.cos(vv * math.pi * 0.5) ** 0.70) * 1.045
            return (r * math.cos(uu), r * math.sin(uu), H * vv)

        C.parametric_surface("DOME_GLASS_%d" % k, fp, (0, 1), (0, 1),
                             12, 18, C.MAT["irid"], coll, loc=centre)
    # meridian ribs
    for k in range(6):
        a = TAU * k / 6.0
        pts = []
        for j in range(15):
            v = j / 14 * 0.985
            r = R * (math.cos(v * math.pi * 0.5) ** 0.70) * 1.048
            pts.append((r * math.cos(a), r * math.sin(a), H * v))
        C.curve_tube("DOME_RIB_%d" % k, pts, 0.115, C.MAT["white"],
                     coll, res=5, bevel_res=3, location=centre)
    # latitude bands
    for j, v in enumerate((0.26, 0.48, 0.68, 0.84)):
        r = R * (math.cos(v * math.pi * 0.5) ** 0.70) * 1.05
        C.torus("DOME_LAT_%d" % j, r, 0.055,
                (centre[0], centre[1], centre[2] + H * v),
                C.MAT["white"], coll, 64, 6)
    C.torus("DOME_BASE_RING", R * 1.06, 0.13,
            (centre[0], centre[1], centre[2]), C.MAT["white"], coll, 64, 8)
    C.cyl("DOME_FINIAL", 0.14, 0.62, (0, 6.5, 10.05), C.MAT["white"],
          coll, verts=12, r2=0.045)
    C.sphere("DOME_BALL", 0.14, (0, 6.5, 10.42), C.MAT["neon"], coll,
             seg=12, rings=8)


def build_arch():
    coll = C.COLL["ARCH"]
    pts = []
    for i in range(41):
        t = math.pi * i / 40
        x = 4.45 * math.cos(t)
        z = 6.15 * (math.sin(t) ** 0.82)
        pts.append((x, 0.0, z))
    C.curve_tube("STAGE_ARCH", pts, 0.43, C.MAT["white"], coll,
                 res=8, bevel_res=5, location=(0, 3.85, 0))
    # inner soft neon line
    pts2 = []
    for i in range(41):
        t = math.pi * i / 40
        x = 4.02 * math.cos(t)
        z = 5.65 * (math.sin(t) ** 0.82)
        pts2.append((x, 0.0, z))
    C.curve_tube("STAGE_ARCH_NEON", pts2, 0.035, C.MAT["neon"], coll,
                 res=6, bevel_res=2, location=(0, 3.38, 0))
    # side cheeks connecting the arch to the balconies
    for side in (-1, 1):
        C.box("ARCH_CHEEK_%d" % side, (0.65, 3.0, 3.8),
              (side * 4.35, 5.0, 1.9), C.MAT["white"], coll,
              bevel=0.12, smooth=True, bevel_seg=3)


def build_canopy():
    """Festoon lights and hanging vines frame the top; the sky stays open."""
    coll = C.COLL["CANOPY"]
    # two long catenary strings across the forecourt
    for j, (y0, z0, sag) in enumerate(((-5.6, 8.0, 0.55),
                                       (-2.8, 8.4, 0.65))):
        pts = []
        for i in range(31):
            t = i / 30
            x = -9.6 + 19.2 * t
            z = z0 - sag * 4.0 * t * (1.0 - t)
            pts.append((x, y0, z))
        C.curve_tube("FESTOON_WIRE_%d" % j, pts, 0.010,
                     C.MAT["dark_metal"], coll, res=6, bevel_res=1)
        for i in range(1, 30, 2):
            p = pts[i]
            C.sphere("FESTOON_BULB_%d_%02d" % (j, i), 0.055,
                     (p[0], p[1], p[2] - 0.07), C.MAT["white_emit"],
                     C.COLL["PRACTICALS"], seg=8, rings=5)

    # hanging vine curtains at the two upper corners
    for side in (-1, 1):
        for k in range(3):
            x = side * (7.6 + k * 0.45)
            y = -4.6 + k * 0.55
            z = 8.2 - 0.15 * k
            pts = [(x, y, z),
                   (x + side * 0.10, y + 0.08, z - 0.75),
                   (x - side * 0.04, y + 0.02, z - 1.55),
                   (x - side * 0.16, y - 0.04, z - 2.30)]
            C.curve_tube("HANG_VINE_%d_%d" % (side, k), pts, 0.022,
                         C.MAT["leaf_deep"], C.COLL["PLANTS"], res=6,
                         bevel_res=2)
            for j, t in enumerate((0.22, 0.40, 0.58, 0.76, 0.92)):
                C.sphere("HANG_LEAF_%d_%d_%d" % (side, k, j), 0.15,
                         (x - side * 0.10 * t, y, z - 2.30 * t),
                         C.MAT["leaf_mid"], C.COLL["PLANTS"], seg=8,
                         rings=4, scale=(0.3, 1.0, 1.5),
                         rot=(0, math.radians(30), 0))


def build_balconies():
    coll = C.COLL["BALCONIES"]
    for side in (-1, 1):
        x = side * 5.3
        C.box("BALCONY_%d" % side, (3.4, 2.7, 0.25), (x, 5.0, 3.55),
              C.MAT["white"], coll, bevel=0.25, smooth=True, bevel_seg=4)
        # slim railing posts + top rail along the outer edge
        for k in range(7):
            t = k / 6.0
            px = x + side * (1.60 - 0.08 * math.sin(t * math.pi))
            py = 3.75 + 2.5 * t
            C.cyl("BAL_RAIL_POST_%d_%d" % (side, k), 0.028, 0.92,
                  (px, py, 4.12), C.MAT["white"], coll, verts=8)
        C.curve_tube("BAL_RAIL_%d" % side,
                     [(x + side * 1.60, 3.75, 4.58),
                      (x + side * 1.60, 5.0, 4.58),
                      (x + side * 1.60, 6.25, 4.58)],
                     0.042, C.MAT["white"], coll, res=5, bevel_res=2)
        # glass balustrade panels, subtle turquoise
        for k in range(3):
            C.box("BAL_GLASS_%d_%d" % (side, k), (0.035, 0.78, 0.72),
                  (x + side * 1.60, 4.05 + k * 0.82, 4.16),
                  C.MAT["turquoise_glass"], coll, bevel=0.01, smooth=True)
        # 12 shallow steps from the forecourt to the balcony
        for k in range(12):
            z = 0.14 + k * 0.295
            y = 1.30 + k * 0.31
            C.box("BAL_STEP_%d_%d" % (side, k), (1.55, 0.34, 0.295),
                  (side * 6.15, y, z), C.MAT["white"], coll,
                  bevel=0.035, smooth=True)
        # slim side stringer
        C.box("BAL_STRINGER_%d" % side, (0.10, 3.9, 0.38),
              (side * 6.95, 3.05, 1.72), C.MAT["white"], coll,
              rot=(math.radians(43.5), 0, 0), bevel=0.04, smooth=True)
        # checkered white stone base under the stairs
        C.box("BAL_BASE_%d" % side, (1.7, 4.2, 0.10),
              (side * 6.15, 3.05, 0.05), C.MAT["stone"], coll,
              bevel=0.02, smooth=True)


def build_stage():
    coll = C.COLL["STAGE_PLATFORM"]
    C.box("STAGE_BASE", (7.0, 3.5, 0.60), (0, 4.2, 0.30),
          C.MAT["white"], coll, bevel=0.22, smooth=True, bevel_seg=4)
    # turquoise edge strip
    C.box("STAGE_EDGE_NEON", (7.1, 0.06, 0.05), (0, 2.42, 0.56),
          C.MAT["neon"], coll)
    for side in (-1, 1):
        C.box("STAGE_EDGE_NEON_%d" % side, (0.06, 3.5, 0.05),
              (side * 3.5, 4.2, 0.56), C.MAT["neon"], coll)
    # front steps
    for k in range(3):
        C.box("STAGE_STEP_%d" % k, (6.5 - k * 0.2, 0.42, 0.18),
              (0, 2.35 - k * 0.34, 0.09 + k * 0.18),
              C.MAT["white"], C.COLL["STAGE_PLATFORM"], bevel=0.05,
              smooth=True)

    # DJ booth
    d = C.COLL["DJ"]
    C.box("DJ_BASE", (2.8, 1.0, 0.95), (0, 4.75, 1.06),
          C.MAT["white"], d, bevel=0.18, smooth=True, bevel_seg=3)
    C.box("DJ_TOP", (2.9, 1.05, 0.08), (0, 4.75, 1.55),
          C.MAT["dark_metal"], d, bevel=0.04, smooth=True)
    for side in (-1, 1):
        C.cyl("DJ_TT_%d" % side, 0.28, 0.05, (side * 0.65, 4.72, 1.61),
              C.MAT["dark_metal"], d, verts=24)
        C.box("DJ_SCREEN_%d" % side, (0.55, 0.04, 0.34),
              (side * 0.95, 4.25, 1.72), C.MAT["led"], d,
              rot=(math.radians(-15), 0, 0))
    C.box("DJ_LED", (2.5, 0.04, 0.04), (0, 4.22, 1.32), C.MAT["neon"], d)

    # LED screen + frame
    l = C.COLL["LED"]
    C.box("LED_BACK", (6.05, 0.18, 3.20), (0, 6.35, 2.80),
          C.MAT["dark_metal"], l)
    C.box("LED_SCREEN", (5.65, 0.06, 2.82), (0, 6.24, 2.80),
          C.MAT["led"], l)
    for side in (-1, 1):
        C.box("LED_FRAME_V_%d" % side, (0.18, 0.32, 3.35),
              (side * 2.95, 6.28, 2.80), C.MAT["white"], l,
              bevel=0.05, smooth=True)
    C.box("LED_FRAME_T", (6.10, 0.32, 0.18), (0, 6.28, 4.46),
          C.MAT["white"], l, bevel=0.05, smooth=True)
    C.box("LED_FRAME_B", (6.10, 0.32, 0.18), (0, 6.28, 1.14),
          C.MAT["white"], l, bevel=0.05, smooth=True)
    # soft turquoise glow washing the stage
    ld = bpy.data.lights.new("LED_WASH_D", "AREA")
    ld.energy = 120.0
    ld.shape = "RECTANGLE"
    ld.size = 4.8
    ld.size_y = 2.2
    ld.color = (0.15, 1.0, 0.86)
    lo = bpy.data.objects.new("LED_WASH", ld)
    lo.location = (0, 5.1, 2.6)
    lo.rotation_euler = (math.radians(-90), 0, 0)
    C.COLL["STAGE_LIGHTS"].objects.link(lo)

    # speakers
    s = C.COLL["SPEAKERS"]
    for side in (-1, 1):
        for k in range(3):
            z = 0.95 + k * 0.92
            C.box("SPEAKER_%d_%d" % (side, k), (1.15, 0.90, 0.86),
                  (side * 3.2, 5.2, z), C.MAT["white"], s,
                  bevel=0.10, smooth=True, bevel_seg=3)
            for j in range(2):
                C.cyl("SPK_DRIVER_%d_%d_%d" % (side, k, j), 0.25, 0.06,
                      (side * 3.2, 4.73, z - 0.20 + j * 0.42),
                      C.MAT["dark_metal"], s, verts=20,
                      rot=(math.radians(90), 0, 0))
            C.box("SPK_NEON_%d_%d" % (side, k), (1.17, 0.04, 0.035),
                  (side * 3.2, 4.71, z + 0.40), C.MAT["neon"], s)
    # stage monitor wedges
    for side in (-1, 1):
        C.box("MONITOR_%d" % side, (0.8, 0.55, 0.38),
              (side * 1.5, 3.0, 0.78), C.MAT["white"], s,
              rot=(math.radians(-20), 0, 0), bevel=0.06, smooth=True)

    # arch fixtures, kept low so they never cross the sign
    for k, x in enumerate((-3.1, -2.0, -0.9, 0.9, 2.0, 3.1)):
        z = 4.55 + 0.10 * math.cos(x)
        C.cyl("STAGE_LAMP_%d" % k, 0.10, 0.28,
              (x, 3.55, z), C.MAT["dark_metal"],
              C.COLL["STAGE_LIGHTS"], verts=12, rot=(math.radians(90), 0, 0))
        C.sphere("STAGE_LAMP_GLOW_%d" % k, 0.065,
                 (x, 3.39, z), C.MAT["white_emit"],
                 C.COLL["STAGE_LIGHTS"], seg=8, rings=4)


def build_arch_sign():
    # slim dark plaque in front of the arch, with 3D brand type
    C.box("ARCH_SIGN_PANEL", (5.05, 0.10, 0.60), (0, 2.98, 5.55),
          C.MAT["sign_panel"], C.COLL["ARCH"], bevel=0.06, smooth=True)
    C.box("ARCH_SIGN_NEON", (5.45, 0.03, 0.025), (0, 2.86, 5.23),
          C.MAT["neon"], C.COLL["ARCH"])
    for side in (-1, 1):
        C.cyl("SIGN_STANDOFF_%d" % side, 0.035, 0.62,
              (side * 2.20, 3.28, 5.55), C.MAT["dark_metal"],
              C.COLL["ARCH"], verts=8, rot=(math.radians(90), 0, 0))
    C.text_mesh("ARCH_SIGN_TEXT", "PARADISE AFTER DARK",
                "LeagueSpartan-Bold.otf", 0.335,
                (0, 2.865, 5.60), (math.radians(90), 0, 0),
                C.MAT["white"], C.COLL["SIGNAGE"], extrude=0.025,
                bevel=0.005, spacing=1.04)
    C.text_mesh("ARCH_SIGN_SUB", "ELECTRONIC MUSIC FESTIVAL",
                "LeagueSpartan-Bold.otf", 0.112,
                (0, 2.855, 5.35), (math.radians(90), 0, 0),
                C.MAT["neon"], C.COLL["SIGNAGE"], extrude=0.012,
                bevel=0.003, spacing=1.26)


def build_backdrop():
    # green ground continues behind the pavilion so the world edge is hidden
    C.box("BACK_GROUND", (80, 40, 0.20), (0, 28.0, -0.10),
          C.MAT["leaf_deep"], C.COLL["LANDSCAPE"])
    # near berm under the background palms
    for i, (x, y, r, h) in enumerate(((-15, 18, 8, 2.6), (0, 21, 11, 3.4),
                                       (15, 18, 8, 2.6))):
        C.ico("BACK_MOUND_%d" % i, r, (x, y, 0.0), C.MAT["berm"],
              C.COLL["LANDSCAPE"], sub=2, scale=(1.0, 0.55, h / r))
    # hazy distant ridge for depth
    for i, (x, y, r, h) in enumerate(((-24, 34, 16, 9), (2, 38, 22, 12),
                                       (26, 33, 15, 8))):
        C.ico("FAR_RIDGE_%d" % i, r, (x, y, -0.5), C.MAT["haze"],
              C.COLL["LANDSCAPE"], sub=2, scale=(1.15, 0.55, h / r))
    # low jungle hedge closes the gap between the palms and the hill
    for i, x in enumerate(range(-15, 17, 3)):
        C.ico("JUNGLE_HEDGE_%d" % i, 2.6, (x, 13.2, 0.55),
              C.MAT["leaf_deep"], C.COLL["LANDSCAPE"], sub=2,
              scale=(1.25, 0.70, 0.85))
        C.ico("JUNGLE_HEDGE_B_%d" % i, 1.9, (x + 1.2, 15.0, 0.40),
              C.MAT["berm"], C.COLL["LANDSCAPE"], sub=2,
              scale=(1.25, 0.65, 0.80))
    # dark recess behind the LED so the stage does not look see-through
    C.box("STAGE_RECESS", (8.6, 1.2, 6.2), (0, 7.15, 3.1),
          C.MAT["dark_metal"], C.COLL["ARCH"])
    # two white curved wing walls behind the balconies
    for side in (-1, 1):
        def f(u, v):
            a = -0.6 + 1.2 * u
            z = 6.6 * v
            return (side * (4.9 + 3.3 * math.cos(a)),
                    7.4 + 1.7 * math.sin(a), z)
        ob = C.parametric_surface("BACK_WING_%d" % side, f, (0, 1), (0, 1),
                                  18, 16, C.MAT["white"], C.COLL["ARCH"])
        md = ob.modifiers.new("SOLIDIFY", "SOLIDIFY")
        md.thickness = 0.22
        md.offset = 0
        for p in ob.data.polygons:
            p.use_smooth = True


def build_decor():
    d = C.COLL["DECOR"]
    # vines spilling over the balcony edges
    for side in (-1, 1):
        for k in range(3):
            x = side * (4.15 + 0.16 * k)
            y = 4.15 + 0.75 * k
            z = 3.42
            pts = [(x, y, z),
                   (x + side * 0.08, y + 0.04, z - 0.55),
                   (x - side * 0.04, y - 0.02, z - 1.15),
                   (x - side * 0.12, y - 0.06, z - 1.70)]
            C.curve_tube("BAL_VINE_%d_%d" % (side, k), pts, 0.020,
                         C.MAT["leaf_deep"], C.COLL["PLANTS"], res=6,
                         bevel_res=2)
            for j, t in enumerate((0.35, 0.60, 0.85)):
                C.sphere("BAL_VINE_LEAF_%d_%d_%d" % (side, k, j), 0.14,
                         (x, y, z - 1.70 * t), C.MAT["leaf_mid"],
                         C.COLL["PLANTS"], seg=8, rings=4,
                         scale=(0.30, 1.0, 1.4), rot=(0, math.radians(30), 0))

    # floating lanterns on the lagoon
    for i in range(10):
        a = C.RNG.uniform(0, TAU)
        rr = C.RNG.uniform(0.2, 0.78)
        x = math.cos(a) * 5.5 * rr
        y = -3.1 + math.sin(a) * 1.25 * rr
        C.sphere("LANTERN_%02d" % i, 0.075, (x, y, -0.02),
                 C.MAT["lantern"], C.COLL["WATER"], seg=10, rings=6,
                 scale=(1.0, 1.0, 1.25))

    # no portal on the hero side; the planting carries the right edge


def build_all():
    build_ground()
    build_pool()
    build_planters()
    build_petals()
    build_dome()
    build_arch()
    build_canopy()
    build_balconies()
    build_stage()
    build_arch_sign()
    build_backdrop()
    build_decor()
    print("ARCH BUILD objects=%d" % len(bpy.data.objects))
