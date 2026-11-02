"""
abyss_arch.py : building archetypes assembled from abyss_kit.

Each archetype is a complete asset - foundation, body, floor bands, facades,
entrance, roof plant - not a massing block.  Per the production rules these are
built once, bench-rendered, corrected, and only then placed repeatedly.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector


# ---------------------------------------------------------------- helpers
def _facade_row(parts, name, F, face, span, at, z, count, ww, wh, style="plain",
                glass=None, skip=()):
    """Evenly spaced windows along one facade of a rectangular building."""
    for i in range(count):
        if i in skip:
            continue
        t = (i - (count - 1) * 0.5) * (span / max(1, count))
        if face in ("S", "N"):
            lx, ly = t, at
        else:
            lx, ly = at, t
        window(parts, "%s_%s%d" % (name, face, i), F, lx, ly, z, ww, wh, face,
               style, glass)


def _emit(name, parts, coll, bevel=0.006, rot=0.0):
    m = make_master(name, parts, bevel=bevel, weighted=True)
    if m is not None:
        instance(name, coll, loc=(0.0, 0.0, 0.0))
    return m


def _arch_foundation(parts, name, F, w, d, h=1.1):
    parts.append(box(name + "_fnd", (w * 1.07, d * 1.07, h),
                     F.p(0, 0, h * 0.5 - 0.55), MAT["concrete"], C("WORK")))
    parts.append(box(name + "_lip", (w * 1.10, d * 1.10, 0.16),
                     F.p(0, 0, h - 0.50), MAT["steel"], C("WORK")))


# ---------------------------------------------------------------- residential
def apartment(name, x, y, w, d, floors, rot=0.0, coll="RESIDENTIAL",
              body=None, style="plain", seed=0):
    rng = random.Random(seed)
    F = Frame(x, y, seabed_h(x, y), rot)
    body = body or MAT["ceramic"]
    parts = []
    fh = 2.75
    H = floors * fh
    _arch_foundation(parts, name, F, w, d)
    z0 = 0.55

    # main body, with a slightly proud vertical core
    parts.append(box(name + "_body", (w, d, H), F.p(0, 0, z0 + H * 0.5),
                     body, C("WORK")))
    parts.append(box(name + "_core", (w * 0.26, d * 0.26, H * 1.06),
                     F.p(w * 0.30, -d * 0.30, z0 + H * 0.53),
                     MAT["composite"], C("WORK")))

    # floor slabs + window rows
    for f in range(floors + 1):
        z = z0 + f * fh
        if f > 0:
            parts.append(box("%s_slab%d" % (name, f), (w * 1.018, d * 1.018, 0.16),
                             F.p(0, 0, z), MAT["titanium"], C("WORK")))
        if f == floors:
            continue
        zz = z + fh * 0.60
        nz = max(2, int(w / 2.0))
        nx = max(2, int(d / 2.0))
        st = style if f < floors - 1 else "plain"
        _facade_row(parts, "%s_S%d" % (name, f), F, "S", w * 0.80,
                    -d * 0.5 - 0.02, zz, nz, 0.95, 1.30, st)
        _facade_row(parts, "%s_N%d" % (name, f), F, "N", w * 0.80,
                    d * 0.5 + 0.02, zz, nz, 0.95, 1.30, st)
        _facade_row(parts, "%s_E%d" % (name, f), F, "E", d * 0.76,
                    w * 0.5 + 0.02, zz, nx, 0.90, 1.25, st)
        _facade_row(parts, "%s_W%d" % (name, f), F, "W", d * 0.76,
                    -w * 0.5 - 0.02, zz, nx, 0.90, 1.25, st)

    # balconies on alternating floors, south face
    for f in range(1, floors):
        if f % 2 == 0:
            balcony(parts, "%s_bal%d" % (name, f), F,
                    -w * 0.22, -d * 0.5 - 0.02, z0 + f * fh + 0.10,
                    w * 0.34, 1.35, "S")

    # entrance
    door(parts, name + "_door", F, 0, -d * 0.5 - 0.02, z0, 1.5, 2.35, "S", "double")
    canopy(parts, name + "_can", F, 0, -d * 0.5 - 0.02, z0 + 2.75, 3.4, 1.9, "S")
    sign(parts, name + "_sign", F, 0, -d * 0.5 - 0.10, z0 + 3.35, 2.2, 0.42, "S",
         MAT["emit_cyan"])

    # roof
    roof_plant(parts, name + "_roof", F, 0, 0, z0 + H, w * 0.5, d * 0.5, 0.85,
               units=2)
    for s in (-1, 1):
        parts.append(box("%s_par%d" % (name, s), (w * 1.02, 0.14, 0.5),
                         F.p(0, s * d * 0.5, z0 + H + 0.25), MAT["steel_lt"],
                         C("WORK")))
    # external ladder
    ladder(parts, name + "_lad", F, w * 0.46, d * 0.42, z0, H, MAT["steel_lt"])

    return _emit(name, parts, coll)


def pod_house(name, x, y, r, rot=0.0, coll="RESIDENTIAL", seed=0, body=None):
    """Individual habitat pod: sphere shell, airlock collar, glazed band, legs."""
    F = Frame(x, y, seabed_h(x, y), rot)
    parts = []
    stem_h = r * 0.55
    cz = stem_h + r * 0.86
    for i in range(3):
        a = i * TAU / 3.0 + rot
        parts.append(cyl("%s_leg%d" % (name, i), r * 0.10, stem_h,
                         F.p(math.cos(a) * r * 0.55, math.sin(a) * r * 0.55,
                             stem_h * 0.5), MAT["steel"], C("WORK"), verts=8))
    parts.append(cyl(name + "_ring", r * 0.72, 0.22, F.p(0, 0, stem_h),
                     MAT["deck"], C("WORK"), verts=20, smooth=True))
    parts.append(ico(name + "_shell", r, F.p(0, 0, cz), body or MAT["ceramic"],
                     C("WORK"), sub=2, scale=(1.0, 0.94, 0.88)))
    parts.append(torus(name + "_kip", r * 0.98, 0.09, F.p(0, 0, cz),
                       MAT["titanium"], C("WORK"), mseg=28, nseg=5))
    # glazed observation band around the equator
    for i in range(6):
        a = i * TAU / 6.0
        window(parts, "%s_w%d" % (name, i), F,
               math.cos(a) * r * 0.97, math.sin(a) * r * 0.97, cz,
               r * 0.34, r * 0.30, "S", "plain")
    parts.append(cyl(name + "_dock", r * 0.30, 0.7, F.p(0, 0, stem_h + 0.45),
                     MAT["deck"], C("WORK"), verts=12, smooth=True))
    parts.append(sphere(name + "_bea", 0.12, F.p(0, 0, cz + r * 0.92),
                        MAT["emit_cyan"], C("WORK"), seg=8, rings=5))
    return _emit(name, parts, coll)


def terrace_row(name, x, y, units, w=4.8, d=4.6, floors=3, rot=0.0,
                coll="RESIDENTIAL", body=None, seed=0):
    """Adjoining units with stepped heights.

    The plateau has no room for more free-standing blocks: the free pockets between
    the domes are 14-20 BU wide.  A row fits those, and reads as a terrace instead
    of as another detached box, which is what the outer ring needed.
    """
    rng = random.Random(seed)
    F = Frame(x, y, seabed_h(x, y), rot)
    body = body or MAT["ceramic"]
    parts = []
    total = units * w
    _arch_foundation(parts, name, F, total, d, 1.0)
    z0 = 0.45
    base = floors * 2.75

    for i in range(units):
        ox = -total * 0.5 + w * (i + 0.5)
        h = base + rng.choice((-0.55, 0.0, 0.0, 0.55))
        fl = max(2, int(round(h / 2.75)))
        # party wall
        parts.append(box("%s_pw%d" % (name, i), (0.12, d * 1.02, h + 0.35),
                         F.p(ox - w * 0.5, 0, z0 + (h + 0.35) * 0.5),
                         MAT["titanium"], C("WORK")))
        parts.append(box("%s_u%d" % (name, i), (w * 0.995, d, h),
                         F.p(ox, 0, z0 + h * 0.5), body, C("WORK")))
        for f in range(1, fl):
            parts.append(box("%s_b%d_%d" % (name, i, f), (w * 1.01, d * 1.01, 0.14),
                             F.p(ox, 0, z0 + f * h / fl), MAT["titanium"],
                             C("WORK")))
        # front windows, one per floor; ground floor gets the door
        for f in range(fl):
            zz = z0 + (f + 0.5) * h / fl
            window(parts, "%s_S%d_%d" % (name, i, f), F, ox, -d * 0.5 - 0.02, zz,
                   1.05, 1.20, "S", "awning" if f == 0 else "plain")
            window(parts, "%s_N%d_%d" % (name, i, f), F, ox, d * 0.5 + 0.02, zz,
                   0.95, 1.10, "N", "plain")
        door(parts, "%s_d%d" % (name, i), F, ox, -d * 0.5 - 0.02, z0, 1.05, 2.25,
             "S", "single")
        parts.append(box("%s_cap%d" % (name, i), (w * 1.03, d * 1.03, 0.20),
                         F.p(ox, 0, z0 + h), MAT["steel_lt"], C("WORK")))
    roof_plant(parts, name + "_roof", F, 0, 0, z0 + base + 0.20,
               min(3.2, total * 0.4), d * 0.42, 0.75, units=2)
    return _emit(name, parts, coll)


# ---------------------------------------------------------------- commercial
SHOP_TYPES = [
    ("GROCERY", "#2FD9C4"), ("SEAFOOD", "#FFAE43"), ("RESTAURANT", "#FFD2A0"),
    ("COFFEE", "#F0975A"), ("BAKERY", "#E8C07A"), ("CONVENIENCE", "#86F08A"),
    ("PHARMACY", "#63F0E0"), ("MARINE_GEAR", "#4FA8D8"), ("DIVE_SHOP", "#48E9FF"),
    ("SOUVENIR", "#FF6BC8"), ("TECH", "#9A7BFF"), ("CLOTHING", "#F2738F"),
]


def shophouse(name, x, y, w, d, floors, rot=0.0, coll="COMMERCIAL",
              shop=(0, "SHOP", "#48E9FF"), body=None, z=None):
    """Ground-floor shopfront + upper residential floors.  The unit that makes a
    commercial street read as a street rather than a row of boxes."""
    F = Frame(x, y, seabed_h(x, y) if z is None else z, rot)
    body = body or MAT["ceramic"]
    parts = []
    fh = 2.75
    gh = 3.4                       # taller ground floor
    H = gh + (floors - 1) * fh
    _arch_foundation(parts, name, F, w, d)

    parts.append(box(name + "_body", (w, d, H), F.p(0, 0, 0.55 + H * 0.5),
                     body, C("WORK")))
    # ground floor is a different material - the shop plinth
    parts.append(box(name + "_gf", (w * 1.005, d * 1.005, gh),
                     F.p(0, 0, 0.55 + gh * 0.5), MAT["composite"], C("WORK")))
    parts.append(box(name + "_gfcap", (w * 1.03, d * 1.03, 0.22),
                     F.p(0, 0, 0.55 + gh), MAT["titanium"], C("WORK")))

    # --- shopfront: big glazing either side of the door, lit from inside
    gw = w * 0.40
    for s in (-1, 1):
        gx = s * (w * 0.5 - gw * 0.58)
        # lit back wall of the shop, deep enough that the counter silhouettes
        # against it instead of being washed out by a panel behind the glass
        parts.append(box("%s_inglow%d" % (name, s), (gw * 0.96, 0.06, gh * 0.62),
                         F.p(gx, -d * 0.5 + 2.35, 0.55 + gh * 0.42),
                         MAT["emit_shop2"], C("WORK")))
        parts.append(box("%s_gw%d" % (name, s), (gw, 0.05, gh * 0.70),
                         F.p(gx, -d * 0.5 - 0.06, 0.55 + gh * 0.42),
                         MAT["glass_win"], C("WORK")))
        # frame: outer jambs + head + transom
        for k, (ox, oz, sx, sz) in enumerate((
                (-gw * 0.5, gh * 0.42, 0.09, gh * 0.70),
                (gw * 0.5, gh * 0.42, 0.09, gh * 0.70),
                (0, gh * 0.77, gw, 0.10),
                (0, gh * 0.07, gw, 0.12),
                (0, gh * 0.55, gw, 0.06))):
            parts.append(box("%s_gwf%d_%d" % (name, s, k), (sx, 0.15, sz),
                             F.p(gx + ox, -d * 0.5 - 0.04, 0.55 + oz),
                             MAT["titanium"], C("WORK")))
    door(parts, name + "_sd", F, 0, -d * 0.5 - 0.02, 0.55, 1.4, gh * 0.74, "S",
         "double", MAT["glass_dark"])
    # shop counter visible through the glass
    furn_counter(parts, name + "_cnt", F, 0, -d * 0.5 + 1.3, 0.55,
                 w * 0.56, 0.62, 0.95, 0.0, MAT["wood"])
    # ceiling light strip, inside the glazing line
    parts.append(box(name + "_brt", (w * 0.86, 0.12, 0.09),
                     F.p(0, -d * 0.5 - 0.02, 0.55 + gh - 0.18),
                     MAT["glow_strip"], C("WORK")))
    canopy(parts, name + "_cp", F, 0, -d * 0.5 - 0.02, 0.55 + gh - 0.42,
           w * 0.94, 1.8, "S")
    if shop:
        idx, label, col = shop
        parts.append(box(name + "_sgnbk", (w * 0.76, 0.14, 0.70),
                         F.p(0, -d * 0.5 - 0.20, 0.55 + gh - 1.30), MAT["navy"],
                         C("WORK")))
        parts.append(box(name + "_sgn", (w * 0.68, 0.05, 0.50),
                         F.p(0, -d * 0.5 - 0.28, 0.55 + gh - 1.30),
                         MAT["emit_shop2"], C("WORK")))
        # hanging blade sign: dark frame with a dim panel, not a white slab
        parts.append(box(name + "_blade_f", (0.13, 0.88, 0.48),
                         F.p(-w * 0.34, -d * 0.5 - 0.52, 0.55 + gh - 1.55),
                         MAT["navy"], C("WORK")))
        parts.append(box(name + "_blade_p", (0.04, 0.74, 0.34),
                         F.p(-w * 0.34 - 0.09, -d * 0.5 - 0.52, 0.55 + gh - 1.55),
                         MAT["emit_shop"], C("WORK")))
        parts.append(box(name + "_blade_a", (0.06, 0.06, 0.50),
                         F.p(-w * 0.34, -d * 0.5 - 0.52, 0.55 + gh - 1.05),
                         MAT["steel"], C("WORK")))

    # --- upper floors
    for f in range(1, floors):
        z = 0.55 + gh + (f - 1) * fh
        parts.append(box("%s_fs%d" % (name, f), (w * 1.018, d * 1.018, 0.16),
                         F.p(0, 0, z), MAT["titanium"], C("WORK")))
        zz = z + fh * 0.62
        nz = max(2, int(w / 1.9))
        nx = max(2, int(d / 1.9))
        _facade_row(parts, "%s_S%d" % (name, f), F, "S", w * 0.80,
                    -d * 0.5 - 0.02, zz, nz, 0.9, 1.25, "awning")
        _facade_row(parts, "%s_N%d" % (name, f), F, "N", w * 0.80,
                    d * 0.5 + 0.02, zz, nz, 0.9, 1.25, "plain")
        _facade_row(parts, "%s_E%d" % (name, f), F, "E", d * 0.76,
                    w * 0.5 + 0.02, zz, nx, 0.85, 1.18, "plain")
        _facade_row(parts, "%s_W%d" % (name, f), F, "W", d * 0.76,
                    -w * 0.5 - 0.02, zz, nx, 0.85, 1.18, "plain")
        if f == 1:
            balcony(parts, name + "_balc", F, w * 0.20, -d * 0.5 - 0.02,
                    z + 0.08, w * 0.40, 1.1, "S")

    roof_plant(parts, name + "_roof", F, 0, 0, 0.55 + H, w * 0.45, d * 0.45,
               0.7, units=2)
    for s in (-1, 1):
        parts.append(box("%s_par%d" % (name, s), (w * 1.02, 0.13, 0.42),
                         F.p(0, s * d * 0.5, 0.55 + H + 0.21), MAT["steel_lt"],
                         C("WORK")))
    return _emit(name, parts, coll)


def office_tower(name, x, y, w, h, floors, rot=0.0, coll="COMMERCIAL",
                 body=None, taper=0.86):
    """Tapered banded tower: the vertical landmark of a district."""
    F = Frame(x, y, seabed_h(x, y), rot)
    body = body or MAT["ceramic"]
    parts = []
    _arch_foundation(parts, name, F, w, w, 1.3)
    z0 = 0.65

    for f in range(floors):
        t0 = f / float(floors)
        t1 = (f + 1) / float(floors)
        s0 = lerp(1.0, taper, t0)
        s1 = lerp(1.0, taper, t1)
        seg = h / floors
        parts.append(box("%s_seg%d" % (name, f),
                         (w * (s0 + s1) * 0.5, w * (s0 + s1) * 0.5, seg * 0.94),
                         F.p(0, 0, z0 + seg * (f + 0.5)), body, C("WORK")))
        parts.append(box("%s_band%d" % (name, f),
                         (w * s1 * 1.05, w * s1 * 1.05, 0.16),
                         F.p(0, 0, z0 + seg * (f + 1)), MAT["titanium"],
                         C("WORK")))
        # continuous glazing band per floor
        for face, at, span in (("S", -w * s0 * 0.5 - 0.02, w * s0 * 0.74),
                               ("N", w * s0 * 0.5 + 0.02, w * s0 * 0.74),
                               ("E", w * s0 * 0.5 + 0.02, w * s0 * 0.74),
                               ("W", -w * s0 * 0.5 - 0.02, w * s0 * 0.74)):
            if face in ("S", "N"):
                parts.append(box("%s_g%s%d" % (name, face, f),
                                 (span, 0.06, seg * 0.42),
                                 F.p(0, at, z0 + seg * (f + 0.52)),
                                 MAT["glass_win"], C("WORK")))
                parts.append(box("%s_l%s%d" % (name, face, f),
                                 (span * 0.96, 0.04, seg * 0.10),
                                 F.p(0, at - 0.06 if face == "S" else at + 0.06,
                                     z0 + seg * (f + 0.80)),
                                 MAT["glow_strip"], C("WORK")))
            else:
                parts.append(box("%s_g%s%d" % (name, face, f),
                                 (0.06, span, seg * 0.42),
                                 F.p(at, 0, z0 + seg * (f + 0.52)),
                                 MAT["glass_win"], C("WORK")))

    top = z0 + h
    parts.append(box(name + "_crown", (w * taper * 1.10, w * taper * 1.10, 0.30),
                     F.p(0, 0, top + 0.15), MAT["titanium"], C("WORK")))
    parts.append(cyl(name + "_mast", 0.10, h * 0.16,
                     F.p(0, 0, top + h * 0.08), MAT["steel_lt"], C("WORK"),
                     verts=8))
    parts.append(sphere(name + "_bea", 0.16, F.p(0, 0, top + h * 0.16),
                        MAT["emit_amber"], C("WORK"), seg=8, rings=5))
    roof_plant(parts, name + "_roof", F, 0, 0, top, w * 0.3, w * 0.3, 0.6, units=1)
    # external lift core
    parts.append(box(name + "_lift", (w * 0.18, w * 0.18, h * 0.92),
                     F.p(-w * 0.52, 0, z0 + h * 0.46), MAT["composite"], C("WORK")))
    ladder(parts, name + "_lad", F, -w * 0.62, 0, z0 + h * 0.2, h * 0.5)
    return _emit(name, parts, coll)


# ---------------------------------------------------------------- civic / research
def civic_block(name, x, y, w, d, floors, rot=0.0, coll="PUBLIC",
                body=None, accent=None):
    """Hospital / school / administration: horizontal, generous windows, a
    distinct entrance portico."""
    F = Frame(x, y, seabed_h(x, y), rot)
    body = body or MAT["ceramic"]
    accent = accent or MAT["emit_teal"]
    parts = []
    fh = 3.1
    H = floors * fh
    _arch_foundation(parts, name, F, w, d, 1.3)
    z0 = 0.65
    parts.append(box(name + "_body", (w, d, H), F.p(0, 0, z0 + H * 0.5), body,
                     C("WORK")))

    # horizontal ribbon glazing
    for f in range(floors):
        z = z0 + f * fh
        parts.append(box("%s_fs%d" % (name, f), (w * 1.03, d * 1.03, 0.20),
                         F.p(0, 0, z + fh), MAT["titanium"], C("WORK")))
        zz = z + fh * 0.58
        parts.append(box("%s_ribS%d" % (name, f), (w * 0.88, 0.07, fh * 0.40),
                         F.p(0, -d * 0.5 - 0.02, zz), MAT["glass_win"], C("WORK")))
        parts.append(box("%s_ribN%d" % (name, f), (w * 0.88, 0.07, fh * 0.40),
                         F.p(0, d * 0.5 + 0.02, zz), MAT["glass_win"], C("WORK")))
        parts.append(box("%s_ribE%d" % (name, f), (0.07, d * 0.80, fh * 0.40),
                         F.p(w * 0.5 + 0.02, 0, zz), MAT["glass_win"], C("WORK")))
        parts.append(box("%s_ribW%d" % (name, f), (0.07, d * 0.80, fh * 0.40),
                         F.p(-w * 0.5 - 0.02, 0, zz), MAT["glass_win"], C("WORK")))
        # vertical mullions
        for k in range(int(w / 2.4)):
            t = (k - (int(w / 2.4) - 1) * 0.5) * 2.4
            parts.append(box("%s_mulS%d_%d" % (name, f, k), (0.10, 0.12, fh * 0.40),
                             F.p(t, -d * 0.5 - 0.03, zz), MAT["titanium"],
                             C("WORK")))

    # entrance portico
    door(parts, name + "_door", F, 0, -d * 0.5 - 0.02, z0, 2.4, 2.9, "S", "double")
    parts.append(box(name + "_port", (w * 0.34, 2.4, 0.34),
                     F.p(0, -d * 0.5 - 1.0, z0 + 3.3), MAT["titanium"], C("WORK")))
    for s in (-1, 1):
        parts.append(cyl("%s_col%d" % (name, s), 0.16, 3.3,
                         F.p(s * w * 0.15, -d * 0.5 - 1.9, z0 + 1.65),
                         MAT["steel_lt"], C("WORK"), verts=10))
    parts.append(box(name + "_em", (w * 0.20, 0.08, 0.30),
                     F.p(0, -d * 0.5 - 2.05, z0 + 3.55), accent, C("WORK")))
    parts.append(box(name + "_crs", (w * 0.13, 0.08, 0.9),
                     F.p(0, -d * 0.5 - 2.05, z0 + 4.55), MAT["emit_green"],
                     C("WORK")))

    roof_plant(parts, name + "_roof", F, 0, 0, z0 + H, w * 0.5, d * 0.5, 0.9,
               units=2)
    for s in (-1, 1):
        parts.append(box("%s_par%d" % (name, s), (w * 1.02, 0.15, 0.55),
                         F.p(0, s * d * 0.5, z0 + H + 0.27), MAT["steel_lt"],
                         C("WORK")))
    return _emit(name, parts, coll)


def lab_block(name, x, y, w, d, floors, rot=0.0, coll="RESEARCH"):
    """Research block: louvred plant deck, instrument mast, sample hatch."""
    F = Frame(x, y, seabed_h(x, y), rot)
    parts = []
    fh = 3.0
    H = floors * fh
    _arch_foundation(parts, name, F, w, d, 1.2)
    z0 = 0.6
    parts.append(box(name + "_body", (w, d, H), F.p(0, 0, z0 + H * 0.5),
                     MAT["composite_lt"], C("WORK")))
    for f in range(floors):
        z = z0 + f * fh
        parts.append(box("%s_fs%d" % (name, f), (w * 1.03, d * 1.03, 0.18),
                         F.p(0, 0, z + fh), MAT["titanium"], C("WORK")))
        zz = z + fh * 0.56
        n = max(3, int(w / 1.7))
        _facade_row(parts, "%s_S%d" % (name, f), F, "S", w * 0.84,
                    -d * 0.5 - 0.02, zz, n, 0.85, 1.15, "louvre")
        _facade_row(parts, "%s_N%d" % (name, f), F, "N", w * 0.84,
                    d * 0.5 + 0.02, zz, n, 0.85, 1.15, "plain")
        _facade_row(parts, "%s_E%d" % (name, f), F, "E", d * 0.80,
                    w * 0.5 + 0.02, zz, max(2, int(d / 2.2)), 0.8, 1.1, "louvre")
    # instrument mast + dishes
    top = z0 + H
    parts.append(cyl(name + "_mast", 0.14, 7.0, F.p(w * 0.32, d * 0.28, top + 3.5),
                     MAT["titanium"], C("WORK"), verts=8))
    for i in range(3):
        parts.append(cyl("%s_arm%d" % (name, i), 0.06, 2.2,
                         F.p(w * 0.32, d * 0.28, top + 2.0 + i * 1.6),
                         MAT["steel_lt"], C("WORK"),
                         rot=(0, math.pi * 0.5, rot), verts=6))
    parts.append(cyl(name + "_dish", 1.5, 0.18,
                     F.p(w * 0.32, d * 0.28, top + 6.6), MAT["alu"], C("WORK"),
                     verts=16, smooth=True))
    parts.append(sphere(name + "_bea", 0.13, F.p(w * 0.32, d * 0.28, top + 7.05),
                        MAT["emit_cyan"], C("WORK"), seg=8, rings=5))
    # external equipment bays
    for i in range(3):
        parts.append(box("%s_bay%d" % (name, i), (w * 0.20, 0.9, 1.6),
                         F.p(-w * 0.5 + 1.2 + i * w * 0.26, -d * 0.5 - 0.5, 1.4),
                         MAT["steel"], C("WORK")))
        parts.append(box("%s_bayl%d" % (name, i), (w * 0.14, 0.06, 0.5),
                         F.p(-w * 0.5 + 1.2 + i * w * 0.26, -d * 0.5 - 0.96, 1.7),
                         MAT["emit_screen"], C("WORK")))
    # sample hatch
    parts.append(cyl(name + "_hatch", 0.9, 0.4, F.p(w * 0.30, -d * 0.42, 0.85),
                     MAT["steel_lt"], C("WORK"), verts=16, smooth=True))
    parts.append(torus(name + "_hl", 0.9, 0.06, F.p(w * 0.30, -d * 0.42, 1.05),
                       MAT["paint_safe"], C("WORK"), mseg=16, nseg=4))
    roof_plant(parts, name + "_roof", F, -w * 0.25, 0, top, w * 0.35, d * 0.4,
               0.8, units=2)
    return _emit(name, parts, coll)


# ---------------------------------------------------------------- resort
def hotel_stack(name, x, y, w, d, floors, rot=0.0, coll="RESORT", body=None):
    """Hotel: stepped plan, panoramic glazing, sky lounge on top."""
    F = Frame(x, y, seabed_h(x, y), rot)
    parts = []
    fh = 3.2
    _arch_foundation(parts, name, F, w, d, 1.4)
    z0 = 0.7
    for f in range(floors):
        t = f / float(floors)
        ww = w * (1.0 - 0.16 * t)
        dd = d * (1.0 - 0.10 * t)
        ox = math.sin(f * 0.9) * w * 0.06
        z = z0 + f * fh
        parts.append(box("%s_fl%d" % (name, f), (ww, dd, fh * 0.94),
                         F.p(ox, 0, z + fh * 0.5), body or MAT["ceramic"], C("WORK")))
        parts.append(box("%s_sl%d" % (name, f), (ww * 1.06, dd * 1.06, 0.18),
                         F.p(ox, 0, z + fh), MAT["titanium"], C("WORK")))
        # panoramic band
        parts.append(box("%s_pn%d" % (name, f), (ww * 0.92, 0.07, fh * 0.46),
                         F.p(ox, -dd * 0.5 - 0.02, z + fh * 0.58),
                         MAT["glass_win"], C("WORK")))
        parts.append(box("%s_pnN%d" % (name, f), (ww * 0.92, 0.07, fh * 0.46),
                         F.p(ox, dd * 0.5 + 0.02, z + fh * 0.58),
                         MAT["glass_win"], C("WORK")))
        parts.append(box("%s_pnL%d" % (name, f), (ww * 0.86, 0.05, fh * 0.07),
                         F.p(ox, -dd * 0.5 - 0.06, z + fh * 0.84),
                         MAT["emit_shop"], C("WORK")))
    top = z0 + floors * fh
    # sky lounge: a wider drum on top
    parts.append(cyl(name + "_lounge", w * 0.40, 3.2, F.p(0, 0, top + 1.6),
                     MAT["glass_win"], C("WORK"), verts=20, smooth=True))
    parts.append(cyl(name + "_lounge_roof", w * 0.44, 0.30, F.p(0, 0, top + 3.3),
                     MAT["titanium"], C("WORK"), verts=20, smooth=True))
    parts.append(torus(name + "_lounge_ring", w * 0.41, 0.08,
                       F.p(0, 0, top + 1.6), MAT["emit_cyan"], C("WORK"),
                       mseg=24, nseg=5))
    for i in range(8):
        a = i * TAU / 8.0
        parts.append(cyl("%s_lc%d" % (name, i), 0.10, 3.2,
                         F.p(math.cos(a) * w * 0.40, math.sin(a) * w * 0.40,
                             top + 1.6), MAT["titanium"], C("WORK"), verts=6))
    # entrance
    door(parts, name + "_door", F, 0, -d * 0.5 - 0.02, z0, 2.6, 3.0, "S", "double",
         MAT["glass_dark"])
    canopy(parts, name + "_can", F, 0, -d * 0.5 - 0.02, z0 + 3.4, 6.0, 2.6, "S")
    sign(parts, name + "_sign", F, 0, -d * 0.5 - 0.20, z0 + 4.1, 3.2, 0.55, "S",
         MAT["emit_teal"])
    return _emit(name, parts, coll)


# ---------------------------------------------------------------- industrial
def industrial_hall(name, x, y, w, d, h, rot=0.0, coll="INDUSTRIAL", body=None):
    F = Frame(x, y, seabed_h(x, y), rot)
    parts = []
    _arch_foundation(parts, name, F, w, d, 1.0)
    z0 = 0.5
    parts.append(box(name + "_body", (w, d, h), F.p(0, 0, z0 + h * 0.5),
                     body or MAT["steel"], C("WORK")))
    # ribbed wall
    n = max(4, int(w / 1.6))
    for i in range(n):
        t = (i - (n - 1) * 0.5) * (w / n)
        parts.append(box("%s_rib%d" % (name, i), (0.18, d * 1.02, h * 0.92),
                         F.p(t, 0, z0 + h * 0.5), MAT["steel_lt"], C("WORK")))
    # clerestory + roof
    parts.append(box(name + "_clr", (w * 0.9, 0.10, h * 0.14),
                     F.p(0, -d * 0.5 - 0.03, z0 + h * 0.82),
                     MAT["glow_strip"], C("WORK")))
    parts.append(box(name + "_roofcap", (w * 1.03, d * 1.03, 0.22),
                     F.p(0, 0, z0 + h), MAT["titanium"], C("WORK")))
    # big doors
    door(parts, name + "_door", F, -w * 0.22, -d * 0.5 - 0.02, z0, 4.2, h * 0.62,
         "S", "double", MAT["steel_lt"])
    # pipe run along the south face
    pipe_run(parts, name + "_pipe", F,
             [(-w * 0.5, -d * 0.5 - 0.55, z0 + h * 0.72),
              (0, -d * 0.5 - 0.55, z0 + h * 0.72),
              (w * 0.5, -d * 0.5 - 0.55, z0 + h * 0.72)], 0.16, MAT["steel_lt"])
    for i in range(3):
        prop_valve(parts, "%s_vv%d" % (name, i), F,
                   -w * 0.3 + i * w * 0.3, -d * 0.5 - 0.55, z0 + h * 0.72)
    # stack
    parts.append(cyl(name + "_stack", 0.55, h * 1.4, F.p(w * 0.34, d * 0.30,
                     z0 + h * 0.7), MAT["steel"], C("WORK"), verts=14,
                     smooth=True, r2=0.40))
    ladder(parts, name + "_lad", F, -w * 0.44, d * 0.44, z0, h)
    roof_plant(parts, name + "_roof", F, -w * 0.2, 0, z0 + h, w * 0.3, d * 0.3,
               0.9, units=3)
    return _emit(name, parts, coll)


# ---------------------------------------------------------------- aggregation
def scatter_props(coll, name_prefix, xs, ys, rng, n, z_fn=None):
    """Small set dressing so a district is not just buildings on sand."""
    for i in range(n):
        x = rng.uniform(xs[0], xs[1])
        y = rng.uniform(ys[0], ys[1])
        z = seabed_h(x, y) if z_fn is None else z_fn(x, y)
        r = rng.random()
        nm = "%s_P%d" % (name_prefix, i)
        F = Frame(x, y, z, rng.uniform(0, TAU))
        parts = []
        if r < 0.4:
            prop_crate(parts, nm, F, 0, 0, 0, rng.uniform(0.5, 0.9))
        elif r < 0.7:
            prop_barrel(parts, nm, F, 0, 0, 0, rng.uniform(0.26, 0.36))
        else:
            prop_bin(parts, nm, F, 0, 0, 0)
        _emit(nm, parts, coll, bevel=0.006)
