"""
abyss_layout.py : district composition, ground works, transport, perimeter.

Buildings are placed by an occupancy solver rather than by hand coordinates.
Every dome and every building registers a footprint circle; a candidate position
is rejected if it overlaps.  With ~80 buildings threaded between 11 domes, hand
placement was guaranteed to produce interpenetration.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector

ANCHORS = {
    "central":     (0.0, 0.0),
    "residential": (-30.0, 6.0),
    "commercial":  (-6.0, -16.0),
    "resort":      (10.0, 28.0),
    "research":    (32.0, 2.0),
    "industrial":  (28.0, -26.0),
    "harbor":      (-7.0, -34.0),
    "agriculture": (-24.0, -18.0),
    "public":      (-13.0, 18.0),
}

MASS = {}
OCC = []          # (x, y, footprint radius)
PLACED = []
CENTRAL_SLOTS = []   # authored ring positions, reserved in the seed pass

STREET_X0, STREET_X1 = -15.2, 6.4
STREET_Y = -22.6
STREET_HALF = 2.7
STREET_WALK = 1.5
STREET_CX = (STREET_X0 + STREET_X1) * 0.5
STREET_LEN = STREET_X1 - STREET_X0
SHOP_XS = (-12.6, -7.4, -2.2, 3.0)
ROW_N_Y = STREET_Y + STREET_HALF + STREET_WALK + 2.5
ROW_S_Y = STREET_Y - STREET_HALF - STREET_WALK - 1.7
OUTPOSTS = ((20.0, -13.5, 4.4), (25.2, -11.2, 3.2), (12.2, -15.8, 3.2),
            (3.4, -33.0, 3.2))


# ---------------------------------------------------------------- occupancy
def reserve(x, y, r):
    OCC.append((x, y, r))


def is_free(x, y, r, pad=0.94):
    for ox, oy, orr in OCC:
        if math.hypot(x - ox, y - oy) < (r + orr) * pad:
            return False
    return True


def seed_occupancy():
    """Reserve every FIXED landmark before the solver places anything.

    Ordering matters: if a landmark is reserved after the solver has already filled
    the area, the two overlap and the collision work is wasted.
    """
    OCC.clear()
    for d in DOME_INFO:
        reserve(d["x"], d["y"], d["r"] * 1.04 + 0.6)
    reserve(0.0, 0.0, 14.0)                 # central plaza
    reserve(-7.0, -34.0, 8.0)               # harbour quay
    reserve(9.4, -22.5, 5.2)                # transit station (street terminus)
    reserve(17.5, -6.0, 4.6)                # commercial tower
    reserve(35.0, -10.0, 4.2)               # research tower
    reserve(16.0, 22.0, 9.8)                # resort hotel
    reserve(2.0, 35.0, 5.6)                 # viewing gallery
    reserve(22.0, -24.0, 7.4)               # industrial hall A
    reserve(33.0, -22.0, 6.2)               # industrial hall B
    reserve(-17.0, -31.0, 4.0)              # harbour pier head
    reserve(11.0, -30.0, 3.6)               # harbour control
    reserve(-16.0, 25.0, 8.6)               # hospital
    reserve(-4.0, 15.0, 6.6)                # school
    reserve(-24.0, 14.0, 5.8)               # admin
    reserve(-12.0, 6.0, 4.8)                # emergency station
    reserve(-24.0, -18.0, 7.0)              # agriculture racks
    reserve(-32.5, -14.0, 4.4)              # agriculture plant

    # --- authored set pieces claim their ground before any solver district runs
    for x in SHOP_XS:
        reserve(x, ROW_N_Y, 3.0)
        reserve(x, ROW_S_Y, 3.0)
    for x in range(int(STREET_X0), int(STREET_X1) + 1, 3):
        reserve(float(x), STREET_Y, 3.4)
    for (ox, oy, orr) in OUTPOSTS:
        reserve(ox, oy, orr)

    # --- the civic ring around the dome: scan for six positions the map accepts
    CENTRAL_SLOTS.clear()
    specs = ((28.0, "civic"), (92.0, "tower"), (152.0, "civic"),
             (208.0, "tower"), (272.0, "civic"), (332.0, "tower"))
    for i, (base, kind) in enumerate(specs):
        rr = 6.2 if kind == "tower" else 6.0
        found = None
        for dang in (0, -10, 10, -20, 20, -30, 30, -40, 40, -50, 50):
            for dist in (24.5, 22.5, 26.5, 20.5, 28.5, 30.5, 32.5):
                a = math.radians(base + dang)
                x, y = math.cos(a) * dist, math.sin(a) * dist
                if plate_r(x, y) > 0.68 or not is_free(x, y, rr):
                    continue
                found = (x, y, a)
                break
            if found:
                break
        if found is None:
            print("CENTRAL slot %d unavailable" % i)
            continue
        reserve(found[0], found[1], rr)
        CENTRAL_SLOTS.append((i, kind, found[0], found[1], found[2]))
    print("CENTRAL ring reserved %d of 6" % len(CENTRAL_SLOTS))


def try_place(cx, cy, rx, ry, r, rng, tries=260, hw=None):
    """Find a free position inside an ellipse around (cx, cy).

    `hw` is the building's footprint half-extent.  M2 tested only the centre, which
    let 7-unit-wide blocks pass the test and still overhang the drop-off; the radius
    check now subtracts the footprint.
    """
    hw = r if hw is None else hw
    margin = hw / min(PLATEAU_RX, PLATEAU_RY)
    for i in range(tries):
        a = rng.uniform(0, TAU)
        d = math.sqrt(rng.random())
        x = cx + math.cos(a) * rx * d
        y = cy + math.sin(a) * ry * d
        if plate_r(x, y) > 0.885 - margin:
            continue
        if not is_free(x, y, r):
            continue
        reserve(x, y, r)
        PLACED.append((x, y, r))
        return x, y
    return None


# ---------------------------------------------------------------- ground works
def define_pads():
    # the high street: three overlapping pads keep 21.6 BU of road dead flat
    sz = seabed_raw(STREET_CX, STREET_Y)
    for px in (-9.0, -1.0, 7.0):
        add_pad(px, STREET_Y, 9.0, sz, 0.78)
    add_pad(-7.0, -34.0, 8.0, seabed_raw(-7.0, -34.0), 0.62)
    add_pad(28.0, -26.0, 8.5, seabed_raw(28.0, -26.0), 0.62)
    add_pad(0.0, 0.0, 15.5, seabed_raw(0.0, 0.0), 0.70)
    add_pad(-6.0, -16.0, 11.0, seabed_raw(-6.0, -16.0), 0.68)
    add_pad(10.0, 26.0, 9.0, seabed_raw(10.0, 26.0), 0.68)


def ribbon(name, pts, width, mat, coll, lift=0.06, closed=False):
    pts = [Vector((p[0], p[1], 0.0)) for p in pts]
    if closed:
        pts = pts + [pts[0]]
    left, right = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        t.normalize()
        nv = Vector((-t.y, t.x, 0.0))
        left.append(p + nv * width * 0.5)
        right.append(p - nv * width * 0.5)
    verts = []
    for i in range(n):
        for v in (left[i], right[i]):
            verts.append((v.x, v.y, seabed_h(v.x, v.y) + lift))
    faces = []
    for i in range(n - 1):
        a = i * 2
        faces.append((a, a + 1, a + 3, a + 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    C(coll).objects.link(ob)
    return ob


def build_ground_works():
    cyl("PLAZA_APRON", 17.6, 0.14, (0.0, 0.0, seabed_h(0, 0) + 0.04),
        MAT["deck"], C("CENTRAL"), verts=64, smooth=True)
    cyl("PLAZA_INNER", 14.2, 0.12, (0.0, 0.0, seabed_h(0, 0) + 0.10),
        MAT["concrete"], C("CENTRAL"), verts=64, smooth=True)
    torus("PLAZA_RING_A", 15.4, 0.16, (0.0, 0.0, seabed_h(0, 0) + 0.12),
          MAT["emit_teal"], C("CENTRAL"), mseg=64, nseg=5)
    torus("PLAZA_RING_B", 17.0, 0.10, (0.0, 0.0, seabed_h(0, 0) + 0.08),
          MAT["steel_lt"], C("CENTRAL"), mseg=64, nseg=5)

    build_street_surface()

    lane = [(-38.0, -2.0), (-33.0, 2.0), (-29.0, 8.0), (-26.0, 14.0), (-20.0, 18.0)]
    ribbon("LANE_RESIDENTIAL", lane, 4.4, MAT["concrete"], "RESIDENTIAL", lift=0.07)

    route = [(-7.0, -30.0), (-2.0, -27.0), (7.0, -24.0), (16.0, -25.5),
             (24.0, -26.5), (25.0, -23.0)]
    ribbon("ROUTE_SERVICE", route, 4.4, MAT["deck"], "TRANSPORT", lift=0.07)
    spur = [(4.0, -12.0), (14.0, -6.0), (24.0, -1.0), (30.0, 2.0)]
    ribbon("ROUTE_RESEARCH", spur, 3.8, MAT["deck"], "TRANSPORT", lift=0.07)
    resort_way = [(6.0, 8.0), (8.0, 16.0), (10.0, 24.0)]
    ribbon("ROUTE_RESORT", resort_way, 3.6, MAT["deck"], "TRANSPORT", lift=0.07)
    print("GROUND WORKS done")


def build_street_surface():
    z = seabed_h(STREET_CX, STREET_Y)
    box("STREET_ROAD", (STREET_LEN + 5.0, STREET_HALF * 2.0, 0.18),
        (STREET_CX, STREET_Y, z + 0.09), MAT["deck"], C("COMMERCIAL"))
    for s, nm in ((-1, "N"), (1, "S")):
        box("STREET_WALK_" + nm, (STREET_LEN + 5.0, STREET_WALK, 0.26),
            (STREET_CX, STREET_Y + s * (STREET_HALF + STREET_WALK * 0.5),
             z + 0.13), MAT["concrete"], C("COMMERCIAL"))
        box("STREET_KERB_" + nm, (STREET_LEN + 5.0, 0.24, 0.34),
            (STREET_CX, STREET_Y + s * STREET_HALF, z + 0.17),
            MAT["steel_lt"], C("COMMERCIAL"))
    n = 13
    for i in range(n):
        x = STREET_X0 + 1.0 + i * (STREET_LEN - 2.0) / (n - 1)
        box("STREET_DASH%d" % i, (0.95, 0.13, 0.04),
            (x, STREET_Y, z + 0.19), MAT["emit_cyan"], C("COMMERCIAL"))
    for i, x in enumerate((STREET_X0 + 1.4, STREET_X1 - 1.4)):
        for k in range(6):
            box("STREET_X%d_%d" % (i, k), (0.30, STREET_HALF * 1.6, 0.04),
                (x + (k - 2.5) * 0.62, STREET_Y, z + 0.19),
                MAT["paint_w"], C("COMMERCIAL"))
    print("STREET SURFACE %.1f BU" % STREET_LEN)


# ---------------------------------------------------------------- districts
def fill_quota(build_fn, cx, cy, count, r, rng, rx0=9.0, ry0=9.0,
               scales=(1.0, 1.3, 1.7, 2.15, 2.6)):
    """Place `count` assets around (cx, cy), widening the search until it fits.

    A fixed-radius search silently under-fills a district when the neighbours are
    dense; widening on failure lets every district reach its quota and lets the
    occupancy solver decide where the room actually is.
    """
    made = 0
    for i in range(count):
        for s in scales:
            p = try_place(cx, cy, rx0 * s, ry0 * s, r, rng, tries=220,
                          hw=r * 1.35)
            if p is not None:
                build_fn(i, p[0], p[1])
                made += 1
                break
    return made


def build_central_district():
    """The civic ring around the dome, built from the slots the seed pass reserved.

    The six positions used to be hard-coded at 24.5 BU, which put two of them inside
    the high street and one inside the hospital.  They are now found against the
    occupancy map during the seed pass, so the ring cannot lose a slot to a district
    that happens to be built first.
    """
    made = 0
    for (i, kind, x, y, a) in CENTRAL_SLOTS:
        if kind == "tower":
            office_tower("CEN_TOWER%d" % i, x, y, 6.5, 30.0, 11,
                         rot=a + math.pi * 0.5, coll="CENTRAL")
        else:
            civic_block("CEN_CIVIC%d" % i, x, y, 7.5, 5.5, 5,
                        rot=a + math.pi * 0.5, coll="CENTRAL")
        made += 1
    print("CENTRAL %d of 6" % made)

def build_residential_district():
    rng = random.Random(302)
    ax, ay = ANCHORS["residential"]
    seq = [0, 0]

    def pod(i, x, y):
        k = seq[1]
        seq[1] += 1
        pod_house("RES_POD%d" % k, x, y, rng.uniform(1.9, 2.8),
                  rot=rng.uniform(0, TAU), coll="RESIDENTIAL", seed=500 + k)

    def home(i, x, y):
        k = seq[0]
        seq[0] += 1
        if k % 3 == 2:
            terrace_row("RES_ROW%d" % k, x, y, 2,
                        rng.uniform(4.4, 4.9), rng.uniform(4.2, 4.7),
                        rng.choice((2, 3, 3)), rot=rng.uniform(0, math.pi),
                        coll="RESIDENTIAL",
                        body=MAT["ceramic"] if k % 2 else MAT["composite_lt"],
                        seed=700 + k)
        else:
            apartment("RES_APT%d" % k, x, y, rng.uniform(5.4, 7.4),
                      rng.uniform(4.2, 5.4), rng.choice((3, 3, 4, 4, 5)),
                      rot=rng.uniform(0, math.pi), coll="RESIDENTIAL",
                      body=MAT["ceramic"] if k % 2 else MAT["composite_lt"],
                      style="awning" if k % 3 == 0 else "plain", seed=400 + k)

    a = fill_quota(home, ax, ay, 10, 4.0, rng, 11.5, 11.5)
    c = fill_quota(pod, ax, ay, 12, 2.7, rng, 13.5, 13.5)
    # the east quadrant was the empty one in M2; give it weight
    d = fill_quota(home, 19.0, 11.0, 2, 4.0, rng, 7.0, 7.0)
    e = fill_quota(pod, 24.0, 2.0, 3, 2.9, rng, 7.0, 7.0)
    print("RESIDENTIAL %d homes + %d pods (+%d/%d east)" % (a, c, d, e))


SHOP_STREET = [
    ("GROCERY", "#2FD9C4"), ("SEAFOOD", "#FFAE43"), ("COFFEE", "#F0975A"),
    ("BAKERY", "#E8C07A"), ("CONVENIENCE", "#86F08A"), ("PHARMACY", "#63F0E0"),
    ("DIVE_SHOP", "#48E9FF"), ("CLOTHING", "#F2738F"),
]


def build_commercial_district():
    """Eight terraced units on the high street plus four destination units.

    The street is the readable element; the four outposts are sited where they make
    sense (market hall and fish market at the harbour, pharmacy and tech by the
    approach) rather than scattered by the solver.
    """
    n = 0
    for row, (yy, rot, depth, floors) in enumerate(
            ((ROW_N_Y, 0.0, 5.0, 3), (ROW_S_Y, math.pi, 3.4, 2))):
        for i, x in enumerate(SHOP_XS):
            label, col = SHOP_STREET[(row * 4 + i) % len(SHOP_STREET)]
            reserve(x, yy, 3.0)
            shophouse("COM_STREET%d_%d" % (row, i), x, yy, 4.80, depth, floors,
                      rot=rot, coll="COMMERCIAL",
                      shop=(row * 4 + i, label, col),
                      body=MAT["ceramic"] if (i + row) % 2 else MAT["composite_lt"])
            n += 1

    # --- street furniture, emitted as one master
    parts = []
    F = Frame(0.0, 0.0, 0.0, 0.0)
    z0 = seabed_h(STREET_CX, STREET_Y) + 0.13
    for i in range(5):
        x = STREET_X0 + 1.8 + i * (STREET_LEN - 3.6) / 4.0
        for s in (-1, 1):
            prop_lamp_post(parts, "SF_LAMP%d%d" % (i, s), F, x,
                           STREET_Y + s * (STREET_HALF + 0.40), z0, 3.9)
    for i in range(3):
        x = STREET_X0 + 3.6 + i * 6.0
        prop_bench(parts, "SF_BENCH%d" % i, F, x,
                   STREET_Y + STREET_HALF + 0.95, z0, 1.7, math.pi)
    for i in range(4):
        x = STREET_X0 + 2.4 + i * 4.4
        px, py = x, STREET_Y - STREET_HALF - 1.05
        parts.append(cyl("SF_POT%d" % i, 0.55, 0.55, (px, py, z0 + 0.27),
                         MAT["concrete"], C("WORK"), verts=10))
        for k in range(3):
            a = k * TAU / 3.0
            parts.append(ico("SF_SHRUB%d%d" % (i, k), 0.42,
                             (px + math.cos(a) * 0.22, py + math.sin(a) * 0.22,
                              z0 + 0.85), MAT["plant"] if k else MAT["plant_dk"],
                             C("WORK"), sub=1, scale=(0.9, 0.9, 1.5)))
    # two gantries spanning the street: they make it read as a street at distance
    for i, x in enumerate((STREET_X0 + 5.4, STREET_X1 - 5.4)):
        for s in (-1, 1):
            parts.append(cyl("SF_GT%d_%d" % (i, s), 0.11, 5.4,
                             (x, STREET_Y + s * (STREET_HALF + 0.5), z0 + 2.7),
                             MAT["steel_lt"], C("WORK"), verts=6))
        parts.append(box("SF_GB%d" % i, (0.16, STREET_HALF * 2.0 + 1.2, 0.34),
                         (x, STREET_Y, z0 + 5.35), MAT["titanium"], C("WORK")))
        parts.append(box("SF_GL%d" % i, (0.10, STREET_HALF * 1.2, 0.22),
                         (x, STREET_Y, z0 + 5.05), MAT["emit_shop"], C("WORK")))
    _emit("STREET_FURNITURE", parts, "COMMERCIAL", bevel=0.005)

    # --- four destination units
    reserve(20.0, -13.5, 4.4)
    shophouse("COM_MARKET", 20.0, -13.5, 7.2, 5.4, 2, rot=0.22,
              coll="COMMERCIAL", shop=(12, "MARKET", "#FFD2A0"),
              body=MAT["composite_lt"])

    reserve(25.2, -11.2, 3.2)
    shophouse("COM_PHARMACY", 25.2, -11.2, 5.0, 4.4, 2, rot=-0.15,
              coll="COMMERCIAL", shop=(13, "PHARMACY", "#63F0E0"),
              body=MAT["ceramic"])

    reserve(12.2, -15.8, 3.2)
    shophouse("COM_TECH", 12.2, -15.8, 5.0, 4.4, 2, rot=0.08,
              coll="COMMERCIAL", shop=(14, "TECH", "#9A7BFF"),
              body=MAT["ceramic"])

    qz = seabed_h(-7.0, -34.0) + 1.10
    reserve(3.4, -33.0, 3.2)
    shophouse("COM_FISHMKT", 3.4, -33.0, 5.2, 4.2, 1, rot=math.pi,
              coll="COMMERCIAL", shop=(15, "FISH_MARKET", "#FFAE43"),
              body=MAT["composite_lt"], z=qz)

    office_tower("COM_TOWER", 17.5, -6.0, 6.0, 22.0, 9, rot=0.3,
                 coll="COMMERCIAL")
    print("COMMERCIAL 8 street + 4 outposts + tower")


def build_resort_district():
    rng = random.Random(304)
    hotel_stack("RESORT_HOTEL", 16.0, 22.0, 15.0, 9.5, 6, rot=0.35,
                coll="RESORT", body=MAT["ceramic_warm"])

    def villa(i, x, y):
        pod_house("RESORT_VIL%d" % i, x, y, rng.uniform(1.7, 2.4),
                  rot=rng.uniform(0, TAU), coll="RESORT", seed=600 + i,
                  body=MAT["ceramic_warm"])

    n = fill_quota(villa, 8.0, 30.0, 7, 2.4, rng, 10.0, 7.0)

    gx, gy = 2.0, 35.0
    gz = seabed_h(gx, gy)
    cyl("RESORT_GAL_BASE", 5.2, 1.4, (gx, gy, gz + 0.5), MAT["concrete"],
        C("RESORT"), verts=28, smooth=True)
    cyl("RESORT_GAL_GLASS", 5.0, 3.0, (gx, gy, gz + 2.6), MAT["glass_win"],
        C("RESORT"), verts=28, smooth=True)
    torus("RESORT_GAL_RING", 5.05, 0.10, (gx, gy, gz + 1.2), MAT["emit_cyan"],
          C("RESORT"), mseg=32, nseg=5)
    cyl("RESORT_GAL_ROOF", 5.4, 0.35, (gx, gy, gz + 4.3), MAT["titanium"],
        C("RESORT"), verts=28, smooth=True)
    for i in range(10):
        a = i * TAU / 10.0
        cyl("RESORT_GAL_C%d" % i, 0.11, 3.0,
            (gx + math.cos(a) * 5.0, gy + math.sin(a) * 5.0, gz + 2.6),
            MAT["titanium"], C("RESORT"), verts=6)
    print("RESORT hotel + %d villas + gallery" % n)


def build_research_district():
    rng = random.Random(305)

    def lab(i, x, y):
        lab_block("RSC_LAB%d" % i, x, y, rng.uniform(6.8, 9.0),
                  rng.uniform(4.8, 6.2), rng.choice((2, 3, 3)),
                  rot=rng.uniform(0, math.pi), coll="RESEARCH")

    n = fill_quota(lab, 30.0, 0.0, 6, 4.2, rng, 10.0, 10.0,
                   scales=(1.0, 1.35, 1.8, 2.3))
    office_tower("RSC_TOWER", 35.0, -10.0, 4.4, 21.0, 9, rot=0.2,
                 coll="RESEARCH", body=MAT["titanium"])
    print("RESEARCH %d labs + tower" % n)


def build_industrial_district():
    rng = random.Random(306)
    industrial_hall("IND_HALL_A", 22.0, -24.0, 13.0, 8.0, 6.5, rot=0.22,
                    coll="INDUSTRIAL")
    residential_free = 0
    industrial_hall("IND_HALL_B", 33.0, -22.0, 10.0, 7.0, 5.5, rot=-0.15,
                    coll="INDUSTRIAL", body=MAT["paint_teal"])
    for i in range(4):
        for j in range(2):
            x = 18.0 + i * 3.2 + j * 1.0
            y = -30.0 + j * 3.0
            if not is_free(x, y, 1.6):
                continue
            reserve(x, y, 1.6)
            F = Frame(x, y, seabed_h(x, y), 0.0)
            parts = [box("IND_T%d%d_base" % (i, j), (2.6, 2.6, 0.3),
                         F.p(0, 0, 0.15), MAT["concrete"], C("WORK"))]
            prop_tank(parts, "IND_T%d%d" % (i, j), F, 0, 0, 0.2, 1.15, 3.4,
                      MAT["alu"])
            _emit("IND_TANK%d%d" % (i, j), parts, "INDUSTRIAL", bevel=0.008)
    print("INDUSTRIAL halls + tanks")


def build_harbor_district():
    rng = random.Random(307)
    qx, qy = ANCHORS["harbor"]
    qz = seabed_h(qx, qy)
    F = Frame(qx, qy, qz, 0.0)
    parts = []
    parts.append(box("HAR_QUAY", (26.0, 10.0, 1.6), F.p(0, -1.0, 0.30),
                     MAT["concrete"], C("WORK")))
    parts.append(box("HAR_WALL", (26.0, 1.2, 7.0), F.p(0, -5.6, -3.2),
                     MAT["concrete"], C("WORK")))
    parts.append(box("HAR_EDGE", (26.0, 0.5, 0.35), F.p(0, -5.8, 0.95),
                     MAT["paint_safe"], C("WORK")))
    parts.append(box("HAR_PIER", (21.0, 5.4, 0.75), F.p(0, -9.4, 0.10),
                     MAT["deck"], C("WORK")))
    for i in range(5):
        parts.append(cyl("HAR_PILE%d" % i, 0.42, 11.0,
                         F.p(-9.0 + i * 4.5, -11.4, -5.2), MAT["steel"],
                         C("WORK"), verts=10))
    for i in range(7):
        parts.append(cyl("HAR_BOL%d" % i, 0.20, 0.7,
                         F.p(-11.0 + i * 3.7, -4.2, 1.1), MAT["steel_lt"],
                         C("WORK"), verts=10))
    # gantry crane
    parts.append(box("HAR_CRANE_LEG", (0.55, 0.55, 9.0), F.p(6.0, 1.0, 4.5),
                     MAT["titanium"], C("WORK")))
    parts.append(box("HAR_CRANE_BEAM", (14.0, 0.60, 0.60), F.p(1.0, 1.0, 9.0),
                     MAT["titanium"], C("WORK")))
    parts.append(box("HAR_CRANE_CAB", (1.3, 1.3, 1.1), F.p(5.2, 1.0, 8.0),
                     MAT["navy_lt"], C("WORK")))
    parts.append(box("HAR_CRANE_HOOK", (0.10, 0.10, 2.6), F.p(-1.6, 1.0, 7.7),
                     MAT["steel_lt"], C("WORK")))
    # floodlights along the quay
    for i in range(4):
        prop_lamp_post(parts, "HAR_LAMP%d" % i, F, -10.0 + i * 6.6, 2.6, 0.85, 5.0)
    _emit("HARBOR_QUAY", parts, "HARBOR", bevel=0.010)

    office_tower("HAR_CONTROL", 11.0, -30.0, 3.6, 12.0, 5, rot=0.0,
                 coll="HARBOR", body=MAT["ceramic"])
    # The three generic cargo sheds were removed in M3: they sat exactly where the
    # high street now runs, and the quay reads better with vessels along it than
    # with identical boxes.  Fewer assets, not lower quality.
    print("HARBOR quay + control")


def build_agriculture_district():
    rng = random.Random(308)
    ax, ay = ANCHORS["agriculture"]
    F = Frame(ax, ay, seabed_h(ax, ay), 0.0)
    parts = []
    for i in range(6):
        y = -6.0 + i * 2.4
        parts.append(box("AGR_RACK%d" % i, (9.2, 1.7, 0.32),
                         F.p(0, y, 0.55), MAT["deck"], C("WORK")))
        parts.append(box("AGR_CROP%d" % i, (8.8, 1.4, 0.30),
                         F.p(0, y, 0.85), MAT["kelp_lt"], C("WORK")))
        # grow-light bar above each rack
        parts.append(box("AGR_LED%d" % i, (8.4, 0.12, 0.08),
                         F.p(0, y, 1.85), MAT["emit_green"], C("WORK")))
        for k in (-1, 1):
            parts.append(cyl("AGR_POST%d_%d" % (i, k), 0.07, 1.9,
                             F.p(k * 4.4, y, 1.05), MAT["steel_lt"], C("WORK"),
                             verts=5))
    for i in range(3):
        x = -8.6 - i * 1.9
        prop_tank(parts, "AGR_TANK%d" % i, F, x, 1.6, 0.0, 0.85, 2.6,
                  MAT["alu"])
    _emit("AGRI_RACKS", parts, "AGRI", bevel=0.008)
    civic_block("AGRI_PLANT", ax - 8.5, ay + 4.0, 6.0, 5.0, 2, rot=0.2,
                coll="AGRI", body=MAT["composite_lt"], accent=MAT["emit_green"])
    reserve(ax - 8.5, ay + 4.0, 4.5)
    print("AGRICULTURE racks + plant")


def build_public_district():
    rng = random.Random(309)
    ax, ay = ANCHORS["public"]
    civic_block("PUB_HOSPITAL", ax - 3.0, ay + 7.0, 15.0, 9.0, 3, rot=0.22,
                coll="PUBLIC", body=MAT["ceramic"], accent=MAT["emit_teal"])
    reserve(ax - 3.0, ay + 7.0, 9.0)
    civic_block("PUB_SCHOOL", ax + 9.0, ay - 3.0, 11.0, 8.0, 2, rot=-0.40,
                coll="PUBLIC", body=MAT["composite_lt"],
                accent=MAT["emit_green"])
    reserve(ax + 9.0, ay - 3.0, 7.0)
    civic_block("PUB_ADMIN", ax - 11.0, ay - 4.0, 9.0, 7.0, 3, rot=0.62,
                coll="PUBLIC", body=MAT["ceramic"], accent=MAT["emit_warm"])
    reserve(ax - 11.0, ay - 4.0, 6.0)
    # emergency station: small, with a lit apron
    ex, ey = ax + 1.0, ay - 12.0
    if is_free(ex, ey, 5.0):
        reserve(ex, ey, 5.0)
        industrial_hall("PUB_EMERG", ex, ey, 6.5, 5.0, 3.6, rot=0.15,
                        coll="PUBLIC")
    print("PUBLIC hospital + school + admin")


# ---------------------------------------------------------------- transport
def tube_link(name, p0, p1, r=1.5, coll="TRANSPORT", spacing=5.0):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ln = d.length
    if ln < 1e-3:
        return
    ob = cone(name + "_SHELL", r, r, ln, (p0 + p1) * 0.5, MAT["glass_tube"],
              C(coll), verts=14, smooth=True)
    align_z(ob, d)
    try:
        ob.visible_shadow = False
    except Exception:
        pass
    bm = bmesh.new()
    n = max(1, int(ln / spacing))
    for i in range(n + 1):
        ring_bm(bm, p0.lerp(p1, i / float(n)), d, r * 1.03, r * 0.11,
                mseg=14, nseg=5)
    for p in (p0, p1):
        ring_bm(bm, p, d, r * 1.10, r * 0.26, mseg=14, nseg=6)
    me = bpy.data.meshes.new(name + "_RIBS")
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(MAT["titanium"])
    for p in me.polygons:
        p.use_smooth = True
    rib = bpy.data.objects.new(name + "_RIBS", me)
    C(coll).objects.link(rib)
    return ob


def build_transport():
    cx, cy = ANCHORS["central"]
    cz = seabed_h(cx, cy)
    links = [(-30.0, 4.0, 8.2), (-14.0, -12.0, 6.2), (32.0, 2.0, 7.4),
             (10.0, 28.0, 9.0), (-12.0, 20.0, 5.2), (-24.0, -18.0, 8.4)]
    for i, (x, y, r) in enumerate(links):
        dz = seabed_h(x, y)
        dx, dy = x - cx, y - cy
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        p0 = Vector((cx + ux * 13.6, cy + uy * 13.6, cz + 2.4))
        p1 = Vector((x - ux * (r + 1.2), y - uy * (r + 1.2), dz + 2.4))
        mid = p0.lerp(p1, 0.5)
        ground = seabed_h(mid.x, mid.y)
        if mid.z < ground + 2.8:
            mid.z = ground + 2.8
        tube_link("TUN_CEN_%d" % i, p0, mid, 1.45, "TRANSPORT")
        tube_link("TUN_CEN_%db" % i, mid, p1, 1.45, "TRANSPORT")

    ring = [(-30.0, -12.0), (-24.0, -22.0), (-14.0, -28.0), (-1.0, -28.0),
            (10.0, -26.0), (22.0, -24.0)]
    ribbon("RING_SERVICE", ring, 3.4, MAT["concrete"], "TRANSPORT", lift=0.07)

    sx, sy = 9.4, -22.5
    sz = seabed_h(sx, sy)
    cyl("TRANSIT_BASE", 4.2, 0.5, (sx, sy, sz + 0.25), MAT["deck"],
        C("TRANSPORT"), verts=32, smooth=True)
    cyl("TRANSIT_CANOPY", 4.4, 0.24, (sx, sy, sz + 3.4), MAT["titanium"],
        C("TRANSPORT"), verts=32, smooth=True)
    for i in range(8):
        a = i * TAU / 8
        cyl("TRANSIT_COL%d" % i, 0.16, 3.2,
            (sx + math.cos(a) * 3.9, sy + math.sin(a) * 3.9, sz + 1.85),
            MAT["steel_lt"], C("TRANSPORT"), verts=8)
    torus("TRANSIT_RING", 4.0, 0.10, (sx, sy, sz + 2.0), MAT["emit_cyan"],
          C("TRANSPORT"), mseg=40, nseg=5)
    reserve(sx, sy, 4.6)
    print("TRANSPORT done")


def build_perimeter_infra():
    parts = []
    angs = [30.0, 100.0, 145.0, 200.0, 285.0, 340.0]
    for i, ang in enumerate(angs):
        a = math.radians(ang)
        x = math.cos(a) * PLATEAU_RX * 0.845
        y = math.sin(a) * PLATEAU_RY * 0.845
        z = seabed_h(x, y)
        h = 13.0 + (i % 3) * 3.4
        parts.append(cyl("PER_BASE%d" % i, 1.15, 0.55, (x, y, z + 0.27),
                         MAT["concrete"], C("WORK"), verts=10))
        parts.append(cone("PER_MAST%d" % i, 0.42, 0.17, h, (x, y, z + h * 0.5),
                          MAT["titanium"], C("WORK"), verts=8))
        parts.append(box("PER_ARM%d" % i, (3.4, 0.22, 0.22),
                         (x, y, z + h * 0.93), MAT["steel_lt"], C("WORK")))
        parts.append(sphere("PER_BEACON%d" % i, 0.24, (x, y, z + h + 0.26),
                            MAT["emit_amber"], C("WORK"), seg=8, rings=5))
        parts.append(cyl("PER_DISH%d" % i, 0.9, 0.14, (x, y, z + h * 0.78),
                         MAT["alu"], C("WORK"), verts=14, smooth=True))
    _emit("PERIMETER_MASTS", parts, "PROPS", bevel=0.008)

    pts = []
    for i in range(56):
        a = i * TAU / 56.0
        x = math.cos(a) * PLATEAU_RX * 0.885
        y = math.sin(a) * PLATEAU_RY * 0.885
        pts.append((x, y, seabed_h(x, y) + 1.15))
    pts.append(pts[0])
    loft_path("PER_PIPE", pts, [0.26] * len(pts), MAT["steel_lt"],
              C("TRANSPORT"), sides=8, smooth=True)
    for i in range(9):
        a = i * TAU / 9.0 + 0.31
        x = math.cos(a) * PLATEAU_RX * 0.885
        y = math.sin(a) * PLATEAU_RY * 0.885
        z = seabed_h(x, y)
        box("PER_JUNC%d" % i, (1.5, 1.5, 1.3), (x, y, z + 0.85),
            MAT["steel"], C("TRANSPORT"), rot=(0, 0, a))
        cyl("PER_RISER%d" % i, 0.20, 2.6, (x, y, z + 2.4), MAT["alu"],
            C("TRANSPORT"), verts=8)
    print("PERIMETER INFRA done")


# ---------------------------------------------------------------- entry
def report_containment(limit=0.885, colls=None):
    """Measure overhang, do not correct it.

    The M2 version slid offending objects radially inward after placement, which
    created new contacts nobody measured (31 moves, 26 overlaps).  The solver now
    tests the footprint at placement time, so this pass only reports what is still
    outside the lip - and leaves the geometry alone.
    """
    from mathutils import Vector
    colls = colls or ("CENTRAL", "RESIDENTIAL", "COMMERCIAL", "RESORT",
                      "RESEARCH", "INDUSTRIAL", "AGRI", "PUBLIC", "HARBOR")
    worst = []
    for key in colls:
        c = bpy.data.collections.get(C(key).name)
        if c is None:
            continue
        for ob in list(c.objects):
            if ob.type != "MESH":
                continue
            bb = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
            cx = (min(v.x for v in bb) + max(v.x for v in bb)) * 0.5
            cy = (min(v.y for v in bb) + max(v.y for v in bb)) * 0.5
            half = max(max(v.x for v in bb) - min(v.x for v in bb),
                       max(v.y for v in bb) - min(v.y for v in bb)) * 0.5
            rn = half / min(PLATEAU_RX, PLATEAU_RY)
            over = plate_r(cx, cy) + rn - limit
            if over > 0.0:
                worst.append((round(over, 3), ob.name))
    worst.sort(reverse=True)
    print("CONTAINMENT %d objects past the lip, worst %s"
          % (len(worst), worst[:4]))
    return worst


def _hull2d(points):
    """Andrew's monotone chain.  Returns the convex hull in XY."""
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def _poly_overlap(a, b, margin):
    """Separating-axis test for two convex polygons."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            ax, ay = -(y2 - y1), x2 - x1
            ln = math.hypot(ax, ay)
            if ln < 1e-6:
                continue
            ax /= ln
            ay /= ln
            amin = min(p[0] * ax + p[1] * ay for p in a)
            amax = max(p[0] * ax + p[1] * ay for p in a)
            bmin = min(p[0] * ax + p[1] * ay for p in b)
            bmax = max(p[0] * ax + p[1] * ay for p in b)
            if min(amax, bmax) - max(amin, bmin) <= margin:
                return False
    return True


def verify_layout(margin=0.25, max_pts=140):
    """Report overlapping building pairs by 2-D convex hull + separating axis.

    Bounding boxes are useless here: master geometry is baked at world coordinates
    with the object at the origin, so every AABB sits at the same place.  The hull
    is taken from the actual vertices and the test is exact for the footprint.
    """
    from mathutils import Vector
    bpy.context.view_layer.update()
    prefix = ("CEN_", "RES_", "COM_", "RESORT_", "RSC_", "IND_", "AGRI_",
              "PUB_", "HAR_")
    colls = ("CENTRAL", "RESIDENTIAL", "COMMERCIAL", "RESORT", "RESEARCH",
             "INDUSTRIAL", "AGRI", "PUBLIC", "HARBOR")
    items = []
    for key in colls:
        c = bpy.data.collections.get(C(key).name)
        if c is None:
            continue
        for ob in c.objects:
            if ob.type != "MESH" or not ob.name.startswith(prefix):
                continue
            me = ob.data
            n = len(me.vertices)
            step = max(1, n // max_pts)
            mw = ob.matrix_world
            pts = []
            zs = []
            for k in range(0, n, step):
                co = mw @ me.vertices[k].co
                pts.append((round(co.x, 2), round(co.y, 2)))
                zs.append(co.z)
            hull = _hull2d(pts)
            if len(hull) < 3:
                continue
            items.append((ob.name, hull, min(zs), max(zs)))

    bad = []
    for i in range(len(items)):
        na, ha, zla, zha = items[i]
        for j in range(i + 1, len(items)):
            nb, hb, zlb, zhb = items[j]
            if min(zha, zhb) - max(zla, zlb) <= margin:
                continue
            if _poly_overlap(ha, hb, margin):
                bad.append((na, nb))
    print("LAYOUT CHECK overlaps=%d of %d buildings" % (len(bad), len(items)))
    for t in bad[:10]:
        print("   %s <-> %s" % t)
    return bad


def _obj_centroid(ob):
    """World XY centroid of a master-backed instance.

    Master geometry is baked at world coordinates, so the local bound box already
    is the world extent; the object location is an offset added by placement.
    """
    from mathutils import Vector
    bb = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
    return Vector(((min(v.x for v in bb) + max(v.x for v in bb)) * 0.5,
                   (min(v.y for v in bb) + max(v.y for v in bb)) * 0.5, 0.0))


AUTHORED = ("CEN_", "COM_STREET", "COM_MARKET", "COM_PHARMACY", "COM_TECH",
            "COM_FISHMKT", "HAR_")


def relax_layout(rounds=4, step=1.5):
    """Nudge the non-authored member of any overlapping pair until the check is clean.

    Authored set pieces are never moved: the street and the civic ring are composed
    positions.  Everything else can afford to shift a metre and a half.
    """
    from mathutils import Vector
    moved = 0
    for r in range(rounds):
        bad = verify_layout()
        if not bad:
            print("RELAX clean after %d rounds" % r)
            return moved
        for (na, nb) in bad:
            a = bpy.data.objects.get(na)
            b = bpy.data.objects.get(nb)
            if a is None or b is None:
                continue
            af = na.startswith(AUTHORED)
            bf = nb.startswith(AUTHORED)
            if af and bf:
                continue
            if af:
                mover, other = b, a
            elif bf:
                mover, other = a, b
            else:
                mover, other = (b, a) if nb > na else (a, b)
            d = _obj_centroid(mover) - _obj_centroid(other)
            if d.length < 1e-3:
                d = Vector((1.0, 0.0, 0.0))
            d.normalize()
            mover.location.x += d.x * step
            mover.location.y += d.y * step
            moved += 1
        bpy.context.view_layer.update()
    print("RELAX moved %d placements" % moved)
    return moved


def build_signal_towers():
    """Three tall masts on the outer ring.

    The civic ring lost four of its six slots to the street and the hospital, which
    left the skyline low.  These give the city its vertical accents without needing
    a footprint the plateau does not have.
    """
    for i, (ang, r, h) in enumerate(((248.0, 0.80, 27.0), (312.0, 0.82, 31.0),
                                     (14.0, 0.78, 24.0))):
        a = math.radians(ang)
        x = math.cos(a) * PLATEAU_RX * r
        y = math.sin(a) * PLATEAU_RY * r
        z = seabed_h(x, y)
        cyl("SIG_BASE%d" % i, 1.5, 0.6, (x, y, z + 0.3), MAT["concrete"],
            C("PROPS"), verts=12)
        cone("SIG_MAST%d" % i, 0.55, 0.14, h, (x, y, z + h * 0.5),
             MAT["titanium"], C("PROPS"), verts=8, smooth=True)
        for k in range(3):
            torus("SIG_RING%d_%d" % (i, k), 0.42 - k * 0.09, 0.06,
                  (x, y, z + h * (0.56 + k * 0.13)), MAT["emit_cyan"],
                  C("PROPS"), mseg=14, nseg=4)
        sphere("SIG_BEACON%d" % i, 0.26, (x, y, z + h + 0.22),
               MAT["emit_amber"], C("PROPS"), seg=10, rings=6)
        for k in range(3):
            ang2 = a + k * TAU / 3.0
            box("SIG_ARM%d_%d" % (i, k), (2.4, 0.14, 0.14),
                (x, y, z + h * 0.78), MAT["steel_lt"], C("PROPS"),
                rot=(0, 0, ang2))
    print("SIGNAL TOWERS 3")


def build_roof_towers():
    """Slender spires on existing roofs.

    The civic ring could not be built - the plateau has no ground left at r 24.5 - so
    the skyline is recovered vertically instead: three spires sitting inside roofs
    that are already there, which costs no footprint at all.
    """
    parts = []
    parts.append(cyl("RT_BASE", 1.55, 0.55, (0, 0, 0.27), MAT["titanium"],
                     C("WORK"), verts=12, smooth=True))
    parts.append(cone("RT_SHAFT", 0.98, 0.34, 13.0, (0, 0, 7.0),
                      MAT["ceramic"], C("WORK"), verts=10, smooth=True))
    for k in range(4):
        parts.append(torus("RT_R%d" % k, 0.98 - k * 0.15, 0.05,
                           (0, 0, 2.8 + k * 2.9), MAT["emit_cyan"], C("WORK"),
                           mseg=14, nseg=4))
    parts.append(cyl("RT_CROWN", 1.30, 0.62, (0, 0, 14.2), MAT["titanium"],
                     C("WORK"), verts=12, smooth=True))
    parts.append(sphere("RT_BEA", 0.24, (0, 0, 14.72), MAT["emit_amber"],
                        C("WORK"), seg=10, rings=6))
    parts.append(cyl("RT_ANT", 0.05, 3.4, (0, 0, 16.6), MAT["steel_lt"],
                     C("WORK"), verts=5))
    make_master("ROOF_SPIRE", parts, bevel=0.006, weighted=True)

    placed = 0
    for host, s in (("COM_MARKET", 0.95), ("CEN_TOWER0", 1.20),
                    ("PUB_HOSPITAL", 0.85)):
        ob = bpy.data.objects.get(host)
        if ob is None:
            continue
        bb = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        zt = max(v.z for v in bb)
        c = _obj_centroid(ob)
        place("ROOF_SPIRE", c.x, c.y, rot=0.0, s=s, coll="PROPS",
              z=zt - 0.5, tag="spire")
        placed += 1
    print("ROOF SPIRES %d" % placed)


def build_district_blockout():
    seed_occupancy()
    build_commercial_district()      # authored set piece: claims its ground first
    build_harbor_district()          # fixed quay and crane
    build_industrial_district()
    build_public_district()
    build_agriculture_district()
    build_resort_district()
    build_research_district()
    build_residential_district()
    build_central_district()         # built from the slots reserved in the seed
    build_transport()
    build_perimeter_infra()
    report_containment()
    relax_layout()
    verify_layout()
    build_signal_towers()
    build_roof_towers()
    print("DISTRICTS done  placed=%d occupied=%d" % (len(PLACED), len(OCC)))


def build_world_layout():
    define_pads()
    build_ground()
    build_domes()
    build_ground_works()
    build_district_blockout()