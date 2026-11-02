"""
abyss_kit.py : reusable architectural and interior components.

Nothing here is a finished asset.  These are the parts every building is assembled
from, so a facade, a shop counter or a roof plant is authored once and re-used.

Coordinate convention: every kit function takes a `Frame` and builds in LOCAL
space.  The Frame converts local (lx, ly, lz) to world, which keeps each archetype
readable instead of littered with trig.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix


# ---------------------------------------------------------------- frame
class Frame:
    """Local-to-world for one building: translation + a single Z rotation."""

    def __init__(self, x=0.0, y=0.0, z=0.0, rot=0.0):
        self.x, self.y, self.z = x, y, z
        self.rot = rot
        self.c = math.cos(rot)
        self.s = math.sin(rot)

    def p(self, lx, ly, lz):
        return (self.x + lx * self.c - ly * self.s,
                self.y + lx * self.s + ly * self.c,
                self.z + lz)

    def r(self, lr=0.0):
        return (0.0, 0.0, self.rot + lr)

    def dir(self, lx, ly):
        return (lx * self.c - ly * self.s, lx * self.s + ly * self.c)


def face_rot(face):
    """Rotation that makes a +Y-facing panel face the requested side."""
    return {"S": 0.0, "N": math.pi, "E": -math.pi * 0.5,
            "W": math.pi * 0.5}[face]


# ---------------------------------------------------------------- facade parts
def window(parts, name, F, lx, ly, lz, w=1.1, h=1.4, face="S", style="plain",
           glass=None, frame_mat=None, mullions=1):
    """Recessed window: reveal frame, glass, mullion, sill, optional awning."""
    glass = glass or MAT["glass_win"]
    frame_mat = frame_mat or MAT["titanium"]
    fr = face_rot(face)
    fw = 0.09
    # reveal: four thin boxes around the opening
    parts.append(box(name + "_t", (w, 0.16, fw), F.p(lx, ly, lz + h * 0.5),
                     frame_mat, C("WORK"), rot=F.r(fr)))
    parts.append(box(name + "_b", (w, 0.16, fw), F.p(lx, ly, lz - h * 0.5),
                     frame_mat, C("WORK"), rot=F.r(fr)))
    parts.append(box(name + "_l", (fw, 0.16, h), F.p(lx - w * 0.5, ly, lz),
                     frame_mat, C("WORK"), rot=F.r(fr)))
    parts.append(box(name + "_r", (fw, 0.16, h), F.p(lx + w * 0.5, ly, lz),
                     frame_mat, C("WORK"), rot=F.r(fr)))
    parts.append(box(name + "_g", (w - fw, 0.05, h - fw),
                     F.p(lx, ly + 0.06, lz), glass, C("WORK"), rot=F.r(fr)))
    for i in range(mullions):
        off = (i - (mullions - 1) * 0.5) * (w / max(1, mullions + 1))
        parts.append(box(name + "_m%d" % i, (0.055, 0.10, h - fw),
                         F.p(lx + off, ly + 0.02, lz), frame_mat, C("WORK"),
                         rot=F.r(fr)))
    # sill
    parts.append(box(name + "_sill", (w + 0.18, 0.26, 0.09),
                     F.p(lx, ly + 0.06, lz - h * 0.5 - 0.10), frame_mat,
                     C("WORK"), rot=F.r(fr)))
    if style == "awning":
        aw = box(name + "_aw", (w + 0.34, 0.75, 0.07),
                 F.p(lx, ly + 0.36, lz + h * 0.5 + 0.16), MAT["steel_lt"],
                 C("WORK"), rot=F.r(fr))
        aw.rotation_euler = (math.radians(-16.0), 0.0, F.rot + fr)
        parts.append(aw)
    elif style == "louvre":
        for i in range(3):
            parts.append(box(name + "_lv%d" % i, (w * 0.94, 0.10, 0.055),
                             F.p(lx, ly + 0.10, lz - h * 0.25 + i * h * 0.25),
                             MAT["steel_lt"], C("WORK"), rot=F.r(fr)))
    elif style == "round":
        parts.append(torus(name + "_ring", w * 0.5, 0.06,
                           F.p(lx, ly + 0.06, lz), frame_mat, C("WORK"),
                           rot=(math.pi * 0.5, 0.0, F.rot + fr), mseg=16, nseg=4))


def door(parts, name, F, lx, ly, lz, w=1.3, h=2.3, face="S", style="service",
         mat=None):
    mat = mat or MAT["steel"]
    fr = face_rot(face)
    parts.append(box(name + "_frt", (w + 0.30, 0.20, 0.14),
                     F.p(lx, ly, lz + h + 0.05), MAT["titanium"], C("WORK"),
                     rot=F.r(fr)))
    for s in (-1, 1):
        parts.append(box(name + "_fr%d" % s, (0.15, 0.20, h + 0.14),
                         F.p(lx + s * (w * 0.5 + 0.075), ly, lz + h * 0.5 - 0.05),
                         MAT["titanium"], C("WORK"), rot=F.r(fr)))
    if style == "double":
        for s in (-1, 1):
            parts.append(box(name + "_lf%d" % s, (w * 0.47, 0.07, h * 0.96),
                             F.p(lx + s * w * 0.24, ly + 0.10, lz + h * 0.48),
                             mat, C("WORK"), rot=F.r(fr)))
    else:
        parts.append(box(name + "_lf", (w, 0.07, h * 0.96),
                         F.p(lx, ly + 0.10, lz + h * 0.48), mat, C("WORK"),
                         rot=F.r(fr)))
    # handle
    parts.append(cyl(name + "_hd", 0.035, 0.22,
                     F.p(lx + w * 0.34, ly + 0.16, lz + h * 0.46),
                     MAT["alu"], C("WORK"), rot=(math.pi * 0.5, 0, F.rot + fr),
                     verts=6))
    if style == "shop":
        # glazed shopfront above the door
        parts.append(box(name + "_tr", (w + 0.9, 0.10, h * 0.26),
                         F.p(lx, ly + 0.12, lz + h * 1.06), MAT["glass_win"],
                         C("WORK"), rot=F.r(fr)))


def balcony(parts, name, F, lx, ly, lz, w=3.0, depth=1.5, face="S",
            rail_mat=None):
    fr = face_rot(face)
    rail_mat = rail_mat or MAT["steel_lt"]
    parts.append(box(name + "_slab", (w, depth, 0.16),
                     F.p(lx, ly + depth * 0.5, lz), MAT["deck"], C("WORK"),
                     rot=F.r(fr)))
    parts.append(box(name + "_rail", (w, 0.07, 0.06),
                     F.p(lx, ly + depth - 0.06, lz + 1.0), rail_mat, C("WORK"),
                     rot=F.r(fr)))
    n = max(2, int(w / 0.5))
    for i in range(n + 1):
        t = -w * 0.5 + i * (w / n)
        parts.append(cyl(name + "_pb%d" % i, 0.028, 1.0,
                         F.p(lx + t, ly + depth - 0.06, lz + 0.5), rail_mat,
                         C("WORK"), verts=5))
    for s in (-1, 1):
        parts.append(box(name + "_sr%d" % s, (0.06, depth, 0.06),
                         F.p(lx + s * w * 0.5, ly + depth * 0.5, lz + 1.0),
                         rail_mat, C("WORK"), rot=F.r(fr)))


def sign(parts, name, F, lx, ly, lz, w=1.8, h=0.55, face="S", mat=None):
    mat = mat or MAT["emit_shop"]
    fr = face_rot(face)
    parts.append(box(name + "_bk", (w + 0.12, 0.10, h + 0.12),
                     F.p(lx, ly, lz), MAT["navy"], C("WORK"), rot=F.r(fr)))
    parts.append(box(name + "_sf", (w, 0.05, h),
                     F.p(lx, ly + 0.06, lz), mat, C("WORK"), rot=F.r(fr)))
    # bracket
    parts.append(box(name + "_br", (w * 0.7, 0.06, 0.06),
                     F.p(lx, ly - 0.12, lz + h * 0.5 + 0.2), MAT["steel"],
                     C("WORK"), rot=F.r(fr)))


def canopy(parts, name, F, lx, ly, lz, w=4.0, depth=2.2, face="S"):
    fr = face_rot(face)
    parts.append(box(name + "_cp", (w, depth, 0.14),
                     F.p(lx, ly + depth * 0.5, lz), MAT["titanium"], C("WORK"),
                     rot=F.r(fr)))
    parts.append(box(name + "_lit", (w * 0.86, depth * 0.72, 0.06),
                     F.p(lx, ly + depth * 0.5, lz - 0.10),
                     MAT["glow_strip"], C("WORK"), rot=F.r(fr)))
    for s in (-1, 1):
        parts.append(cyl(name + "_sp%d" % s, 0.05, 0.7,
                         F.p(lx + s * w * 0.42, ly + depth * 0.85, lz - 0.35),
                         MAT["steel_lt"], C("WORK"), verts=6))


def roof_plant(parts, name, F, lx, ly, lz, w=2.0, d=2.0, h=0.8, units=2):
    """Rooftop mechanical clutter - what separates a box from a building."""
    parts.append(box(name + "_pad", (w * 1.15, d * 1.15, 0.10),
                     F.p(lx, ly, lz + 0.05), MAT["steel"], C("WORK")))
    for i in range(units):
        ox = (i - (units - 1) * 0.5) * w * 0.48
        parts.append(box(name + "_u%d" % i, (w * 0.40, d * 0.66, h),
                         F.p(lx + ox, ly, lz + 0.10 + h * 0.5), MAT["steel_lt"],
                         C("WORK")))
        parts.append(cyl(name + "_f%d" % i, w * 0.15, 0.10,
                         F.p(lx + ox, ly, lz + 0.10 + h + 0.05),
                         MAT["steel"], C("WORK"), verts=12))
    parts.append(cyl(name + "_vent", 0.10, 1.2,
                     F.p(lx, ly - d * 0.30, lz + 0.7), MAT["alu"],
                     C("WORK"), verts=8))
    parts.append(cyl(name + "_ant", 0.03, 2.2,
                     F.p(lx - w * 0.4, ly + d * 0.3, lz + 1.2), MAT["titanium"],
                     C("WORK"), verts=5))
    parts.append(sphere(name + "_bea", 0.09,
                        F.p(lx - w * 0.4, ly + d * 0.3, lz + 2.34),
                        MAT["emit_amber"], C("WORK"), seg=8, rings=5))


def pipe_run(parts, name, F, pts, r=0.11, mat=None, sides=7, brackets=3):
    mat = mat or MAT["steel_lt"]
    wp = [F.p(*p) for p in pts]
    loft_path(name, wp, [r] * len(wp), mat, C("WORK"), sides=sides)
    n = len(pts) - 1
    for i in range(1, n):
        p = pts[i]
        parts.append(cyl(name + "_br%d" % i, r * 1.5, 0.16,
                         F.p(p[0], p[1], p[2]), MAT["steel"], C("WORK"),
                         verts=8))


def railing(parts, name, F, pts, h=1.0, mat=None):
    mat = mat or MAT["steel_lt"]
    wp = [F.p(*p) for p in pts]
    for i in range(len(wp) - 1):
        tube_between(name + "_rl%d" % i, (wp[i][0], wp[i][1], wp[i][2] + h),
                     (wp[i + 1][0], wp[i + 1][1], wp[i + 1][2] + h),
                     0.035, 0.035, mat, C("WORK"), sides=5)
    for i, p in enumerate(pts):
        parts.append(cyl(name + "_p%d" % i, 0.032, h,
                         F.p(p[0], p[1], p[2] + h * 0.5), mat, C("WORK"),
                         verts=5))


def ladder(parts, name, F, lx, ly, lz, h=4.0, mat=None):
    mat = mat or MAT["steel_lt"]
    for s in (-1, 1):
        parts.append(cyl(name + "_s%d" % s, 0.035, h,
                         F.p(lx + s * 0.22, ly, lz + h * 0.5), mat, C("WORK"),
                         verts=5))
    n = max(2, int(h / 0.34))
    for i in range(n):
        parts.append(cyl(name + "_r%d" % i, 0.026, 0.44,
                         F.p(lx, ly, lz + 0.3 + i * (h - 0.4) / n), mat,
                         C("WORK"), rot=(0, math.pi * 0.5, 0), verts=5))


def cable_bundle(parts, name, F, p0, p1, sag=0.45, mat=None):
    mat = mat or MAT["rubber"]
    a, b = Vector(F.p(*p0)), Vector(F.p(*p1))
    mid = (a + b) * 0.5
    mid.z -= sag
    pts = [a.lerp(mid, t) for t in (0.0, 0.5)] + [mid] + \
          [mid.lerp(b, t) for t in (0.5, 1.0)]
    loft_path(name, pts, [0.045] * len(pts), mat, C("WORK"), sides=5)


# ---------------------------------------------------------------- interior
def furn_bed(parts, name, F, lx, ly, lz, w=1.5, l=2.0, rot=0.0, mat=None):
    mat = mat or MAT["fabric_blue"]
    parts.append(box(name + "_fr", (w, l, 0.34),
                     F.p(lx, ly, lz + 0.17), MAT["wood"], C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_mt", (w * 0.94, l * 0.94, 0.20),
                     F.p(lx, ly, lz + 0.42), mat, C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_pl", (w * 0.70, l * 0.20, 0.12),
                     F.p(lx, ly - l * 0.34, lz + 0.56), MAT["fabric_grey"],
                     C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_hd", (w, 0.10, 0.62),
                     F.p(lx, ly + l * 0.5, lz + 0.62), MAT["wood"], C("WORK"),
                     rot=F.r(rot)))


def furn_sofa(parts, name, F, lx, ly, lz, w=2.0, d=0.85, rot=0.0, mat=None):
    mat = mat or MAT["fabric_grey"]
    parts.append(box(name + "_b", (w, d, 0.40), F.p(lx, ly, lz + 0.20), mat,
                     C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_bk", (w, 0.20, 0.72),
                     F.p(lx, ly + d * 0.40, lz + 0.52), mat, C("WORK"),
                     rot=F.r(rot)))
    for s in (-1, 1):
        parts.append(box(name + "_a%d" % s, (0.18, d, 0.56),
                         F.p(lx + s * w * 0.5, ly, lz + 0.44), mat, C("WORK"),
                         rot=F.r(rot)))


def furn_table(parts, name, F, lx, ly, lz, w=1.4, d=0.8, h=0.74, rot=0.0,
               mat=None):
    mat = mat or MAT["wood_lt"]
    parts.append(box(name + "_t", (w, d, 0.07), F.p(lx, ly, lz + h), mat,
                     C("WORK"), rot=F.r(rot)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + "_l%d%d" % (sx, sy), 0.035, h,
                             F.p(lx + sx * w * 0.42, ly + sy * d * 0.38,
                                 lz + h * 0.5), MAT["steel"], C("WORK"),
                             verts=5))


def furn_chair(parts, name, F, lx, ly, lz, rot=0.0, mat=None):
    mat = mat or MAT["fabric_blue"]
    parts.append(box(name + "_s", (0.42, 0.42, 0.06),
                     F.p(lx, ly, lz + 0.44), mat, C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_bk", (0.42, 0.06, 0.48),
                     F.p(lx, ly + 0.18, lz + 0.68), mat, C("WORK"), rot=F.r(rot)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + "_l%d%d" % (sx, sy), 0.022, 0.44,
                             F.p(lx + sx * 0.16, ly + sy * 0.16, lz + 0.22),
                             MAT["steel"], C("WORK"), verts=4))


def furn_counter(parts, name, F, lx, ly, lz, w=2.4, d=0.7, h=1.0, rot=0.0,
                 mat=None):
    mat = mat or MAT["wood"]
    parts.append(box(name + "_b", (w, d, h), F.p(lx, ly, lz + h * 0.5), mat,
                     C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_top", (w * 1.04, d * 1.08, 0.07),
                     F.p(lx, ly, lz + h + 0.03), MAT["titanium"], C("WORK"),
                     rot=F.r(rot)))
    parts.append(box(name + "_lit", (w * 0.9, 0.06, 0.08),
                     F.p(lx, ly - d * 0.52, lz + h - 0.14),
                     MAT["glow_strip"], C("WORK"), rot=F.r(rot)))


def furn_shelf(parts, name, F, lx, ly, lz, w=2.0, h=1.9, d=0.4, rot=0.0,
               rows=4, mat=None):
    mat = mat or MAT["steel_lt"]
    for s in (-1, 1):
        parts.append(box(name + "_s%d" % s, (0.05, d, h),
                         F.p(lx + s * w * 0.5, ly, lz + h * 0.5), mat,
                         C("WORK"), rot=F.r(rot)))
    for r in range(rows):
        parts.append(box(name + "_r%d" % r, (w, d, 0.04),
                         F.p(lx, ly, lz + 0.16 + r * (h - 0.2) / max(1, rows - 1)),
                         mat, C("WORK"), rot=F.r(rot)))
    # merchandise blocks
    for r in range(min(rows, 3)):
        for k in range(3):
            parts.append(box(name + "_m%d%d" % (r, k), (w * 0.22, d * 0.55,
                             (h - 0.2) / max(1, rows - 1) * 0.55),
                             F.p(lx - w * 0.28 + k * w * 0.28, ly,
                                 lz + 0.26 + r * (h - 0.2) / max(1, rows - 1)),
                             MAT["ceramic"] if (r + k) % 2 else MAT["fabric_red"],
                             C("WORK"), rot=F.r(rot)))


def furn_screen(parts, name, F, lx, ly, lz, w=1.6, h=0.95, rot=0.0):
    parts.append(box(name + "_b", (w, 0.10, h), F.p(lx, ly, lz + h * 0.5),
                     MAT["navy"], C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_f", (w * 0.92, 0.04, h * 0.86),
                     F.p(lx, ly - 0.07, lz + h * 0.5), MAT["emit_screen"],
                     C("WORK"), rot=F.r(rot)))
    parts.append(cyl(name + "_st", 0.04, 0.35, F.p(lx, ly, lz + 0.17),
                     MAT["steel"], C("WORK"), verts=5))


def furn_plant(parts, name, F, lx, ly, lz, s=1.0, rot=0.0):
    parts.append(cyl(name + "_pot", 0.24 * s, 0.34 * s,
                     F.p(lx, ly, lz + 0.17 * s), MAT["ceramic"], C("WORK"),
                     verts=10))
    for i in range(4):
        a = i * math.pi * 0.5 + rot
        parts.append(ico(name + "_lf%d" % i, 0.26 * s,
                         F.p(lx + math.cos(a) * 0.10 * s,
                             ly + math.sin(a) * 0.10 * s, lz + (0.52 + 0.10 * i) * s),
                         MAT["plant"] if i % 2 else MAT["plant_dk"], C("WORK"),
                         sub=1, scale=(0.8, 0.8, 1.35)))


def furn_lamp(parts, name, F, lx, ly, lz, h=2.2):
    parts.append(cyl(name + "_p", 0.045, h, F.p(lx, ly, lz + h * 0.5),
                     MAT["steel"], C("WORK"), verts=6))
    parts.append(cone(name + "_s", 0.26, 0.10, 0.22,
                      F.p(lx, ly, lz + h - 0.10), MAT["titanium"], C("WORK"),
                      verts=10))
    parts.append(sphere(name + "_b", 0.10, F.p(lx, ly, lz + h - 0.24),
                        MAT["emit_warm"], C("WORK"), seg=8, rings=5))


def furn_rug(parts, name, F, lx, ly, lz, w=2.4, d=1.6, rot=0.0):
    parts.append(box(name + "_r", (w, d, 0.03), F.p(lx, ly, lz + 0.015),
                     MAT["fabric_red"], C("WORK"), rot=F.r(rot)))


# ---------------------------------------------------------------- props
def prop_crate(parts, name, F, lx, ly, lz, s=0.7, rot=0.0, mat=None):
    mat = mat or MAT["wood_lt"]
    parts.append(box(name + "_b", (s, s, s), F.p(lx, ly, lz + s * 0.5), mat,
                     C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_st", (s * 1.02, 0.05, s * 0.14),
                     F.p(lx, ly - s * 0.5, lz + s * 0.5), MAT["steel"],
                     C("WORK"), rot=F.r(rot)))


def prop_barrel(parts, name, F, lx, ly, lz, r=0.32, h=0.9, mat=None):
    mat = mat or MAT["paint_safe"]
    parts.append(cyl(name + "_b", r, h, F.p(lx, ly, lz + h * 0.5), mat,
                     C("WORK"), verts=12))
    for k in (-1, 1):
        parts.append(torus(name + "_r%d" % k, r * 1.02, 0.035,
                           F.p(lx, ly, lz + h * 0.5 + k * h * 0.28),
                           MAT["steel"], C("WORK"), mseg=12, nseg=4))


def prop_bench(parts, name, F, lx, ly, lz, w=1.8, rot=0.0):
    parts.append(box(name + "_s", (w, 0.44, 0.07),
                     F.p(lx, ly, lz + 0.45), MAT["wood_lt"], C("WORK"),
                     rot=F.r(rot)))
    parts.append(box(name + "_bk", (w, 0.07, 0.40),
                     F.p(lx, ly + 0.18, lz + 0.66), MAT["wood_lt"], C("WORK"),
                     rot=F.r(rot)))
    for s in (-1, 1):
        parts.append(box(name + "_l%d" % s, (0.07, 0.38, 0.45),
                         F.p(lx + s * w * 0.42, ly, lz + 0.22),
                         MAT["steel"], C("WORK"), rot=F.r(rot)))


def prop_lamp_post(parts, name, F, lx, ly, lz, h=4.2):
    parts.append(cyl(name + "_b", 0.16, 0.30, F.p(lx, ly, lz + 0.15),
                     MAT["concrete"], C("WORK"), verts=8))
    parts.append(cyl(name + "_p", 0.075, h, F.p(lx, ly, lz + h * 0.5),
                     MAT["steel_lt"], C("WORK"), verts=7))
    parts.append(box(name + "_a", (0.7, 0.10, 0.10),
                     F.p(lx + 0.30, ly, lz + h), MAT["steel_lt"], C("WORK")))
    parts.append(box(name + "_l", (0.34, 0.16, 0.09),
                     F.p(lx + 0.50, ly, lz + h - 0.10), MAT["emit_warm"],
                     C("WORK")))


def prop_kiosk(parts, name, F, lx, ly, lz, w=1.6, d=1.2, rot=0.0):
    parts.append(box(name + "_b", (w, d, 0.9), F.p(lx, ly, lz + 0.45),
                     MAT["composite"], C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_sc", (w * 0.8, 0.05, 0.55),
                     F.p(lx, ly - d * 0.5, lz + 0.70), MAT["emit_screen"],
                     C("WORK"), rot=F.r(rot)))
    parts.append(box(name + "_tp", (w * 1.1, d * 1.1, 0.08),
                     F.p(lx, ly, lz + 0.94), MAT["titanium"], C("WORK"),
                     rot=F.r(rot)))


def prop_bin(parts, name, F, lx, ly, lz, r=0.28, h=0.8):
    parts.append(cyl(name + "_b", r, h, F.p(lx, ly, lz + h * 0.5),
                     MAT["steel"], C("WORK"), verts=10))
    parts.append(cyl(name + "_l", r * 0.9, 0.10, F.p(lx, ly, lz + h + 0.05),
                     MAT["paint_safe"], C("WORK"), verts=10))


def prop_tank(parts, name, F, lx, ly, lz, r=1.1, h=3.0, mat=None):
    mat = mat or MAT["alu"]
    parts.append(cyl(name + "_b", r, h, F.p(lx, ly, lz + h * 0.5), mat,
                     C("WORK"), verts=16))
    parts.append(sphere(name + "_d", r * 1.01, F.p(lx, ly, lz + h),
                        MAT["steel_lt"], C("WORK"), seg=16, rings=7,
                        scale=(1.0, 1.0, 0.40)))
    for k in (-1, 1):
        parts.append(torus(name + "_rb%d" % k, r * 1.02, 0.05,
                           F.p(lx, ly, lz + h * 0.5 + k * h * 0.30),
                           MAT["steel"], C("WORK"), mseg=16, nseg=4))
    parts.append(cyl(name + "_p", 0.10, 1.2, F.p(lx + r * 0.7, ly, lz + h * 0.9),
                     MAT["steel_lt"], C("WORK"), verts=6))


def prop_valve(parts, name, F, lx, ly, lz, rot=0.0):
    parts.append(torus(name + "_w", 0.22, 0.05, F.p(lx, ly, lz), MAT["paint_safe"],
                       C("WORK"), rot=(math.pi * 0.5, 0, F.rot + rot),
                       mseg=12, nseg=4))
    parts.append(cyl(name + "_s", 0.05, 0.30, F.p(lx, ly, lz), MAT["steel"],
                     C("WORK"), rot=(0, math.pi * 0.5, F.rot + rot), verts=6))
