"""
abyss_people.py : the population.

Nine masters (three poses x three uniform colours), placed ~55 times.  At hero
framing a figure is about 26 px tall, so the read is silhouette and colour block,
not face detail - but the models still hold up in the close-up cameras, which is
where M4 will use them.

Every figure wears a pressure helmet: this is the seabed, not a beach.
"""

import bpy
import math
import random

UNIFORMS = ("CIV", "TEC", "SCI")
POSES = ("stand", "walk", "carry")


def figure(name, suit, accent, pose="stand", seed=0):
    rng = random.Random(seed)
    parts = []
    hip = 0.86
    # --- legs
    if pose == "walk":
        legs = ((0.20, 0.30), (-0.16, -0.34))
    elif pose == "carry":
        legs = ((0.16, 0.10), (-0.16, -0.10))
    else:
        legs = ((0.17, 0.0), (-0.17, 0.0))
    for i, (ox, tilt) in enumerate(legs):
        parts.append(cyl("P_L%d" % i, 0.105, 0.80, (ox, tilt * 0.28, 0.44),
                         suit, C("WORK"), rot=(tilt * 0.55, 0, 0), verts=8))
        parts.append(box("P_B%d" % i, (0.16, 0.28, 0.12),
                         (ox, tilt * 0.28 + 0.04, 0.06), accent, C("WORK")))
    # --- torso, slightly tapered
    parts.append(cyl("P_T", 0.21, 0.62, (0, 0, hip + 0.24), suit, C("WORK"),
                     verts=10, r2=0.24))
    parts.append(box("P_CH", (0.30, 0.20, 0.16), (0, 0, hip + 0.50), accent,
                     C("WORK")))
    # --- backpack / rebreather
    parts.append(box("P_PACK", (0.20, 0.30, 0.44), (0, 0.24, hip + 0.28),
                     MAT["steel"], C("WORK")))
    parts.append(cyl("P_TANK", 0.075, 0.36, (0.02, 0.40, hip + 0.30),
                     MAT["alu"], C("WORK"), verts=8))
    # --- arms
    if pose == "carry":
        arms = ((0.24, -1.35, -0.55), (-0.24, -1.35, -0.55))
    elif pose == "walk":
        arms = ((0.26, 0.55, 0.05), (-0.26, -0.55, 0.05))
    else:
        arms = ((0.26, 0.0, 0.05), (-0.26, 0.0, 0.05))
    for i, (ox, swing, lift) in enumerate(arms):
        parts.append(cyl("P_A%d" % i, 0.072, 0.60, (ox, swing * 0.20, hip + 0.22),
                         suit, C("WORK"), rot=(swing, 0, lift), verts=6))
        hz = hip + 0.22 - 0.30 if pose != "carry" else hip - 0.02
        hy = swing * 0.20 + (0.34 if pose == "carry" else 0.0)
        parts.append(sphere("P_H%d" % i, 0.075, (ox, hy, hz), MAT["fabric_grey"],
                            C("WORK"), seg=7, rings=5))
    # --- head + pressure helmet
    hz = hip + 0.72
    parts.append(sphere("P_HEAD", 0.125, (0, 0, hz), MAT["fabric_grey"],
                        C("WORK"), seg=12, rings=8))
    parts.append(ico("P_HAIR", 0.13, (0, -0.02, hz + 0.03),
                     MAT["hair_dark"] if rng.random() < 0.6 else MAT["hair_brown"],
                     C("WORK"), sub=1, scale=(1.0, 1.0, 0.72)))
    parts.append(sphere("P_HELM", 0.185, (0, 0, hz + 0.01), MAT["glass_win"],
                        C("WORK"), seg=16, rings=10))
    parts.append(torus("P_RING", 0.185, 0.030, (0, 0, hz - 0.16), accent,
                       C("WORK"), mseg=18, nseg=4))
    parts.append(cyl("P_LAMP", 0.035, 0.10, (0.10, -0.16, hz + 0.13),
                     MAT["emit_white"], C("WORK"), rot=(0.7, 0, 0), verts=6))
    if pose == "carry":
        parts.append(box("P_CRATE", (0.42, 0.30, 0.26), (0, -0.38, hip + 0.04),
                         MAT["wood_lt"], C("WORK")))
    return make_master(name, parts, bevel=0.004, weighted=True)


def build_population(seed=1010):
    rng = random.Random(seed)
    suits = (("CIV", MAT["fabric_blue"], MAT["deck"]),
             ("TEC", MAT["fabric_red"], MAT["steel"]),
             ("SCI", MAT["fabric_grey"], MAT["alu"]))
    masters = []
    for suf, suit, accent in suits:
        for pose in POSES:
            nm = "PEOPLE_%s_%s" % (suf, pose.upper())
            figure(nm, suit, accent, pose, seed=rng.randrange(9999))
            masters.append(nm)

    n = 0

    def put(nm, x, y, rot, z=None, s=1.0):
        nonlocal n
        place(nm, x, y, rot=rot, s=s, coll="PEOPLE", z=z, tag="person")
        n += 1

    # --- the high street: people on both pavements, walking its length
    for i in range(9):
        x = -13.5 + i * 2.3
        for s in (-1, 1):
            if rng.random() < 0.28:
                continue
            y = -22.6 + s * (2.7 + 0.75)
            nm = rng.choice(masters)
            put(nm, x + rng.uniform(-0.4, 0.4), y + rng.uniform(-0.25, 0.25),
                rng.uniform(0, math.tau) if "WALK" not in nm else
                (0.0 if s < 0 else math.pi))

    # --- central plaza apron: the civic crowd
    for i in range(13):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(9.0, 12.2)
        x, y = math.cos(a) * r, math.sin(a) * r
        put(rng.choice(masters), x, y, rng.uniform(0, math.tau))

    # --- harbour quay, along the edge
    for i in range(9):
        x = -15.0 + i * 3.0
        y = -32.6 + rng.uniform(-0.8, 0.8)
        put(rng.choice(masters), x, y, rng.uniform(-0.4, 3.5),
            z=seabed_h(-7.0, -34.0) + 1.10)

    # --- resort terrace and residential lanes
    for i in range(7):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(8.0, 13.0)
        put(rng.choice(masters), 14.0 + math.cos(a) * r,
            20.0 + math.sin(a) * r, rng.uniform(0, math.tau))
    for i in range(6):
        put(rng.choice(masters), -30.0 + rng.uniform(-9, 9),
            6.0 + rng.uniform(-9, 9), rng.uniform(0, math.tau))
    for i in range(4):
        put(rng.choice(masters), 32.0 + rng.uniform(-5, 5),
            2.0 + rng.uniform(-5, 5), rng.uniform(0, math.tau))

    print("POPULATION %d masters, %d placed" % (len(masters), n))
    return n
