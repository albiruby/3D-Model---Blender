"""
island_arch.py : construction kit + parametric tropical architecture.

Local convention for every building: footprint centred on the origin, front
faces -Y, ground at z = 0.  place() applies the world transform afterwards.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- transforms
def xform(ob, M):
    """Bake the object's own transform plus M into the mesh, then clear it."""
    B = ob.matrix_basis.copy()
    me = ob.data
    for v in me.vertices:
        v.co = M @ (B @ v.co)
    ob.matrix_basis = Matrix.Identity(4)
    return ob


def face_matrix(cx, cy, yaw_deg, z, u=0.0, inset=0.0):
    """Matrix for an element on a wall face: local -Y is outward."""
    return (Matrix.Translation(Vector((cx, cy, z)))
            @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")
            @ Matrix.Translation(Vector((u, -inset, 0.0))))


FACE_YAW = {"S": 0.0, "N": 180.0, "E": 90.0, "W": -90.0}


def wall_point(w, d, face, u, z, inset=0.0):
    if face == "S":
        return (u, -d * 0.5 + inset, z), FACE_YAW["S"]
    if face == "N":
        return (u, d * 0.5 - inset, z), FACE_YAW["N"]
    if face == "E":
        return (w * 0.5 - inset, u, z), FACE_YAW["E"]
    return (-w * 0.5 + inset, u, z), FACE_YAW["W"]


# ---------------------------------------------------------------- openings
def window_unit(parts, prefix, M, ww=1.15, wh=1.30, shutters=False,
                mullion=True, curtain=False, sill=True, frame_mat=None,
                glass_mat=None):
    fm = frame_mat or MAT["paint_w"]
    gm = glass_mat or MAT["glass_dark"]
    t = 0.085
    # recessed dark interior behind the glass
    parts.append(xform(box(prefix + "_rec", (ww, 0.30, wh), (0, 0.16, 0),
                           MAT["wood_dark"], C("WORK")), M))
    parts.append(xform(box(prefix + "_gl", (ww - 0.10, 0.03, wh - 0.10), (0, 0.01, 0),
                           gm, C("WORK")), M))
    if curtain:
        parts.append(xform(box(prefix + "_cu", (ww * 0.34, 0.03, wh - 0.16),
                               (-ww * 0.30, -0.02, 0.02), MAT["fabric_w"], C("WORK")), M))
    parts.append(xform(box(prefix + "_ft", (ww + t, 0.13, t), (0, -0.02, wh * 0.5),
                           fm, C("WORK")), M))
    parts.append(xform(box(prefix + "_fb", (ww + t, 0.13, t), (0, -0.02, -wh * 0.5),
                           fm, C("WORK")), M))
    parts.append(xform(box(prefix + "_fl", (t, 0.13, wh), (-ww * 0.5, -0.02, 0),
                           fm, C("WORK")), M))
    parts.append(xform(box(prefix + "_fr", (t, 0.13, wh), (ww * 0.5, -0.02, 0),
                           fm, C("WORK")), M))
    if mullion:
        parts.append(xform(box(prefix + "_mu", (0.05, 0.09, wh - 0.06), (0, -0.03, 0),
                               fm, C("WORK")), M))
    if sill:
        parts.append(xform(box(prefix + "_si", (ww + 0.24, 0.26, 0.07),
                               (0, -0.10, -wh * 0.5 - 0.04), MAT["concrete"], C("WORK")), M))
    if shutters:
        sw = ww * 0.52
        for sgn in (-1, 1):
            parts.append(xform(box(prefix + "_sh%d" % sgn, (sw, 0.05, wh),
                                   (sgn * (ww * 0.5 + sw * 0.52), -0.10, 0),
                                   MAT["paint_teal"], C("WORK")), M))


def door_unit(parts, prefix, M, dw=0.95, dh=2.05, double=False, open_=False):
    fm = MAT["paint_w"]
    parts.append(xform(box(prefix + "_rec", (dw, 0.26, dh), (0, 0.14, 0),
                           MAT["wood_dark"], C("WORK")), M))
    if double:
        parts.append(xform(box(prefix + "_p1", (dw * 0.46, 0.06, dh - 0.14),
                               (-dw * 0.24, 0.0, -0.03), MAT["wood"], C("WORK")), M))
        parts.append(xform(box(prefix + "_p2", (dw * 0.46, 0.06, dh - 0.14),
                               (dw * 0.24, 0.0, -0.03), MAT["wood"], C("WORK")), M))
        for sgn in (-1, 1):
            parts.append(xform(cyl(prefix + "_h%d" % sgn, 0.030, 0.16,
                                   (sgn * 0.10, -0.05, 0.02), MAT["metal"], C("WORK"),
                                   rot=(math.radians(90), 0, 0), verts=6), M))
    else:
        parts.append(xform(box(prefix + "_p", (dw - 0.12, 0.06, dh - 0.14),
                               (0, 0.0, -0.03), MAT["wood"], C("WORK")), M))
        parts.append(xform(cyl(prefix + "_h", 0.030, 0.16, (dw * 0.32, -0.06, 0.0),
                               MAT["metal"], C("WORK"), rot=(math.radians(90), 0, 0),
                               verts=6), M))
    parts.append(xform(box(prefix + "_ft", (dw + 0.20, 0.14, 0.09), (0, -0.02, dh * 0.5),
                           fm, C("WORK")), M))
    parts.append(xform(box(prefix + "_fl", (0.09, 0.14, dh), (-dw * 0.5, -0.02, 0),
                           fm, C("WORK")), M))
    parts.append(xform(box(prefix + "_fr", (0.09, 0.14, dh), (dw * 0.5, -0.02, 0),
                           fm, C("WORK")), M))


def step_unit(parts, prefix, M, width=1.4, n=2, rise=0.18, run=0.30):
    for i in range(n):
        parts.append(xform(box(prefix + "_st%d" % i, (width, run, rise * (i + 1)),
                               (0, -run * (i + 0.5), -rise * (i + 1) * 0.5),
                               MAT["concrete"], C("WORK")), M))


def lamp_unit(parts, prefix, M, z=2.6, arm=0.35):
    parts.append(xform(box(prefix + "_arm", (0.06, arm, 0.06), (0, -arm * 0.5, z),
                           MAT["metal_dark"], C("WORK")), M))
    parts.append(xform(cone(prefix + "_shade", 0.16, 0.07, 0.18,
                            (0, -arm, z - 0.11), MAT["metal_dark"], C("WORK"), verts=10), M))
    parts.append(xform(sphere(prefix + "_bulb", 0.075, (0, -arm, z - 0.20),
                              MAT["glow"], C("WORK"), seg=8, rings=5), M))


def railing_unit(parts, prefix, p0, p1, z0, height=1.0, mat=None, posts=4):
    mat = mat or MAT["wood_light"]
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ln = d.length
    if ln < 1e-4:
        return
    n = max(2, int(posts))
    for i in range(n + 1):
        p = p0 + d * (i / float(n))
        parts.append(box(prefix + "_p%d" % i, (0.07, 0.07, height),
                         (p.x, p.y, z0 + height * 0.5), mat, C("WORK")))
    for zz, th in ((height, 0.08), (height * 0.52, 0.05)):
        b = box(prefix + "_r%.2f" % zz, (0.06, ln, th),
                ((p0.x + p1.x) * 0.5, (p0.y + p1.y) * 0.5, z0 + zz), mat, C("WORK"))
        align_z(b, (0, 0, 1))
        b.rotation_euler = (0, 0, math.atan2(d.y, d.x) - math.pi / 2)
        parts.append(b)


# ---------------------------------------------------------------- roofs
def roof_gable(parts, prefix, w, d, z0, rise=1.5, ov=0.45, mat=None,
               thick=0.16, battens=7, ridge=True, wall_m=None):
    mat = mat or MAT["roof_terra"]
    wall_m = wall_m or MAT["paint_w"]
    half = d * 0.5 + ov
    slope = math.hypot(half, rise)
    ang = math.atan2(rise, half)
    for sgn in (-1, 1):
        ob = box(prefix + "_sl%d" % sgn, (w + 2 * ov, slope, thick), (0, 0, 0), mat, C("WORK"))
        ob.rotation_euler = (-sgn * ang, 0, 0)
        ob.location = (0, sgn * half * 0.5, z0 + rise * 0.5 - 0.02)
        parts.append(ob)
        # eave fascia
        parts.append(box(prefix + "_fa%d" % sgn, (w + 2 * ov, 0.10, 0.20),
                         (0, sgn * half, z0 - 0.06 + rise * 0.0), MAT["wood_dark"], C("WORK")))
    # gable end walls (triangles)
    for sgn in (-1, 1):
        bm = bmesh.new()
        x = sgn * w * 0.5
        a0 = bm.verts.new((x, -d * 0.5, z0))
        a1 = bm.verts.new((x, d * 0.5, z0))
        a2 = bm.verts.new((x, 0, z0 + rise))
        b0 = bm.verts.new((x - sgn * 0.18, -d * 0.5, z0))
        b1 = bm.verts.new((x - sgn * 0.18, d * 0.5, z0))
        b2 = bm.verts.new((x - sgn * 0.18, 0, z0 + rise))
        bm.faces.new((a0, a1, a2))
        bm.faces.new((b2, b1, b0))
        bm.faces.new((a0, a2, b2, b0))
        bm.faces.new((a1, b1, b2, a2))
        bm.faces.new((a0, b0, b1, a1))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(prefix + "_gw%d" % sgn)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(wall_m)
        ob = bpy.data.objects.new(prefix + "_gw%d" % sgn, me)
        C("WORK").objects.link(ob)
        parts.append(ob)
    if ridge:
        parts.append(box(prefix + "_ridge", (w + 2 * ov + 0.1, 0.20, 0.16),
                         (0, 0, z0 + rise + 0.04), MAT["roof_metal"], C("WORK")))
    if battens:
        for i in range(battens):
            t = (i + 0.5) / battens
            for sgn in (-1, 1):
                yy = sgn * half * (1 - t)
                zz = z0 + rise * t + 0.10
                ob = box(prefix + "_bt%d_%d" % (sgn, i), (w + 2 * ov * 0.96, 0.055, 0.055),
                         (0, yy, zz), MAT["roof_metal"], C("WORK"))
                ob.rotation_euler = (-sgn * ang, 0, 0)
                parts.append(ob)


def roof_hip(parts, prefix, w, d, z0, rise=1.6, ov=0.55, mat=None, nseg=26,
             ridge_frac=0.45, wave=0.0, seed=0):
    mat = mat or MAT["roof_thatch"]
    rng = random.Random(seed)
    hw, hd = w * 0.5 + ov, d * 0.5 + ov
    ring0, ring1 = [], []
    per = 2 * (hw + hd)
    for i in range(nseg):
        t = i / float(nseg) * per
        if t < 2 * hw:
            x, y = -hw + t, -hd
        elif t < 2 * hw + 2 * hd:
            x, y = hw, -hd + (t - 2 * hw)
        elif t < 4 * hw + 2 * hd:
            x, y = hw - (t - 2 * hw - 2 * hd), hd
        else:
            x, y = -hw, hd - (t - 4 * hw - 2 * hd)
        k = 1.0 + (rng.uniform(-wave, wave) if wave else 0.0)
        ring0.append((x * k, y * k, z0 - 0.10))
        rx = max(0.05, (hw - hd) * ridge_frac + hw * 0.18)
        ring1.append((clamp(x, -rx, rx), 0.0, z0 + rise))
    parts.append(loft(prefix + "_roof", [ring0, ring1], mat, C("WORK")))
    # eave trim
    parts.append(box(prefix + "_eavef", (w + 2 * ov, 0.09, 0.14),
                     (0, -(d * 0.5 + ov), z0 - 0.14), MAT["wood_dark"], C("WORK")))
    parts.append(box(prefix + "_eaveb", (w + 2 * ov, 0.09, 0.14),
                     (0, (d * 0.5 + ov), z0 - 0.14), MAT["wood_dark"], C("WORK")))
    if wave:
        # shaggy thatch fringe
        for i in range(18):
            a = i * TAU / 18
            parts.append(cone(prefix + "_fr%d" % i, 0.16, 0.02, 0.55,
                              (math.cos(a) * (hw - 0.1), math.sin(a) * (hd - 0.1),
                               z0 - 0.42), MAT["roof_thatch"], C("WORK"),
                              verts=5, smooth=False))


def roof_flat(parts, prefix, w, d, z0, parapet=0.42, mat=None):
    mat = mat or MAT["concrete"]
    parts.append(box(prefix + "_deck", (w, d, 0.16), (0, 0, z0 - 0.02), MAT["concrete_dark"], C("WORK")))
    for sx in (-1, 1):
        parts.append(box(prefix + "_pp%d" % sx, (0.16, d, parapet),
                         (sx * (w * 0.5 - 0.08), 0, z0 + parapet * 0.5), mat, C("WORK")))
    for sy in (-1, 1):
        parts.append(box(prefix + "_pq%d" % sy, (w, 0.16, parapet),
                         (0, sy * (d * 0.5 - 0.08), z0 + parapet * 0.5), mat, C("WORK")))


# ---------------------------------------------------------------- walls / shells
def wall_shell(parts, prefix, w, d, h, z0, mat, thick=0.16):
    parts.append(box(prefix + "_wf", (w, thick, h), (0, -d * 0.5 + thick * 0.5, z0 + h * 0.5),
                     mat, C("WORK")))
    parts.append(box(prefix + "_wb", (w, thick, h), (0, d * 0.5 - thick * 0.5, z0 + h * 0.5),
                     mat, C("WORK")))
    parts.append(box(prefix + "_wl", (thick, d - thick * 2, h),
                     (-w * 0.5 + thick * 0.5, 0, z0 + h * 0.5), mat, C("WORK")))
    parts.append(box(prefix + "_wr", (thick, d - thick * 2, h),
                     (w * 0.5 - thick * 0.5, 0, z0 + h * 0.5), mat, C("WORK")))
    # dark interior so windows read as depth
    parts.append(box(prefix + "_in", (w - thick * 2.6, d - thick * 2.6, h - 0.1),
                     (0, 0, z0 + h * 0.5), MAT["interior"], C("WORK")))
    parts.append(box(prefix + "_floor", (w + 0.12, d + 0.12, 0.20),
                     (0, 0, z0 - 0.08), MAT["concrete_dark"], C("WORK")))


def posts(parts, prefix, w, d, z0, h, mat=None, inset=0.10, size=0.16):
    mat = mat or MAT["wood_dark"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(box(prefix + "_po%d%d" % (sx, sy), (size, size, h),
                             (sx * (w * 0.5 - inset), sy * (d * 0.5 - inset),
                              z0 + h * 0.5), mat, C("WORK")))


def awning(parts, prefix, w, d, z, mat=None, drop=0.35, cy=0.0):
    mat = mat or MAT["fabric_coral"]
    ob = box(prefix + "_aw", (w, d, 0.06), (0, cy, z), mat, C("WORK"))
    ob.rotation_euler = (math.radians(-18), 0, 0)
    parts.append(ob)
    parts.append(box(prefix + "_awf", (w, 0.05, drop), (0, cy - d * 0.5, z - drop * 0.55),
                     mat, C("WORK")))


def sign_board(parts, prefix, M, text_w=1.3, text_h=0.36, z=2.9, mat=None):
    mat = mat or MAT["paint_yellow"]
    parts.append(xform(box(prefix + "_sgn", (text_w, 0.07, text_h), (0, -0.06, z),
                           mat, C("WORK")), M))
    # border frame + two text bars: reads as signage at any distance
    for sx in (-1, 1):
        parts.append(xform(box(prefix + "_sb%d" % sx, (0.06, 0.09, text_h),
                               (sx * (text_w * 0.5 - 0.05), -0.08, z),
                               MAT["wood_dark"], C("WORK")), M))
    parts.append(xform(box(prefix + "_st", (text_w, 0.09, 0.05), (0, -0.08, z + text_h * 0.5),
                           MAT["wood_dark"], C("WORK")), M))
    parts.append(xform(box(prefix + "_sbo", (text_w, 0.09, 0.05), (0, -0.08, z - text_h * 0.5),
                           MAT["wood_dark"], C("WORK")), M))
    parts.append(xform(box(prefix + "_tx", (text_w * 0.62, 0.02, text_h * 0.30),
                           (-text_w * 0.06, -0.11, z + text_h * 0.10),
                           MAT["wood_dark"], C("WORK")), M))
    parts.append(xform(box(prefix + "_ty", (text_w * 0.40, 0.02, text_h * 0.20),
                           (-text_w * 0.17, -0.11, z - text_h * 0.20),
                           MAT["wood_dark"], C("WORK")), M))


# ---------------------------------------------------------------- archetypes
PAL_WALLS = ["paint_w", "paint_mint", "paint_yellow", "paint_coral",
             "wood_light", "paint_blue"]


def house_coastal(name, w=6.4, d=5.2, h=2.9, wall=None, roof=None, seed=0,
                  shutters=True, veranda=1.9, storeys=1):
    rng = random.Random(seed * 31 + 7)
    coll = C("WORK")
    parts = []
    wall_m = wall or MAT[rng.choice(PAL_WALLS)]
    roof_m = roof or (MAT["roof_terra"] if rng.random() < 0.65 else MAT["roof_metal"])
    z0 = 0.32
    # foundation + steps
    parts.append(box(name + "_found", (w + 0.5, d + 0.5, z0), (0, 0, z0 * 0.5),
                     MAT["stone"], coll))
    wall_shell(parts, name, w, d, h, z0, wall_m)
    # veranda deck at the front
    parts.append(box(name + "_deck", (w, veranda, 0.16), (0, -(d * 0.5 + veranda * 0.5), z0 - 0.02),
                     MAT["wood"], coll))
    posts(parts, name + "_vp", w, veranda + 0.1, z0, h - 0.20, MAT["wood_dark"], inset=0.16)
    # veranda roof: a lean-to attached under the main eave
    vr = box(name + "_vroof", (w + 0.9, veranda + 0.55, 0.13),
             (0, -(d * 0.5 + (veranda + 0.55) * 0.5), z0 + h - 0.18), roof_m, coll,
             rot=(math.radians(-7), 0, 0))
    parts.append(vr)
    parts.append(box(name + "_vbeam", (w + 0.9, 0.12, 0.14),
                     (0, -(d * 0.5 + veranda + 0.45), z0 + h - 0.30), MAT["wood_dark"], coll))
    railing_unit(parts, name + "_rail", (-w * 0.5 + 0.12, -(d * 0.5 + veranda - 0.08), z0),
                 (w * 0.5 - 0.12, -(d * 0.5 + veranda - 0.08), z0), z0 - 0.02, 0.95,
                 MAT["wood_light"], posts=int(w / 0.8))
    # door + steps
    M, _ = wall_point(w, d, "S", 0.0, z0)
    door_unit(parts, name + "_door", Matrix.Translation(Vector((0, -d * 0.5, z0))), double=False)
    step_unit(parts, name + "_step", Matrix.Translation(Vector((0, -(d * 0.5 + veranda), 0.30))),
              width=1.7, n=2)
    # windows front + sides
    for i, u in enumerate((-w * 0.30, w * 0.30)):
        M = Matrix.Translation(Vector((u, -d * 0.5, z0 + 1.55)))
        window_unit(parts, name + "_wf%d" % i, M, shutters=shutters)
    for face in ("E", "W"):
        for i, u in enumerate((-d * 0.18, d * 0.18)):
            p, yaw = wall_point(w, d, face, u, z0 + 1.55)
            window_unit(parts, name + "_w%s%d" % (face, i), face_matrix(p[0], p[1], yaw, p[2]),
                        ww=1.0, wh=1.15)
    # back window
    p, yaw = wall_point(w, d, "N", 0.0, z0 + 1.55)
    window_unit(parts, name + "_wn", face_matrix(p[0], p[1], yaw, p[2]), ww=1.1, wh=1.15)
    lamp_unit(parts, name + "_lamp", Matrix.Translation(Vector((0.95, -d * 0.5, 0))), 2.35)
    roof_gable(parts, name, w, d, z0 + h, rise=1.55, ov=0.5, mat=roof_m, battens=8)
    # small chimney / vent
    parts.append(box(name + "_vent", (0.34, 0.34, 0.7), (w * 0.28, d * 0.10, z0 + h + 0.7),
                     MAT["stone"], coll))
    return make_master(name, parts, bevel=0.014, weighted=True)


def house_stilt(name, w=5.4, d=5.0, h=2.7, lift=1.35, wall=None, roof=None, seed=0):
    rng = random.Random(seed * 57 + 3)
    coll = C("WORK")
    parts = []
    wall_m = wall or MAT[rng.choice(["wood_light", "paint_w", "paint_mint", "wood"])]
    roof_m = roof or MAT["roof_thatch"]
    # stilts
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + "_st%d%d" % (sx, sy), 0.15, lift,
                             (sx * (w * 0.5 - 0.45), sy * (d * 0.5 - 0.45), lift * 0.5),
                             MAT["wood_dark"], coll, verts=8))
    parts.append(box(name + "_deck", (w + 0.4, d + 0.4, 0.18), (0, 0, lift), MAT["wood"], coll))
    wall_shell(parts, name, w, d, h, lift + 0.09, wall_m, thick=0.13)
    # front veranda + railing
    parts.append(box(name + "_vdeck", (w - 0.4, 1.5, 0.14),
                     (0, -(d * 0.5 + 0.75), lift), MAT["wood"], coll))
    railing_unit(parts, name + "_vr", (-w * 0.5 + 0.3, -(d * 0.5 + 1.45), lift),
                 (w * 0.5 - 0.3, -(d * 0.5 + 1.45), lift), lift + 0.06, 0.9,
                 MAT["wood_light"], posts=int(w / 0.85))
    for sgn in (-1, 1):
        railing_unit(parts, name + "_vs%d" % sgn, (sgn * (w * 0.5 - 0.3), -(d * 0.5 + 1.45), lift),
                     (sgn * (w * 0.5 - 0.3), -d * 0.5, lift), lift + 0.06, 0.9,
                     MAT["wood_light"], posts=2)
    # stairs
    M = Matrix.Translation(Vector((-w * 0.5 + 0.2, -(d * 0.5 + 1.6), 0)))
    for i in range(5):
        parts.append(box(name + "_stp%d" % i, (1.0, 0.34, 0.16),
                         (-w * 0.5 + 0.2, -(d * 0.5 + 1.2 - i * 0.30),
                          lift * (i + 1) / 5.0), MAT["wood_light"], coll))
    door_unit(parts, name + "_door", Matrix.Translation(Vector((-w * 0.5 + 1.4, -d * 0.5, lift + 0.09))))
    for i, u in enumerate((w * 0.18,)):
        window_unit(parts, name + "_wf%d" % i,
                    Matrix.Translation(Vector((u, -d * 0.5, lift + 1.55))), ww=1.0, wh=1.1,
                    shutters=True)
    p, yaw = wall_point(w, d, "E", 0.0, lift + 1.55)
    window_unit(parts, name + "_we", face_matrix(p[0], p[1], yaw, p[2]), ww=0.95, wh=1.1)
    # rear elevation: window + service door
    p, yaw = wall_point(w, d, "N", -w * 0.18, lift + 1.55)
    window_unit(parts, name + "_wn", face_matrix(p[0], p[1], yaw, p[2]), ww=0.9, wh=1.05)
    p, yaw = wall_point(w, d, "N", w * 0.26, lift + 1.05)
    parts.append(xform(box(name + "_bd", (0.78, 0.10, 1.85), (0, -0.02, 0),
                           MAT["wood_dark"], C("WORK")),
                       face_matrix(p[0], p[1], yaw, p[2])))
    roof_gable(parts, name, w, d, lift + h + 0.09, rise=1.35, ov=0.6, mat=roof_m,
               battens=0, ridge=False)
    # hanging net / gear under the house
    parts.append(box(name + "_net", (1.8, 0.06, 0.9), (0.7, -d * 0.2, lift - 0.55),
                     MAT["fabric_teal"], coll, rot=(0, math.radians(6), 0)))
    return make_master(name, parts, bevel=0.012, weighted=True)


def villa_modern(name, w=7.6, d=6.2, seed=0, pool=False):
    rng = random.Random(seed * 91 + 5)
    coll = C("WORK")
    parts = []
    h1 = 3.0
    parts.append(box(name + "_plinth", (w + 0.8, d + 0.8, 0.30), (0, 0, 0.15),
                     MAT["concrete"], coll))
    wall_shell(parts, name, w, d, h1, 0.30, MAT["cream"], thick=0.18)
    # upper volume offset for a modern massing
    w2, d2 = w * 0.62, d * 0.78
    ox = -w * 0.16
    wall_shell(parts, name + "_u", w2, d2, 2.7, 0.30 + h1, MAT["wood_light"], thick=0.16)
    parts.append(box(name + "_slab", (w2 + 0.5, d2 + 0.5, 0.20), (ox, 0, 0.30 + h1 - 0.05),
                     MAT["concrete"], coll))
    roof_flat(parts, name, w, d, 0.30 + h1, 0.40, MAT["concrete"])
    roof_flat(parts, name + "_u", w2, d2, 0.30 + h1 + 2.7, 0.36, MAT["concrete"])
    # rooftop service clutter: water tank, solar panels, planter
    parts.append(cyl(name + "_tank", 0.62, 1.15, (ox + w2 * 0.22, 0.6, 0.30 + h1 + 2.7 + 0.58),
                     MAT["paint_w"], coll, verts=12))
    parts.append(cyl(name + "_tankcap", 0.66, 0.10, (ox + w2 * 0.22, 0.6, 0.30 + h1 + 2.7 + 1.18),
                     MAT["metal_dark"], coll, verts=12))
    for i in range(3):
        parts.append(box(name + "_solar%d" % i, (1.5, 0.9, 0.06),
                         (-w * 0.18 + i * 1.7, d * 0.18, 0.30 + h1 + 0.34),
                         MAT["glass_dark"], coll, rot=(math.radians(-8), 0, 0)))
    parts.append(box(name + "_planter", (1.4, 0.5, 0.42),
                     (w * 0.24, -d * 0.22, 0.30 + h1 + 0.28), MAT["concrete"], coll))
    # full-height glazing on the front (recessed, framed)
    for i in range(3):
        x = -w * 0.30 + i * (w * 0.30)
        window_unit(parts, name + "_gl%d" % i,
                    Matrix.Translation(Vector((x, -d * 0.5, 0.30 + h1 * 0.52))),
                    ww=w * 0.24, wh=h1 - 0.85, shutters=False, mullion=False,
                    sill=False, frame_mat=MAT["metal_dark"], glass_mat=MAT["glass"])
    # pergola over the terrace
    for i in range(6):
        x = -w * 0.45 + i * (w * 0.18)
        parts.append(box(name + "_per%d" % i, (0.10, 2.4, 0.10),
                         (ox + x, -(d * 0.5 + 1.2), 0.30 + h1 + 0.55), MAT["wood_dark"], coll))
    for sgn in (-1, 1):
        parts.append(box(name + "_perb%d" % sgn, (w2 + 1.0, 0.12, 0.14),
                         (ox, -(d * 0.5 + 0.1), 0.30 + h1 + 0.58), MAT["wood_dark"], coll))
        parts.append(box(name + "_perp%d" % sgn, (0.14, 0.14, h1 + 0.6),
                         (ox + sgn * (w2 * 0.5), -(d * 0.5 + 2.2), 0.30 + (h1 + 0.6) * 0.5),
                         MAT["wood_dark"], coll))
    # terrace + pool
    parts.append(box(name + "_terr", (w + 0.6, 3.0, 0.16), (0, -(d * 0.5 + 1.5), 0.30),
                     MAT["paving"], coll))
    if pool:
        # recessed pool: coping rim + water slightly below deck
        parts.append(box(name + "_poolr", (3.9, 2.3, 0.12), (w * 0.1, -(d * 0.5 + 1.6), 0.30),
                         MAT["paint_w"], coll))
        parts.append(box(name + "_poolb", (3.4, 1.8, 0.10), (w * 0.1, -(d * 0.5 + 1.6), 0.335),
                         MAT["concrete_dark"], coll))
        parts.append(box(name + "_pool", (3.4, 1.8, 0.04), (w * 0.1, -(d * 0.5 + 1.6), 0.395),
                         MAT["pool_water"], coll))
    railing_unit(parts, name + "_pr", (-w * 0.5 - 0.2, -(d * 0.5 + 2.9), 0.38),
                 (w * 0.5 + 0.2, -(d * 0.5 + 2.9), 0.38), 0.38, 0.95, MAT["metal_dark"], 8)
    door_unit(parts, name + "_door", Matrix.Translation(Vector((w * 0.18, -d * 0.5, 0.30))),
              dw=1.2, dh=2.3, double=True)
    for i in range(2):
        window_unit(parts, name + "_uw%d" % i,
                    Matrix.Translation(Vector((ox - w2 * 0.28 + i * w2 * 0.5, -d2 * 0.5,
                                               0.30 + h1 + 1.35))),
                    ww=1.5, wh=1.3, frame_mat=MAT["wood_dark"])
    # rear + side windows so the building never reads as a blank box
    for face in ("N", "E", "W"):
        for i in (-1, 1):
            u = i * (w * 0.24 if face == "N" else d * 0.20)
            p, yaw = wall_point(w, d, face, u, 0.30 + h1 * 0.55)
            window_unit(parts, name + "_w%s%d" % (face, i),
                        face_matrix(p[0], p[1], yaw, 0), ww=1.15, wh=1.25,
                        frame_mat=MAT["metal_dark"], mullion=False, sill=False)
            if face == "N":
                p2, yaw2 = wall_point(w2, d2, face, i * w2 * 0.26, 0.30 + h1 + 1.45)
                window_unit(parts, name + "_uw%s%d" % (face, i),
                            face_matrix(ox + p2[0], p2[1], yaw2, 0), ww=1.2, wh=1.15,
                            frame_mat=MAT["wood_dark"], mullion=False, sill=False)
    return make_master(name, parts, bevel=0.012, weighted=True)


def house_family(name, w=5.8, d=4.8, seed=0, two_storey=False):
    rng = random.Random(seed * 17 + 11)
    coll = C("WORK")
    parts = []
    h = 2.8 if not two_storey else 2.7
    wall_m = MAT[rng.choice(["paint_w", "paint_mint", "paint_yellow", "wood_light"])]
    parts.append(box(name + "_found", (w + 0.4, d + 0.4, 0.34), (0, 0, 0.17), MAT["stone"], coll))
    wall_shell(parts, name, w, d, h, 0.30, wall_m)
    roof_gable(parts, name, w, d, 0.30 + h, rise=1.45, ov=0.55,
               mat=MAT["roof_terra"] if rng.random() < 0.6 else MAT["roof_metal"], battens=7)
    if two_storey:
        wall_shell(parts, name + "_u", w * 0.92, d * 0.92, 2.6, 0.30 + h, wall_m)
        roof_gable(parts, name + "_u", w * 0.92, d * 0.92, 0.30 + h + 2.6, rise=1.2, ov=0.5,
                   mat=MAT["roof_terra"], battens=6)
        for i, u in enumerate((-w * 0.26, 0.0, w * 0.26)):
            window_unit(parts, name + "_uw%d" % i,
                        Matrix.Translation(Vector((u, -d * 0.46, 0.30 + h + 1.4))),
                        ww=0.95, wh=1.1)
    door_unit(parts, name + "_door", Matrix.Translation(Vector((0, -d * 0.5, 0.30))),
              dw=0.95)
    for i, u in enumerate((-w * 0.28, w * 0.28)):
        window_unit(parts, name + "_w%d" % i,
                    Matrix.Translation(Vector((u, -d * 0.5, 1.85))), ww=1.05, wh=1.2,
                    shutters=True)
    for face in ("E", "W"):
        p, yaw = wall_point(w, d, face, 0.0, 1.85)
        window_unit(parts, name + "_w%s" % face, face_matrix(p[0], p[1], yaw, p[2]),
                    ww=0.9, wh=1.05)
    # rear elevation
    for i, u in enumerate((-w * 0.24, w * 0.24)):
        p, yaw = wall_point(w, d, "N", u, 1.85)
        window_unit(parts, name + "_rn%d" % i, face_matrix(p[0], p[1], yaw, p[2]),
                    ww=0.9, wh=1.05)
    p, yaw = wall_point(w, d, "N", 0.0, 1.02)
    parts.append(xform(box(name + "_rdoor", (0.85, 0.10, 1.95), (0, -0.02, 0),
                           MAT["wood_dark"], C("WORK")),
                       face_matrix(p[0], p[1], yaw, p[2])))
    lamp_unit(parts, name + "_lamp", Matrix.Translation(Vector((-0.9, -d * 0.5, 0))), 2.4)
    # garden fence + gate posts
    for sgn in (-1, 1):
        parts.append(box(name + "_fence%d" % sgn, (w * 0.45, 0.07, 0.85),
                         (sgn * (w * 0.45), -(d * 0.5 + 2.2), 0.42), MAT["wood_light"], coll))
    for sgn in (-1, 1):
        parts.append(box(name + "_post%d" % sgn, (0.16, 0.16, 1.15),
                         (sgn * 1.1, -(d * 0.5 + 2.2), 0.57), MAT["wood_dark"], coll))
    return make_master(name, parts, bevel=0.012, weighted=True)


def shophouse(name, w=5.0, d=6.0, seed=0, mat_key=None):
    rng = random.Random(seed * 41 + 13)
    coll = C("WORK")
    parts = []
    h1, h2 = 3.2, 2.7
    wall_m = mat_key or MAT[rng.choice(["paint_w", "paint_yellow", "paint_mint", "paint_coral"])]
    parts.append(box(name + "_found", (w + 0.2, d + 0.2, 0.26), (0, 0, 0.13), MAT["concrete"], coll))
    # ground floor: open front, interior shop
    parts.append(box(name + "_bl", (0.18, d, h1), (-w * 0.5 + 0.09, 0, 0.26 + h1 * 0.5), wall_m, coll))
    parts.append(box(name + "_br", (0.18, d, h1), (w * 0.5 - 0.09, 0, 0.26 + h1 * 0.5), wall_m, coll))
    parts.append(box(name + "_bk", (w, 0.18, h1), (0, d * 0.5 - 0.09, 0.26 + h1 * 0.5), wall_m, coll))
    # header beam over the open shopfront (no wall below it)
    parts.append(box(name + "_hdr", (w, 0.22, 1.15), (0, -d * 0.5 + 0.10, 0.26 + h1 - 0.575),
                     wall_m, coll))
    parts.append(box(name + "_ceil", (w, d, 0.20), (0, 0, 0.26 + h1), MAT["wood_light"], coll))
    parts.append(box(name + "_floor", (w, d, 0.16), (0, 0, 0.30), MAT["paving"], coll))
    # interior: counter + shelves + goods
    parts.append(box(name + "_cnt", (w * 0.72, 0.55, 0.95), (0, -d * 0.18, 0.26 + 0.55),
                     MAT["wood"], coll))
    parts.append(box(name + "_cntt", (w * 0.74, 0.62, 0.09), (0, -d * 0.18, 0.26 + 1.03),
                     MAT["stone"], coll))
    for i in range(3):
        parts.append(box(name + "_shelf%d" % i, (w * 0.7, 0.30, 0.06),
                         (0, d * 0.30, 0.26 + 0.85 + i * 0.55), MAT["wood_light"], coll))
        for k in range(5):
            parts.append(box(name + "_gd%d_%d" % (i, k), (0.18, 0.16, 0.24),
                             (-w * 0.28 + k * w * 0.14, d * 0.30, 0.26 + 1.05 + i * 0.55),
                             MAT["cloth_%d" % ((i + k) % 10)], coll))
    # upper floor
    wall_shell(parts, name + "_u", w, d, h2, 0.26 + h1 + 0.10, wall_m)
    for i, u in enumerate((-w * 0.26, 0.0, w * 0.26)):
        window_unit(parts, name + "_uw%d" % i,
                    Matrix.Translation(Vector((u, -d * 0.5, 0.26 + h1 + 1.45))),
                    ww=0.85, wh=1.1, shutters=True)
    # rear elevation
    for i, u in enumerate((-w * 0.26, w * 0.26)):
        p, yaw = wall_point(w, d, "N", u, 0.26 + h1 + 1.45)
        window_unit(parts, name + "_rw%d" % i, face_matrix(p[0], p[1], yaw, p[2]),
                    ww=0.85, wh=1.05)
    p, yaw = wall_point(w, d, "N", 0.0, 0.26 + 1.05)
    parts.append(xform(box(name + "_rdoor", (0.9, 0.10, 1.85), (0, -0.02, 0),
                           MAT["wood_dark"], C("WORK")),
                       face_matrix(p[0], p[1], yaw, p[2])))
    # balcony
    parts.append(box(name + "_bal", (w, 1.0, 0.14), (0, -(d * 0.5 + 0.5), 0.26 + h1 + 0.10),
                     MAT["wood_light"], coll))
    railing_unit(parts, name + "_br", (-w * 0.5 + 0.1, -(d * 0.5 + 0.95), 0.26 + h1 + 0.10),
                 (w * 0.5 - 0.1, -(d * 0.5 + 0.95), 0.26 + h1 + 0.10),
                 0.26 + h1 + 0.10, 0.9, MAT["wood_light"], int(w / 0.7))
    roof_flat(parts, name, w, d, 0.26 + h1 + 0.10 + h2, 0.35, MAT["concrete"])
    parts.append(cyl(name + "_wtank", 0.48, 0.95, (w * 0.26, d * 0.22,
                                                  0.26 + h1 + 0.10 + h2 + 0.60),
                     MAT["paint_w"], coll, verts=10))
    parts.append(box(name + "_acu", (0.72, 0.5, 0.42), (-w * 0.22, d * 0.18,
                                                       0.26 + h1 + 0.10 + h2 + 0.24),
                     MAT["metal"], coll))
    # awning + sign
    awning(parts, name + "_awn", w - 0.2, 1.6, 0.26 + h1 - 0.10, MAT["fabric_coral"], 0.42,
           cy=-(d * 0.5 + 0.55))
    sign_board(parts, name + "_sign", Matrix.Translation(Vector((0, -d * 0.5 - 0.02, 0))),
               text_w=w * 0.66, text_h=0.44, z=0.26 + h1 - 0.85,
               mat=MAT["paint_yellow"] if rng.random() < 0.5 else MAT["paint_teal"])
    # balcony brackets
    for sgn in (-1, 1):
        parts.append(box(name + "_brk%d" % sgn, (0.12, 1.0, 0.55),
                         (sgn * (w * 0.30), -(d * 0.5 + 0.5), 0.26 + h1 - 0.20),
                         MAT["wood_dark"], coll))
    # crates outside
    for i in range(2):
        parts.append(box(name + "_cr%d" % i, (0.5, 0.5, 0.42),
                         (-w * 0.32 + i * 0.62, -d * 0.5 - 0.4, 0.26 + 0.21),
                         MAT["wood_light"], coll))
    return make_master(name, parts, bevel=0.012, weighted=True)


def market_stall(name, w=3.2, d=2.4, seed=0, awning_mat=None):
    rng = random.Random(seed * 71 + 2)
    coll = C("WORK")
    parts = []
    parts.append(box(name + "_floor", (w, d, 0.12), (0, 0, 0.06), MAT["paving"], coll))
    posts(parts, name, w, d, 0.06, 2.35, MAT["wood_dark"], inset=0.12, size=0.11)
    parts.append(box(name + "_cnt", (w * 0.86, 0.62, 0.9), (0, -d * 0.12, 0.56),
                     MAT["wood"], coll))
    parts.append(box(name + "_ctop", (w * 0.9, 0.68, 0.08), (0, -d * 0.12, 1.03),
                     MAT["wood_light"], coll))
    # goods: fruit piles
    for i in range(6):
        parts.append(sphere(name + "_fr%d" % i, 0.11,
                            (-w * 0.32 + (i % 3) * 0.30, -d * 0.12 + (i // 3) * 0.22, 1.14),
                            [MAT["paint_coral"], MAT["paint_yellow"], MAT["leaf_dry"]][i % 3],
                            coll, seg=7, rings=5))
    awning(parts, name + "_aw", w + 0.3, d + 0.4, 2.30,
           awning_mat or [MAT["fabric_coral"], MAT["fabric_teal"], MAT["paint_yellow"]][seed % 3],
           0.3)
    for i in range(3):
        parts.append(box(name + "_cr%d" % i, (0.46, 0.5, 0.36),
                         (w * 0.18, d * 0.24 + i * 0.1, 0.18 + i * 0.30), MAT["wood_light"], coll))
    return make_master(name, parts, bevel=0.010, weighted=True)


def pavilion(name, w=5.0, d=4.4, seed=0, thatch=True):
    coll = C("WORK")
    parts = []
    parts.append(box(name + "_deck", (w + 0.6, d + 0.6, 0.22), (0, 0, 0.11),
                     MAT["wood_light"], coll))
    posts(parts, name, w, d, 0.22, 2.6, MAT["wood_dark"], inset=0.16, size=0.16)
    # low railing on three sides
    railing_unit(parts, name + "_r1", (-w * 0.5 + 0.2, d * 0.5 - 0.2, 0.22),
                 (w * 0.5 - 0.2, d * 0.5 - 0.2, 0.22), 0.22, 0.75, MAT["wood_light"], 6)
    if thatch:
        roof_hip(parts, name, w, d, 0.22 + 2.6, rise=1.9, ov=0.85, mat=MAT["roof_thatch"],
                 nseg=30, wave=0.05, seed=seed)
    else:
        roof_hip(parts, name, w, d, 0.22 + 2.6, rise=1.5, ov=0.7, mat=MAT["roof_terra"], nseg=24)
    # furniture inside
    parts.append(box(name + "_tbl", (1.5, 0.9, 0.10), (0, 0, 0.95), MAT["wood"], coll))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl(name + "_tl%d%d" % (sx, sy), 0.05, 0.72,
                             (sx * 0.6, sy * 0.32, 0.58), MAT["wood_dark"], coll, verts=6))
    for i, sy in enumerate((-1.0, 1.0)):
        parts.append(box(name + "_bench%d" % i, (1.5, 0.34, 0.08), (0, sy * 0.75, 0.60),
                         MAT["wood"], coll))
    return make_master(name, parts, bevel=0.010, weighted=True)


def civic_building(name, w=12.0, d=8.0, h=4.0, seed=0, roof_mat=None, wall_mat=None):
    coll = C("WORK")
    parts = []
    wall_m = wall_mat or MAT["paint_w"]
    parts.append(box(name + "_plinth", (w + 1.0, d + 1.0, 0.45), (0, 0, 0.22),
                     MAT["stone"], coll))
    wall_shell(parts, name, w, d, h, 0.45, wall_m, thick=0.22)
    roof_hip(parts, name, w, d, 0.45 + h, rise=2.2, ov=0.95,
             mat=roof_mat or MAT["roof_terra"], nseg=30)
    # window rows
    n = max(3, int(w / 2.0))
    for i in range(n):
        u = -w * 0.5 + (i + 0.5) * (w / n)
        window_unit(parts, name + "_wf%d" % i,
                    Matrix.Translation(Vector((u, -d * 0.5, 0.45 + h * 0.58))),
                    ww=1.15, wh=1.55, mullion=True)
        window_unit(parts, name + "_wb%d" % i,
                    face_matrix(u, d * 0.5, 180, 0.45 + h * 0.58),
                    ww=1.15, wh=1.55)
    for face in ("E", "W"):
        for i in range(2):
            p, yaw = wall_point(w, d, face, (i - 0.5) * d * 0.4, 0.45 + h * 0.58)
            window_unit(parts, name + "_w%s%d" % (face, i), face_matrix(p[0], p[1], yaw, p[2]),
                        ww=1.1, wh=1.45)
    # entrance portico
    parts.append(box(name + "_port", (3.2, 1.6, 0.28), (0, -(d * 0.5 + 0.8), 0.58),
                     MAT["concrete"], coll))
    for sx in (-1, 1):
        parts.append(cyl(name + "_col%d" % sx, 0.16, 3.0, (sx * 1.4, -(d * 0.5 + 1.3), 2.1),
                         MAT["paint_w"], coll, verts=12))
    parts.append(box(name + "_pf", (3.6, 1.8, 0.22), (0, -(d * 0.5 + 0.9), 3.7),
                     MAT["concrete"], coll))
    door_unit(parts, name + "_door", Matrix.Translation(Vector((0, -d * 0.5, 0.45))),
              dw=1.6, dh=2.5, double=True)
    step_unit(parts, name + "_st", Matrix.Translation(Vector((0, -(d * 0.5 + 1.4), 0.0))),
              width=3.0, n=2)
    sign_board(parts, name + "_sign", Matrix.Translation(Vector((0, -d * 0.5, 0))),
               text_w=3.0, text_h=0.5, z=0.45 + h - 0.55, mat=MAT["paint_teal"])
    # flag pole
    parts.append(cyl(name + "_flagp", 0.05, 4.0, (w * 0.34, -d * 0.5 - 1.6, 2.6),
                     MAT["metal"], coll, verts=6))
    parts.append(box(name + "_flag", (1.2, 0.04, 0.7), (w * 0.34 + 0.6, -d * 0.5 - 1.6, 4.2),
                     MAT["fabric_coral"], coll))
    return make_master(name, parts, bevel=0.012, weighted=True)


def clock_tower(name, size=2.6, h=9.0):
    coll = C("WORK")
    parts = []
    parts.append(box(name + "_base", (size + 1.0, size + 1.0, 0.6), (0, 0, 0.30),
                     MAT["stone"], coll))
    parts.append(box(name + "_shaft", (size, size, h), (0, 0, 0.6 + h * 0.5),
                     MAT["paint_w"], coll))
    for i in range(3):
        parts.append(box(name + "_band%d" % i, (size + 0.14, size + 0.14, 0.16),
                         (0, 0, 0.6 + h * (0.25 + i * 0.25)), MAT["wood_light"], coll))
    # clock faces
    for yaw in (0, 90, 180, -90):
        M = face_matrix(0, 0, yaw, 0.6 + h * 0.80)
        parts.append(xform(cyl(name + "_cf%d" % yaw, 0.72, 0.10, (0, -size * 0.5 - 0.01, 0),
                               MAT["paint_w"], coll, rot=(math.radians(90), 0, 0), verts=20), M))
        parts.append(xform(cyl(name + "_cr%d" % yaw, 0.62, 0.06, (0, -size * 0.5 - 0.07, 0),
                               MAT["glass_dark"], coll, rot=(math.radians(90), 0, 0), verts=20), M))
        parts.append(xform(box(name + "_ch%d" % yaw, (0.05, 0.03, 0.44),
                               (0, -size * 0.5 - 0.11, 0.20), MAT["wood_dark"], coll), M))
        parts.append(xform(box(name + "_cm%d" % yaw, (0.32, 0.03, 0.05),
                               (0.14, -size * 0.5 - 0.11, 0.0), MAT["wood_dark"], coll), M))
    # belfry + spire
    parts.append(box(name + "_belfry", (size + 0.3, size + 0.3, 1.5),
                     (0, 0, 0.6 + h + 0.75), MAT["wood_light"], coll))
    for i in range(4):
        a = i * TAU / 4
        parts.append(box(name + "_bel%d" % i, (size * 0.5, 0.10, 0.9),
                         (math.cos(a) * (size * 0.5 + 0.14), math.sin(a) * (size * 0.5 + 0.14),
                          0.6 + h + 0.75), MAT["wood_dark"], coll,
                         rot=(0, 0, a + math.pi / 2)))
    roof_hip(parts, name + "_spire", size + 0.4, size + 0.4, 0.6 + h + 1.5, rise=3.2,
             ov=0.22, mat=MAT["roof_terra"], nseg=4)
    parts.append(sphere(name + "_finial", 0.12, (0, 0, 0.6 + h + 4.8), MAT["metal"], coll))
    return make_master(name, parts, bevel=0.012, weighted=True)


def lighthouse(name, h=11.0, r0=1.9, r1=1.1):
    coll = C("WORK")
    parts = []
    parts.append(cyl(name + "_base", 2.9, 1.2, (0, 0, 0.6), MAT["stone"], coll, verts=20))
    seg = 5
    for i in range(seg):
        z0 = 1.2 + i * (h / seg)
        rr0 = r0 + (r1 - r0) * (i / seg)
        rr1 = r0 + (r1 - r0) * ((i + 1) / seg)
        parts.append(cone(name + "_t%d" % i, rr0, rr1, h / seg,
                          (0, 0, z0 + h / (seg * 2)),
                          MAT["paint_w"] if i % 2 == 0 else MAT["paint_coral"],
                          coll, verts=24))
        parts.append(torus(name + "_ring%d" % i, rr1 + 0.04, 0.06,
                           (0, 0, z0 + h / seg), MAT["metal_dark"], coll,
                           mseg=24, nseg=6))
    # gallery + lantern
    zt = 1.2 + h
    parts.append(cyl(name + "_gal", r1 + 0.55, 0.18, (0, 0, zt), MAT["metal_dark"],
                     coll, verts=24))
    for i in range(12):
        a = i * TAU / 12
        parts.append(cyl(name + "_p%d" % i, 0.03, 0.6,
                         (math.cos(a) * (r1 + 0.45), math.sin(a) * (r1 + 0.45), zt + 0.39),
                         MAT["metal_dark"], coll, verts=5))
    parts.append(torus(name + "_rail", r1 + 0.45, 0.04, (0, 0, zt + 0.68),
                       MAT["metal_dark"], coll, mseg=24, nseg=5))
    parts.append(cyl(name + "_lantern", r1 * 0.92, 1.5, (0, 0, zt + 0.85),
                     MAT["glass"], coll, verts=12))
    parts.append(cyl(name + "_lampcore", 0.34, 1.1, (0, 0, zt + 0.85), MAT["glow"], coll,
                     verts=10))
    parts.append(cone(name + "_cap", r1 * 1.05, 0.10, 0.9, (0, 0, zt + 1.95),
                      MAT["metal_dark"], coll, verts=12))
    parts.append(sphere(name + "_tip", 0.10, (0, 0, zt + 2.45), MAT["metal"], coll))
    return make_master(name, parts, bevel=0.010, weighted=True)


# ---------------------------------------------------------------- master set (S1)
def build_arch_masters():
    house_coastal("HOUSE_COASTAL_A", 6.4, 5.2, 2.9, seed=1)
    house_coastal("HOUSE_COASTAL_B", 7.2, 5.6, 3.0, seed=2, shutters=False, veranda=2.2)
    house_stilt("HOUSE_STILT_A", 5.4, 5.0, 2.7, 1.35, seed=3)
    house_stilt("HOUSE_STILT_B", 4.8, 4.4, 2.6, 1.05, seed=4)
    villa_modern("VILLA_A", 7.6, 6.2, seed=5, pool=True)
    villa_modern("VILLA_B", 6.8, 5.8, seed=6, pool=False)
    house_family("HOUSE_FAMILY_A", 5.8, 4.8, seed=7)
    house_family("HOUSE_FAMILY_B", 5.6, 4.6, seed=8, two_storey=True)
    shophouse("SHOP_A", 5.2, 6.0, seed=9)
    shophouse("SHOP_B", 4.8, 5.6, seed=10)
    market_stall("STALL_A", 3.2, 2.4, seed=11)
    market_stall("STALL_B", 2.8, 2.2, seed=12)
    pavilion("PAVILION_A", 5.0, 4.4, seed=13)
    pavilion("PAVILION_B", 4.2, 3.8, seed=14)
    civic_building("CIVIC_A", 12.0, 8.0, 4.0, seed=15)
    civic_building("CIVIC_B", 9.0, 7.0, 3.6, seed=16, roof_mat=MAT["roof_metal"],
                   wall_mat=MAT["paint_mint"])
    clock_tower("CLOCK_TOWER", 2.6, 9.0)
    lighthouse("LIGHTHOUSE", 11.0, 1.9, 1.1)
    print("ARCH MASTERS", len(POOL))
