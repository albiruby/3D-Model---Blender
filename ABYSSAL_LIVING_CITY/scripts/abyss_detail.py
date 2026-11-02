"""
abyss_detail.py : environmental storytelling props.

The city had architecture and life but no evidence of use.  These are the objects
that say a place is occupied: cargo waiting to move, crates stacked by a door,
bollards along a quay, planters where a pavement is too wide, a market stall that
has not been packed away.

Placement is authored where the ground is known (street pavements, quay edge) and
solver-assisted where it is not.
"""

import bpy
import math
import random

DETAIL = {}


def _d_m(name, parts, bevel=0.005):
    ob = make_master(name, parts, bevel=bevel, weighted=True)
    DETAIL[name] = ob
    return ob


def prop_free(x, y, r=0.6, slack=1.1):
    """Free for a prop: buildings may be hugged, they just may not be entered."""
    for ox, oy, orr in OCC:
        if math.hypot(x - ox, y - oy) < max(0.0, orr - slack) + r:
            return False
    return True


def _crate_stack(seed=0):
    rng = random.Random(seed + 1)
    parts = []
    for i in range(4):
        s = rng.uniform(0.42, 0.62)
        x = rng.uniform(-0.25, 0.25)
        y = rng.uniform(-0.25, 0.25)
        z = 0.0 if i < 3 else s
        parts.append(box("DS_C%d" % i, (s, s * 0.9, s),
                         (x, y, z + s * 0.5),
                         MAT["wood_lt"] if i % 2 else MAT["wood"], C("WORK")))
        parts.append(box("DS_S%d" % i, (s * 1.02, 0.05, s * 0.12),
                         (x, y - s * 0.45, z + s * 0.5), MAT["steel"],
                         C("WORK")))
    return _d_m("DET_CRATES", parts)


def _barrels(seed=0):
    rng = random.Random(seed + 2)
    parts = []
    for i in range(3):
        a = i * TAU / 3.0
        r = rng.uniform(0.26, 0.32)
        h = rng.uniform(0.78, 0.96)
        px, py = math.cos(a) * 0.34, math.sin(a) * 0.34
        parts.append(cyl("DB_B%d" % i, r, h, (px, py, h * 0.5),
                         MAT["paint_safe"] if i % 2 else MAT["alu"], C("WORK"),
                         verts=12))
        for k in (-1, 1):
            parts.append(torus("DB_R%d%d" % (i, k), r * 1.03, 0.03,
                               (px, py, h * 0.5 + k * h * 0.30),
                               MAT["steel"], C("WORK"), mseg=12, nseg=4))
    return _d_m("DET_BARRELS", parts)


def _bollard(seed=0):
    parts = []
    parts.append(cyl("DBO_B", 0.20, 0.16, (0, 0, 0.08), MAT["concrete"],
                     C("WORK"), verts=10))
    parts.append(cyl("DBO_P", 0.09, 0.72, (0, 0, 0.44), MAT["paint_safe"],
                     C("WORK"), verts=8, r2=0.07))
    parts.append(sphere("DBO_T", 0.11, (0, 0, 0.82), MAT["paint_safe"],
                        C("WORK"), seg=8, rings=5))
    parts.append(torus("DBO_R", 0.10, 0.022, (0, 0, 0.62), MAT["emit_shop"],
                       C("WORK"), mseg=12, nseg=3))
    return _d_m("DET_BOLLARD", parts)


def _planter(seed=0):
    parts = []
    parts.append(cyl("DP_B", 0.62, 0.46, (0, 0, 0.23), MAT["concrete"],
                     C("WORK"), verts=12))
    parts.append(cyl("DP_S", 0.54, 0.08, (0, 0, 0.46), MAT["sand_dk"],
                     C("WORK"), verts=12))
    for i in range(4):
        a = i * TAU / 4.0 + 0.4
        parts.append(ico("DP_L%d" % i, 0.34,
                         (math.cos(a) * 0.20, math.sin(a) * 0.20, 0.72),
                         MAT["plant"] if i % 2 else MAT["plant_dk"], C("WORK"),
                         sub=1, scale=(0.85, 0.85, 1.5)))
    parts.append(sphere("DP_G", 0.06, (0.1, -0.1, 0.92), MAT["emit_green"],
                        C("WORK"), seg=6, rings=4))
    return _d_m("DET_PLANTER", parts)


def _stall(seed=0):
    parts = []
    parts.append(box("DST_T", (2.0, 1.1, 0.08), (0, 0, 0.86), MAT["wood_lt"],
                     C("WORK")))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("DST_L%d%d" % (sx, sy), 0.05, 0.86,
                             (sx * 0.86, sy * 0.44, 0.43), MAT["steel_lt"],
                             C("WORK"), verts=5))
    parts.append(box("DST_AW", (2.3, 1.4, 0.06), (0, 0, 1.86),
                     MAT["fabric_red"], C("WORK")))
    for sx in (-1, 1):
        parts.append(cyl("DST_P%d" % sx, 0.04, 1.0, (sx * 0.95, 0.55, 1.36),
                         MAT["steel_lt"], C("WORK"), verts=5))
    for i in range(5):
        parts.append(box("DST_G%d" % i, (0.20, 0.16, 0.12),
                         (-0.72 + i * 0.36, 0.10, 0.96),
                         MAT["coral_orange"] if i % 2 else MAT["coral_lime"],
                         C("WORK")))
    parts.append(box("DST_S", (1.0, 0.05, 0.22), (0, -0.56, 1.60),
                     MAT["emit_shop"], C("WORK")))
    return _d_m("DET_STALL", parts)


def build_detailing(seed=1212):
    for fn in (_crate_stack, _barrels, _bollard, _planter, _stall):
        fn()
    rng = random.Random(seed)
    n = 0

    def put(name, x, y, rot=None, z=None, s=1.0, coll="PROPS"):
        nonlocal n
        if z is None and not prop_free(x, y, 0.7):
            return False
        place(name, x, y, rot=rng.uniform(0, TAU) if rot is None else rot,
              s=s, coll=coll, z=z, tag="detail")
        n += 1
        return True

    # --- high street: stalls at the east end, planters along both pavements
    put("DET_STALL", 1.6, -19.9, rot=0.0, s=0.95)
    put("DET_STALL", 1.9, -25.3, rot=math.pi, s=0.95)
    for i in range(5):
        x = -13.0 + i * 3.4
        put("DET_PLANTER", x, -19.2, s=0.9)
        put("DET_PLANTER", x, -26.0, s=0.9)
    put("DET_CRATES", -14.2, -20.4, s=0.85)
    put("DET_BARRELS", 4.4, -20.3, s=0.85)

    # --- quay: bollards along the edge, cargo waiting to be loaded
    qz = seabed_h(-7.0, -34.0) + 1.10
    for i in range(8):
        x = -18.0 + i * 3.1
        put("DET_BOLLARD", x, -31.2, rot=0.0, z=qz)
    for (x, y) in ((-14.6, -31.9), (-12.9, -32.4), (2.2, -31.9),
                   (-4.4, -31.6)):
        put("DET_CRATES", x, y, z=qz, s=0.9)
    put("DET_BARRELS", 5.2, -32.3, z=qz, s=0.9)

    # --- industrial apron
    for (x, y) in ((15.0, -29.4), (16.6, -30.2), (13.6, -28.6)):
        put("DET_CRATES", x, y, s=1.0)
    put("DET_BARRELS", 18.2, -30.4, s=1.0)

    # --- plaza ring: planters at the radial gaps
    for i in range(8):
        a = i * TAU / 8.0 + 0.30
        put("DET_PLANTER", math.cos(a) * 16.4, math.sin(a) * 16.4, s=1.05)

    # --- research and resort aprons
    for (x, y) in ((29.0, -4.0), (27.4, -2.2), (31.0, 0.6)):
        put("DET_CRATES", x, y, s=0.9)
    put("DET_PLANTER", 12.5, 18.0, s=1.0)
    put("DET_PLANTER", 19.5, 16.0, s=1.0)

    # --- a few loose props around the residential lanes
    for i in range(6):
        put("DET_BARRELS", -34.0 + rng.uniform(-6, 6),
            4.0 + rng.uniform(-6, 6), s=0.85)

    print("DETAIL %d masters, %d placed" % (len(DETAIL), n))
    return n
