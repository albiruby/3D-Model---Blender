"""
island_nature.py : palms, broadleaf, banana, mangrove, bushes, ferns, flowers,
beach grass, rocks, coral.  Every generator returns a single joined master mesh
with its base at local z = 0.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- leaf cards
def leaf_cluster(name, center, r, count, mat, coll, seed=0,
                 leaf=0.30, flat=0.78, inner=0.55):
    """A cloud of individual leaf cards: breaks the 'sphere tree' silhouette."""
    rng = random.Random(seed * 7919 + 3)
    c = Vector(center)
    bm = bmesh.new()
    for i in range(count):
        # point on an ellipsoid shell
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if 0.05 < v.length <= 1.0:
                break
        v.normalize()
        rad = r * rng.uniform(inner, 1.0)
        p = c + Vector((v.x * rad, v.y * rad, v.z * rad * flat))
        n = (v + Vector((rng.uniform(-0.45, 0.45), rng.uniform(-0.45, 0.45),
                         rng.uniform(-0.35, 0.5)))).normalized()
        roll = rng.uniform(0, TAU)
        s = leaf * rng.uniform(0.72, 1.35)
        q = n.to_track_quat("Z", "Y").to_matrix().to_4x4()
        m = (Matrix.Translation(p) @ q @ Matrix.Rotation(roll, 4, "Z")
             @ Matrix.Diagonal(Vector((s, s * 0.62, 1.0, 1.0))))
        pts = [m @ Vector((0.0, -0.62, 0.0)), m @ Vector((-0.42, 0.0, 0.0)),
               m @ Vector((0.0, 0.62, 0.0)), m @ Vector((0.42, 0.0, 0.0))]
        vs = [bm.verts.new(p) for p in pts]
        bm.faces.new(vs)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    return ob


def _lumpify(ob, amp=0.30, freq=2.4, seed=0):
    me = ob.data
    for v in me.vertices:
        n = v.normal
        k = 1.0 + (fbm(v.co.x * freq + seed, v.co.y * freq - seed, 91, 2) - 0.5) * amp
        v.co.x += n.x * (k - 1.0) * 0.55
        v.co.y += n.y * (k - 1.0) * 0.55
        v.co.z += n.z * (k - 1.0) * 0.55
    return ob


def blob(name, r, loc, mat, coll, sub=2, scale=(1, 1, 1), amp=0.34, seed=0, freq=2.6,
         smooth=True):
    ob = ico(name, r, loc, mat, coll, sub=sub, scale=scale)
    _lumpify(ob, amp, freq, seed)
    if not smooth:
        for p in ob.data.polygons:
            p.use_smooth = False
    return ob


def palm_frond(name, base, direction, length, width, rise, droop, mat, coll,
               mats=None, seed=0, pairs=16, droop_pow=2.0):
    """Coconut frond: thin rachis carrying individual leaflets (feathery read)."""
    rng = random.Random(seed * 977 + 11)
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()

    def spine(t):
        return (Vector(base) + d * (length * t)
                + up * (rise * t - droop * (t ** droop_pow)))

    # rachis
    rp = [tuple(spine(t)) for t in [i / 7.0 for i in range(8)]]
    rr = [width * 0.075 * (1.0 - 0.6 * (i / 7.0)) + 0.012 for i in range(8)]
    parts = [loft_path(name + "_rachis", rp, rr, mat, coll, sides=5)]

    bm = bmesh.new()
    for i in range(pairs):
        t = 0.10 + 0.86 * (i / max(1, pairs - 1.0))
        p = spine(t)
        p2 = spine(min(1.0, t + 0.02))
        tang = (p2 - p).normalized()
        s = tang.cross(up).normalized()
        w = width * (math.sin(math.pi * min(1.0, t * 1.05)) ** 0.42) * (1.0 - 0.30 * t)
        ll = w * rng.uniform(0.9, 1.25) + 0.05
        for sgn in (-1, 1):
            droop_v = Vector((0, 0, -0.10 - 0.22 * t))
            tip = p + s * (sgn * ll) + tang * (ll * 0.55) + droop_v
            mid = (p + tip) * 0.5 + Vector((0, 0, 0.02))
            wid = ll * 0.30
            a = bm.verts.new(p)
            b = bm.verts.new(mid - tang * wid)
            c = bm.verts.new(tip)
            e = bm.verts.new(mid + tang * wid)
            bm.faces.new((a, b, c, e))
    me = bpy.data.meshes.new(name + "_leaflets")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mats[0] if mats else mat)
    ob = bpy.data.objects.new(name + "_leaflets", me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    parts.append(ob)
    return parts


def frond(name, base, direction, length, width, rise, droop, mat, coll,
          stations=9, droop_pow=2.0, tilt=0.0, saw=0.16):
    """Palm / fern frond: tapered ribbon with a raised centre spine."""
    d = Vector(direction).normalized()
    up = Vector((0, 0, 1))
    side = d.cross(up)
    if side.length < 1e-4:
        side = Vector((1, 0, 0))
    side.normalize()
    if tilt:
        side = (side * math.cos(tilt) + d.cross(side) * math.sin(tilt)).normalized()
    pts_l, pts_r, pts_c = [], [], []
    for i in range(stations):
        t = i / (stations - 1.0)
        p = (Vector(base) + d * (length * t)
             + up * (rise * t - droop * (t ** droop_pow)))
        w = width * (math.sin(math.pi * min(1.0, t * 1.02)) ** 0.50) * (1.0 - 0.45 * t)
        w *= 1.0 + saw * math.sin(t * 22.0)
        c = p + up * (width * 0.26 * math.sin(math.pi * t))
        pts_l.append(p - side * w)
        pts_r.append(p + side * w)
        pts_c.append(c)
    verts, faces, idx = [], [], []
    for i in range(stations):
        a = len(verts)
        verts.extend([pts_l[i], pts_c[i], pts_r[i]])
        idx.append(a)
    for i in range(stations - 1):
        a, b = idx[i], idx[i + 1]
        faces.append((a, a + 1, b + 1, b))
        faces.append((a + 1, a + 2, b + 2, b + 1))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    return ob


# ---------------------------------------------------------------- palm
def palm_master(name, height=8.0, lean=0.0, lean_dir=0.0, fronds=12,
                trunk_r=0.28, seed=0, coconuts=4):
    rng = random.Random(seed * 7919 + 13)
    coll = C("WORK")
    parts = []
    n = 14
    pts, radii = [], []
    for i in range(n):
        t = i / (n - 1.0)
        bend = (t ** 1.85) * lean
        ang = lean_dir + math.sin(t * 3.2 + seed) * 0.12
        pts.append((math.cos(ang) * bend, math.sin(ang) * bend, height * t))
        radii.append(trunk_r * (1.0 - 0.50 * t))
    parts.append(loft_path(name + "_trunk", pts, radii, MAT["trunk_palm"], coll, sides=9))
    parts.append(cone(name + "_root", trunk_r * 1.85, trunk_r * 0.92, 0.7,
                      (0, 0, 0.28), MAT["trunk_palm"], coll, verts=10))
    top = Vector(pts[-1])
    parts.append(ico(name + "_crown", trunk_r * 1.25, top + Vector((0, 0, 0.12)),
                     MAT["leaf_dark"], coll, sub=2, scale=(1, 1, 0.7)))

    mats = [MAT["leaf_dark"], MAT["leaf_mid"], MAT["leaf_light"]]
    tiers = [
        # (count, up_amt, length, rise, droop, width, droop_pow)
        (max(5, fronds - 5), 0.30, height * 0.66, height * 0.030, height * 0.44,
         height * 0.105, 2.2),
        (3, 0.95, height * 0.46, height * 0.115, height * 0.32,
         height * 0.082, 1.9),
        (2, 1.75, height * 0.26, height * 0.080, height * 0.06,
         height * 0.055, 1.6),
    ]
    k = 0
    for cnt, up_amt, ln, rise, droop, wid, dp in tiers:
        for i in range(cnt):
            a = k * TAU / fronds + rng.uniform(-0.12, 0.12)
            out = Vector((math.cos(a), math.sin(a), 0.0))
            parts.extend(palm_frond(
                name + "_fr%d" % k, top + Vector((0, 0, 0.22)) + out * (trunk_r * 0.35),
                (out.x, out.y, up_amt * rng.uniform(0.85, 1.15)), ln,
                wid, rise=rise, droop=droop,
                mat=mats[k % 3], coll=coll, mats=(mats[k % 3], mats[(k + 1) % 3]),
                seed=k + seed, pairs=13 + (k % 4), droop_pow=dp))
            k += 1
    for i in range(coconuts):
        a = rng.uniform(0, TAU)
        parts.append(sphere(name + "_coco%d" % i, trunk_r * 0.58,
                            top + Vector((math.cos(a) * trunk_r * 0.85,
                                          math.sin(a) * trunk_r * 0.85, -0.26)),
                            MAT["coconut"], coll, seg=9, rings=6))
    return make_master(name, parts, bevel=0.0, weighted=False)


def palm_variants():
    specs = [
        ("PALM_A", dict(height=9.6, lean=1.6, lean_dir=0.6, fronds=13, seed=1)),
        ("PALM_B", dict(height=7.8, lean=0.8, lean_dir=2.4, fronds=12, seed=2)),
        ("PALM_C", dict(height=11.2, lean=2.4, lean_dir=4.1, fronds=14, seed=3)),
        ("PALM_D", dict(height=6.6, lean=0.3, lean_dir=1.2, fronds=11, seed=4)),
        ("PALM_E", dict(height=8.8, lean=2.8, lean_dir=5.3, fronds=13, seed=5)),
    ]
    for name, kw in specs:
        palm_master(name, **kw)
    print("PALMS", len(specs))


# ---------------------------------------------------------------- broadleaf
def broadleaf_master(name, height=7.0, spread=3.6, seed=0, clusters=7, leaf=0.34):
    rng = random.Random(seed * 104729 + 7)
    coll = C("WORK")
    parts = []
    trunk_pts = [(0, 0, 0), (0.10, 0.04, height * 0.30), (0.02, -0.08, height * 0.56),
                 (0.14, 0.10, height * 0.74)]
    parts.append(loft_path(name + "_trunk", trunk_pts, [0.46, 0.34, 0.26, 0.19],
                           MAT["trunk"], coll, sides=9))
    parts.append(cone(name + "_root", 0.80, 0.46, 0.6, (0, 0, 0.24),
                      MAT["trunk"], coll, verts=10))
    crown = Vector(trunk_pts[-1])
    R = height * 0.42
    crown_c = crown + Vector((0.0, 0.0, R * 0.45))
    for i in range(5):
        a = i * TAU / 5 + rng.uniform(-0.35, 0.35)
        d = Vector((math.cos(a), math.sin(a), rng.uniform(0.30, 0.62))).normalized()
        ln = R * rng.uniform(0.55, 0.72)
        p0 = crown
        p1 = crown + d * (ln * 0.55)
        p2 = crown + d * ln
        parts.append(loft_path(name + "_br%d" % i, [tuple(p0), tuple(p1), tuple(p2)],
                               [0.17, 0.12, 0.07], MAT["trunk"], coll, sides=6))
    # small dark core, then a dense field of leaf cards: silhouette is broken by
    # hundreds of individual leaves rather than reading as a sphere
    parts.append(blob(name + "_core", R * 0.55, crown_c, MAT["leaf_dark"], coll,
                      sub=2, scale=(1, 1, 0.86), amp=0.55, seed=seed, freq=3.2,
                      smooth=False))
    for i in range(clusters):
        a = rng.uniform(0, TAU)
        el = rng.uniform(-0.75, 1.0)
        rr = R * rng.uniform(0.15, 0.55)
        c = crown_c + Vector((math.cos(a) * rr, math.sin(a) * rr, el * R * 0.45))
        mat = [MAT["leaf_mid"], MAT["leaf_dark"], MAT["leaf_light"]][i % 3]
        parts.append(leaf_cluster(name + "_lc%d" % i, c, R * rng.uniform(0.55, 0.72),
                                  int(150 + 50 * rng.random()), mat, coll,
                                  seed=i + seed * 13, leaf=leaf, flat=0.80, inner=0.20))
    return make_master(name, parts, bevel=0.0, weighted=False)


def broadleaf_variants():
    for name, kw in (
        ("BROADLEAF_A", dict(height=8.4, spread=4.4, seed=11, clusters=8, leaf=0.36)),
        ("BROADLEAF_B", dict(height=6.2, spread=3.1, seed=12, clusters=7, leaf=0.30)),
        ("BROADLEAF_C", dict(height=10.0, spread=5.2, seed=13, clusters=9, leaf=0.38)),
    ):
        broadleaf_master(name, **kw)
    print("BROADLEAF 3")


# ---------------------------------------------------------------- banana
def banana_master(name, height=3.0, seed=0):
    rng = random.Random(seed * 31337 + 3)
    coll = C("WORK")
    parts = []
    stem_pts = [(0, 0, 0), (0.05, 0.02, height * 0.35), (0.10, 0.04, height * 0.70),
                (0.14, 0.05, height)]
    parts.append(loft_path(name + "_stem", stem_pts, [0.21, 0.17, 0.15, 0.14],
                           MAT["leaf_banana"], coll, sides=8))
    top = Vector(stem_pts[-1])
    for i in range(9):
        a = i * TAU / 9 + rng.uniform(-0.18, 0.18)
        out = Vector((math.cos(a), math.sin(a), 0))
        f = frond(name + "_leaf%d" % i, top + Vector((0, 0, 0.10)) + out * 0.05,
                  (out.x, out.y, rng.uniform(0.25, 0.8)), height * rng.uniform(0.72, 0.95),
                  height * 0.13, rise=height * 0.05, droop=height * 0.30,
                  mat=MAT["leaf_banana"] if i % 3 else MAT["leaf_mid"],
                  coll=coll, stations=8, droop_pow=1.7, saw=0.22)
        parts.append(f)
    bc = top + Vector((0.17, 0.06, -0.34))
    parts.append(cyl(name + "_bunch", 0.055, 0.40, bc, MAT["leaf_dark"], coll, verts=6))
    for i in range(7):
        a = i * 0.9
        parts.append(cone(name + "_fruit%d" % i, 0.048, 0.02, 0.22,
                          bc + Vector((math.cos(a) * 0.11, math.sin(a) * 0.11,
                                       -0.05 - (i % 3) * 0.08)),
                          MAT["leaf_dry"], coll, verts=6))
    return make_master(name, parts, bevel=0.0, weighted=False)


# ---------------------------------------------------------------- mangrove
def mangrove_master(name, height=4.6, seed=0):
    rng = random.Random(seed * 6151 + 5)
    coll = C("WORK")
    parts = []
    trunk_top = Vector((0.0, 0.0, height * 0.52))
    parts.append(loft_path(name + "_trunk",
                           [(0, 0, 0.2), (0.1, 0.05, height * 0.22), tuple(trunk_top)],
                           [0.32, 0.25, 0.17], MAT["trunk"], coll, sides=7))
    for i in range(7):
        a = i * TAU / 7 + rng.uniform(-0.2, 0.2)
        out = Vector((math.cos(a), math.sin(a), 0))
        prow = out * rng.uniform(1.0, 1.9)
        parts.append(loft_path(name + "_root%d" % i,
                               [(prow.x, prow.y, -0.06),
                                (prow.x * 0.60, prow.y * 0.60, height * 0.15),
                                (0.02, 0.01, height * 0.40)],
                               [0.085, 0.10, 0.13], MAT["trunk"], coll, sides=6))
    for i in range(4):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.2, 1.0)
        c = trunk_top + Vector((math.cos(a) * rr, math.sin(a) * rr,
                                rng.uniform(0.3, 1.1)))
        parts.append(blob(name + "_core%d" % i, rng.uniform(0.55, 0.85), c,
                          MAT["leaf_dark"], coll, sub=2, scale=(1, 1, 0.7),
                          amp=0.45, seed=i + seed))
    for i in range(6):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.5, 1.7)
        c = trunk_top + Vector((math.cos(a) * rr, math.sin(a) * rr,
                                rng.uniform(0.2, 1.4)))
        parts.append(leaf_cluster(name + "_lc%d" % i, c, rng.uniform(0.55, 0.95),
                                  44, MAT["leaf_mid"] if i % 2 else MAT["leaf_dark"],
                                  coll, seed=i + seed * 7, leaf=0.24, flat=0.65))
    return make_master(name, parts, bevel=0.0, weighted=False)


# ---------------------------------------------------------------- ground cover
def bush_master(name, r=0.65, clumps=4, seed=0, leaf=0.17):
    rng = random.Random(seed * 911 + 1)
    coll = C("WORK")
    parts = []
    for i in range(clumps):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.0, r * 0.55)
        c = (math.cos(a) * rr, math.sin(a) * rr, rng.uniform(0.30, 0.50) * r)
        parts.append(blob(name + "_b%d" % i, r * rng.uniform(0.45, 0.72), c,
                          MAT["leaf_dark"], coll, sub=2, scale=(1, 1, 0.8),
                          amp=0.40, seed=i + seed))
    for i in range(clumps + 2):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.0, r * 0.75)
        c = (math.cos(a) * rr, math.sin(a) * rr, rng.uniform(0.25, 0.75) * r)
        parts.append(leaf_cluster(name + "_l%d" % i, c, r * rng.uniform(0.55, 0.85),
                                  int(26 + 14 * rng.random()),
                                  [MAT["leaf_mid"], MAT["leaf_light"], MAT["leaf_dark"]][i % 3],
                                  coll, seed=i + seed * 5, leaf=leaf, flat=0.8))
    return make_master(name, parts, bevel=0.0, weighted=False)


def fern_master(name, size=0.9, seed=0):
    coll = C("WORK")
    parts = []
    for i in range(8):
        a = i * TAU / 8
        out = Vector((math.cos(a), math.sin(a), 0))
        parts.append(frond(name + "_f%d" % i, (0, 0, 0.03), (out.x, out.y, 1.45),
                           size, size * 0.15, rise=size * 0.52,
                           droop=size * 0.42,
                           mat=MAT["leaf_mid"] if i % 2 else MAT["leaf_light"],
                           coll=coll, stations=7, droop_pow=1.6, saw=0.28))
    return make_master(name, parts, bevel=0.0, weighted=False)


def flower_master(name, h=0.45, petal_mat=None, seed=0):
    coll = C("WORK")
    parts = []
    rng = random.Random(seed * 53 + 9)
    pm = petal_mat or MAT["paint_coral"]
    n = 6
    for i in range(n):
        a = i * TAU / n + rng.uniform(-0.2, 0.2)
        x, y = math.cos(a) * 0.15, math.sin(a) * 0.15
        parts.append(cyl(name + "_s%d" % i, 0.010, h, (x, y, h * 0.5),
                         MAT["leaf_dark"], coll, verts=4))
        parts.append(sphere(name + "_p%d" % i, 0.070, (x, y, h),
                            pm, coll, seg=8, rings=5, scale=(1, 1, 0.42)))
        parts.append(sphere(name + "_c%d" % i, 0.026, (x, y, h + 0.010),
                            MAT["paint_yellow"], coll, seg=6, rings=4))
    return make_master(name, parts, bevel=0.0, weighted=False)


def grass_master(name, r=0.5, blades=18, seed=0):
    rng = random.Random(seed * 131 + 4)
    coll = C("WORK")
    bm = bmesh.new()
    for i in range(blades):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0, r)
        base = Vector((math.cos(a) * rr, math.sin(a) * rr, 0.0))
        hgt = rng.uniform(0.26, 0.66)
        hw = rng.uniform(0.018, 0.034)
        lean = rng.uniform(0.12, 0.40)
        ang = rng.uniform(0, TAU)
        off = Vector((math.cos(ang) * hw, math.sin(ang) * hw, 0))
        tip_off = Vector((math.cos(ang + 1.2) * lean, math.sin(ang + 1.2) * lean, 0))
        vs = [bm.verts.new(base - off), bm.verts.new(base + off),
              bm.verts.new(base + off + tip_off * 0.55 + Vector((0, 0, hgt * 0.6))),
              bm.verts.new(base - off + tip_off * 0.55 + Vector((0, 0, hgt * 0.6))),
              bm.verts.new(base + tip_off + Vector((0, 0, hgt)))]
        bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
        bm.faces.new((vs[3], vs[2], vs[4]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MAT["grass_blade"])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    return make_master(name, [ob], bevel=0.0, weighted=False)


def rock_master(name, r=1.0, seed=0, flat=0.6):
    coll = C("WORK")
    ob = ico(name + "_r", r, (0, 0, r * flat * 0.55), MAT["stone"], coll,
             sub=2, scale=(1.0, 0.85, flat))
    me = ob.data
    for v in me.vertices:
        k = 1.0 + (fbm(v.co.x * 1.6 + seed, v.co.y * 1.6 - seed, 77, 3) - 0.5) * 0.55
        v.co.x *= k
        v.co.y *= k * 0.95
        v.co.z *= 1.0 + (k - 1.0) * 0.6
    return make_master(name, [ob], bevel=0.0, weighted=False)


def coral_master(name, r=0.7, mat=None, seed=0):
    coll = C("WORK")
    rng = random.Random(seed * 37 + 2)
    parts = []
    for i in range(7):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0, r * 0.7)
        h = rng.uniform(r * 0.5, r * 1.4)
        p0 = (math.cos(a) * rr, math.sin(a) * rr, 0.0)
        p1 = (p0[0] * 1.25, p0[1] * 1.25, h)
        parts.append(loft_path(name + "_b%d" % i,
                               [p0, ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, h * 0.55), p1],
                               [r * 0.16, r * 0.12, r * 0.07],
                               mat or MAT["coral_pink"], coll, sides=5))
        parts.append(sphere(name + "_t%d" % i, r * 0.13, p1,
                            MAT["coral_orange"] if i % 2 else (mat or MAT["coral_pink"]),
                            coll, seg=6, rings=4))
    return make_master(name, parts, bevel=0.0, weighted=False)


# ---------------------------------------------------------------- build all masters
def build_nature_masters():
    palm_variants()
    broadleaf_variants()
    banana_master("BANANA_A", 3.6, 1)
    banana_master("BANANA_B", 2.9, 2)
    mangrove_master("MANGROVE_A", 5.4, 1)
    mangrove_master("MANGROVE_B", 4.3, 2)
    bush_master("BUSH_A", 0.80, 4, 1)
    bush_master("BUSH_B", 0.55, 3, 2)
    bush_master("BUSH_C", 1.05, 6, 3)
    fern_master("FERN_A", 0.85, 1)
    fern_master("FERN_B", 1.20, 2)
    flower_master("FLOWER_CORAL", 0.42, MAT["paint_coral"], 1)
    flower_master("FLOWER_BLUE", 0.38, MAT["paint_blue"], 2)
    flower_master("FLOWER_YELLOW", 0.44, MAT["paint_yellow"], 3)
    grass_master("BEACHGRASS_A", 0.60, 20, 1)
    grass_master("BEACHGRASS_B", 0.42, 14, 2)
    rock_master("ROCK_A", 1.15, 1, 0.62)
    rock_master("ROCK_B", 0.65, 2, 0.70)
    rock_master("ROCK_C", 1.90, 3, 0.55)
    coral_master("CORAL_A", 0.75, MAT["coral_pink"], 1)
    coral_master("CORAL_B", 0.60, MAT["coral_orange"], 2)
    coral_master("CORAL_C", 0.85, MAT["coral_purple"], 3)
    print("NATURE MASTERS", len(POOL))
