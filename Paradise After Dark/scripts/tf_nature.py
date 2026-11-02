"""
PARADISE AFTER DARK — tropical botanical kit and placement.
All plants are custom procedural meshes; no external textures.
"""

import bpy
import bmesh
import math
import random

from mathutils import Vector, Matrix, Euler

import tf_core as C

TAU = math.tau


# ------------------------------------------------------------------ mesh builder

class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.mi = {}

    def mat(self, m):
        if m.name not in self.mi:
            self.mi[m.name] = len(self.mats)
            self.mats.append(m)
        return self.mi[m.name]

    def add_bm(self, bm, matrix, mat):
        mi = self.mat(mat)
        vmap = {}
        for v in bm.verts:
            vmap[v] = self.bm.verts.new(matrix @ v.co)
        for f in bm.faces:
            try:
                nf = self.bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = mi
            nf.smooth = True
        bm.free()

    def quad(self, vs, mat, smooth=True):
        mi = self.mat(mat)
        verts = [self.bm.verts.new(v) for v in vs]
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return
        f.material_index = mi
        f.smooth = smooth

    def finish(self, name, coll):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(name + "_M")
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        for p in me.polygons:
            p.use_smooth = True
        return ob


def cyl_between(B, p0, p1, r0, r1, mat, seg=8):
    p0 = Vector(p0)
    p1 = Vector(p1)
    d = p1 - p0
    L = d.length
    if L < 1e-5:
        return
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r0, radius2=r1, depth=L)
    M = Matrix.Translation((p0 + p1) * 0.5) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    B.add_bm(bm, M, mat)


def add_cyl(B, loc, radius, depth, mat, seg=8, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=radius, radius2=radius, depth=depth)
    M = Matrix.Translation(loc) @ Euler(rot).to_matrix().to_4x4()
    B.add_bm(bm, M, mat)


# ------------------------------------------------------------------ palm

def add_palm_frond(B, base, angle, length, rise, droop, leaf_mat, rib_mat,
                   leaflets=13, width=0.62):
    """A palm frond with a deep V-fold so it reads from eye level.

    A flat horizontal frond disappears edge-on. Each half of this frond
    slopes down from the rachis, and the leaflets hang below it, so the
    crown shows real surface and silhouette from the ground.
    """
    b = Vector(base)
    n = 14
    pts = []
    for i in range(n + 1):
        u = i / n
        r = length * u
        z = rise * math.sin(math.pi * u * 0.52) - droop * (u ** 2.3)
        pts.append(b + Vector((math.cos(angle) * r,
                               math.sin(angle) * r, z)))
    side = Vector((-math.sin(angle), math.cos(angle), 0.0))
    out = Vector((math.cos(angle), math.sin(angle), 0.0))

    # folded lamina, two sloped halves per segment
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        p, q = pts[i], pts[i + 1]
        w0 = width * (math.sin(math.pi * (0.08 + 0.88 * u0)) ** 0.55)
        w1 = width * (math.sin(math.pi * (0.08 + 0.88 * u1)) ** 0.55)
        fold0, fold1 = 0.34 * w0, 0.34 * w1
        for s in (-1, 1):
            a = p + side * (w0 * s) + Vector((0, 0, -fold0))
            bb = q + side * (w1 * s) + Vector((0, 0, -fold1))
            B.quad([p, a, bb, q], leaf_mat)

    # hanging leaflets break up the silhouette
    for s in (-1, 1):
        for j in range(leaflets):
            u = 0.10 + 0.82 * j / (leaflets - 1)
            idx = min(int(u * n), n - 1)
            p, q = pts[idx], pts[idx + 1]
            t = (q - p).normalized()
            w = width * (math.sin(math.pi * (0.08 + 0.88 * u)) ** 0.55)
            root = p + side * (s * w * 0.94) + Vector((0, 0, -0.34 * w))
            llen = (0.46 + 0.26 * math.sin(math.pi * u)) * (1.0 - 0.30 * u)
            d = (side * s + out * 0.30 + Vector((0, 0, -0.85))).normalized()
            tip = root + d * llen
            B.quad([root - t * 0.055, root + t * 0.055,
                    tip + t * 0.018, tip - t * 0.018], leaf_mat)

    # pale rachis
    for i in range(n):
        p, q = pts[i], pts[i + 1]
        s2 = side * 0.028 * (1.0 - 0.7 * i / n)
        B.quad([p - s2, p + s2, q + s2, q - s2], rib_mat)


def palm_master(name, height=7.0, crown=12, length=2.8, scale=1.0):
    B = Builder()
    trunk_mat = C.MAT["bark"]
    leaf = C.MAT["leaf_mid"]
    leaf2 = C.MAT["leaf_deep"]
    leaf3 = C.MAT["leaf_bright"]
    # curved, ringed trunk
    n = 13
    pts = []
    lean = 0.55 * scale
    for i in range(n + 1):
        t = i / n
        pts.append(Vector((lean * (t ** 1.8), 0.10 * math.sin(t * 2.2),
                           height * t)))
    for i in range(n):
        r0 = (0.21 - 0.09 * i / n) * scale
        r1 = (0.21 - 0.09 * (i + 1) / n) * scale
        cyl_between(B, pts[i], pts[i + 1], r0 * 1.06, r1, trunk_mat, 10)
        cyl_between(B, pts[i], pts[i] + (pts[i + 1] - pts[i]) * 0.20,
                    r0 * 1.18, r0 * 1.18, trunk_mat, 10)
    # green crownshaft
    top = pts[-1]
    cyl_between(B, top - Vector((0, 0, 0.65)),
                top + Vector((0, 0, 0.34)),
                0.15 * scale, 0.10 * scale, C.MAT["leaf_deep"], 10)
    # coconuts
    for k in range(5):
        a = TAU * k / 5 + 0.3
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6,
                                  radius=0.10 * scale)
        M = Matrix.Translation(top + Vector((math.cos(a) * 0.16 * scale,
                                             math.sin(a) * 0.16 * scale,
                                             -0.10 * scale)))
        B.add_bm(bm, M, C.MAT["coconut"])
    # crown: alternate length/droop for a layered, wind-blown silhouette
    for k in range(crown):
        a = TAU * k / crown + 0.11
        ln = length * scale * (0.80 + 0.26 * ((k * 7) % 5) / 7.0)
        dr = (1.35 + 0.60 * ((k * 3) % 4) / 4.0) * scale
        ris = (0.52 + 0.20 * (k % 3)) * scale
        mat = (leaf2 if k % 4 == 0 else leaf3 if k % 5 == 0 else leaf)
        add_palm_frond(B, top + Vector((0, 0, 0.30 * scale)), a,
                       ln, ris, dr, mat, C.MAT["leaf_lime"],
                       leaflets=15, width=0.50 * scale)
    # a few young upright fronds in the centre
    for k in range(4):
        a = TAU * k / 4 + 0.7
        add_palm_frond(B, top + Vector((0, 0, 0.36 * scale)), a,
                       length * 0.42 * scale, 0.60 * scale, 0.12 * scale,
                       leaf3, C.MAT["leaf_lime"], leaflets=9,
                       width=0.26 * scale)
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def fan_palm_master(name, height=4.4, leaves=15):
    """Traveller's palm: a flat fan of broad paddles, strong silhouette."""
    B = Builder()
    cyl_between(B, (0, 0, 0), (0.1, 0, height), 0.17, 0.13,
                C.MAT["bark"], 9)
    top = Vector((0.1, 0, height))
    for k in range(leaves):
        a = -1.30 + 2.60 * k / (leaves - 1)
        d = Vector((math.sin(a), 0.22, math.cos(a))).normalized()
        L = 2.05 - 0.42 * abs(a)
        M = Matrix.Translation(top) @ d.to_track_quat("Y", "Z").to_matrix().to_4x4()
        banana_leaf(B, M, L, C.MAT["leaf_bright"] if k % 3 else C.MAT["leaf_mid"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def heliconia_master(name):
    B = Builder()
    for k in range(5):
        a = TAU * k / 5 + 0.2
        base = Vector((math.cos(a) * 0.10, math.sin(a) * 0.10, 0.05))
        top = base + Vector((math.cos(a) * 0.18, math.sin(a) * 0.18,
                             0.95 + 0.15 * (k % 3)))
        cyl_between(B, base, top, 0.022, 0.012, C.MAT["leaf_deep"], 6)
        M = Matrix.Translation(top) @ Euler((math.radians(-50), 0,
                                             a + 0.8)).to_matrix().to_4x4()
        banana_leaf(B, M, 0.65, C.MAT["leaf_mid"])
        for j in range(4):
            h = 0.20 + 0.13 * j
            add_bract(B, top + Vector((0, 0, -h)), a + 0.3 * j,
                      0.40 - 0.05 * j, 0.34, 0.10,
                      C.MAT["flower_coral"] if j % 2 else C.MAT["flower_orange"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


# ------------------------------------------------------------------ monstera

def monstera_leaf(B, M, size, mat, holes=True):
    L = size
    W = size * 0.72
    nu, nv = 14, 12

    def width(u):
        return W * (math.sin(math.pi * u) ** 0.55) * (1.0 - 0.12 * u)

    verts = []
    idx = {}
    for i in range(nu + 1):
        u = i / nu
        w = width(u)
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = v * w
            y = u * L
            z = 0.08 * math.sin(math.pi * u) * (1 - v * v)
            idx[(i, j)] = len(verts)
            verts.append(M @ Vector((x, y, z)))

    def in_hole(u, v):
        if not holes:
            return False
        # 5 fenestrations per side along the blade
        for side in (-1, 1):
            for k in range(4):
                cu = 0.30 + 0.45 * k / 3
                cv = side * (0.28 + 0.06 * math.sin(k))
                ru, rv = 0.055, 0.12
                if ((u - cu) / ru) ** 2 + ((v - cv) / rv) ** 2 < 1.0:
                    return True
        return False

    for i in range(nu):
        for j in range(nv):
            u0, u1 = i / nu, (i + 1) / nu
            v0, v1 = -1 + 2 * j / nv, -1 + 2 * (j + 1) / nv
            if in_hole((u0 + u1) * 0.5, (v0 + v1) * 0.5):
                continue
            B.quad([verts[idx[(i, j)]], verts[idx[(i + 1, j)]],
                    verts[idx[(i + 1, j + 1)]], verts[idx[(i, j + 1)]]],
                   mat)
    # central rib
    for i in range(nu):
        u0, u1 = i / nu, (i + 1) / nu
        p = M @ Vector((0, u0 * L, 0.006))
        q = M @ Vector((0, u1 * L, 0.006))
        t = (q - p).normalized()
        side = Vector((-t.y, t.x, 0)).normalized() * 0.012
        B.quad([p - side, p + side, q + side, q - side], C.MAT["leaf_deep"])


def monstera_master(name, size=1.0, leaves=5):
    B = Builder()
    for k in range(leaves):
        a = TAU * k / leaves + 0.4
        stem_top = Vector((math.cos(a) * 0.25, math.sin(a) * 0.25,
                           0.35 + 0.28 * (k / max(1, leaves - 1))))
        cyl_between(B, (0, 0, 0.05), stem_top, 0.018, 0.012,
                    C.MAT["leaf_deep"], 6)
        yaw = a + 0.8
        tilt = math.radians(-58 - 8 * k)
        M = Matrix.Translation(stem_top) @ Euler((tilt, 0, yaw)).to_matrix().to_4x4()
        monstera_leaf(B, M, size * (0.78 + 0.10 * (k % 3)),
                      C.MAT["leaf_mid"] if k % 2 else C.MAT["leaf_bright"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


# ------------------------------------------------------------------ banana

def banana_leaf(B, M, size, mat):
    L = size
    W = size * 0.17
    nu, nv = 12, 8
    verts = []
    for i in range(nu + 1):
        u = i / nu
        w = W * (math.sin(math.pi * u) ** 0.35) * (1.0 - 0.1 * u)
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = v * w
            y = u * L
            z = 0.18 * math.sin(math.pi * u) * (1 - v * v)
            verts.append(M @ Vector((x, y, z)))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            B.quad([verts[a], verts[a + nv + 1],
                    verts[a + nv + 2], verts[a + 1]], mat)
    # rib
    for i in range(nu):
        p = M @ Vector((0, (i / nu) * L, 0.012))
        q = M @ Vector((0, ((i + 1) / nu) * L, 0.012))
        t = (q - p).normalized()
        side = Vector((-t.y, t.x, 0)).normalized() * 0.014
        B.quad([p - side, p + side, q + side, q - side], C.MAT["leaf_deep"])


def banana_master(name, size=1.5, leaves=4):
    B = Builder()
    for k in range(leaves):
        a = TAU * k / leaves + 0.3
        base = Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.25))
        top = Vector((math.cos(a) * 0.35, math.sin(a) * 0.35,
                      0.85 + 0.18 * k))
        cyl_between(B, base, top, 0.03, 0.015, C.MAT["leaf_deep"], 7)
        M = Matrix.Translation(top) @ Euler((math.radians(-55 - 8 * k), 0,
                                             a + 0.4)).to_matrix().to_4x4()
        banana_leaf(B, M, size * (0.9 + 0.04 * k),
                    C.MAT["leaf_bright"] if k % 2 else C.MAT["leaf_mid"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


# ------------------------------------------------------------------ bird of paradise / fern / hibiscus

def add_bract(B, base, angle, tilt, length, width, mat):
    # a curved petal-like blade
    nu, nv = 8, 3
    verts = []
    for i in range(nu + 1):
        u = i / nu
        w = width * math.sin(math.pi * (0.15 + 0.8 * u)) * (1 - 0.3 * u)
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = math.cos(angle) * length * u + math.cos(angle + math.pi / 2) * v * w
            y = math.sin(angle) * length * u + math.sin(angle + math.pi / 2) * v * w
            z = tilt * u - 0.15 * u * u
            verts.append((base[0] + x, base[1] + y, base[2] + z))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            B.quad([verts[a], verts[a + nv + 1],
                    verts[a + nv + 2], verts[a + 1]], mat)


def bird_master(name):
    B = Builder()
    # stems
    for k in range(3):
        a = k * 2.1
        top = Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.7 + 0.15 * k))
        cyl_between(B, (0, 0, 0.02), top, 0.025, 0.012,
                    C.MAT["leaf_deep"], 7)
        # leaves
        M = Matrix.Translation(top) @ Euler((math.radians(-62), 0, a + 1.0)).to_matrix().to_4x4()
        banana_leaf(B, M, 0.75 + 0.1 * k, C.MAT["leaf_mid"])
    # flower on the central stem
    base = Vector((0.0, 0.0, 0.92))
    for k in range(5):
        add_bract(B, base, TAU * k / 5, 0.45, 0.55, 0.14,
                  C.MAT["flower_orange"] if k % 2 else C.MAT["flower_coral"])
    for k in range(3):
        add_bract(B, (0.0, 0.0, 0.96), TAU * k / 3 + 0.4, 0.35, 0.35, 0.07,
                  C.MAT["flower_lav"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def fern_master(name, fronds=7, size=0.75):
    B = Builder()
    for k in range(fronds):
        a = TAU * k / fronds + 0.2
        base = (math.cos(a) * 0.08, math.sin(a) * 0.08, 0.08)
        # reuse the palm frond logic with smaller leaflet length
        bx, by, bz = base
        pts = []
        n = 9
        for i in range(n + 1):
            u = i / n
            x = bx + math.cos(a) * size * u
            y = by + math.sin(a) * size * u
            z = bz + 0.28 * math.sin(math.pi * u * 0.9) - 0.35 * u * u
            pts.append((x, y, z))
        for i in range(n):
            p = Vector(pts[i]); q = Vector(pts[i + 1])
            t = (q - p).normalized()
            side = Vector((-t.y, t.x, 0))
            B.quad([p - side * 0.016, p + side * 0.016,
                    q + side * 0.012, q - side * 0.012],
                   C.MAT["leaf_deep"])
        for s in (-1, 1):
            for i in range(7):
                u = 0.18 + 0.72 * i / 6
                p = Vector(pts[min(int(u * n), n - 1)])
                side = Vector((-math.sin(a), math.cos(a), 0))
                llen = 0.18 * (1 - 0.3 * u)
                tip = p + side * s * llen + Vector((0, 0, -0.04))
                B.quad([p - side * 0.015, p + side * 0.015,
                        tip + side * 0.006, tip - side * 0.006],
                       C.MAT["leaf_mid"] if i % 2 else C.MAT["leaf_lime"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def hibiscus_flower(B, center, size, petal_mat):
    for k in range(5):
        a = TAU * k / 5
        # a simple rounded petal quad fan
        p0 = Vector(center)
        p1 = p0 + Vector((math.cos(a - 0.3) * size, math.sin(a - 0.3) * size,
                          -0.02))
        p2 = p0 + Vector((math.cos(a) * size * 1.15, math.sin(a) * size * 1.15,
                          0.03))
        p3 = p0 + Vector((math.cos(a + 0.3) * size, math.sin(a + 0.3) * size,
                          -0.02))
        B.quad([p0, p1, p2, p3], petal_mat, smooth=True)
    add_cyl(B, (center[0], center[1], center[2] + 0.03), 0.018, 0.14,
            C.MAT["flower_yellow"], 6, (0, 0, 0))


def hibiscus_master(name):
    B = Builder()
    for k in range(9):
        a = TAU * k / 9
        top = Vector((math.cos(a) * 0.28, math.sin(a) * 0.28, 0.28 + 0.10 * (k % 3)))
        cyl_between(B, (0, 0, 0.02), top, 0.012, 0.008,
                    C.MAT["leaf_deep"], 5)
        M = Matrix.Translation(top) @ Euler((math.radians(-65), 0, a + 0.5)).to_matrix().to_4x4()
        monstera_leaf(B, M, 0.28, C.MAT["leaf_mid"], holes=False)
    for k in range(4):
        a = TAU * k / 4 + 0.3
        c = (math.cos(a) * 0.22, math.sin(a) * 0.22, 0.55 + 0.08 * k)
        hibiscus_flower(B, c, 0.16,
                        C.MAT["flower_pink"] if k % 2 else C.MAT["flower_coral"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def croton_master(name):
    """Colour break: coral, orange and lime croton leaves."""
    B = Builder()
    for k in range(7):
        a = TAU * k / 7 + 0.4
        top = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22,
                      0.42 + 0.13 * (k % 3)))
        cyl_between(B, (0, 0, 0.02), top, 0.016, 0.010,
                    C.MAT["leaf_deep"], 6)
        M = Matrix.Translation(top) @ Euler((math.radians(-52 - 10 * (k % 2)),
                                             0, a + 0.7)).to_matrix().to_4x4()
        mat = (C.MAT["flower_coral"] if k % 3 == 0 else
               C.MAT["flower_orange"] if k % 3 == 1 else
               C.MAT["flower_yellow"])
        monstera_leaf(B, M, 0.58 + 0.05 * (k % 3), mat, holes=False)
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def broadleaf_master(name):
    B = Builder()
    for k in range(4):
        a = TAU * k / 4 + 0.5
        top = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, 0.45 + 0.12 * k))
        cyl_between(B, (0, 0, 0.02), top, 0.015, 0.009,
                    C.MAT["leaf_deep"], 5)
        M = Matrix.Translation(top) @ Euler((math.radians(-62), 0, a + 0.9)).to_matrix().to_4x4()
        monstera_leaf(B, M, 0.55 + 0.05 * k,
                      C.MAT["leaf_bright"] if k % 2 else C.MAT["leaf_mid"],
                      holes=False)
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def groundcover_master(name):
    B = Builder()
    for k in range(10):
        a = TAU * k / 10
        r = 0.14
        p0 = (math.cos(a) * 0.05, math.sin(a) * 0.05, 0.01)
        p1 = (math.cos(a) * r, math.sin(a) * r, 0.12 + 0.08 * (k % 3))
        # blade as a thin triangle
        B.quad([(p0[0] - 0.02, p0[1], p0[2]), (p0[0] + 0.02, p0[1], p0[2]),
                (p1[0], p1[1], p1[2])],
               C.MAT["leaf_lime"] if k % 2 else C.MAT["leaf_mid"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


# ------------------------------------------------------------------ placement

def place(master, name, x, y, z=0.0, scale=1.0, rot=0.0, coll=None):
    ob = master.copy()
    ob.data = master.data
    ob.name = name
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (scale, scale, scale)
    ob.hide_render = False
    (coll or C.COLL["PLANTS"]).objects.link(ob)
    return ob


def person_master(name, shirt, pants, skin, arms_up=False):
    B = Builder()
    # legs
    for s in (-1, 1):
        cyl_between(B, (s * 0.095, 0, 0.02), (s * 0.095, 0, 0.74),
                    0.055, 0.052, pants, 6)
        B.add_bm(_sphere_bm(0.065, (s * 0.095, 0.03, 0.04)), Matrix.Identity(4),
                 pants)
    # torso, slightly tapered
    cyl_between(B, (0, 0, 0.70), (0, 0, 1.34), 0.155, 0.215, shirt, 8)
    B.add_bm(_sphere_bm(0.20, (0, 0, 1.35), scale=(1.0, 0.72, 0.45)),
             Matrix.Identity(4), shirt)
    # arms
    for s in (-1, 1):
        if arms_up:
            cyl_between(B, (s * 0.20, 0, 1.32), (s * 0.34, 0.02, 1.86),
                        0.048, 0.038, shirt, 6)
            B.add_bm(_sphere_bm(0.045, (s * 0.35, 0.03, 1.88)),
                     Matrix.Identity(4), skin)
        else:
            cyl_between(B, (s * 0.20, 0, 1.32), (s * 0.25, 0.02, 0.82),
                        0.048, 0.040, shirt, 6)
            B.add_bm(_sphere_bm(0.045, (s * 0.255, 0.03, 0.80)),
                     Matrix.Identity(4), skin)
    # neck + head
    cyl_between(B, (0, 0, 1.36), (0, 0, 1.44), 0.052, 0.052, skin, 6)
    B.add_bm(_sphere_bm(0.115, (0, 0.012, 1.55), scale=(0.92, 0.95, 1.08)),
             Matrix.Identity(4), skin)
    # hair cap
    B.add_bm(_sphere_bm(0.120, (0, 0.005, 1.60), scale=(0.96, 0.98, 0.62)),
             Matrix.Identity(4), C.MAT["dark_metal"])
    ob = B.finish(name, C.COLL["MASTERS"])
    ob.hide_render = True
    return ob


def _sphere_bm(r, loc, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=r)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
        v.co += Vector(loc)
    return bm


def build_crowd():
    shirts = (C.MAT["flower_coral"], C.MAT["dark_metal"],
              C.MAT["flower_yellow"], C.MAT["leaf_deep"],
              C.MAT["neon_pink"], C.MAT["white"], C.MAT["flower_orange"],
              C.MAT["dark_metal"], C.MAT["flower_lav"], C.MAT["leaf_bright"])
    pants = (C.MAT["dark_metal"], C.MAT["dark_metal"], C.MAT["white"],
             C.MAT["dark_metal"], C.MAT["dark_metal"], C.MAT["dark_metal"],
             C.MAT["dark_metal"], C.MAT["stone"], C.MAT["white"],
             C.MAT["dark_metal"])
    skins = (C.MAT["wood"], C.MAT["flower_coral"], C.MAT["wood"],
             C.MAT["flower_yellow"], C.MAT["wood"], C.MAT["stone"],
             C.MAT["wood"], C.MAT["wood"], C.MAT["flower_coral"],
             C.MAT["wood"])
    masters = []
    for i in range(10):
        masters.append(person_master("PERSON_%02d" % i, shirts[i], pants[i],
                                     skins[i], arms_up=(i in (1, 6))))
    # no ground crowd in the hero shot; only the DJ and stage performers

    # a single dark DJ silhouette behind the booth
    dj = person_master("PERSON_DJ", C.MAT["dark_metal"], C.MAT["dark_metal"],
                       C.MAT["wood"], arms_up=True)
    ob = dj.copy()
    ob.data = dj.data
    ob.name = "CROWD_DJ"
    ob.location = (0.0, 5.65, 0.60)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1.02, 1.02, 1.02)
    ob.hide_render = False
    C.COLL["CROWD"].objects.link(ob)


def build_all():
    tall = palm_master("PALM_TALL", height=7.4, crown=19, length=3.15)
    tall2 = palm_master("PALM_TALL2", height=9.0, crown=17, length=2.8)
    bed = palm_master("PALM_BED", height=4.7, crown=16, length=2.6)
    fan = fan_palm_master("FAN_PALM", height=4.6, leaves=16)
    mon = monstera_master("MONSTERA", size=1.0, leaves=5)
    mon2 = monstera_master("MONSTERA_SMALL", size=0.72, leaves=4)
    ban = banana_master("BANANA", size=1.55, leaves=4)
    bird = bird_master("BIRD")
    fern = fern_master("FERN", 8, 0.8)
    hib = hibiscus_master("HIBISCUS")
    broad = broadleaf_master("BROADLEAF")
    ground = groundcover_master("GROUNDCOVER")
    heli = heliconia_master("HELICONIA")
    croton = croton_master("CROTON")

    # layered jungle wall: three staggered rows of palms
    rows = [
        (9.8, (-12.0, -8.4, -4.6, -1.2, 2.0, 5.4, 8.8, 12.2), tall, 0.95, 0.16),
        (14.2, (-10.6, -6.0, -1.5, 3.0, 7.5, 11.0), tall2, 1.0, 0.20),
        (18.6, (-8.0, -2.0, 4.0, 9.0), tall, 1.15, 0.24),
    ]
    n = 0
    for y, xs, master, s0, jit in rows:
        for x in xs:
            place(master, "BG_PALM_%02d" % n,
                  x + C.RNG.uniform(-0.5, 0.5), y + C.RNG.uniform(-0.6, 0.6),
                  0.0, s0 + jit * C.RNG.uniform(0, 1),
                  C.RNG.uniform(0, TAU), C.COLL["TREES"])
            n += 1
    # signature fan palms framing the dome and the stage wings
    for i, (x, y, s) in enumerate(((-5.3, 8.4, 1.15), (5.3, 8.4, 1.15),
                                    (0.0, 12.6, 1.35), (-8.9, 10.4, 1.55),
                                    (8.9, 10.4, 1.55))):
        place(fan, "FAN_PALM_%02d" % i, x, y, 0.0, s,
              C.RNG.uniform(0, TAU), C.COLL["TREES"])
    for i, (x, y, s) in enumerate(((-7.2, 9.2, 2.0), (7.2, 9.2, 2.0),
                                    (-10.2, 8.6, 1.8), (10.2, 8.6, 1.8))):
        place(ban, "STAGE_BAN_%02d" % i, x, y, 0.0, s,
              C.RNG.uniform(0, TAU), C.COLL["TREES"])
    # hero palms whose crowns break the skyline above the flower
    for i, (x, y, s) in enumerate(((-3.6, 12.2, 1.45), (3.6, 12.2, 1.45),
                                    (-8.2, 10.6, 1.30), (8.2, 10.6, 1.30),
                                    (-12.4, 13.0, 1.25), (-10.4, 16.0, 1.35),
                                    (12.4, 13.0, 1.25))):
        place(tall2, "BG_HERO_%02d" % i, x, y, 0.0, s,
              C.RNG.uniform(0, TAU), C.COLL["TREES"])
    for i, x in enumerate((-10.8, -7.6, -4.4, 4.4, 7.6, 10.8)):
        place(ban, "BG_BAN_%02d" % i, x, 8.8 + 0.4 * (i % 2),
              0.0, 1.6 + 0.2 * (i % 2), C.RNG.uniform(0, TAU),
              C.COLL["TREES"])
    # side palms in the raised beds
    for i, (x, y) in enumerate(((-8.6, 4.2), (8.6, 4.2), (-9.2, -3.0),
                                 (9.2, -3.0))):
        place(bed, "BED_PALM_%02d" % i, x, y, 0.58, 0.9 + 0.1 * (i % 2),
              C.RNG.uniform(0, TAU), C.COLL["TREES"])

    # monstera / banana / bird / fern / hibiscus in the four beds
    beds = [(-8.6, -3.0), (8.6, -3.0), (-8.6, 4.2), (8.6, 4.2)]
    for bi, (bx, by) in enumerate(beds):
        for k in range(3):
            place(mon, "BED_MON_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.3, 1.3), by + C.RNG.uniform(-1.3, 1.3),
                  0.62, C.RNG.uniform(1.35, 1.8), C.RNG.uniform(0, TAU))
        for k in range(2):
            place(mon2, "BED_MON2_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.5, 1.5), by + C.RNG.uniform(-1.5, 1.5),
                  0.62, C.RNG.uniform(1.2, 1.6), C.RNG.uniform(0, TAU))
        for k in range(2):
            place(ban, "BED_BAN_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.1, 1.1), by + C.RNG.uniform(-1.1, 1.1),
                  0.62, C.RNG.uniform(1.25, 1.6), C.RNG.uniform(0, TAU))
        for k in range(3):
            place(bird, "BED_BIRD_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.2, 1.2), by + C.RNG.uniform(-1.2, 1.2),
                  0.62, C.RNG.uniform(1.35, 1.7), C.RNG.uniform(0, TAU))
        for k in range(4):
            place(fern, "BED_FERN_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.4, 1.4), by + C.RNG.uniform(-1.4, 1.4),
                  0.62, C.RNG.uniform(1.2, 1.6), C.RNG.uniform(0, TAU))
        for k in range(3):
            place(hib, "BED_HIB_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.2, 1.2), by + C.RNG.uniform(-1.2, 1.2),
                  0.62, C.RNG.uniform(1.3, 1.7), C.RNG.uniform(0, TAU))
        place(broad, "BED_BROAD_%d" % bi, bx + C.RNG.uniform(-0.8, 0.8),
              by + C.RNG.uniform(-0.8, 0.8), 0.62, 1.35,
              C.RNG.uniform(0, TAU))
        place(heli, "BED_HELI_%d" % bi, bx + C.RNG.uniform(-1.0, 1.0),
              by + C.RNG.uniform(-1.0, 1.0), 0.62, C.RNG.uniform(1.2, 1.5),
              C.RNG.uniform(0, TAU))
        for k in range(2):
            place(croton, "BED_CROTON_%d_%d" % (bi, k),
                  bx + C.RNG.uniform(-1.3, 1.3),
                  by + C.RNG.uniform(-1.3, 1.3), 0.62,
                  C.RNG.uniform(1.3, 1.7), C.RNG.uniform(0, TAU))

    # taller accents at the stage sides
    for i, (x, y, s, m) in enumerate(((-6.7, 0.3, 1.9, bird),
                                       (-7.4, -0.6, 1.7, ban),
                                       (6.7, 0.4, 1.8, ban),
                                       (7.5, -0.4, 1.7, bird))):
        place(m, "SIDE_ACCENT_%02d" % i, x, y, 0.0, s,
              C.RNG.uniform(0, TAU), C.COLL["PLANTS"])

    # low flowers hugging the pool coping
    for i in range(16):
        side = -1 if i % 2 else 1
        x = side * C.RNG.uniform(6.9, 8.0)
        y = C.RNG.uniform(-1.8, 1.2)
        place(hib, "POOL_HIB_%02d" % i, x, y, 0.0,
              C.RNG.uniform(0.8, 1.2), C.RNG.uniform(0, TAU),
              C.COLL["FLOWERS"])
        place(ground, "POOL_GC_%02d" % i, x + side * 0.3, y + 0.3, 0.0,
              C.RNG.uniform(0.8, 1.3), C.RNG.uniform(0, TAU),
              C.COLL["GROUNDCOVER"])

    # groundcover inside the beds, hugging the planter edges
    for i in range(40):
        side = -1 if i % 2 else 1
        x = side * C.RNG.uniform(6.6, 10.2)
        y = C.RNG.uniform(-4.9, 6.2)
        if abs(x) < 8.5 and abs(y) < 4.6:
            continue
        place(ground, "GC_%02d" % i, x, y, 0.62,
              C.RNG.uniform(0.8, 1.5), C.RNG.uniform(0, TAU),
              C.COLL["GROUNDCOVER"])
    build_crowd()
    print("NATURE objects=%d" % len(bpy.data.objects))
