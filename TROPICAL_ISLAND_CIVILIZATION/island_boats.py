"""
island_boats.py : hulls with sheer, transom, deck, gunwale, cabins and gear.
"""

import bpy
import bmesh
import math
from mathutils import Vector


def _hull_rings(length, beam, draft, freeboard, n=16):
    """Returns (side_rings, deck_rows) - a real hull: pointed bow, transom stern,
    sheer that rises forward, flared topsides."""
    side_rings, deck_rows = [], []
    for i in range(n):
        t = i / (n - 1.0)          # 0 = stern, 1 = bow
        # plan view: full beam amidships, transom at 62 %, knife bow
        if t < 0.30:
            wf = 0.62 + 0.38 * (t / 0.30)
        else:
            wf = math.sin(math.pi * min(1.0, (t - 0.02) / 1.02)) ** 0.55
        w = max(0.012, beam * 0.5 * wf)
        # sheer line rises toward the bow
        h = freeboard * (0.82 + 0.34 * t * t + 0.10 * math.sin(math.pi * t))
        # draft: deepest amidships, shallower at bow
        d = max(0.03, draft * (math.sin(math.pi * t) ** 0.42))
        x = -length * 0.5 + length * t
        ring = [
            (x, 0.0, -d * 1.02),                    # keel
            (x, -w * 0.55, -d * 0.62),              # port bilge
            (x, -w * 1.00, h * 0.18),               # port chine
            (x, -w * 0.99, h * 0.62),               # port topside
            (x, -w * 0.93, h),                      # port gunwale
            (x, 0.0, h * 0.965),                    # deck centre (slight camber)
            (x, w * 0.93, h),                       # starboard gunwale
            (x, w * 0.99, h * 0.62),
            (x, w * 1.00, h * 0.18),
            (x, w * 0.55, -d * 0.62),
        ]
        side_rings.append(ring)
        deck_rows.append((x, w, h))
    return side_rings, deck_rows


def boat_master(name, length=5.4, beam=1.9, draft=0.50, freeboard=0.62,
                cabin=False, colour=None, seed=0, mast=False, open_deck=True):
    coll = C("WORK")
    hull_m = colour or MAT["paint_w"]
    parts = []
    rings, deck_rows = _hull_rings(length, beam, draft, freeboard)
    # strip the top cap: loft() closes the last ring, so build sides then deck
    hull = loft(name + "_hull", rings, hull_m, coll, close_start=True, close_end=True)
    parts.append(hull)

    # deck planks (thin strips for texture at close range); the hull skin already
    # carries the cambered deck so no separate deck surface is needed
    for i in range(5):
        t = 0.18 + i * 0.16
        idx = int(t * (len(deck_rows) - 1))
        x, w, h = deck_rows[idx]
        parts.append(box(name + "_pl%d" % i, (length * 0.10, w * 1.7, 0.018),
                         (x, 0, h + 0.012), MAT["wood_dark"], coll))
    # gunwale rim + rub rail
    for sgn in (-1, 1):
        pts = [(x, sgn * w * 0.95, h + 0.02) for (x, w, h) in deck_rows]
        parts.append(loft_path(name + "_gw%d" % sgn, pts, [0.045] * len(pts),
                               MAT["wood_dark"], coll, sides=5))

    if cabin:
        cz = freeboard * 0.86
        cw, cd, ch = length * 0.30, beam * 0.60, 0.95
        cx = -length * 0.04
        parts.append(box(name + "_cab", (cw, cd, ch), (cx, 0, cz + ch * 0.5), hull_m, coll))
        parts.append(box(name + "_cabroof", (cw * 1.16, cd * 1.14, 0.08),
                         (cx, 0, cz + ch + 0.04), MAT["paint_w"], coll))
        # wheelhouse glazing: 3 front panes + 2 side panes
        for k in (-1, 0, 1):
            parts.append(box(name + "_cf%d" % k, (0.05, cd * 0.24, ch * 0.42),
                             (cx + cw * 0.5 + 0.01, k * cd * 0.26, cz + ch * 0.62),
                             MAT["glass_dark"], coll))
        for sgn in (-1, 1):
            for k in (-1, 1):
                parts.append(box(name + "_cs%d%d" % (sgn, k), (cw * 0.26, 0.05, ch * 0.40),
                                 (cx + k * cw * 0.24, sgn * (cd * 0.5 + 0.01),
                                  cz + ch * 0.62), MAT["glass_dark"], coll))
            parts.append(box(name + "_cb%d" % sgn, (cw * 0.22, 0.05, ch * 0.46),
                             (cx - cw * 0.34, sgn * (cd * 0.5 + 0.01), cz + ch * 0.52),
                             MAT["glass_dark"], coll))
        parts.append(box(name + "_cabdoor", (0.05, cd * 0.22, ch * 0.72),
                         (cx + cw * 0.5 + 0.02, -cd * 0.30, cz + ch * 0.42),
                         MAT["wood_dark"], coll))
        # wheel + console
        parts.append(cyl(name + "_wheel", 0.10, 0.04, (cx + cw * 0.30, 0, cz + 0.62),
                         MAT["metal_dark"], coll, rot=(0, math.radians(90), 0), verts=10))
        parts.append(box(name + "_console", (0.30, 0.55, 0.40),
                         (cx + cw * 0.26, 0, cz + 0.42), MAT["metal_dark"], coll))
        # roof handrail
        parts.append(box(name + "_cabrail", (cw * 1.1, 0.05, 0.05),
                         (cx, 0, cz + ch + 0.42), MAT["metal"], coll))
        for sgn in (-1, 1):
            parts.append(cyl(name + "_crp%d" % sgn, 0.025, 0.36,
                             (cx + sgn * cw * 0.5, 0, cz + ch + 0.24), MAT["metal"],
                             coll, verts=5))
    else:
        # open boat: thwarts + a small console
        for i in range(3):
            parts.append(box(name + "_thw%d" % i, (0.24, beam * 0.80, 0.08),
                             (-length * 0.24 + i * length * 0.22, 0, freeboard * 0.62),
                             MAT["wood_light"], coll))
        parts.append(box(name + "_cons", (0.34, 0.5, 0.42), (length * 0.20, 0, freeboard * 0.62),
                         MAT["metal_dark"], coll))

    if mast:
        parts.append(cyl(name + "_mast", 0.055, length * 0.62,
                         (length * 0.10, 0, freeboard + length * 0.31),
                         MAT["metal"], coll, verts=6))
        for i in range(2):
            parts.append(cyl(name + "_boom%d" % i, 0.03, length * 0.30,
                             (length * 0.10 + (i - 0.5) * length * 0.16, 0,
                              freeboard + length * 0.30),
                             MAT["metal"], coll, rot=(0, math.radians(90), 0), verts=5))
    # outboard motor + prop
    parts.append(box(name + "_motor", (0.26, 0.20, 0.44),
                     (-length * 0.5 - 0.06, 0, freeboard * 0.62), MAT["metal_dark"], coll))
    parts.append(cyl(name + "_leg", 0.05, 0.45, (-length * 0.5 - 0.06, 0, freeboard * 0.20),
                     MAT["metal_dark"], coll, verts=6))
    parts.append(cyl(name + "_prop", 0.05, 0.46, (-length * 0.5 - 0.06, 0, -0.02),
                     MAT["metal"], coll, rot=(0, math.radians(90), 0), verts=6))
    # bow rail + cleats
    for sgn in (-1, 1):
        parts.append(cyl(name + "_rail%d" % sgn, 0.022, length * 0.26,
                         (length * 0.30, sgn * beam * 0.20, freeboard + 0.22),
                         MAT["metal"], coll, verts=5))
        parts.append(box(name + "_cleat%d" % sgn, (0.14, 0.05, 0.05),
                         (length * 0.18, sgn * beam * 0.34, freeboard + 0.02),
                         MAT["metal"], coll))
    # fenders + gear
    for sgn in (-1, 1):
        parts.append(cyl(name + "_fend%d" % sgn, 0.10, 0.34,
                         (-length * 0.05, sgn * beam * 0.50, freeboard * 0.55),
                         MAT["paint_coral"], coll, verts=8))
    parts.append(box(name + "_crate", (0.42, 0.38, 0.30),
                     (-length * 0.30, beam * 0.16, freeboard + 0.18),
                     MAT["wood_light"], coll))
    parts.append(box(name + "_net", (0.55, 0.45, 0.18),
                     (-length * 0.30, -beam * 0.16, freeboard + 0.12),
                     MAT["fabric_teal"], coll))
    return make_master(name, parts, bevel=0.008, weighted=False)


def build_boat_masters():
    boat_master("BOAT_A", 5.4, 1.9, 0.50, 0.62, False, MAT["paint_w"], 1)
    boat_master("BOAT_B", 6.4, 2.1, 0.56, 0.66, True, MAT["paint_teal"], 2)
    boat_master("BOAT_C", 7.6, 2.6, 0.66, 0.74, True, MAT["paint_w"], 3, mast=True)
    boat_master("BOAT_D", 4.4, 1.7, 0.42, 0.54, False, MAT["paint_yellow"], 4)
    boat_master("BOAT_E", 6.0, 2.0, 0.52, 0.64, True, MAT["paint_blue"], 5)
    print("BOAT MASTERS 5")
