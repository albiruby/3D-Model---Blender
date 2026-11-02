"""
island_people.py : stylised low/mid-poly islanders.

No armatures, no keyframes, no rigs - every pose is baked into the mesh from a
static joint skeleton.  Base at local z = 0, facing -Y.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# joint tables in units of body height H
HEAD_R = 0.072
NECK = 0.855
SHOULDER = 0.805
CHEST = 0.72
HIP = 0.505
KNEE = 0.275
ANKLE = 0.045
ELBOW = 0.635
WRIST = 0.475


def _limb(parts, name, p0, p1, r0, r1, mat, coll, sides=7):
    ob = cone(name, r0, r1, (Vector(p1) - Vector(p0)).length, (0, 0, 0), mat, coll,
              verts=sides)
    align_z(ob, Vector(p1) - Vector(p0))
    ob.location = (Vector(p0) + Vector(p1)) * 0.5
    parts.append(ob)
    # joint sphere hides the seam
    parts.append(sphere(name + "_j", r0 * 0.96, p0, mat, coll, seg=7, rings=5))


def person_master(name, pose="stand", H=1.75, skin=1, shirt=3, pants=1, hat=0,
                  hair=0, seed=0, apron=False, bag=False):
    coll = C("WORK")
    parts = []
    rng = random.Random(seed * 7919 + 5)
    skin_m = MAT["skin_%d" % (1 + (skin % 4))]
    shirt_m = MAT["cloth_%d" % (shirt % 10)]
    pants_m = MAT["pants_%d" % (pants % 5)]
    head_z = NECK + HEAD_R * 1.15

    # ---- skeleton (H units) ------------------------------------------------
    hip_c = Vector((0.0, 0.0, HIP))
    sh_l = Vector((-0.115, 0.0, SHOULDER))
    sh_r = Vector((0.115, 0.0, SHOULDER))
    el_l = Vector((-0.150, 0.0, ELBOW))
    el_r = Vector((0.150, 0.0, ELBOW))
    wr_l = Vector((-0.165, -0.02, WRIST))
    wr_r = Vector((0.165, -0.02, WRIST))
    hip_l = Vector((-0.062, 0.0, HIP - 0.03))
    hip_r = Vector((0.062, 0.0, HIP - 0.03))
    kn_l = Vector((-0.070, 0.0, KNEE))
    kn_r = Vector((0.070, 0.0, KNEE))
    an_l = Vector((-0.075, 0.0, ANKLE))
    an_r = Vector((0.075, 0.0, ANKLE))
    lean = 0.0
    if pose == "walk":
        kn_l += Vector((0.0, -0.10, 0.02))
        an_l += Vector((0.0, -0.18, 0.0))
        kn_r += Vector((0.0, 0.08, 0.0))
        an_r += Vector((0.0, 0.12, 0.0))
        el_l += Vector((0.02, 0.10, 0.02))
        wr_l += Vector((0.02, 0.16, 0.06))
        el_r += Vector((0.02, -0.10, 0.0))
        wr_r += Vector((0.02, -0.14, 0.02))
    elif pose == "sit":
        hip_c = Vector((0.0, 0.10, 0.30))
        sh_l = Vector((-0.115, 0.10, 0.60))
        sh_r = Vector((0.115, 0.10, 0.60))
        el_l = Vector((-0.150, -0.02, 0.50))
        el_r = Vector((0.150, -0.02, 0.50))
        wr_l = Vector((-0.165, -0.12, 0.44))
        wr_r = Vector((0.165, -0.12, 0.44))
        hip_l = Vector((-0.062, 0.10, 0.28))
        hip_r = Vector((0.062, 0.10, 0.28))
        kn_l = Vector((-0.070, -0.20, 0.28))
        kn_r = Vector((0.070, -0.20, 0.28))
        an_l = Vector((-0.075, -0.22, 0.045))
        an_r = Vector((0.075, -0.22, 0.045))
    elif pose == "fish":
        el_r = Vector((0.20, -0.10, ELBOW + 0.03))
        wr_r = Vector((0.22, -0.20, WRIST + 0.10))
        el_l = Vector((-0.17, -0.10, ELBOW - 0.02))
        wr_l = Vector((-0.16, -0.20, WRIST - 0.02))
        lean = 0.05
    elif pose == "carry":
        el_l = Vector((-0.20, -0.02, ELBOW + 0.10))
        el_r = Vector((0.20, -0.02, ELBOW + 0.10))
        wr_l = Vector((-0.16, -0.04, NECK + 0.10))
        wr_r = Vector((0.16, -0.04, NECK + 0.10))
    elif pose == "serve":
        el_r = Vector((0.16, -0.18, ELBOW + 0.02))
        wr_r = Vector((0.14, -0.34, WRIST + 0.02))
        el_l = Vector((-0.17, 0.04, ELBOW - 0.04))
        wr_l = Vector((-0.18, 0.02, WRIST - 0.10))
    elif pose == "bend":
        hip_c = Vector((0.0, 0.06, HIP - 0.03))
        sh_l = Vector((-0.115, -0.14, 0.70))
        sh_r = Vector((0.115, -0.14, 0.70))
        el_l = Vector((-0.15, -0.24, 0.58))
        el_r = Vector((0.15, -0.24, 0.58))
        wr_l = Vector((-0.16, -0.34, 0.48))
        wr_r = Vector((0.16, -0.34, 0.48))
    elif pose == "cycle":
        hip_c = Vector((0.0, 0.05, 0.60))
        sh_l = Vector((-0.115, -0.05, 0.90))
        sh_r = Vector((0.115, -0.05, 0.90))
        el_l = Vector((-0.16, -0.22, 0.80))
        el_r = Vector((0.16, -0.22, 0.80))
        wr_l = Vector((-0.17, -0.34, 0.74))
        wr_r = Vector((0.17, -0.34, 0.74))
        kn_l = Vector((-0.08, -0.12, 0.42))
        kn_r = Vector((0.08, -0.06, 0.46))
        an_l = Vector((-0.08, 0.02, 0.16))
        an_r = Vector((0.08, -0.18, 0.20))

    # pre-assemble the whole figure at the origin, then scale by H
    # torso: lofted, slightly tapered
    torso_pts = [
        (0.0, 0.0, hip_c.z - 0.02),
        (0.0, -0.005, (hip_c.z + SHOULDER) * 0.5),
        (0.0, -0.010, SHOULDER + 0.015),
    ]
    torso_r = [0.098, 0.112, 0.108]
    parts.append(loft_path(name + "_torso", torso_pts, torso_r, shirt_m, C("WORK"), sides=9))
    parts.append(sphere(name + "_hips", 0.105, (hip_c.x, hip_c.y, hip_c.z - 0.01),
                        pants_m, C("WORK"), seg=9, rings=6, scale=(1.0, 0.86, 0.8)))
    # neck + head
    parts.append(cyl(name + "_neck", 0.034, 0.055, (0, 0.005, NECK + 0.02),
                     skin_m, C("WORK"), verts=7))
    parts.append(sphere(name + "_head", HEAD_R, (0, 0.0, head_z), skin_m, C("WORK"),
                        seg=12, rings=9, scale=(0.94, 0.92, 1.06)))
    # hair / hat
    if hat == 1:      # straw hat
        parts.append(cyl(name + "_brim", 0.145, 0.014, (0, 0, head_z + HEAD_R * 0.86),
                         MAT["leaf_dry"], C("WORK"), verts=14))
        parts.append(cyl(name + "_crown", 0.070, 0.075, (0, 0, head_z + HEAD_R * 0.98),
                         MAT["leaf_dry"], C("WORK"), verts=12))
    elif hat == 2:    # cap
        parts.append(sphere(name + "_cap", HEAD_R * 1.03, (0, 0.004, head_z + 0.012),
                            shirt_m, C("WORK"), seg=10, rings=6, scale=(1, 1, 0.72)))
        parts.append(box(name + "_peak", (0.10, 0.07, 0.015), (0, -0.062, head_z + 0.012),
                         shirt_m, C("WORK")))
    else:
        parts.append(sphere(name + "_hair", HEAD_R * 1.02, (0, 0.006, head_z + 0.010),
                            MAT["hair_dark"] if hair == 0 else MAT["hair_brown"],
                            C("WORK"), seg=10, rings=7, scale=(1.0, 1.0, 0.86)))
    # arms
    _limb(parts, name + "_ual", (sh_l.x, sh_l.y, sh_l.z), (el_l.x, el_l.y, el_l.z),
          0.036, 0.030, skin_m, C("WORK"))
    _limb(parts, name + "_fal", (el_l.x, el_l.y, el_l.z), (wr_l.x, wr_l.y, wr_l.z),
          0.030, 0.024, skin_m, C("WORK"))
    _limb(parts, name + "_uar", (sh_r.x, sh_r.y, sh_r.z), (el_r.x, el_r.y, el_r.z),
          0.036, 0.030, skin_m, C("WORK"))
    _limb(parts, name + "_far", (el_r.x, el_r.y, el_r.z), (wr_r.x, wr_r.y, wr_r.z),
          0.030, 0.024, skin_m, C("WORK"))
    parts.append(sphere(name + "_hl", 0.028, (wr_l.x, wr_l.y, wr_l.z), skin_m, C("WORK"),
                        seg=6, rings=4))
    parts.append(sphere(name + "_hr", 0.028, (wr_r.x, wr_r.y, wr_r.z), skin_m, C("WORK"),
                        seg=6, rings=4))
    # legs
    _limb(parts, name + "_thl", (hip_l.x, hip_l.y, hip_l.z), (kn_l.x, kn_l.y, kn_l.z),
          0.052, 0.042, pants_m, C("WORK"))
    _limb(parts, name + "_shl", (kn_l.x, kn_l.y, kn_l.z), (an_l.x, an_l.y, an_l.z),
          0.042, 0.030, pants_m if pose != "fish" else skin_m, C("WORK"))
    _limb(parts, name + "_thr", (hip_r.x, hip_r.y, hip_r.z), (kn_r.x, kn_r.y, kn_r.z),
          0.052, 0.042, pants_m, C("WORK"))
    _limb(parts, name + "_shr", (kn_r.x, kn_r.y, kn_r.z), (an_r.x, an_r.y, an_r.z),
          0.042, 0.030, pants_m if pose != "fish" else skin_m, C("WORK"))
    for sgn, an in ((0, an_l), (1, an_r)):
        parts.append(box(name + "_ft%d" % sgn, (0.058, 0.11, 0.038),
                         (an.x, an.y - 0.022, 0.020), MAT["hair_dark"], C("WORK")))
    # optional apron / bag
    if apron:
        parts.append(box(name + "_apron", (0.16, 0.02, 0.30), (0, -0.098, 0.40),
                         MAT["fabric_w"], C("WORK")))
    if bag:
        parts.append(box(name + "_bag", (0.10, 0.06, 0.16), (0.13, 0.06, 0.40),
                         MAT["wood"], C("WORK")))

    ob = make_master(name, parts, bevel=0.0, weighted=False)
    # scale to real height
    for v in ob.data.vertices:
        v.co *= H
    return ob


def build_people_masters():
    specs = [
        ("PERSON_STAND", dict(pose="stand", hat=0)),
        ("PERSON_STAND_HAT", dict(pose="stand", hat=1)),
        ("PERSON_WALK", dict(pose="walk", hat=1)),
        ("PERSON_WALK_HAT", dict(pose="walk", hat=1)),        ("PERSON_WALK_CAP", dict(pose="walk", hat=2)),
        ("PERSON_SIT", dict(pose="sit")),
        ("PERSON_FISH", dict(pose="fish", hat=1)),
        ("PERSON_CARRY", dict(pose="carry", hat=1)),
        ("PERSON_SERVE", dict(pose="serve", apron=True)),
        ("PERSON_BEND", dict(pose="bend", hat=2)),
        ("PERSON_CYCLE", dict(pose="cycle", hat=1)),
    ]
    for i, (nm, kw) in enumerate(specs):
        person_master(nm, H=1.72, skin=i % 4, shirt=(i * 3) % 10, pants=i % 5,
                      seed=i + 1, **kw)
    print("PEOPLE MASTERS", len(specs))
