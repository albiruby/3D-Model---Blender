"""
abyss_eco.py : the reef, the kelp forest and the living edges of the city.

M3's first rule here is that nothing is a blob.  Each coral type has a different
silhouette - branching, domed, tabular, tubular, fan - because from the hero camera
at 15 px/BU what separates one reef from another is shape, not colour.

Placement is banded by plateau radius: reef on the rim outside the built ring,
kelp in the abyss beyond the drop, planting inside the districts.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector

ECO = {}
CORAL_MATS = ("coral_blue", "coral_lime", "coral_orange", "coral_pink",
              "coral_purple")


def _eco_m(name, parts, bevel=0.004):
    ob = make_master(name, parts, bevel=bevel, weighted=True)
    ECO[name] = ob
    return ob


def _cmat(rng):
    return MAT[CORAL_MATS[rng.randrange(len(CORAL_MATS))]]


# ---------------------------------------------------------------- coral
def _branch(bm, base, direction, length, radius, depth, rng):
    """Recursive tapered branch written straight into one bmesh."""
    end = base + direction * length
    seg = 5 if depth > 0 else 4
    tmp = bmesh.new()
    bmesh.ops.create_cone(tmp, cap_ends=True, segments=seg,
                          radius1=radius, radius2=radius * 0.62,
                          depth=length)
    # orient +Z onto direction
    quat = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    mat = quat.to_matrix().to_4x4()
    mat.translation = (base + end) * 0.5
    bmesh.ops.transform(tmp, matrix=mat, verts=tmp.verts)
    me = bpy.data.meshes.new("_t")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    if depth <= 0:
        return
    for i in range(2 if depth > 1 else 3):
        a = rng.uniform(0, TAU)
        tilt = rng.uniform(0.35, 0.85)
        nd = Vector((math.cos(a) * tilt, math.sin(a) * tilt, 1.0)).normalized()
        nd = (direction * 0.35 + nd * 0.75).normalized()
        _branch(bm, end, nd, length * rng.uniform(0.58, 0.76),
                radius * 0.62, depth - 1, rng)


def coral_branch(seed=0):
    rng = random.Random(seed + 11)
    bm = bmesh.new()
    for i in range(3):
        a = i * TAU / 3.0 + rng.uniform(-0.3, 0.3)
        d = Vector((math.cos(a) * 0.28, math.sin(a) * 0.28, 1.0)).normalized()
        _branch(bm, Vector((math.cos(a) * 0.16, math.sin(a) * 0.16, 0)),
                d, 0.62, 0.085, 2, rng)
    me = bpy.data.meshes.new("CORAL_BRANCH")
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(_cmat(rng))
    ob = bpy.data.objects.new("CORAL_BRANCH", me)
    C("WORK").objects.link(ob)
    return _eco_m("CORAL_BRANCH", [ob])


def coral_brain(seed=0):
    rng = random.Random(seed + 21)
    parts = []
    parts.append(ico("CB_B", 0.60, (0, 0, 0.30), _cmat(rng), C("WORK"), sub=2,
                     scale=(1.0, 1.0, 0.68)))
    for i in range(4):
        parts.append(torus("CB_R%d" % i, 0.16 + i * 0.10, 0.045,
                           (0, 0, 0.30 + 0.13 - i * 0.02), _cmat(rng),
                           C("WORK"), mseg=18, nseg=4))
    return _eco_m("CORAL_BRAIN", parts)


def coral_table(seed=0):
    rng = random.Random(seed + 31)
    parts = []
    parts.append(cyl("CT_S", 0.11, 0.75, (0, 0, 0.36), _cmat(rng), C("WORK"),
                     verts=7))
    parts.append(ico("CT_T", 0.70, (0, 0, 0.74), _cmat(rng), C("WORK"), sub=2,
                     scale=(1.0, 1.0, 0.16)))
    for i in range(3):
        a = i * TAU / 3.0
        parts.append(cyl("CT_P%d" % i, 0.05, 0.26,
                         (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.62),
                         _cmat(rng), C("WORK"), verts=5))
    return _eco_m("CORAL_TABLE", parts)


def coral_tube(seed=0):
    rng = random.Random(seed + 41)
    parts = []
    for i in range(6):
        a = i * TAU / 6.0 + rng.uniform(-0.2, 0.2)
        r = rng.uniform(0.10, 0.22)
        d = rng.uniform(0.55, 1.35)
        parts.append(cyl("CU_T%d" % i, r, d,
                         (math.cos(a) * rng.uniform(0.10, 0.42),
                          math.sin(a) * rng.uniform(0.10, 0.42), d * 0.5),
                         _cmat(rng), C("WORK"), verts=8, r2=r * 0.86))
    return _eco_m("CORAL_TUBE", parts)


def coral_fan(seed=0):
    rng = random.Random(seed + 51)
    parts = []
    parts.append(cyl("CF_S", 0.07, 0.9, (0, 0, 0.42), MAT["coral_pink"],
                     C("WORK"), verts=6))
    n = 7
    for i in range(n):
        a = -0.62 + i * (1.24 / (n - 1))
        h = 0.55 + 0.35 * math.cos(a * 1.6)
        plate = box("CF_P%d" % i, (0.03, 0.30, h),
                    (0, 0, 0.80 + h * 0.32), MAT["coral_pink"], C("WORK"))
        plate.rotation_euler = (0.0, a, 0.0)
        parts.append(plate)
    return _eco_m("CORAL_FAN", parts)


# ---------------------------------------------------------------- vegetation
def kelp(seed=0, h=9.0):
    rng = random.Random(seed + 61)
    parts = []
    n = 7
    for i in range(n):
        t = i / float(n)
        z = 0.4 + t * h
        x = math.sin(t * 3.1) * 0.55
        parts.append(cyl("KL_S%d" % i, 0.13 * (1.0 - t * 0.7), h / n + 0.12,
                         (x, 0, z), MAT["kelp"], C("WORK"), verts=6))
        for k in range(2):
            a = rng.uniform(0, TAU)
            blade = box("KL_B%d_%d" % (i, k), (0.06, 0.85, 0.02),
                        (x + math.cos(a) * 0.42, math.sin(a) * 0.42, z),
                        MAT["kelp_lt"] if k else MAT["kelp"], C("WORK"))
            blade.rotation_euler = (rng.uniform(-0.3, 0.3), 0.0, a)
            parts.append(blade)
    return _eco_m("KELP", parts)


def seagrass(seed=0):
    rng = random.Random(seed + 71)
    parts = []
    for i in range(11):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.0, 0.55)
        h = rng.uniform(0.7, 1.9)
        blade = box("SG_B%d" % i, (0.09, 0.02, h),
                    (math.cos(a) * r, math.sin(a) * r, h * 0.5),
                    MAT["seagrass"], C("WORK"))
        blade.rotation_euler = (rng.uniform(-0.22, 0.22),
                                rng.uniform(-0.22, 0.22), a)
        parts.append(blade)
    return _eco_m("SEAGRASS", parts)


def biolum_cluster(seed=0):
    rng = random.Random(seed + 81)
    parts = []
    for i in range(7):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.05, 0.55)
        h = rng.uniform(0.25, 0.95)
        parts.append(cyl("BL_S%d" % i, 0.025, h,
                         (math.cos(a) * r, math.sin(a) * r, h * 0.5),
                         MAT["algae"], C("WORK"), verts=4))
        parts.append(sphere("BL_G%d" % i, rng.uniform(0.05, 0.10),
                            (math.cos(a) * r, math.sin(a) * r, h + 0.04),
                            MAT["emit_cyan"] if i % 3 else MAT["emit_teal"],
                            C("WORK"), seg=8, rings=5))
    return _eco_m("BIOLUM", parts)


def reef_rock(seed=0):
    rng = random.Random(seed + 91)
    parts = []
    for i in range(3):
        parts.append(ico("RR_%d" % i, rng.uniform(0.5, 1.0),
                         (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5),
                          rng.uniform(0.10, 0.28)),
                         MAT["rock"] if i else MAT["rock_dk"], C("WORK"),
                         sub=1, scale=(1.0, 0.9, rng.uniform(0.55, 0.8)),
                         flat=True))
    return _eco_m("REEF_ROCK", parts)


# ---------------------------------------------------------------- scatter
def build_foreground_shelf(seed=808):
    """Near reef shelf on the camera-facing side.

    The hero frame's bottom fifth was open water.  A band of large rock and kelp just
    outside the rim fills that space and gives the drop-off a foreground to fall away
    from, instead of a black edge.
    """
    rng = random.Random(seed)
    made = 0
    for i in range(16):
        a = math.radians(rng.uniform(195.0, 345.0))
        rr = rng.uniform(0.96, 1.16)
        x = math.cos(a) * rr * PLATEAU_RX
        y = math.sin(a) * rr * PLATEAU_RY
        place("REEF_ROCK", x, y, rot=rng.uniform(0, TAU),
              s=rng.uniform(2.4, 4.6), coll="CORAL", sink=0.6, tag="shelf")
        made += 1
        if i % 2 == 0:
            place("KELP", x + rng.uniform(-3, 3), y + rng.uniform(-3, 3),
                  rot=rng.uniform(0, TAU), s=rng.uniform(1.8, 2.8),
                  coll="VEG", sink=0.3, tag="shelf")
            made += 1
        if i % 3 == 0:
            place("CORAL_TABLE", x + rng.uniform(-2, 2), y + rng.uniform(-2, 2),
                  rot=rng.uniform(0, TAU), s=rng.uniform(1.5, 2.4),
                  coll="CORAL", sink=0.2, tag="shelf")
            made += 1
    print("SHELF %d pieces" % made)
    return made


def build_ecosystem(seed=777):
    for fn in (coral_branch, coral_brain, coral_table, coral_tube, coral_fan):
        fn(seed)
    kelp(seed, 9.0)
    seagrass(seed)
    biolum_cluster(seed)
    reef_rock(seed)

    rng = random.Random(seed)

    def band(lo, hi, count, kinds, srange=(0.7, 1.6), jitter=0.0, min_free=2.4):
        made = 0
        for i in range(count):
            for _ in range(40):
                a = rng.uniform(0, TAU)
                rr = rng.uniform(lo, hi)
                x = math.cos(a) * rr * PLATEAU_RX
                y = math.sin(a) * rr * PLATEAU_RY
                if not is_free(x, y, min_free):
                    continue
                name, s = kinds[rng.randrange(len(kinds))]
                place(name, x, y, rot=rng.uniform(0, TAU),
                      s=s * rng.uniform(*srange), coll="CORAL", sink=0.12,
                      tag="reef")
                made += 1
                break
        return made

    reef = (("CORAL_BRANCH", 1.0), ("CORAL_BRAIN", 1.1), ("CORAL_TABLE", 1.0),
            ("CORAL_TUBE", 0.9), ("CORAL_FAN", 0.8), ("REEF_ROCK", 1.2))
    # 1. the rim ring: the living edge the city sits inside
    n1 = band(0.845, 0.945, 46, reef, (0.8, 1.5), min_free=1.6)
    # 2. the abyssal plain beyond the drop, sparse and large
    n2 = band(1.02, 1.32, 16, reef, (1.6, 3.0), min_free=0.0)
    # 3. inside the districts: planters, corners, street ends
    n3 = band(0.10, 0.80, 30, reef, (0.5, 0.9), min_free=1.2)
    print("REEF rim=%d abyss=%d inner=%d" % (n1, n2, n3))

    # kelp forest: tall silhouettes in the fog, both inside the rim and beyond
    kn = 0
    for i in range(26):
        for _ in range(30):
            a = rng.uniform(0, TAU)
            rr = rng.choice((rng.uniform(0.88, 0.96), rng.uniform(1.00, 1.30)))
            x = math.cos(a) * rr * PLATEAU_RX
            y = math.sin(a) * rr * PLATEAU_RY
            if not is_free(x, y, 2.2):
                continue
            place("KELP", x, y, rot=rng.uniform(0, TAU),
                  s=rng.uniform(0.85, 2.3), coll="VEG", sink=0.3, tag="kelp")
            kn += 1
            break

    # seagrass meadows where the ground is flat and nobody built
    sn = 0
    for i in range(34):
        for _ in range(24):
            a = rng.uniform(0, TAU)
            rr = rng.uniform(0.20, 0.86)
            x = math.cos(a) * rr * PLATEAU_RX
            y = math.sin(a) * rr * PLATEAU_RY
            if not is_free(x, y, 1.9):
                continue
            place("SEAGRASS", x, y, rot=rng.uniform(0, TAU),
                  s=rng.uniform(0.8, 1.7), coll="VEG", sink=0.05,
                  tag="seagrass")
            sn += 1
            break

    # bioluminescent gardens: only near the city, where their light reads
    bn = 0
    for i in range(18):
        for _ in range(24):
            a = rng.uniform(0, TAU)
            rr = rng.uniform(0.30, 0.90)
            x = math.cos(a) * rr * PLATEAU_RX
            y = math.sin(a) * rr * PLATEAU_RY
            if not is_free(x, y, 2.2):
                continue
            place("BIOLUM", x, y, rot=rng.uniform(0, TAU),
                  s=rng.uniform(0.9, 1.8), coll="VEG", sink=0.05,
                  tag="biolum")
            bn += 1
            break

    print("ECO kelp=%d seagrass=%d biolum=%d" % (kn, sn, bn))
    return n1 + n2 + n3 + kn + sn + bn
