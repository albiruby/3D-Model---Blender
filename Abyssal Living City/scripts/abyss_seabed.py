"""
abyss_seabed.py : the abyssal plateau - height field, drop-off, rock formations.

The city sits on a raised plateau. Beyond its rim the floor falls away in two
steps into unlit water; that drop is the composition's background and it does
most of the depth work in the hero frame.
"""

import bpy
import bmesh
import math
from mathutils import Vector

# Reuse the elliptical plateau from core.
PADS = []
TRENCH = []          # (x0, y0, x1, y1, half_width, depth) carved channels


# ---------------------------------------------------------------- field
def plate_r(x, y):
    return math.hypot(x / PLATEAU_RX, y / PLATEAU_RY)


def seabed_raw(x, y):
    r0 = plate_r(x, y)
    # organic rim: perturb the radius so the cliff line is not a perfect ellipse
    r = r0 + (fbm(x * 0.075, y * 0.075, 64, 3) - 0.5) * 0.055
    rim = smoothstep(0.84, 1.22, r)

    # city terrace: a shallow dish, highest at the centre
    base = -1.4 + 2.6 * (1.0 - smoothstep(0.0, 0.84, r))
    base += (fbm(x * 0.052, y * 0.052, 5, 4) - 0.5) * 2.9 * (1.0 - 0.55 * rim)
    base += (fbm(x * 0.16, y * 0.16, 7, 3) - 0.5) * 0.7

    # step drop-off: a narrow lip, then a steep face.  A soft quadratic falloff
    # reads as a beach, not as the edge of an abyssal plateau.
    lip = smoothstep(0.895, 0.960, r)
    cliff = smoothstep(0.950, 1.075, r)
    z = base - 5.0 * lip - 23.0 * cliff
    # buttresses so the face is not a smooth cone
    z += cliff * (1.0 - cliff) * 4.5 * (fbm(x * 0.10, y * 0.10, 66, 4) - 0.5)

    # ridge along the west / north-west rim: a wall of rock the city leans on
    ridge = math.exp(-((r - 0.945) / 0.045) ** 2)
    ang = math.atan2(y, x)
    ridge *= smoothstep(-0.7, 0.7, math.sin(ang + 2.2))
    z += ridge * (3.2 + 3.4 * fbm(x * 0.06, y * 0.06, 61, 3))

    # a trench cutting into the shelf, for the industrial intake
    for (x0, y0, x1, y1, hw, dep) in TRENCH:
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy
        t = clamp(((x - x0) * dx + (y - y0) * dy) / L2)
        px, py = x0 + dx * t, y0 + dy * t
        d = math.hypot(x - px, y - py)
        w = 1.0 - smoothstep(hw * 0.45, hw, d)
        if w > 0.0:
            z -= dep * w * w

    # open abyssal plain: sediment drifts
    abyss = ABYSS_Z + (fbm(x * 0.021, y * 0.021, 9, 4) - 0.5) * 7.0
    z = lerp(z, abyss, smoothstep(1.02, 1.38, r))
    return z


def add_pad(x, y, r, z=None, falloff=0.55):
    PADS.append([x, y, r, seabed_raw(x, y) if z is None else z, falloff])


def seabed_h(x, y):
    z = seabed_raw(x, y)
    for px, py, r, pz, fo in PADS:
        d = math.hypot(x - px, y - py)
        if d < r:
            w = 1.0 - smoothstep(r * fo, r, d)
            z += (pz - z) * w
    return z


def seabed_slope(x, y, h=1.1):
    dx = seabed_h(x + h, y) - seabed_h(x - h, y)
    dy = seabed_h(x, y + h) - seabed_h(x, y - h)
    return math.hypot(dx, dy) / (2.0 * h)


def is_plateau(x, y):
    return plate_r(x, y) < 0.95


# ---------------------------------------------------------------- colour
C_SED_DK = None
C_SED_LT = None
C_ALGAE = None
C_ALGAE_DK = None
C_ROCK_DK = None
C_ROCK_LT = None
C_ABYSS = None


def _init_cols():
    global C_SED_DK, C_SED_LT, C_ALGAE, C_ALGAE_DK, C_ROCK_DK, C_ROCK_LT, C_ABYSS
    if C_SED_DK is not None:
        return
    C_SED_DK = hexcol(PAL["sand_dk"])
    C_SED_LT = hexcol(PAL["sand_lt"])
    C_ALGAE = hexcol(PAL["algae"])
    C_ALGAE_DK = hexcol(PAL["kelp"])
    C_ROCK_DK = hexcol(PAL["rock_dk"])
    C_ROCK_LT = hexcol(PAL["rock_lt"])
    C_ABYSS = hexcol("#0A131A")


def _mix(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def seabed_color(x, y, z):
    _init_cols()
    n = fbm(x * 0.13, y * 0.13, 21, 4)
    sed = _mix(C_SED_DK, C_SED_LT, n)
    # algae film over sediment, patchy
    aw = smoothstep(0.46, 0.78, fbm(x * 0.062, y * 0.062, 44, 3))
    algae = _mix(C_ALGAE_DK, C_ALGAE, fbm(x * 0.21, y * 0.21, 33, 3))
    col = _mix(sed, algae, aw * 0.60)
    # rock on slopes and on the rim
    sl = seabed_slope(x, y, 1.3)
    rw = smoothstep(0.24, 0.80, sl)
    rw = max(rw, smoothstep(0.90, 0.99, plate_r(x, y)))
    rock = _mix(C_ROCK_DK, C_ROCK_LT, fbm(x * 0.26, y * 0.26, 55, 3))
    col = _mix(col, rock, rw)

    # the cliff lip catches light - one bright line separates the city from the void
    rr = plate_r(x, y)
    lipw = smoothstep(0.815, 0.875, rr) * (1.0 - smoothstep(0.895, 0.975, rr))
    col = _mix(col, hexcol("#7C8890"), lipw * 0.62)
    # and the face below it falls into shadow
    facew = smoothstep(0.93, 1.00, rr) * (1.0 - smoothstep(1.05, 1.28, rr))
    col = _mix(col, hexcol("#141C24"), facew * 0.72)

    # depth falloff into the abyss
    dk = smoothstep(-3.0, -27.0, z)
    col = _mix(col, C_ABYSS, dk * 0.88)
    # fine sediment brightness variation
    k = 0.92 + 0.16 * fbm(x * 0.62, y * 0.62, 77, 2)
    return (clamp(col[0] * k, 0, 1), clamp(col[1] * k, 0, 1), clamp(col[2] * k, 0, 1))


# ---------------------------------------------------------------- mesh
def _axis_expand(a, b, step, ext, growth=1.36):
    n = int(round((b - a) / step))
    xs = [a + i * step for i in range(n + 1)]
    left, v, cur = [], step * 1.3, xs[0]
    while cur > -ext:
        v *= growth
        cur -= v
        left.append(cur)
    right, v, cur = [], step * 1.3, xs[-1]
    while cur < ext:
        v *= growth
        cur += v
        right.append(cur)
    return list(reversed(left)) + xs + right


def build_seabed():
    step = 0.72
    xs = _axis_expand(-58.0, 58.0, step, 250.0)
    ys = _axis_expand(-52.0, 52.0, step, 250.0)
    nx, ny = len(xs), len(ys)
    verts, cols = [], []
    zmin, zmax = 1e9, -1e9
    for y in ys:
        for x in xs:
            z = seabed_h(x, y)
            zmin = min(zmin, z)
            zmax = max(zmax, z)
            verts.append((x, y, z))
            cols.append(seabed_color(x, y, z))
    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    me = bpy.data.meshes.new("SEABED")
    me.from_pydata(verts, [], faces)
    me.update()
    attr = me.color_attributes.new("terr_col", "FLOAT_COLOR", "POINT")
    for i, c in enumerate(cols):
        attr.data[i].color = (c[0], c[1], c[2], 1.0)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(MAT["seabed"])
    ob = bpy.data.objects.new("SEABED_PLATEAU", me)
    C("TERRAIN").objects.link(ob)
    print("SEABED verts=%d faces=%d  z=[%.2f, %.2f]" % (len(verts), len(faces), zmin, zmax))
    return ob


# ---------------------------------------------------------------- rock forms
def rock_cluster(name, r=4.0, h=5.0, seed=0, coll="OCEAN", pieces=5, sink=0.35,
                 mat_a=None, mat_b=None):
    """A cluster of eroded boulders, built at the ORIGIN.

    Position is applied by place().  An earlier version baked world coordinates
    into the pieces and then translated again on placement, which silently
    double-offset every rock in the scene.
    """
    rng = random.Random(seed)
    parts = []
    for i in range(pieces):
        a = rng.uniform(0, TAU)
        d = rng.uniform(0.0, r * 0.85)
        rr = r * rng.uniform(0.34, 0.78)
        hh = h * rng.uniform(0.42, 1.0)
        px = math.cos(a) * d
        py = math.sin(a) * d
        pz = hh * 0.5 - hh * sink
        ob = ico("%s_%d" % (name, i), rr, (px, py, pz),
                 (mat_b if i % 3 == 0 else mat_a)
                 or (MAT["rock"] if i % 3 else MAT["rock_dk"]), C("WORK"),
                 sub=2, scale=(1.0, rng.uniform(0.7, 1.25), hh / rr * 0.62), flat=True,
                 rot=(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), a))
        parts.append(ob)
    return make_master(name, parts, bevel=0.0, weighted=False)


def build_rim_rocks():
    """Silhouettes on the lip of the drop-off.

    Placed in polar coordinates on purpose: an earlier pass put them at a fixed
    x/y which landed them halfway down the cliff face, where they read as falling
    debris.  r=0.90 sits on the lip; r=1.06 is deliberate scree on the face.
    """
    specs = [
        # name,        angle, r_frac, radius, height, seed, pieces, sink
        ("RIM_ROCK_SW", 208.0, 0.90, 7.0, 10.0, 11, 7, 0.30),
        ("RIM_ROCK_S", 262.0, 0.91, 6.0, 8.0, 12, 6, 0.30),
        ("RIM_ROCK_SE", 320.0, 0.90, 8.0, 12.0, 13, 8, 0.30),
        ("RIM_ROCK_E", 6.0, 0.92, 7.5, 11.0, 14, 6, 0.30),
        ("RIM_ROCK_NE", 48.0, 0.90, 6.5, 9.0, 15, 6, 0.30),
        ("RIM_ROCK_N", 84.0, 0.91, 8.0, 10.0, 16, 7, 0.30),
        ("RIM_ROCK_NW", 128.0, 0.90, 7.0, 9.0, 17, 6, 0.30),
        ("RIM_ROCK_W", 168.0, 0.91, 8.5, 13.0, 18, 8, 0.30),
    ]
    for nm, ang, rf, r, h, sd, pc, sk in specs:
        a = math.radians(ang)
        x = math.cos(a) * PLATEAU_RX * rf
        y = math.sin(a) * PLATEAU_RY * rf
        rock_cluster(nm, r, h, sd, "OCEAN", pc)
        place(nm, x, y, rot=sd * 0.37, s=1.0, coll="OCEAN", z=seabed_h(x, y),
              sink=0.0)
    # scree further down the face, small and frequent
    scree = [("SCREE_%d" % i, 15 + i * 21.0, 1.04 + (i % 3) * 0.035)
             for i in range(16)]
    for nm, ang, rf in scree:
        a = math.radians(ang)
        x = math.cos(a) * PLATEAU_RX * rf
        y = math.sin(a) * PLATEAU_RY * rf
        rock_cluster(nm, 1.6 + (ang % 7) * 0.14, 2.2, int(ang) + 3,
                     "OCEAN", 3, sink=0.10)
        place(nm, x, y, rot=ang * 0.11, s=1.0, coll="OCEAN", z=seabed_h(x, y))
    print("RIM ROCKS %d + scree %d" % (len(specs), len(scree)))


def ray_to_seabed(u, v, cam_name="CAMERA_ABYSSAL_HERO", step=0.6, max_steps=6000):
    """March the pixel's view ray until it hits the seabed.

    Unprojecting at a fixed depth and then dropping to the floor puts the object
    somewhere else entirely - the floor can be 60 BU below the sampled point.
    Marching the actual ray is the only way to make a mass appear at a chosen
    pixel.
    """
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        return None
    m3 = cam.matrix_world.to_3x3()
    f = (m3 @ Vector((0, 0, -1))).normalized()
    right = (m3 @ Vector((1, 0, 0))).normalized()
    up = (m3 @ Vector((0, 1, 0))).normalized()
    tan = 18.0 / cam.data.lens
    d = (f + right * ((u - 0.5) * 2.0 * tan)
         + up * ((v - 0.5) * 2.0 * tan)).normalized()
    p = cam.location.copy()
    for _ in range(max_steps):
        p = p + d * step
        if p.z <= seabed_h(p.x, p.y):
            return p
    return None


def build_foreground_framed():
    """Near-water masses placed by pixel, not by guesswork.

    At 40 deg elevation the plateau fills only ~44% of a square frame's height, so
    the lower band is open water.  These masses enter from the bottom corners and
    give the eye a foreground value to measure the city against.
    """
    cam = bpy.data.objects.get("CAMERA_ABYSSAL_HERO")
    if cam is None:
        print("FOREGROUND skipped: no hero camera")
        return
    specs = [
        # name, screen u, screen v, radius, height, pieces, seed
        ("FORE_LEFT", 0.000, 0.000, 17.0, 52.0, 9, 81),
        ("FORE_RIGHT", 1.000, 0.000, 16.0, 46.0, 8, 82),
        ("FORE_MID_L", 0.100, 0.020, 10.0, 30.0, 7, 83),
        ("FORE_MID_R", 0.895, 0.010, 9.0, 25.0, 6, 84),
    ]
    made = 0
    for nm, u, v, r, h, pc, sd in specs:
        p = ray_to_seabed(u, v)
        if p is None:
            print("  foreground miss", nm)
            continue
        rock_cluster(nm, r, h, sd, "OCEAN", pc, sink=0.20,
                     mat_a=MAT["rock_dk"], mat_b=MAT["rock"])
        place(nm, p.x, p.y, rot=sd * 0.41, s=1.0, coll="OCEAN",
              z=seabed_h(p.x, p.y))
        made += 1
    print("FOREGROUND FRAMED %d" % made)


def build_plateau_detail():
    """Outcrops in the outer ring only.

    The first version scattered them through the middle of the city, where boulders
    between apartment blocks read as debris rather than geology.  r=0.72..0.88 keeps
    them on the open rim, between the districts and the drop-off.
    """
    specs = [
        # name, angle, r_frac, radius, height, seed, pieces
        ("OUT_A", 24.0, 0.80, 3.0, 2.0, 31, 4),
        ("OUT_B", 62.0, 0.76, 2.6, 1.6, 32, 3),
        ("OUT_C", 108.0, 0.82, 2.4, 1.4, 33, 3),
        ("OUT_D", 152.0, 0.78, 3.2, 2.2, 34, 4),
        ("OUT_E", 186.0, 0.84, 2.8, 1.8, 35, 4),
        ("OUT_F", 232.0, 0.80, 2.2, 1.3, 36, 3),
        ("OUT_G", 296.0, 0.78, 3.4, 2.4, 37, 4),
        ("OUT_H", 338.0, 0.83, 2.4, 1.5, 38, 3),
    ]
    for nm, ang, rf, r, h, sd, pc in specs:
        a = math.radians(ang)
        x = math.cos(a) * PLATEAU_RX * rf
        y = math.sin(a) * PLATEAU_RY * rf
        rock_cluster(nm, r, h, sd, "OCEAN", pc)
        place(nm, x, y, rot=sd * 0.61, s=1.0, coll="OCEAN", z=seabed_h(x, y))
    print("PLATEAU DETAIL %d" % len(specs))


def build_ground():
    build_seabed()
    build_rim_rocks()
    build_plateau_detail()
