"""
island_animals.py : species-specific stylised animals (static, no rigs).
"""

import bpy
import bmesh
import math
from mathutils import Vector


def _ell(name, r, loc, mat, coll, sx=1.0, sy=1.0, sz=1.0, seg=10, rings=7):
    return sphere(name, r, loc, mat, coll, seg=seg, rings=rings, scale=(sx, sy, sz))


def chicken_master(name, scale=1.0, colour=None, rooster=False):
    coll = C("WORK")
    parts = []
    body_m = colour or MAT["paint_w"]
    parts.append(_ell(name + "_body", 0.16, (0, 0, 0.20), body_m, coll, 0.90, 1.25, 0.95))
    parts.append(_ell(name + "_neck", 0.075, (0, -0.13, 0.30), body_m, coll, 1.0, 0.9, 1.1))
    parts.append(_ell(name + "_head", 0.062, (0, -0.15, 0.37), body_m, coll))
    parts.append(cone(name + "_beak", 0.035, 0.005, 0.07, (0, -0.21, 0.37),
                      MAT["paint_yellow"], coll, rot=(math.radians(-80), 0, 0), verts=6))
    if rooster:
        for i in range(3):
            parts.append(cone(name + "_comb%d" % i, 0.026, 0.004, 0.06,
                              (0, -0.15 + i * 0.028, 0.425), MAT["paint_coral"], coll,
                              verts=5))
        parts.append(_ell(name + "_tail", 0.09, (0, 0.16, 0.30), MAT["leaf_dark"], coll,
                          0.35, 0.9, 1.15))
    for i in range(2):
        parts.append(cyl(name + "_leg%d" % i, 0.014, 0.16, (i * 0.05 - 0.025, -0.01, 0.08),
                         MAT["paint_yellow"], coll, verts=5))
    parts.append(_ell(name + "_wing", 0.10, (0.13, 0.0, 0.22), MAT["leaf_dry"], coll,
                      0.24, 0.85, 0.7))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def dog_master(name, scale=1.0, colour=None):
    coll = C("WORK")
    parts = []
    m = colour or MAT["wood"]
    parts.append(_ell(name + "_body", 0.17, (0, 0, 0.36), m, coll, 0.72, 1.55, 0.85))
    parts.append(_ell(name + "_chest", 0.14, (0, -0.17, 0.38), m, coll, 0.80, 0.9, 0.9))
    parts.append(_ell(name + "_neck", 0.085, (0, -0.27, 0.46), m, coll, 0.9, 0.9, 1.2))
    parts.append(_ell(name + "_head", 0.105, (0, -0.33, 0.56), m, coll, 0.9, 1.15, 0.9))
    parts.append(_ell(name + "_muzzle", 0.062, (0, -0.44, 0.52), m, coll, 0.8, 1.1, 0.75))
    parts.append(_ell(name + "_nose", 0.023, (0, -0.50, 0.525), MAT["hair_dark"], coll))
    for sgn in (-1, 1):
        parts.append(cone(name + "_ear%d" % sgn, 0.045, 0.005, 0.10,
                          (sgn * 0.065, -0.30, 0.645), m, coll,
                          rot=(math.radians(10), sgn * math.radians(18), 0), verts=5))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(cyl(name + "_leg%d" % i, 0.036, 0.34,
                         (sx * 0.085, sy * 0.14, 0.17), m, coll, verts=6))
        parts.append(box(name + "_paw%d" % i, (0.07, 0.11, 0.05),
                         (sx * 0.085, sy * 0.15 - 0.02, 0.025), m, coll))
    parts.append(loft_path(name + "_tail",
                           [(0, 0.24, 0.42), (0, 0.31, 0.50), (0, 0.33, 0.60)],
                           [0.032, 0.026, 0.018], m, coll, sides=5))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def cat_master(name, scale=1.0, colour=None):
    coll = C("WORK")
    parts = []
    m = colour or MAT["hair_brown"]
    parts.append(_ell(name + "_body", 0.11, (0, 0, 0.19), m, coll, 0.72, 1.5, 0.85))
    parts.append(_ell(name + "_head", 0.078, (0, -0.20, 0.27), m, coll, 1.0, 0.95, 0.9))
    for sgn in (-1, 1):
        parts.append(cone(name + "_ear%d" % sgn, 0.032, 0.003, 0.07,
                          (sgn * 0.042, -0.19, 0.335), m, coll, verts=4))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        parts.append(cyl(name + "_leg%d" % i, 0.022, 0.19,
                         (sx * 0.055, sy * 0.09, 0.095), m, coll, verts=5))
    parts.append(loft_path(name + "_tail",
                           [(0, 0.15, 0.22), (0, 0.22, 0.33), (0, 0.16, 0.42)],
                           [0.022, 0.017, 0.013], m, coll, sides=5))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def gull_master(name, scale=1.0, flying=False):
    coll = C("WORK")
    parts = []
    parts.append(_ell(name + "_body", 0.10, (0, 0, 0.16), MAT["paint_w"], coll,
                      0.85, 1.5, 0.85))
    parts.append(_ell(name + "_head", 0.058, (0, -0.15, 0.21), MAT["paint_w"], coll))
    parts.append(cone(name + "_beak", 0.022, 0.003, 0.07, (0, -0.21, 0.205),
                      MAT["paint_yellow"], coll, rot=(math.radians(-90), 0, 0), verts=5))
    span = 0.42 if flying else 0.30
    for sgn in (-1, 1):
        ob = box(name + "_wing%d" % sgn, (span, 0.16, 0.02), (sgn * span * 0.5, 0, 0.19),
                 MAT["paint_w"], coll, rot=(0, sgn * (math.radians(18) if flying else 0),
                                            sgn * math.radians(-8)))
        parts.append(ob)
    parts.append(box(name + "_tail", (0.09, 0.11, 0.015), (0, 0.15, 0.16),
                     MAT["paint_w"], coll))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def crab_master(name, scale=1.0):
    coll = C("WORK")
    parts = []
    parts.append(_ell(name + "_shell", 0.13, (0, 0, 0.08), MAT["paint_coral"], coll,
                      1.25, 0.95, 0.55))
    for sgn in (-1, 1):
        parts.append(loft_path(name + "_claw%d" % sgn,
                               [(sgn * 0.10, -0.08, 0.07), (sgn * 0.20, -0.16, 0.10),
                                (sgn * 0.24, -0.24, 0.12)],
                               [0.035, 0.045, 0.02], MAT["paint_coral"], coll, sides=5))
        parts.append(sphere(name + "_clawt%d" % sgn, 0.045, (sgn * 0.24, -0.26, 0.12),
                            MAT["paint_coral"], coll, seg=6, rings=4, scale=(0.6, 1, 0.6)))
        for i in range(4):
            a = -0.5 - i * 0.30
            parts.append(loft_path(name + "_lg%d_%d" % (sgn, i),
                                   [(sgn * 0.09, 0.02 + i * 0.03, 0.06),
                                    (sgn * 0.18, 0.05 + i * 0.035, 0.02),
                                    (sgn * 0.22, 0.03 + i * 0.04, 0.0)],
                                   [0.016, 0.011, 0.008], MAT["paint_coral"], coll, sides=4))
    for sgn in (-1, 1):
        parts.append(cyl(name + "_eye%d" % sgn, 0.010, 0.05, (sgn * 0.045, -0.10, 0.13),
                         MAT["hair_dark"], coll, verts=4))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def turtle_master(name, scale=1.0):
    coll = C("WORK")
    parts = []
    parts.append(_ell(name + "_shell", 0.30, (0, 0, 0.16), MAT["leaf_dark"], coll,
                      1.0, 1.15, 0.42))
    parts.append(torus(name + "_rim", 0.30, 0.028, (0, 0, 0.115), MAT["leaf_dry"], coll,
                       mseg=16, nseg=5))
    parts.append(_ell(name + "_head", 0.085, (0, -0.36, 0.17), MAT["leaf_mid"], coll,
                      0.9, 1.2, 0.85))
    for sgn in (-1, 1):
        for sy, s in ((-1, 0.16), (1, 0.20)):
            parts.append(box(name + "_fl%d_%d" % (sgn, sy), (0.20, 0.13, 0.035),
                             (sgn * 0.30, sy * 0.9, 0.10), MAT["leaf_mid"], coll,
                             rot=(0, 0, sgn * math.radians(25))))
    parts.append(cone(name + "_tail", 0.035, 0.008, 0.12, (0, 0.34, 0.12),
                      MAT["leaf_mid"], coll, rot=(math.radians(80), 0, 0), verts=5))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    for v in ob.data.vertices:
        v.co *= scale
    return ob


def fish_master(name, length=0.42, colour=None, seed=0):
    coll = C("WORK")
    m = colour or MAT["paint_yellow"]
    parts = []
    rings = []
    n = 7
    for i in range(n):
        t = i / (n - 1.0)
        h = math.sin(math.pi * t) ** 0.7
        x = -length * 0.5 + length * t
        ring = []
        for k in range(6):
            a = k * TAU / 6
            ring.append((x, math.cos(a) * 0.070 * h, math.sin(a) * 0.100 * h))
        rings.append(ring)
    parts.append(loft(name + "_body", rings, m, coll))
    parts.append(cone(name + "_tail", 0.09, 0.008, 0.13, (length * 0.55, 0, 0),
                      m, coll, rot=(0, math.radians(-90), 0), verts=4))
    parts.append(cone(name + "_fin", 0.05, 0.004, 0.10, (0, 0, 0.10),
                      m, coll, verts=4))
    ob = make_master(name, parts, bevel=0.0, weighted=False)
    return ob


def build_animal_masters():
    chicken_master("CHICKEN", 1.0, MAT["paint_w"], False)
    chicken_master("ROOSTER", 1.1, MAT["roof_terra"], True)
    dog_master("DOG", 1.0, MAT["wood"])
    dog_master("DOG_B", 0.85, MAT["paint_w"])
    cat_master("CAT", 1.0, MAT["hair_brown"])
    gull_master("GULL", 1.0, False)
    gull_master("GULL_FLY", 1.0, True)
    crab_master("CRAB", 1.0)
    turtle_master("TURTLE", 1.0)
    fish_master("FISH_A", 0.45, MAT["paint_yellow"])
    fish_master("FISH_B", 0.36, MAT["paint_coral"])
    print("ANIMAL MASTERS 11")
