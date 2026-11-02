"""
abyss_fauna.py : fifteen species masters, posed and placed.

Each animal is a silhouette problem first.  At hero framing a fish is 20-40 px, so
unusual shapes - a manta's wings, an eel's ribbon, a jelly's bell - carry the read;
surface detail does not.  All static, all one mesh per species.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector

FAUNA = {}
SPECIES = []


def _fauna_m(name, parts, bevel=0.003):
    ob = make_master(name, parts, bevel=bevel, weighted=True)
    FAUNA[name] = ob
    SPECIES.append(name)
    return ob


def _feye(parts, name, x, y, z, r=0.035):
    parts.append(sphere(name, r, (x, y, z), MAT["navy"], C("WORK"), seg=6,
                        rings=4))


# ---------------------------------------------------------------- fish
def fish_glass():
    """Small schooling fish: the shoal that fills the gaps."""
    parts = []
    parts.append(ico("FG_B", 0.30, (0, 0, 0), MAT["coral_blue"], C("WORK"),
                     sub=2, scale=(1.9, 0.62, 0.95), flat=False))
    parts.append(cone("FG_T", 0.16, 0.02, 0.30, (-0.36, 0, 0), MAT["coral_blue"],
                      C("WORK"), rot=(0, -math.pi * 0.5, 0), verts=6))
    parts.append(box("FG_D", (0.22, 0.02, 0.16), (0.05, 0, 0.16),
                     MAT["glass_win"], C("WORK")))
    _feye(parts, "FG_E", 0.34, 0.10, 0.06)
    return _fauna_m("FISH_GLASS", parts)


def fish_grouper():
    parts = []
    parts.append(ico("GP_B", 0.85, (0, 0, 0), MAT["coral_orange"], C("WORK"),
                     sub=2, scale=(1.7, 0.72, 1.15)))
    parts.append(cone("GP_T", 0.34, 0.03, 0.62, (-0.95, 0, 0),
                      MAT["coral_orange"], C("WORK"),
                      rot=(0, -math.pi * 0.5, 0), verts=6))
    parts.append(cone("GP_D", 0.30, 0.02, 0.44, (-0.05, 0, 0.72),
                      MAT["coral_pink"], C("WORK"), rot=(0, 0, 0), verts=5))
    parts.append(box("GP_M", (0.20, 0.05, 0.10), (0.80, 0, 0.10), MAT["navy"],
                     C("WORK")))
    _feye(parts, "GP_E", 0.92, 0.34, 0.24, 0.06)
    _feye(parts, "GP_E2", 0.92, -0.34, 0.24, 0.06)
    return _fauna_m("FISH_GROUPER", parts)


def fish_shark():
    parts = []
    parts.append(ico("SH_B", 1.0, (0, 0, 0), MAT["steel"], C("WORK"), sub=2,
                     scale=(2.6, 0.55, 0.72)))
    parts.append(cone("SH_T", 0.26, 0.02, 0.85, (-1.30, 0, 0.05),
                      MAT["steel"], C("WORK"),
                      rot=(0, -math.pi * 0.5, 0), verts=5))
    parts.append(cone("SH_D", 0.34, 0.02, 0.58, (0.10, 0, 0.55), MAT["steel"],
                      C("WORK"), verts=5))
    for s in (-1, 1):
        parts.append(box("SH_P%d" % s, (0.55, 0.90, 0.05), (0.35, s * 0.48,
                         -0.10), MAT["steel"], C("WORK")))
    _feye(parts, "SH_E", 1.02, 0.22, 0.10, 0.05)
    return _fauna_m("FISH_SHARK", parts)


def fish_ray():
    parts = []
    parts.append(ico("RY_B", 1.0, (0, 0, 0), MAT["navy_lt"], C("WORK"), sub=2,
                     scale=(1.15, 2.1, 0.16)))
    parts.append(cone("RY_T", 0.11, 0.01, 1.5, (-1.35, 0, 0), MAT["navy_lt"],
                      C("WORK"), rot=(0, -math.pi * 0.5, 0), verts=5))
    for s in (-1, 1):
        parts.append(cone("RY_C%d" % s, 0.09, 0.02, 0.44, (0.75, s * 0.30, 0.06),
                          MAT["navy_lt"], C("WORK"),
                          rot=(0, math.pi * 0.5, 0), verts=4))
    parts.append(box("RY_H", (0.32, 0.30, 0.10), (0.72, 0, 0.05), MAT["navy_lt"],
                     C("WORK")))
    return _fauna_m("FISH_RAY", parts)


# ---------------------------------------------------------------- soft bodies
def fish_jelly():
    parts = []
    parts.append(ico("JL_B", 0.55, (0, 0, 0), MAT["coral_purple"], C("WORK"),
                     sub=2, scale=(1.0, 1.0, 0.72)))
    parts.append(torus("JL_R", 0.50, 0.045, (0, 0, -0.18), MAT["emit_magenta"],
                       C("WORK"), mseg=18, nseg=4))
    for i in range(8):
        a = i * TAU / 8.0
        parts.append(cyl("JL_T%d" % i, 0.022, 1.5,
                         (math.cos(a) * 0.30, math.sin(a) * 0.30, -0.95),
                         MAT["coral_purple"], C("WORK"), verts=4))
    return _fauna_m("FISH_JELLY", parts)


def fish_squid():
    parts = []
    parts.append(cone("SQ_M", 0.26, 0.06, 1.1, (0.30, 0, 0), MAT["coral_pink"],
                      C("WORK"), rot=(0, math.pi * 0.5, 0), verts=10))
    for i in range(8):
        a = i * TAU / 8.0
        parts.append(cyl("SQ_T%d" % i, 0.030, 0.85,
                         (-0.42 + math.cos(a) * 0.06, math.sin(a) * 0.11,
                          -0.42 + math.cos(a) * 0.11),
                         MAT["coral_pink"], C("WORK"),
                         rot=(0, math.pi * 0.62, a), verts=4))
    for s in (-1, 1):
        parts.append(sphere("SQ_E%d" % s, 0.07, (0.62, s * 0.13, -0.02),
                            MAT["navy"], C("WORK"), seg=6, rings=4))
    return _fauna_m("FISH_SQUID", parts)


def fish_eel():
    parts = []
    n = 9
    for i in range(n):
        t = i / float(n - 1)
        parts.append(cyl("EL_S%d" % i, 0.11 * (1.0 - t * 0.55), 0.34,
                         (t * 2.0 - 1.0, math.sin(t * 4.2) * 0.42,
                          math.sin(t * 3.0) * 0.20),
                         MAT["coral_lime"], C("WORK"),
                         rot=(0, math.pi * 0.5, 0), verts=6))
    parts.append(cone("EL_H", 0.13, 0.04, 0.30, (1.10, 0.12, 0.06),
                      MAT["coral_lime"], C("WORK"),
                      rot=(0, math.pi * 0.5, 0), verts=6))
    _feye(parts, "EL_E", 1.12, 0.22, 0.12, 0.035)
    return _fauna_m("FISH_EEL", parts)


def fish_angler():
    parts = []
    parts.append(ico("AN_B", 0.55, (0, 0, 0), MAT["navy"], C("WORK"), sub=2,
                     scale=(1.3, 0.95, 1.0)))
    parts.append(box("AN_J", (0.34, 0.42, 0.16), (0.55, 0, -0.10), MAT["navy_lt"],
                     C("WORK")))
    parts.append(cyl("AN_ST", 0.03, 0.55, (0.55, 0, 0.52), MAT["steel_lt"],
                     C("WORK"), rot=(0, -0.45, 0), verts=4))
    parts.append(sphere("AN_L", 0.11, (0.78, 0, 0.78), MAT["emit_white"],
                        C("WORK"), seg=8, rings=5))
    for i in range(5):
        parts.append(cone("AN_T%d" % i, 0.02, 0.005, 0.16,
                          (0.52, -0.16 + i * 0.08, -0.20), MAT["ceramic"],
                          C("WORK"), verts=4))
    return _fauna_m("FISH_ANGLER", parts)


# ---------------------------------------------------------------- bottom life
def fish_crab():
    parts = []
    parts.append(ico("CR_B", 0.38, (0, 0, 0), MAT["coral_orange"], C("WORK"),
                     sub=1, scale=(1.25, 1.0, 0.52)))
    for s in (-1, 1):
        parts.append(box("CR_C%d" % s, (0.20, 0.16, 0.14), (0.42, s * 0.26, 0.02),
                         MAT["coral_orange"], C("WORK")))
        for k in range(3):
            parts.append(cyl("CR_L%d%d" % (s, k), 0.035, 0.45,
                             (math.cos(k) * 0.18, s * (0.34 + k * 0.03), -0.16),
                             MAT["coral_pink"], C("WORK"),
                             rot=(s * 0.9, 0, 0), verts=4))
    _feye(parts, "CR_E1", 0.34, 0.10, 0.16, 0.04)
    _feye(parts, "CR_E2", 0.34, -0.10, 0.16, 0.04)
    return _fauna_m("FISH_CRAB", parts)


def fish_starfish():
    parts = []
    parts.append(cyl("SF_C", 0.18, 0.07, (0, 0, 0), MAT["coral_orange"],
                     C("WORK"), verts=10))
    for i in range(5):
        a = i * TAU / 5.0
        arm = box("SF_A%d" % i, (0.62, 0.16, 0.06),
                  (math.cos(a) * 0.30, math.sin(a) * 0.30, 0),
                  MAT["coral_orange"], C("WORK"))
        arm.rotation_euler = (0, 0, a)
        parts.append(arm)
    return _fauna_m("FISH_STARFISH", parts)


def fish_anemone():
    parts = []
    parts.append(cyl("AM_B", 0.34, 0.34, (0, 0, 0.17), MAT["coral_purple"],
                     C("WORK"), verts=12))
    for i in range(14):
        a = i * TAU / 14.0 + 0.2
        r = 0.10 + (i % 3) * 0.09
        h = 0.42 + (i % 4) * 0.10
        parts.append(cyl("AM_T%d" % i, 0.035, h,
                         (math.cos(a) * r, math.sin(a) * r, 0.30 + h * 0.5),
                         MAT["coral_pink"] if i % 2 else MAT["coral_purple"],
                         C("WORK"), verts=4))
        parts.append(sphere("AM_G%d" % i, 0.045,
                            (math.cos(a) * r, math.sin(a) * r, 0.30 + h),
                            MAT["emit_magenta"], C("WORK"), seg=6, rings=4))
    return _fauna_m("FISH_ANEMONE", parts)


def fish_turtle():
    parts = []
    parts.append(ico("TU_SH", 0.80, (0, 0, 0), MAT["coral_lime"], C("WORK"),
                     sub=2, scale=(1.25, 1.0, 0.42)))
    parts.append(box("TU_HD", (0.34, 0.28, 0.24), (0.98, 0, 0.05),
                     MAT["coral_lime"], C("WORK")))
    for s in (-1, 1):
        fl = box("TU_F%d" % s, (0.56, 0.34, 0.05), (0.42, s * 0.82, -0.02),
                 MAT["coral_lime"], C("WORK"))
        fl.rotation_euler = (0, 0, s * 0.5)
        parts.append(fl)
        parts.append(box("TU_R%d" % s, (0.26, 0.22, 0.05), (-0.68, s * 0.42,
                         -0.02), MAT["coral_lime"], C("WORK")))
    _feye(parts, "TU_E1", 1.10, 0.11, 0.12, 0.03)
    _feye(parts, "TU_E2", 1.10, -0.11, 0.12, 0.03)
    return _fauna_m("FISH_TURTLE", parts)


def fish_seahorse():
    parts = []
    parts.append(ico("SE_B", 0.22, (0, 0, 0.55), MAT["coral_orange"], C("WORK"),
                     sub=1, scale=(0.85, 0.60, 1.6)))
    parts.append(cyl("SE_T", 0.06, 0.55, (0, 0.10, 0.10), MAT["coral_orange"],
                     C("WORK"), rot=(0.35, 0, 0), verts=6, r2=0.02))
    parts.append(cyl("SE_S", 0.04, 0.34, (0, -0.10, 0.85), MAT["coral_orange"],
                     C("WORK"), rot=(0, 0.55, 0), verts=4))
    _feye(parts, "SE_E1", 0.10, 0.14, 0.70, 0.03)
    _feye(parts, "SE_E2", -0.02, 0.14, 0.70, 0.03)
    return _fauna_m("FISH_SEAHORSE", parts)


def fish_shrimp():
    parts = []
    parts.append(ico("SM_B", 0.13, (0, 0, 0), MAT["coral_pink"], C("WORK"),
                     sub=1, scale=(2.2, 0.8, 0.9)))
    for i in range(3):
        parts.append(cyl("SM_L%d" % i, 0.012, 0.22,
                         (-0.06 + i * 0.06, 0.08, -0.10), MAT["coral_pink"],
                         C("WORK"), rot=(0.6, 0, 0), verts=3))
    parts.append(cyl("SM_A", 0.010, 0.28, (0.22, 0.04, 0.10), MAT["coral_pink"],
                     C("WORK"), rot=(0, 0.7, 0), verts=3))
    return _fauna_m("FISH_SHRIMP", parts)


def fish_whale():
    """Only ever seen as a silhouette in the fog, so it is built as one."""
    parts = []
    parts.append(ico("WH_B", 2.4, (0, 0, 0), MAT["navy"], C("WORK"), sub=2,
                     scale=(3.1, 1.0, 0.78)))
    parts.append(cone("WH_T", 0.9, 0.10, 2.6, (-4.3, 0, 0.10), MAT["navy"],
                      C("WORK"), rot=(0, -math.pi * 0.5, 0), verts=6))
    for s in (-1, 1):
        parts.append(box("WH_F%d" % s, (1.5, 1.9, 0.16), (1.4, s * 1.35, -0.4),
                         MAT["navy"], C("WORK")))
    _feye(parts, "WH_E", 2.95, 0.72, 0.22, 0.10)
    return _fauna_m("FISH_WHALE", parts)


# ---------------------------------------------------------------- placement
def build_fauna(seed=909):
    for fn in (fish_glass, fish_grouper, fish_shark, fish_ray, fish_jelly,
               fish_squid, fish_eel, fish_angler, fish_crab, fish_starfish,
               fish_anemone, fish_turtle, fish_seahorse, fish_shrimp,
               fish_whale):
        fn()
    rng = random.Random(seed)
    n = 0

    def scatter(name, count, zlo, zhi, srange, lo=0.25, hi=1.15, tilt=True,
                coll="WILDLIFE", tag="fauna"):
        nonlocal n
        for i in range(count):
            for _ in range(30):
                a = rng.uniform(0, TAU)
                rr = rng.uniform(lo, hi)
                x = math.cos(a) * rr * PLATEAU_RX
                y = math.sin(a) * rr * PLATEAU_RY
                z = seabed_h(x, y) + rng.uniform(zlo, zhi)
                place(name, x, y, rot=rng.uniform(0, TAU),
                      s=rng.uniform(*srange), coll=coll, z=z, tag=tag,
                      tilt=(rng.uniform(-0.12, 0.12) if tilt else 0.0,
                            rng.uniform(-0.12, 0.12) if tilt else 0.0))
                n += 1
                break

    # shoals: several small fish together, which is what makes a shoal
    for k in range(4):
        cx = rng.uniform(-30, 30)
        cy = rng.uniform(-30, 30)
        for i in range(5):
            x = cx + rng.uniform(-3.6, 3.6)
            y = cy + rng.uniform(-3.6, 3.6)
            if plate_r(x, y) > 1.25:
                continue
            place("FISH_GLASS", x, y, rot=rng.uniform(0, TAU),
                  s=rng.uniform(0.8, 1.5), coll="WILDLIFE",
                  z=seabed_h(x, y) + rng.uniform(3.0, 14.0), tag="fauna")
            n += 1

    scatter("FISH_GROUPER", 7, 2.5, 12.0, (0.9, 1.6))
    scatter("FISH_SHARK", 3, 10.0, 20.0, (1.0, 1.5))
    scatter("FISH_RAY", 4, 6.0, 16.0, (0.9, 1.4))
    scatter("FISH_JELLY", 8, 4.0, 18.0, (0.9, 1.8))
    scatter("FISH_SQUID", 4, 5.0, 13.0, (0.9, 1.4))
    scatter("FISH_EEL", 5, 1.0, 4.5, (1.0, 1.7))
    scatter("FISH_ANGLER", 3, 1.2, 3.0, (1.0, 1.4))
    scatter("FISH_TURTLE", 3, 4.0, 11.0, (0.9, 1.2))
    scatter("FISH_WHALE", 2, 26.0, 34.0, (1.8, 2.6), lo=0.95, hi=1.45)
    scatter("FISH_SEAHORSE", 5, 0.6, 2.4, (0.9, 1.3))
    scatter("FISH_SHRIMP", 6, 0.3, 1.2, (0.9, 1.4))

    # benthic life sits on the ground, no tilt
    for nm, cnt in (("FISH_CRAB", 7), ("FISH_STARFISH", 9),
                    ("FISH_ANEMONE", 8)):
        for i in range(cnt):
            for _ in range(24):
                a = rng.uniform(0, TAU)
                rr = rng.uniform(0.30, 0.94)
                x = math.cos(a) * rr * PLATEAU_RX
                y = math.sin(a) * rr * PLATEAU_RY
                place(nm, x, y, rot=rng.uniform(0, TAU),
                      s=rng.uniform(0.8, 1.5), coll="WILDLIFE", sink=0.04,
                      tag="fauna")
                n += 1
                break

    print("FAUNA %d species, %d placed" % (len(SPECIES), n))
    return n
