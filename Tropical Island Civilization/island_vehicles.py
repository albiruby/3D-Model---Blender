"""
island_vehicles.py : pickup, compact car, scooter, golf cart, fishing boat.
Base at z = 0, facing -Y.
"""

import bpy
import math
from mathutils import Vector


def _wheel(name, x, y, z, r=0.30, w=0.16, coll=None, mat=None):
    coll = coll or C("WORK")
    tyre = cyl(name, r, w, (x, y, z), mat or MAT["hair_dark"], coll,
               rot=(0, math.radians(90), 0), verts=12)
    hub = cyl(name + "_h", r * 0.48, w * 1.04, (x, y, z), MAT["metal"], coll,
              rot=(0, math.radians(90), 0), verts=8)
    return [tyre, hub]


def pickup_master(name, colour=None, seed=0):
    coll = C("WORK")
    parts = []
    m = colour or MAT["paint_teal"]
    L, Wd = 4.6, 1.9
    parts.append(box(name + "_chassis", (L, Wd, 0.30), (0, 0, 0.55), m, coll))
    parts.append(box(name + "_cab", (1.9, Wd, 0.85), (0.35, 0, 1.05), m, coll))
    parts.append(box(name + "_hood", (1.25, Wd * 0.96, 0.34), (1.55, 0, 0.90), m, coll))
    parts.append(box(name + "_bed", (1.75, Wd, 0.42), (-1.25, 0, 0.80), m, coll))
    parts.append(box(name + "_bedin", (1.55, Wd * 0.82, 0.36), (-1.25, 0, 0.86),
                     MAT["wood_dark"], coll))
    for sy in (-1, 1):
        parts.append(box(name + "_ws%d" % sy, (0.06, 0.06, 0.62),
                         (-0.42, sy * (Wd * 0.5 - 0.03), 1.10), MAT["glass"], coll))
        parts.append(box(name + "_side%d" % sy, (0.9, 0.05, 0.5),
                         (0.45, sy * (Wd * 0.5 - 0.02), 1.15), MAT["glass"], coll))
    parts.append(box(name + "_wsF", (0.05, Wd * 0.82, 0.55), (1.30, 0, 1.15),
                     MAT["glass"], coll))
    for sx in (-1, 1):
        parts.append(box(name + "_hl%d" % sx, (0.06, 0.28, 0.16),
                         (L * 0.5 - 0.02, sx * Wd * 0.32, 0.84), MAT["glow_soft"], coll))
        parts.append(box(name + "_tl%d" % sx, (0.05, 0.24, 0.14),
                         (-L * 0.5 + 0.02, sx * Wd * 0.34, 0.82), MAT["paint_coral"], coll))
    parts.append(box(name + "_bump", (0.16, Wd * 0.98, 0.16), (L * 0.5, 0, 0.52),
                     MAT["metal_dark"], coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts += _wheel(name + "_wh%d%d" % (sx, sy), sx * 1.45, sy * (Wd * 0.5 - 0.03),
                            0.36, coll=coll)
    # cargo in the bed
    parts.append(box(name + "_cargo", (0.7, 0.7, 0.42), (-1.3, 0.2, 1.12),
                     MAT["wood_light"], coll))
    parts.append(box(name + "_cargo2", (0.5, 0.6, 0.34), (-0.7, -0.35, 1.10),
                     MAT["leaf_dry"], coll))
    return make_master(name, parts, bevel=0.012, weighted=True)


def car_master(name, colour=None, seed=0):
    coll = C("WORK")
    parts = []
    m = colour or MAT["paint_coral"]
    L, Wd = 3.9, 1.75
    parts.append(box(name + "_body", (L, Wd, 0.52), (0, 0, 0.62), m, coll))
    parts.append(box(name + "_cabin", (2.0, Wd * 0.90, 0.72), (-0.15, 0, 1.20), m, coll))
    parts.append(box(name + "_hood", (1.0, Wd * 0.94, 0.22), (1.35, 0, 0.92), m, coll))
    for sy in (-1, 1):
        parts.append(box(name + "_side%d" % sy, (1.7, 0.05, 0.46),
                         (-0.15, sy * (Wd * 0.46), 1.26), MAT["glass"], coll))
    parts.append(box(name + "_wsF", (0.06, Wd * 0.78, 0.5), (0.85, 0, 1.24),
                     MAT["glass"], coll, rot=(0, math.radians(-18), 0)))
    parts.append(box(name + "_wsB", (0.06, Wd * 0.78, 0.44), (-1.15, 0, 1.24),
                     MAT["glass"], coll))
    for sx in (-1, 1):
        parts.append(box(name + "_hl%d" % sx, (0.05, 0.26, 0.14),
                         (L * 0.5 - 0.02, sx * Wd * 0.30, 0.86), MAT["glow_soft"], coll))
        parts.append(box(name + "_tl%d" % sx, (0.05, 0.22, 0.12),
                         (-L * 0.5 + 0.02, sx * Wd * 0.32, 0.86), MAT["paint_coral"], coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts += _wheel(name + "_wh%d%d" % (sx, sy), sx * 1.22, sy * (Wd * 0.5 - 0.02),
                            0.32, 0.14, coll=coll)
    return make_master(name, parts, bevel=0.012, weighted=True)


def scooter_master(name, colour=None, seed=0):
    coll = C("WORK")
    parts = []
    m = colour or MAT["paint_yellow"]
    parts.append(box(name + "_deck", (0.9, 0.30, 0.14), (0, 0, 0.38), m, coll))
    parts.append(box(name + "_body", (0.55, 0.34, 0.52), (-0.28, 0, 0.62), m, coll))
    parts.append(box(name + "_seat", (0.52, 0.28, 0.12), (-0.30, 0, 0.90),
                     MAT["hair_dark"], coll))
    parts.append(box(name + "_shield", (0.06, 0.40, 0.55), (0.38, 0, 0.85), m, coll,
                     rot=(0, math.radians(-20), 0)))
    parts.append(cyl(name + "_bar", 0.03, 0.52, (0.42, 0, 1.02), MAT["metal"], coll,
                     rot=(math.radians(90), 0, 0), verts=6))
    parts.append(sphere(name + "_hl", 0.09, (0.48, 0, 0.92), MAT["glow_soft"], coll,
                        seg=8, rings=5))
    for sx in (-1, 1):
        parts += _wheel(name + "_wh%d" % sx, sx * 0.62, 0, 0.26, 0.20, 0.10, coll)
    return make_master(name, parts, bevel=0.008, weighted=True)


def golf_cart_master(name, colour=None, seed=0):
    coll = C("WORK")
    parts = []
    m = colour or MAT["paint_w"]
    L, Wd = 2.6, 1.3
    parts.append(box(name + "_base", (L, Wd, 0.26), (0, 0, 0.46), m, coll))
    parts.append(box(name + "_seat", (0.7, Wd * 0.9, 0.12), (0.1, 0, 0.72),
                     MAT["fabric_teal"], coll))
    parts.append(box(name + "_back", (0.14, Wd * 0.9, 0.5), (-0.28, 0, 0.95),
                     MAT["fabric_teal"], coll))
    parts.append(box(name + "_roof", (L * 0.85, Wd, 0.08), (0, 0, 1.55), m, coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + "_post%d%d" % (sx, sy), 0.035, 1.0,
                             (sx * (L * 0.4), sy * (Wd * 0.44), 1.05), MAT["metal"], coll,
                             verts=5))
    parts.append(cyl(name + "_bar", 0.04, Wd * 0.8, (0.95, 0, 0.95), MAT["metal"], coll,
                     rot=(math.radians(90), 0, 0), verts=6))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts += _wheel(name + "_wh%d%d" % (sx, sy), sx * 0.85, sy * (Wd * 0.5 - 0.02),
                            0.26, 0.12, coll=coll)
    return make_master(name, parts, bevel=0.008, weighted=True)


def build_vehicle_masters():
    pickup_master("PICKUP_A", MAT["paint_teal"], 1)
    pickup_master("PICKUP_B", MAT["paint_coral"], 2)
    car_master("CAR_A", MAT["paint_yellow"], 3)
    car_master("CAR_B", MAT["paint_w"], 4)
    scooter_master("SCOOTER_A", MAT["paint_coral"], 5)
    scooter_master("SCOOTER_B", MAT["paint_blue"], 6)
    golf_cart_master("GOLF_CART", MAT["paint_w"], 7)
    print("VEHICLE MASTERS 7")
