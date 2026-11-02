"""
island_layout.py : district planning, roads, town square, harbor, beach and
vegetation distribution.  Pads must be registered before the terrain is built.
"""

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

KEEPOUT = []      # (x, y, r) circles that vegetation and props must avoid
PATHS = []        # road polylines, also kept clear


def keep(x, y, r):
    KEEPOUT.append((x, y, r))


def blocked(x, y, pad=0.0):
    for kx, ky, kr in KEEPOUT:
        if (x - kx) ** 2 + (y - ky) ** 2 < (kr + pad) ** 2:
            return True
    for pts, wd in PATHS:
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            if L2 < 1e-6:
                continue
            t = clamp(((x - ax) * dx + (y - ay) * dy) / L2)
            px, py = ax + dx * t, ay + dy * t
            if (x - px) ** 2 + (y - py) ** 2 < (wd * 0.5 + 0.6 + pad) ** 2:
                return True
    return False


# ---------------------------------------------------------------- sites
# (master, x, y, yaw_deg, pad_radius, collection, scale)
SITES = [
    # public / civic around the plaza
    ("CIVIC_A", -17.0, 12.0, 180, 8.5, "PUBLIC_FACILITIES", 1.0),
    ("CIVIC_B", 7.0, 14.5, 180, 7.0, "PUBLIC_FACILITIES", 1.0),
    ("CIVIC_B", -17.0, 1.5, 90, 6.0, "PUBLIC_FACILITIES", 0.75),
    # commercial street down to the harbour
    ("SHOP_A", -1.0, -6.5, 180, 5.0, "COMMERCIAL", 1.0),
    ("SHOP_B", 5.4, -5.0, 200, 5.0, "COMMERCIAL", 0.95),
    ("SHOP_A", -5.5, -10.5, 170, 5.0, "COMMERCIAL", 0.95),
    ("SHOP_B", 1.8, -12.0, 190, 5.0, "COMMERCIAL", 0.9),
    ("STALL_A", -10.5, -4.5, 20, 3.2, "COMMERCIAL", 1.0),
    ("STALL_B", -13.0, -6.5, 200, 2.8, "COMMERCIAL", 1.0),
    # residential east
    ("HOUSE_COASTAL_A", 12.5, 7.5, 160, 5.8, "RESIDENTIAL", 1.05),
    ("HOUSE_FAMILY_A", 19.0, 3.6, 145, 5.4, "RESIDENTIAL", 1.0),
    ("HOUSE_COASTAL_B", 9.6, 2.6, 185, 5.6, "RESIDENTIAL", 0.95),
    ("HOUSE_FAMILY_B", 17.5, 12.5, 150, 5.2, "RESIDENTIAL", 1.0),
    ("HOUSE_COASTAL_A", 22.5, -3.0, 130, 5.6, "RESIDENTIAL", 0.95),
    # residential west
    ("HOUSE_STILT_A", -22.0, 4.5, 100, 5.4, "RESIDENTIAL", 1.0),
    ("HOUSE_STILT_B", -25.0, -1.0, 85, 5.0, "RESIDENTIAL", 1.0),
    ("HOUSE_FAMILY_A", -19.5, -7.0, 95, 5.2, "RESIDENTIAL", 0.95),
    ("HOUSE_COASTAL_B", -9.5, 16.0, 140, 5.6, "RESIDENTIAL", 0.9),
    # fishing village
    ("HOUSE_STILT_A", -17.0, -11.4, 15, 5.2, "HARBOR", 0.95),
    ("HOUSE_STILT_B", -21.8, -8.4, 40, 4.8, "HARBOR", 1.0),
    ("HOUSE_STILT_B", -13.4, -16.2, 5, 4.8, "HARBOR", 0.9),
    ("CIVIC_B", -5.5, -13.0, 15, 5.2, "HARBOR", 0.6),
    ("SHOP_B", -11.6, -11.0, 35, 4.6, "HARBOR", 0.75),
    # resort
    ("VILLA_A", 18.4, -7.8, 45, 7.2, "RESORT", 1.15),
    ("VILLA_B", 25.5, -13.5, 60, 6.0, "RESORT", 1.0),
    ("PAVILION_A", 21.0, -18.5, 190, 5.4, "RESORT", 1.0),
    ("PAVILION_B", 14.2, -17.8, 175, 4.8, "RESORT", 0.9),
    ("PAVILION_B", 26.6, -4.6, 235, 4.6, "RESORT", 0.85),
]
SITES = [list(s) for s in SITES]   # mutable: the collision pass nudges them

# landmark singles placed by dedicated code
PLAZA = (-4.2, 5.2, 8.2)
PIER = (-8.0, -16.5, -8.0, -26.0, 2.6)   # x0,y0,x1,y1,width


def _master_size(name):
    me = POOL[name]["obj"].data
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    return (max(xs) - min(xs)), (max(ys) - min(ys))


def _site_obb(site):
    name, x, y, yaw, r, coll, s = site
    if name not in POOL:
        return None
    w, d = _master_size(name)
    a = math.radians(yaw)
    return [x, y, math.cos(a), math.sin(a), w * s * 0.5, d * s * 0.5]


def _obb_mtv(A, B):
    """Minimum translation vector between two 2D oriented boxes, or None."""
    axes = ((A[2], A[3]), (-A[3], A[2]), (B[2], B[3]), (-B[3], B[2]))
    best = None
    for nx, ny in axes:
        ra = A[4] * abs(A[2] * nx + A[3] * ny) + A[5] * abs(-A[3] * nx + A[2] * ny)
        rb = B[4] * abs(B[2] * nx + B[3] * ny) + B[5] * abs(-B[3] * nx + B[2] * ny)
        dist = (B[0] - A[0]) * nx + (B[1] - A[1]) * ny
        ov = ra + rb - abs(dist)
        if ov <= 0:
            return None
        sgn = 1.0 if dist >= 0 else -1.0
        if best is None or ov < best[0]:
            best = (ov, nx * sgn, ny * sgn)
    return best


def solve_sites(iters=16, gap=0.10, max_push=0.55):
    """Push overlapping building footprints apart before the terrain is built."""
    fixed = 0
    for _ in range(iters):
        moved = False
        boxes = [(_site_obb(s), i) for i, s in enumerate(SITES)]
        boxes = [(b, i) for b, i in boxes if b is not None]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                A, ia = boxes[i]
                B, ib = boxes[j]
                mtv = _obb_mtv(A, B)
                if mtv is None:
                    continue
                ov, nx, ny = mtv
                if ov <= 0.0:
                    continue
                push = min(max_push, (ov + gap) * 0.52)
                ax, ay = SITES[ia][1] - nx * push, SITES[ia][2] - ny * push
                bx, by = SITES[ib][1] + nx * push, SITES[ib][2] + ny * push
                ok_a = coast_dist(ax, ay) > 7.0
                ok_b = coast_dist(bx, by) > 7.0
                if not ok_a and not ok_b:
                    continue
                if ok_a:
                    SITES[ia][1], SITES[ia][2] = ax, ay
                    A[0], A[1] = ax, ay
                if ok_b:
                    SITES[ib][1], SITES[ib][2] = bx, by
                    B[0], B[1] = bx, by
                moved = True
                fixed += 1
        if not moved:
            break
    print("COLLISION PASS resolved %d overlapping pairs" % fixed)
    return fixed


def layout_pads():
    # plaza + districts first so the terrain is flat where the town sits
    add_pad(PLAZA[0], PLAZA[1], PLAZA[2] + 2.0)
    add_pad(PLAZA[0], PLAZA[1] + 6.0, 9.0)
    add_pad(-8.0, -14.0, 7.0)          # harbour apron
    add_pad(16.0, -1.0, 13.0)          # residential east apron
    add_pad(-18.0, 6.0, 9.0)           # residential west
    add_pad(21.0, -12.0, 8.0)          # resort
    add_pad(10.0, -22.0, 7.0)          # beach
    add_pad(2.6, -16.2, 5.6)           # agriculture (camera side)
    for name, x, y, yaw, r, coll, s in SITES:
        add_pad(x, y, r * 0.92)
        keep(x, y, r * 0.72)
    print("PADS", len(PADS))


# ---------------------------------------------------------------- roads
def catmull(pts, samples_per_seg=8):
    P = [Vector((p[0], p[1], 0)) for p in pts]
    if len(P) < 2:
        return [(p.x, p.y) for p in P]
    ext = [P[0] - (P[1] - P[0])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(samples_per_seg):
            t = s / float(samples_per_seg)
            t2, t3 = t * t, t * t * t
            pt = 0.5 * ((2 * p1) + (-p0 + p2) * t
                        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append((pt.x, pt.y))
    out.append((P[-1].x, P[-1].y))
    return out


def _ribbon(name, pts, width, zoff, mat, coll, skirt=0.0, crown=0.0):
    n = len(pts)
    if n < 2:
        return None
    verts, faces = [], []
    rows = []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[-2][0], y - pts[-2][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        z = terrain_h(x, y) + zoff
        row_l = (x + nx * width * 0.5, y + ny * width * 0.5, z + crown)
        row_r = (x - nx * width * 0.5, y - ny * width * 0.5, z + crown)
        rows.append((row_l, row_r, z))
    for i in range(n - 1):
        a = len(verts)
        l0, r0, z0 = rows[i]
        l1, r1, z1 = rows[i + 1]
        verts.extend([l0, r0, r1, l1])
        faces.append((a, a + 1, a + 2, a + 3))
        if skirt > 0:
            b = len(verts)
            verts.extend([(l0[0], l0[1], z0 - skirt), (r0[0], r0[1], z0 - skirt),
                          (r1[0], r1[1], z1 - skirt), (l1[0], l1[1], z1 - skirt)])
            faces.append((b, b + 1, b + 2, b + 3))
            faces.append((a, a + 3, b + 3, b))
            faces.append((a + 1, b + 1, b + 2, a + 2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = False
    return ob


ROADS = {
    "main_south": [(-4.2, 3.6), (-2.6, 0.4), (0.2, -2.8), (1.6, -6.6), (-1.2, -10.4),
                   (-5.2, -13.2), (-8.0, -14.6)],
    "east": [(-0.4, 4.2), (3.6, 6.2), (8.0, 7.2), (12.4, 6.6), (16.4, 4.0), (19.6, 0.6)],
    "resort": [(1.4, -6.4), (6.2, -9.2), (11.4, -12.0), (15.8, -14.6), (19.4, -16.4)],
    "agri": [(-6.4, 6.6), (-10.4, 9.2), (-14.6, 11.2), (-19.2, 12.6)],
    "west": [(-6.0, 6.0), (-10.2, 5.4), (-14.6, 6.4), (-18.4, 7.2)],
    "beach": [(16.0, -14.8), (12.4, -18.4), (9.0, -20.6)],
}


def build_roads():
    coll = C("ENVIRONMENTAL_PROPS")
    main_w = 2.6
    for name, pts in ROADS.items():
        fine = catmull(pts, 9)
        w = main_w if name in ("main_south", "east", "resort") else 2.0
        PATHS.append((fine, w))
        _ribbon("ROAD_%s_shoulder" % name, fine, w + 0.85, 0.035, MAT["paving"], coll,
                skirt=0.30)
        _ribbon("ROAD_%s" % name, fine, w, 0.075, MAT["asphalt"], coll, crown=0.02)
        if name in ("main_south", "east", "resort"):
            # dashed centre line
            for i in range(0, len(fine) - 4, 14):
                seg = fine[i:i + 2]
                if len(seg) < 2:
                    continue
                mx = (seg[0][0] + seg[1][0]) * 0.5
                my = (seg[0][1] + seg[1][1]) * 0.5
                ang = math.atan2(seg[1][1] - seg[0][1], seg[1][0] - seg[0][0])
                b = box("ROAD_LINE_%s_%d" % (name, i), (1.2, 0.10, 0.02),
                        (mx, my, terrain_h(mx, my) + 0.10), MAT["line"], coll,
                        rot=(0, 0, ang))
    # stone stairs where the plaza meets the main road
    for i in range(4):
        box("STAIR_PLAZA_%d" % i, (3.2, 0.5, 0.22),
            (-4.2, 0.6 - i * 0.5, terrain_h(-4.2, 0.6) + 0.11 - i * 0.02),
            MAT["stone"], C("PUBLIC_FACILITIES"))
    print("ROADS", len(ROADS))


# ---------------------------------------------------------------- town square
def build_town_square():
    coll = C("PUBLIC_FACILITIES")
    cx, cy = PLAZA[0], PLAZA[1]
    z = terrain_h(cx, cy)
    # paved plaza disc + decorative rings
    cyl("PLAZA", 8.2, 0.16, (cx, cy, z + 0.02), MAT["paving"], coll, verts=48)
    for i, r in enumerate((3.0, 5.4, 7.6)):
        torus("PLAZA_RING_%d" % i, r, 0.10, (cx, cy, z + 0.11), MAT["stone"], coll,
              mseg=64, nseg=5)
    # radial paving spokes
    for i in range(12):
        a = i * TAU / 12
        box("PLAZA_SPOKE_%d" % i, (7.0, 0.16, 0.03),
            (cx + math.cos(a) * 5.3, cy + math.sin(a) * 5.3, z + 0.115),
            MAT["stone"], coll, rot=(0, 0, a))
    # fountain at the centre
    cyl("FOUNTAIN_BASIN", 2.5, 0.55, (cx, cy, z + 0.28), MAT["stone"], coll, verts=32)
    torus("FOUNTAIN_LIP", 2.5, 0.12, (cx, cy, z + 0.55), MAT["stone_dark"], coll, mseg=40)
    cyl("FOUNTAIN_WATER", 2.34, 0.10, (cx, cy, z + 0.52), MAT["pool_water"], coll, verts=32)
    cyl("FOUNTAIN_PLINTH", 0.55, 1.2, (cx, cy, z + 0.9), MAT["concrete"], coll, verts=16)
    cyl("FOUNTAIN_BOWL", 1.3, 0.22, (cx, cy, z + 1.5), MAT["stone"], coll, verts=24)
    cyl("FOUNTAIN_BOWL_W", 1.16, 0.06, (cx, cy, z + 1.62), MAT["pool_water"], coll, verts=24)
    cyl("FOUNTAIN_STEM", 0.22, 0.9, (cx, cy, z + 2.0), MAT["concrete"], coll, verts=12)
    sphere("FOUNTAIN_TOP", 0.30, (cx, cy, z + 2.5), MAT["stone"], coll, seg=16, rings=10)
    # clock tower on the north edge of the plaza
    place("CLOCK_TOWER", cx - 1.4, cy + 6.4, math.radians(0), 1.0, "PUBLIC_FACILITIES",
          z=terrain_h(cx - 1.4, cy + 6.4))
    # monument obelisk
    mx, my = cx + 5.0, cy - 2.6
    mz = terrain_h(mx, my)
    box("MONUMENT_BASE", (1.7, 1.7, 0.5), (mx, my, mz + 0.25), MAT["stone_dark"], coll)
    box("MONUMENT_BASE2", (1.2, 1.2, 0.4), (mx, my, mz + 0.7), MAT["stone"], coll)
    cone("MONUMENT_OBELISK", 0.48, 0.14, 4.4, (mx, my, mz + 3.1), MAT["stone"], coll, verts=4)
    sphere("MONUMENT_CAP", 0.16, (mx, my, mz + 5.35), MAT["metal"], coll)
    # kiosk + notice board + bike rack
    place("STALL_A", cx - 6.2, cy - 3.4, math.radians(20), 0.9, "PUBLIC_FACILITIES",
          z=terrain_h(cx - 6.2, cy - 3.4))
    box("NOTICE_BOARD", (2.0, 0.14, 1.3), (cx + 2.4, cy + 5.4, z + 1.5), MAT["wood"], coll)
    for sx in (-1, 1):
        box("NOTICE_POST_%d" % sx, (0.10, 0.10, 1.6),
            (cx + 2.4 + sx * 0.85, cy + 5.4, z + 0.8), MAT["wood_dark"], coll)
    for i in range(3):
        box("NOTICE_PAPER_%d" % i, (0.5, 0.02, 0.36),
            (cx + 1.95 + i * 0.45, cy + 5.32, z + 1.6),
            MAT["paint_w"] if i % 2 else MAT["fabric_w"], coll)
    # benches + lamps around the plaza
    for i in range(6):
        a = i * TAU / 6 + 0.3
        bx, by = cx + math.cos(a) * 6.9, cy + math.sin(a) * 6.9
        bz = terrain_h(bx, by)
        b = box("BENCH_%d" % i, (1.8, 0.50, 0.09), (bx, by, bz + 0.46),
                MAT["wood_light"], coll, rot=(0, 0, a + math.pi / 2))
        box("BENCH_BACK_%d" % i, (1.8, 0.09, 0.42), (bx, by, bz + 0.66),
            MAT["wood_light"], coll, rot=(0, 0, a + math.pi / 2))
    for i in range(8):
        a = i * TAU / 8
        lx, ly = cx + math.cos(a) * 7.4, cy + math.sin(a) * 7.4
        lz = terrain_h(lx, ly)
        cyl("PLAZA_LAMP_%d" % i, 0.06, 3.0, (lx, ly, lz + 1.5), MAT["metal_dark"], coll, verts=8)
        sphere("PLAZA_LAMP_G%d" % i, 0.15, (lx, ly, lz + 3.1), MAT["glow"], coll,
               seg=8, rings=5)
    # planter beds
    for i in range(4):
        a = i * TAU / 4 + 0.8
        px, py = cx + math.cos(a) * 6.2, cy + math.sin(a) * 6.2
        pz = terrain_h(px, py)
        box("PLANTER_%d" % i, (1.6, 1.0, 0.42), (px, py, pz + 0.21), MAT["stone"], coll)
        place("BUSH_B", px, py, a, 1.0, "PUBLIC_FACILITIES", z=pz + 0.35)
        place("FLOWER_CORAL", px - 0.4, py, a, 1.2, "PUBLIC_FACILITIES", z=pz + 0.40)
    print("TOWN SQUARE done at z=%.1f" % z)


# ---------------------------------------------------------------- harbor
def build_harbor():
    coll = C("HARBOR")
    x0, y0, x1, y1, wd = PIER
    mx, my = (x0 + x1) * 0.5, (y0 + y1) * 0.5
    # pier deck follows the terrain down to the water then stays level
    steps = 16
    z_deck = terrain_h(x0, y0) + 0.55
    for i in range(steps):
        t = i / (steps - 1.0)
        px = x0 + (x1 - x0) * t
        py = y0 + (y1 - y0) * t
        zz = max(z_deck - t * 1.5, 0.85)
        box("PIER_PLANK_%02d" % i, (wd, 0.78, 0.10), (px, py, zz), MAT["wood_light"], coll)
        if i % 3 == 0:
            for sgn in (-1, 1):
                cyl("PIER_POST_%02d_%d" % (i, sgn), 0.13, zz + 2.2,
                    (px + sgn * (wd * 0.5 - 0.15), py, (zz - 2.4) * 0.5 + zz * 0.5),
                    MAT["wood_dark"], coll, verts=8)
    # cross pier at the end
    for i in range(10):
        px = x0 - 5.0 + i * 1.1
        box("PIER_CROSS_%02d" % i, (0.9, 2.4, 0.10), (px, y1 + 0.6, 0.86),
            MAT["wood_light"], coll)
        if i % 3 == 0:
            cyl("PIER_CPOST_%02d" % i, 0.12, 3.2, (px, y1 + 1.6, -0.4),
                MAT["wood_dark"], coll, verts=8)
    # mooring bollards, crates, barrels, nets
    for i in range(6):
        t = i / 5.0
        px = x0 + (x1 - x0) * t
        py = y0 + (y1 - y0) * t
        zz = max(z_deck - t * 1.5, 0.85)
        for sgn in (-1, 1):
            cyl("BOLLARD_%d_%d" % (i, sgn), 0.11, 0.42, (px + sgn * (wd * 0.5 - 0.25), py, zz + 0.25),
                MAT["metal_dark"], coll, verts=8)
    for i in range(7):
        px = x0 - 1.0 + (i % 3) * 1.2
        py = y0 + 1.5 + (i // 3) * 1.3
        box("HARBOR_CRATE_%d" % i, (0.6, 0.6, 0.5), (px, py, terrain_h(px, py) + 0.3),
            MAT["wood_light"], coll, rot=(0, 0, i * 0.4))
    for i in range(4):
        px, py = x0 + 2.2 + i * 0.7, y0 + 2.0
        cyl("HARBOR_BARREL_%d" % i, 0.28, 0.72, (px, py, terrain_h(px, py) + 0.36),
            MAT["metal_dark"], coll, verts=12)
    # harbour office + auction shed on the apron
    place("CIVIC_B", -5.0, -12.4, math.radians(15), 0.62, "HARBOR",
          z=terrain_h(-5.0, -12.4))
    place("SHOP_B", -10.6, -13.6, math.radians(35), 0.8, "HARBOR",
          z=terrain_h(-10.6, -13.6))
    # net drying racks
    for i in range(3):
        px, py = -13.0 + i * 1.8, -14.6
        h = 2.0
        for sgn in (-1, 1):
            cyl("NET_POST_%d_%d" % (i, sgn), 0.07, h, (px, py + sgn * 1.1, terrain_h(px, py) + h * 0.5),
                MAT["wood_dark"], coll, verts=6)
        box("NET_%d" % i, (0.05, 2.2, 1.1), (px, py, terrain_h(px, py) + 1.3),
            MAT["fabric_teal"], coll)
    print("HARBOR done")


def build_boats():
    coll = C("HARBOR")
    build_boat_masters()
    # docked along the pier, bows to the east
    placements = [
        ("BOAT_A", -9.9, -18.2, 92.0),
        ("BOAT_B", -6.4, -19.6, 88.0),
        ("BOAT_C", -11.4, -22.0, 95.0),
        ("BOAT_D", -5.0, -22.8, 80.0),
        ("BOAT_E", -14.0, -24.6, 100.0),
    ]
    for nm, x, y, ang in placements:
        place(nm, x, y, math.radians(ang), 1.0, "HARBOR", z=0.0, sink=0.0)
    # a moored boat further out
    place("BOAT_B", 6.0, -26.5, math.radians(150), 1.1, "HARBOR", z=0.0)
    place("BOAT_E", 1.8, -28.4, math.radians(120), 1.0, "HARBOR", z=0.0)
    # buoys
    for i in range(6):
        x = -12.0 + i * 3.4
        y = -25.5 - (i % 2) * 1.6
        sphere("BUOY_%d" % i, 0.22, (x, y, 0.10),
               MAT["paint_coral"] if i % 2 else MAT["paint_yellow"],
               coll, seg=8, rings=5)
    print("BOATS 6")


# ---------------------------------------------------------------- beach
def build_beach():
    coll = C("RESORT")
    for i in range(7):
        x = 9.0 + i * 2.4
        y = -23.0 - (i % 3) * 1.4
        z = terrain_h(x, y)
        if z < 0.25:
            continue
        ang = (i * 0.7) % TAU
        # lounger
        box("LOUNGER_%d" % i, (1.9, 0.68, 0.10), (x, y, z + 0.34), MAT["paint_w"],
            coll, rot=(0, 0, ang))
        box("LOUNGER_B%d" % i, (0.62, 0.68, 0.08), (x + math.cos(ang) * 0.72,
                                                    y + math.sin(ang) * 0.72, z + 0.60),
            MAT["paint_w"], coll, rot=(0, math.radians(-35), ang))
        for sx in (-1, 1):
            for sy in (-1, 1):
                cyl("LOUNGER_L%d_%d%d" % (i, sx, sy), 0.035, 0.30,
                    (x + sx * 0.75 * math.cos(ang) - sy * 0.25 * math.sin(ang),
                     y + sx * 0.75 * math.sin(ang) + sy * 0.25 * math.cos(ang), z + 0.16),
                    MAT["metal"], coll, verts=5)
        # umbrella
        ux, uy = x + math.cos(ang + 1.4) * 1.4, y + math.sin(ang + 1.4) * 1.4
        cyl("UMB_POLE_%d" % i, 0.04, 2.3, (ux, uy, z + 1.15), MAT["wood_dark"], coll, verts=6)
        cone("UMB_%d" % i, 1.35, 0.10, 0.55, (ux, uy, z + 2.25),
             [MAT["fabric_coral"], MAT["fabric_teal"], MAT["paint_yellow"]][i % 3],
             coll, verts=10)
        # towel
        box("TOWEL_%d" % i, (0.9, 1.6, 0.02), (x - math.cos(ang) * 1.1,
                                               y - math.sin(ang) * 1.1, z + 0.04),
            MAT["fabric_teal"] if i % 2 else MAT["paint_coral"], coll, rot=(0, 0, ang + 0.3))
    # volleyball net
    for sx in (-1, 1):
        cyl("VOLLEY_POST_%d" % sx, 0.06, 2.1, (13.6 + sx * 2.6, -24.6, terrain_h(13.6, -24.6) + 1.05),
            MAT["metal"], coll, verts=6)
    box("VOLLEY_NET", (5.2, 0.02, 0.7), (13.6, -24.6, terrain_h(13.6, -24.6) + 1.7),
        MAT["fabric_w"], coll)
    # lifeguard hut
    hx, hy = 7.4, -21.4
    hz = terrain_h(hx, hy)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl("LG_POST_%d%d" % (sx, sy), 0.09, 1.5, (hx + sx * 0.8, hy + sy * 0.8, hz + 0.75),
                MAT["wood_dark"], coll, verts=6)
    box("LG_HUT", (2.0, 1.8, 1.6), (hx, hy, hz + 2.2), MAT["paint_coral"], coll)
    cone("LG_ROOF", 1.7, 0.15, 0.6, (hx, hy, hz + 3.3), MAT["roof_thatch"], coll, verts=4)
    box("LG_FLAG", (0.06, 0.02, 0.9), (hx + 0.9, hy - 0.9, hz + 3.6), MAT["paint_yellow"], coll)
    print("BEACH done")


# ---------------------------------------------------------------- vegetation
def scatter_vegetation():
    rng = random.Random(4242)
    placed = []

    def ok(x, y, dmin, dmax, mind, slope_max=1.0):
        d = coast_dist(x, y)
        if d < dmin or d > dmax:
            return False
        if terrain_slope(x, y) > slope_max:
            return False
        for px, py in placed:
            if (x - px) ** 2 + (y - py) ** 2 < mind * mind:
                return False
        if blocked(x, y, 0.9):
            return False
        return True

    def run(names, count, dmin, dmax, mind, coll="VEGETATION", smin=0.85, smax=1.2,
            slope_max=1.0):
        n, tries = 0, 0
        while n < count and tries < count * 200:
            tries += 1
            x = rng.uniform(-38, 38)
            y = rng.uniform(-30, 30)
            if not ok(x, y, dmin, dmax, mind, slope_max):
                continue
            place(rng.choice(names), x, y, rng.uniform(0, TAU), rng.uniform(smin, smax), coll)
            placed.append((x, y))
            n += 1
        return n

    print("  palms", run(["PALM_A", "PALM_B", "PALM_C", "PALM_D", "PALM_E"], 34,
                         3.0, 26.0, 3.4, "VEGETATION", 0.62, 0.82))
    print("  broadleaf", run(["BROADLEAF_A", "BROADLEAF_B", "BROADLEAF_C"], 22,
                             5.0, 40.0, 3.8, "VEGETATION", 0.58, 0.80, 0.85))
    print("  bush", run(["BUSH_A", "BUSH_B", "BUSH_C"], 120, 2.2, 40.0, 1.3, "VEGETATION", 0.75, 1.25))
    print("  fern", run(["FERN_A", "FERN_B"], 70, 3.0, 40.0, 1.1, "VEGETATION", 0.8, 1.3))
    print("  grass", run(["BEACHGRASS_A", "BEACHGRASS_B"], 90, 0.9, 5.5, 0.9, "VEGETATION", 0.9, 1.3))
    print("  banana", run(["BANANA_A", "BANANA_B"], 18, 5.0, 30.0, 2.0, "AGRICULTURE", 0.9, 1.2))
    print("  mangrove", run(["MANGROVE_A", "MANGROVE_B"], 14, 0.4, 3.0, 2.6, "VEGETATION", 0.9, 1.2))
    # deliberate shade trees in the settlement (gardens, plaza edge, street)
    town_trees = [
        (5.6, 9.4, "BROADLEAF_B"), (9.8, 0.6, "PALM_B"), (13.8, 2.2, "BROADLEAF_A"),
        (1.0, 0.4, "PALM_D"), (-10.4, 9.6, "BROADLEAF_B"), (-13.0, 12.4, "PALM_B"),
        (8.2, -7.6, "PALM_D"), (-8.6, -12.0, "PALM_B"), (-15.6, -13.4, "BROADLEAF_B"),
        (19.6, -5.6, "PALM_B"), (25.0, -9.0, "BROADLEAF_A"), (12.2, -12.6, "PALM_D"),
        (-23.0, 9.0, "BROADLEAF_B"), (-25.8, 4.6, "PALM_C"), (-8.0, 17.0, "BROADLEAF_A"),
        (11.0, 15.6, "PALM_B"), (-2.0, -14.6, "PALM_D"), (23.0, -18.0, "PALM_B"),
    ]
    for i, (x, y, nm) in enumerate(town_trees):
        if not is_land(x, y) or coast_dist(x, y) < 1.2:
            continue
        if blocked(x, y, -2.2):
            continue
        place(nm, x, y, i * 1.37, 0.72 if nm.startswith("PALM") else 0.66,
              "VEGETATION", z=terrain_h(x, y))
        placed.append((x, y))


def build_prop_masters():
    coll = C("WORK")
    # cafe set: table + two chairs
    parts = []
    parts.append(cyl("CAFE_TOP", 0.52, 0.07, (0, 0, 0.72), MAT["wood_light"], coll, verts=14))
    parts.append(cyl("CAFE_STEM", 0.07, 0.70, (0, 0, 0.36), MAT["metal_dark"], coll, verts=8))
    parts.append(cyl("CAFE_FOOT", 0.30, 0.05, (0, 0, 0.03), MAT["metal_dark"], coll, verts=10))
    for sx in (-1, 1):
        parts.append(box("CHAIR_SEAT%d" % sx, (0.44, 0.44, 0.06), (sx * 0.95, 0, 0.52),
                         MAT["wood"], coll))
        parts.append(box("CHAIR_BACK%d" % sx, (0.44, 0.06, 0.46), (sx * 0.95, 0.19, 0.75),
                         MAT["wood"], coll))
        for sgn in (-1, 1):
            parts.append(box("CHAIR_LEG%d_%d" % (sx, sgn), (0.05, 0.05, 0.50),
                             (sx * 0.95 + sgn * 0.17, 0.0, 0.26), MAT["wood_dark"], coll))
    make_master("CAFE_SET", parts, bevel=0.006, weighted=False)

    # laundry line
    parts = []
    for sgn in (-1, 1):
        parts.append(cyl("LAUNDRY_P%d" % sgn, 0.05, 2.0, (sgn * 1.6, 0, 1.0),
                         MAT["wood_dark"], coll, verts=6))
    parts.append(cyl("LAUNDRY_L", 0.012, 3.2, (0, 0, 1.95), MAT["fabric_w"], coll,
                     rot=(0, math.radians(90), 0), verts=4))
    for i in range(4):
        parts.append(box("LAUNDRY_C%d" % i, (0.42, 0.03, 0.62),
                         (-1.05 + i * 0.70, 0, 1.58),
                         [MAT["paint_w"], MAT["cloth_1"], MAT["fabric_teal"],
                          MAT["cloth_3"]][i % 4], coll))
    make_master("LAUNDRY", parts, bevel=0.0, weighted=False)

    # bicycle
    parts = []
    for sx in (-1, 1):
        parts.append(torus("BIKE_W%d" % sx, 0.32, 0.035, (sx * 0.52, 0, 0.34),
                           MAT["hair_dark"], coll, rot=(math.radians(90), 0, 0),
                           mseg=16, nseg=5))
    parts.append(tube_between("BIKE_F1", (-0.52, 0, 0.34), (0.0, 0, 0.62), 0.026, 0.026,
                              MAT["paint_teal"], coll, 5))
    parts.append(tube_between("BIKE_F2", (0.0, 0, 0.62), (0.52, 0, 0.34), 0.026, 0.026,
                              MAT["paint_teal"], coll, 5))
    parts.append(tube_between("BIKE_F3", (-0.52, 0, 0.34), (0.0, 0, 0.34), 0.026, 0.026,
                              MAT["paint_teal"], coll, 5))
    parts.append(tube_between("BIKE_F4", (0.0, 0, 0.34), (0.30, 0, 0.66), 0.026, 0.026,
                              MAT["paint_teal"], coll, 5))
    parts.append(box("BIKE_SEAT", (0.22, 0.10, 0.05), (0.10, 0, 0.70), MAT["hair_dark"], coll))
    parts.append(box("BIKE_BAR", (0.06, 0.42, 0.05), (-0.42, 0, 0.72), MAT["metal"], coll))
    make_master("BICYCLE", parts, bevel=0.0, weighted=False)

    # street lamp
    parts = []
    parts.append(cyl("LAMP_POST", 0.07, 3.6, (0, 0, 1.8), MAT["metal_dark"], coll, verts=8))
    parts.append(cone("LAMP_HEAD", 0.22, 0.10, 0.28, (0, 0, 3.62), MAT["metal_dark"], coll,
                      verts=8))
    parts.append(sphere("LAMP_BULB", 0.11, (0, 0, 3.48), MAT["glow"], coll, seg=8, rings=5))
    make_master("STREET_LAMP", parts, bevel=0.006, weighted=False)

    # crates stack
    parts = []
    for i in range(3):
        parts.append(box("CRATE_%d" % i, (0.55, 0.55, 0.42),
                         ((i % 2) * 0.60, 0, 0.21 + i * 0.44), MAT["wood_light"], coll))
    make_master("CRATES", parts, bevel=0.008, weighted=False)
    print("PROP MASTERS 4")


def build_props():
    coll = C("ENVIRONMENTAL_PROPS")
    # cafe sets along the commercial street
    for i, (x, y, a) in enumerate(((-7.6, -6.2, 0.3), (-8.8, -8.2, 0.9), (3.4, -6.6, 2.4),
                                    (4.6, -8.4, 1.7), (-2.4, -12.6, 0.5), (6.4, -2.2, 2.8))):
        place("CAFE_SET", x, y, a, 1.0, "COMMERCIAL", z=terrain_h(x, y))
    # laundry lines behind houses
    for i, (x, y, a) in enumerate(((14.2, 3.6, 0.4), (20.6, 0.6, 1.2),
                                    (-20.8, -4.6, 2.0), (11.0, 9.4, 0.9))):
        place("LAUNDRY", x, y, a, 1.0, "RESIDENTIAL", z=terrain_h(x, y))
    # bicycles
    for i, (x, y, a) in enumerate(((6.8, -7.0, 1.1), (-8.0, -3.4, 2.4), (12.0, -14.0, 0.6),
                                    (-4.0, -8.2, 1.9))):
        place("BICYCLE", x, y, a, 1.0, "VEHICLES", z=terrain_h(x, y))
    # street lamps along the main roads
    for name, pts in ROADS.items():
        fine = catmull(pts, 5)
        step = 9 if name in ("main_south", "east", "resort") else 12
        for i in range(2, len(fine) - 2, step):
            x, y = fine[i]
            ang = math.atan2(fine[i + 1][1] - y, fine[i + 1][0] - x) + math.pi / 2
            px, py = x + math.cos(ang) * 2.1, y + math.sin(ang) * 2.1
            if is_land(px, py) and coast_dist(px, py) > 1.5:
                place("STREET_LAMP", px, py, ang, 1.0, "ENVIRONMENTAL_PROPS",
                      z=terrain_h(px, py))
    # crates outside shops and the harbour
    for i, (x, y, a) in enumerate(((2.2, -11.0, 0.4), (-7.8, -11.8, 1.2),
                                    (-9.4, -14.2, 2.2), (7.6, -3.6, 0.8),
                                    (-13.6, -8.4, 1.6))):
        place("CRATES", x, y, a, 1.0, "ENVIRONMENTAL_PROPS", z=terrain_h(x, y))


def build_population():
    coll = "HUMAN_CHARACTERS"
    rng = random.Random(777)
    people = [
        # plaza
        ("PERSON_SIT", -3.2, 8.9, 3.5), ("PERSON_SIT", 1.4, 9.6, 4.2),
        ("PERSON_STAND", -1.2, 3.4, 2.2), ("PERSON_STAND_HAT", -6.6, 3.0, 0.8),
        ("PERSON_WALK", -4.6, 8.0, 1.4), ("PERSON_WALK_CAP", -7.2, 6.6, 5.0),
        ("PERSON_SERVE", -9.6, -4.2, 1.0),
        # commercial street
        ("PERSON_WALK", -1.6, -4.6, 4.6), ("PERSON_WALK_HAT", 3.4, -4.0, 1.8),
        ("PERSON_SIT", 3.4, -6.6, 2.4), ("PERSON_SIT", -8.8, -8.2, 0.9),
        ("PERSON_STAND", 5.0, -6.0, 3.6), ("PERSON_STAND_HAT", -6.2, -9.6, 2.0),
        # harbour
        ("PERSON_FISH", -8.2, -19.5, 1.57), ("PERSON_FISH", -8.8, -24.0, 1.57),
        ("PERSON_CARRY", -9.6, -15.4, 0.6), ("PERSON_CARRY", -6.4, -17.2, 2.4),
        ("PERSON_STAND", -5.0, -12.0, 1.1), ("PERSON_WALK_CAP", -12.0, -13.2, 3.0),
        ("PERSON_BEND", -10.0, -14.6, 0.4),
        # beach + resort
        ("PERSON_SIT", 9.6, -22.6, 2.2), ("PERSON_SIT", 13.2, -21.8, 3.0),
        ("PERSON_STAND_HAT", 15.4, -20.6, 1.0), ("PERSON_WALK_HAT", 11.0, -24.2, 4.0),
        ("PERSON_WALK", 20.0, -15.0, 2.0), ("PERSON_SERVE", 23.2, -17.0, 1.4),
        # agriculture / forest
        ("PERSON_BEND", -19.0, 15.0, 0.5), ("PERSON_BEND", -21.0, 16.2, 1.6),
        ("PERSON_CARRY", -17.2, 13.4, 2.8), ("PERSON_WALK", -12.0, 11.0, 0.4),
        # residential
        ("PERSON_WALK_CAP", 14.0, 5.0, 2.6), ("PERSON_STAND", 17.0, 9.0, 1.2),
        ("PERSON_WALK_HAT", -20.0, 1.6, 4.2), ("PERSON_SIT", -15.0, 2.4, 2.0),
    ]
    for i, (nm, x, y, a) in enumerate(people):
        z = terrain_h(x, y)
        if nm.startswith("PERSON_SIT"):
            z += 0.02
        ob = place(nm, x, y, a, rng.uniform(0.94, 1.06), coll, z=z)
        # clothing variation through object-linked material slots
        try:
            for slot in ob.material_slots:
                if slot.material and slot.material.name.startswith("MAT_CLOTH_"):
                    slot.link = "OBJECT"
                    slot.material = MAT["cloth_%d" % (i * 3 % 10)]
                elif slot.material and slot.material.name.startswith("MAT_SKIN_"):
                    slot.link = "OBJECT"
                    slot.material = MAT["skin_%d" % (1 + i % 4)]
        except Exception:
            pass
    # swimmers: only the top half shows above the water plane
    for x, y in ((7.0, -26.6), (18.4, -27.4)):
        place("PERSON_STAND", x, y, 1.2, 1.0, coll, z=-1.15)
    print("PEOPLE", len(people) + 2)


def build_animals():
    coll = "ANIMALS"
    rng = random.Random(2027)
    # chickens near houses
    for cx, cy in ((-21.0, 2.0), (14.6, 9.0), (-16.0, -11.0), (20.0, 6.0)):
        for i in range(4):
            x = cx + rng.uniform(-2.2, 2.2)
            y = cy + rng.uniform(-2.2, 2.2)
            if terrain_h(x, y) < 0.5:
                continue
            place(rng.choice(["CHICKEN", "ROOSTER"]), x, y, rng.uniform(0, TAU),
                  rng.uniform(0.9, 1.15), coll, z=terrain_h(x, y))
    # dogs
    for x, y, a in ((11.0, 4.4, 0.4), (-19.0, 0.2, 2.2), (-8.0, -10.0, 1.2)):
        place(rng.choice(["DOG", "DOG_B"]), x, y, a, 1.0, coll, z=terrain_h(x, y))
    # cats
    for x, y, a in ((4.2, -6.6, 1.0), (-9.0, -5.4, 2.4), (17.0, -9.4, 0.6)):
        place("CAT", x, y, a, 1.0, coll, z=terrain_h(x, y))
    # gulls over the harbour and beach
    for x, y, z in ((-7.0, -19.0, 8.0), (-3.0, -22.0, 9.5), (10.0, -23.0, 7.0),
                    (15.0, -25.0, 10.0), (-12.0, -16.0, 6.5)):
        place("GULL_FLY", x, y, rng.uniform(0, TAU), 1.0, coll, z=z)
    for x, y in ((-9.0, -22.0), (12.0, -26.0), (-16.0, -18.0)):
        place("GULL", x, y, rng.uniform(0, TAU), 1.0, coll, z=0.0)
    # crabs on the beach
    for i in range(9):
        x = 7.0 + rng.uniform(0, 16.0)
        y = -21.0 - rng.uniform(0, 5.0)
        z = terrain_h(x, y)
        if z > -0.1:
            place("CRAB", x, y, rng.uniform(0, TAU), rng.uniform(0.85, 1.2), coll, z=z)
    # turtles in the shallows
    for x, y, a in ((5.0, -29.0, 0.4), (21.0, -24.0, 2.2)):
        place("TURTLE", x, y, a, 1.0, coll, z=-0.45)
    # fish + coral in the lagoon
    for i in range(10):
        a = rng.uniform(0, TAU)
        x = 12.0 + math.cos(a) * rng.uniform(3, 9)
        y = -23.0 + math.sin(a) * rng.uniform(2, 6)
        if coast_dist(x, y) > -0.8:
            continue
        place(rng.choice(["FISH_A", "FISH_B"]), x, y, rng.uniform(0, TAU),
              rng.uniform(0.9, 1.3), coll, z=-0.55)
    print("ANIMALS placed")


def build_coral():
    coll = "ENVIRONMENTAL_PROPS"
    rng = random.Random(313)
    n = 0
    for i in range(40):
        a = rng.uniform(0, TAU)
        r = rng.uniform(3.0, 12.0)
        x = 14.0 + math.cos(a) * r
        y = -24.0 + math.sin(a) * r * 0.7
        d = coast_dist(x, y)
        if d > -0.6 or d < -9.0:
            continue
        place(rng.choice(["CORAL_A", "CORAL_B", "CORAL_C"]), x, y,
              rng.uniform(0, TAU), rng.uniform(0.8, 1.3), coll, z=-0.9 - rng.uniform(0, 0.8))
        n += 1
    print("CORAL", n)


def build_farm():
    coll = "AGRICULTURE"
    coll_obj = C("AGRICULTURE")
    FX, FY = 2.6, -16.2
    ROT = math.radians(-10)
    # compact kitchen garden on the slope facing the hero camera
    for i in range(5):
        y = FY - 2.0 + i * 1.05
        z = terrain_h(FX, y)
        ob = box("FARM_BED_%d" % i, (5.6, 0.85, 0.26), (FX, y, z + 0.13),
                 MAT["leaf_dry"], coll_obj, rot=(0, 0, ROT))
        box("FARM_SOIL_%d" % i, (5.4, 0.64, 0.10), (FX, y, z + 0.24),
            MAT["paint_coral"], coll_obj, rot=(0, 0, ROT))
        for k in range(6):
            px = FX - 2.3 + k * 0.92
            place("BUSH_B", px, y, k * 0.7, 0.28, coll, z=z + 0.26)
    # irrigation channel + pump
    box("FARM_CHANNEL", (6.0, 0.42, 0.18), (FX, FY - 2.8, terrain_h(FX, FY - 2.8) + 0.02),
        MAT["pool_water"], coll_obj, rot=(0, 0, ROT))
    cyl("FARM_PUMP", 0.20, 0.50, (FX - 2.9, FY - 2.2, terrain_h(FX - 2.9, FY - 2.2) + 0.25),
        MAT["metal"], coll_obj, verts=10)
    # low fence on the seaward side
    for i in range(5):
        x = FX - 2.6 + i * 1.3
        cyl("FARM_POST_%d" % i, 0.055, 0.85, (x, FY + 2.4, terrain_h(x, FY + 2.4) + 0.42),
            MAT["wood_dark"], coll_obj, verts=5)
    box("FARM_RAIL", (5.4, 0.06, 0.07), (FX, FY + 2.4, terrain_h(FX, FY + 2.4) + 0.78),
        MAT["wood_light"], coll_obj)
    # storage shed at the edge of the plot
    sx, sy = FX + 3.9, FY - 1.2
    sz = terrain_h(sx, sy)
    box("FARM_SHED", (2.2, 1.8, 1.9), (sx, sy, sz + 0.95), MAT["wood"], coll_obj,
        rot=(0, 0, ROT))
    cone("FARM_SHED_ROOF", 1.9, 0.25, 0.8, (sx, sy, sz + 2.25), MAT["roof_thatch"],
         coll_obj, verts=4, rot=(0, 0, ROT))
    box("FARM_SHED_DOOR", (0.8, 0.06, 1.35), (sx, sy - 0.92, sz + 0.70),
        MAT["wood_dark"], coll_obj)
    for i in range(3):
        px, py = FX - 3.1 + i * 1.6, FY + 3.3
        place("BANANA_A", px, py, i * 0.6, 0.85, coll, z=terrain_h(px, py))
    print("FARM done at (%.1f, %.1f)" % (FX, FY))


def build_vehicles():
    veh = [
        ("PICKUP_A", 2.2, -7.6, 0.55, "COMMERCIAL"),
        ("PICKUP_B", -6.2, -11.2, 1.9, "HARBOR"),
        ("CAR_A", 10.2, 6.2, 1.62, "RESIDENTIAL"),
        ("CAR_B", 15.0, -14.2, 0.85, "RESORT"),
        ("SCOOTER_A", -8.4, 1.6, 0.3, "COMMERCIAL"),
        ("SCOOTER_B", -12.2, 8.4, 2.2, "RESIDENTIAL"),
        ("GOLF_CART", 20.4, -12.6, 0.6, "RESORT"),
    ]
    for nm, x, y, a, col in veh:
        place(nm, x, y, a, 1.0, col, z=terrain_h(x, y))


def build_island_layout():
    # masters first: the collision pass needs real footprint sizes
    build_nature_masters()
    build_arch_masters()
    build_prop_masters()
    build_animal_masters()
    build_people_masters()
    build_vehicle_masters()
    solve_sites()
    layout_pads()
    build_ground()
    build_roads()
    build_town_square()
    build_harbor()
    build_boats()
    build_beach()
    build_farm()
    for name, x, y, yaw, r, coll, s in SITES:
        if name in POOL:
            place(name, x, y, math.radians(yaw), s, coll, z=terrain_h(x, y))
    build_props()
    build_vehicles()
    build_population()
    build_animals()
    build_coral()
    place("LIGHTHOUSE", -27.5, -7.0, math.radians(90), 1.0, "PUBLIC_FACILITIES",
          z=terrain_h(-27.5, -7.0))
    scatter_vegetation()
    print("LAYOUT DONE objects=%d" % len(bpy.data.objects))
