"""
abyss_look.py : lighting design, cameras, composition solve, QA.

Lighting intent (see references/ART_DIRECTION.md):
  key   - one broad cool source from far above. Everything else is bounce.
  fill  - cyan from the city volume itself, not a lamp at camera.
  rim   - a dim teal up-light so silhouettes separate from the abyss.
  pract - warm interiors, amber industrial, cyan research, all emissive.
"""

import bpy
import math
import os
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

HERO = {"az": 14.0, "elev": 40.0, "lens": 85.0, "fill": 0.80,
        "target": (0.0, 0.0, 2.0), "dist": 0.0}

LIGHT = {}


# ---------------------------------------------------------------- lights
def _light_obj(name, ltype, loc, energy, color, size=1.0, target=None, angle=None):
    li = bpy.data.lights.new(name, ltype)
    li.energy = energy
    li.color = color
    if ltype == "AREA":
        li.shape = "DISK"
        li.size = size
    elif ltype == "SUN":
        li.angle = math.radians(angle if angle else 4.0)
    elif ltype == "POINT":
        li.shadow_soft_size = size
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    C("LIGHT").objects.link(ob)
    if target is not None:
        d = Vector(target) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    LIGHT[name] = ob
    return ob


def build_lights():
    # key: sun through 400 m of water - dim, cold, very soft
    sun = _light_obj("SUN_ABYSS", "SUN", (0, 0, 120), 2.6,
                     (0.58, 0.80, 1.00), angle=6.0)
    d = Vector((0.30, -0.46, -0.84)).normalized()
    sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    # fill: a broad cyan pool over the plateau, motivated by the city's own light
    _light_obj("FILL_CITY", "AREA", (6.0, -18.0, 46.0), 150000.0,
               (0.44, 0.78, 1.00), size=56.0, target=(0.0, -4.0, 0.0))
    # rim / separation
    _light_obj("RIM_ABYSS", "AREA", (-30.0, 46.0, -14.0), 6000.0,
               (0.20, 0.72, 0.78), size=60.0, target=(0.0, 0.0, 6.0))
    # low bounce off the seabed, keeps undersides from going pure black
    _light_obj("BOUNCE_SEABED", "AREA", (-4.0, -12.0, -22.0), 18000.0,
               (0.24, 0.44, 0.56), size=90.0, target=(0.0, 0.0, 8.0))
    # the near third of the hero frame is the drop-off and the abyss floor; without
    # these two it renders as a black band under a lit diorama
    _light_obj("FG_SHELF", "AREA", (0.0, -80.0, 18.0), 24000.0,
               (0.20, 0.52, 0.70), size=76.0, target=(0.0, -34.0, -5.0))
    _light_obj("FG_ABYSS", "AREA", (38.0, -52.0, -8.0), 20000.0,
               (0.14, 0.38, 0.54), size=88.0, target=(4.0, -18.0, -20.0))
    print("LIGHTS %d" % len([o for o in bpy.data.objects if o.type == "LIGHT"]))


# ---------------------------------------------------------------- cameras
def hero_points():
    # The frame is solved on the BUILT city, not on the whole plateau.  Framing the
    # 0.95 rim left a ring of empty seabed around a shrunken city in M2; the outer
    # edge now crops naturally into the foreground.
    pts = []
    for i in range(44):
        a = i * TAU / 44.0
        for f in (0.34, 0.48, 0.64):
            pts.append((math.cos(a) * PLATEAU_RX * f,
                        math.sin(a) * PLATEAU_RY * f, 0.0))
    for d in DOME_INFO:
        pts.append((d["x"], d["y"], d["z"] + d["r"]))
    return pts


def solve_hero_camera(az=None, elev=None, lens=None, fill=None, target=None,
                      name="CAMERA_ABYSSAL_HERO"):
    """Analytic framing solve.

    For a camera at target + dir*d, a point projects inside the frame when
    |x| <= fill*tan(hfov)*depth, and depth = d - (p-target).dir.  Solving for d
    directly is exact and cannot diverge, unlike a binary search followed by a
    recentre that keeps changing the distance.
    """
    sc = bpy.context.scene
    az = HERO["az"] if az is None else az
    elev = HERO["elev"] if elev is None else elev
    lens = HERO["lens"] if lens is None else lens
    fill = HERO["fill"] if fill is None else fill
    tgt = Vector(HERO["target"] if target is None else target)

    HERO.update({"az": az, "elev": elev, "lens": lens, "fill": fill})
    a = math.radians(az)
    e = math.radians(elev)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e),
                   math.sin(e))).normalized()

    cam = bpy.data.objects.get(name)
    if cam is None:
        cam = make_camera(name, tuple(tgt + dirv * 300.0), tuple(tgt), lens=lens)
    cam.data.lens = lens

    f = -dirv
    # right = forward x world-up.  Getting this backwards silently inverts every
    # lateral composition correction, so the sign is stated explicitly.
    right = f.cross(Vector((0.0, 0.0, 1.0))).normalized()
    up_cam = right.cross(f).normalized()
    tan_h = 18.0 / lens
    pts = [Vector(p) for p in hero_points()]

    def proj(t, d):
        cam.location = Vector(t) + dirv * d
        bpy.context.view_layer.update()
        pr = [world_to_camera_view(sc, cam, p) for p in pts]
        xs = [q.x for q in pr]
        ys = [q.y for q in pr]
        return min(xs), max(xs), min(ys), max(ys)

    def fit(t, fr):
        """Bisect the distance until the real projected bbox spans `fr`.

        An analytic bound is conservative: it guarantees every point is inside the
        frame, which leaves the bbox short of the target because the extreme points
        sit at different depths. Measuring the actual bbox is the only way to hit
        the number the composition asks for.
        """
        lo, hi = 20.0, 1400.0
        for _ in range(30):
            mid = (lo + hi) * 0.5
            x0, x1, y0, y1 = proj(t, mid)
            if (x1 - x0) > fr or (y1 - y0) > fr + 0.08:
                lo = mid
            else:
                hi = mid
        return (lo + hi) * 0.5

    t = Vector(tgt)
    d = fit(t, fill)
    for _ in range(4):
        x0, x1, y0, y1 = proj(t, d)
        cx, cy = (x0 + x1) * 0.5, (y0 + y1) * 0.5
        if abs(cx - 0.5) < 0.003 and abs(cy - 0.5) < 0.003:
            break
        span = 2.0 * tan_h * d
        t = t + right * ((cx - 0.5) * span) * 0.92 \
              + up_cam * ((cy - 0.5) * span) * 0.92
        d = fit(t, fill)

    d = fit(t, fill)
    cam.location = t + dirv * d
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()

    x0, x1, y0, y1 = proj(t, d)
    HERO["dist"] = d
    HERO["target"] = tuple(t)
    sc.camera = cam
    print("HERO CAM dist=%.1f az=%.0f elev=%.0f lens=%.0f -> width %.3f height %.3f"
          % (d, az, elev, lens, x1 - x0, y1 - y0))
    print("HERO target=(%.2f, %.2f, %.2f)  centre=(%.3f, %.3f)  px/BU=%.1f" %
          (t.x, t.y, t.z, (x0 + x1) * 0.5, (y0 + y1) * 0.5, 1920.0 / 104.0 * fill))
    return cam


def district_camera(name, tx, ty, tz, dist, elev=26.0, lens=55.0, az=None):
    """Camera outside the district, looking inward toward the city centre.

    An azimuth-based placement can easily end up inside the block being inspected
    - the first harbor camera sat between two cargo sheds and rendered nothing but
    walls.  Pushing outward from the origin guarantees a clear view.  For the city
    centre itself there is no outward direction, so `az` is required there.
    """
    if az is None:
        dx, dy = tx, ty
        L = math.hypot(dx, dy) or 1.0
        ux, uy = dx / L, dy / L
    else:
        a = math.radians(az)
        ux, uy = math.sin(a), -math.cos(a)
    e = math.radians(elev)
    horiz = dist * math.cos(e)
    loc = (tx + ux * horiz, ty + uy * horiz, tz + dist * math.sin(e))
    return make_camera(name, loc, (tx, ty, tz), lens=lens)


def build_cameras():
    hero = solve_hero_camera()
    district_camera("CAMERA_CITY_CENTER", 0.0, 0.0, 7.0, 52.0, 32.0, 68.0,
                    az=14.0)
    district_camera("CAMERA_RESIDENTIAL", -30.0, 6.0, 4.0, 30.0, 26.0, 62.0)
    district_camera("CAMERA_COMMERCIAL", -3.0, -19.0, 4.0, 40.0, 30.0, 52.0)
    district_camera("CAMERA_RESEARCH", 32.0, 2.0, 4.0, 28.0, 26.0, 62.0)
    district_camera("CAMERA_INDUSTRIAL", 25.0, -23.0, 3.0, 28.0, 24.0, 58.0)
    district_camera("CAMERA_HARBOR", -7.0, -33.0, 3.0, 40.0, 26.0, 62.0)
    district_camera("CAMERA_RESORT", 12.0, 24.0, 6.0, 40.0, 30.0, 66.0)
    district_camera("CAMERA_REEF_DETAIL", -34.0, -30.0, 1.0, 20.0, 16.0, 80.0)
    print("CAMERAS %d" % len([o for o in bpy.data.objects if o.type == "CAMERA"]))
    return hero


# ---------------------------------------------------------------- previews
def render_clay(path, res=900, samples=24, cam=None, fog=False):
    """Neutral clay pass. Diagnoses silhouette and composition separately from
    materials and lighting - a rule from the lighting-lookdev workflow.

    Fog is switched off by default: a clay pass that is already tinted by the
    atmosphere cannot answer the question it exists to answer.
    """
    sc = bpy.context.scene
    m = bpy.data.materials.get("MAT_CLAY_PREVIEW")
    if m is None:
        m = make_mat("MAT_CLAY_PREVIEW", "#B9BEC2", 0.0, 0.62)
    vl = bpy.context.view_layer
    prev = vl.material_override
    prev_mode = ATMO["mode"]
    vl.material_override = m
    if not fog:
        set_atmosphere("none")
    cam = cam or sc.camera
    out = render_to(cam, path, res, samples)
    vl.material_override = prev
    if not fog:
        set_atmosphere(prev_mode)
    return out


def render_hero(path, res=1280, samples=32):
    return render_to(bpy.data.objects["CAMERA_ABYSSAL_HERO"], path, res, samples)


# ---------------------------------------------------------------- QA
def qa_report(verbose=True):
    sc = bpy.context.scene
    objs = list(bpy.data.objects)
    tri = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            tri += len(o.data.loop_triangles)
    lights = [o for o in objs if o.type == "LIGHT"]
    cams = [o for o in objs if o.type == "CAMERA"]
    animated = [o for o in objs if o.animation_data and o.animation_data.action]
    sims = [o for o in objs if o.type == "MESH" and any(
        m.type in ("CLOTH", "FLUID", "RIGID_BODY", "DYNAMIC_PAINT", "PARTICLE")
        for m in o.modifiers)]
    districts = {}
    for c in bpy.data.collections:
        if c.name[:2].isdigit():
            districts[c.name[3:]] = len(c.objects)
    print("QA objs=%d meshes=%d lights=%d cameras=%d actions=%d armatures=%d "
          "animated=%d sim_modifiers=%d tris=%d" % (
              len(objs), len([o for o in objs if o.type == "MESH"]),
              len(lights), len(cams), len(bpy.data.actions),
              len([o for o in objs if o.type == "ARMATURE"]), len(animated),
              len(sims), tri))
    if verbose:
        print("QA districts " + " ".join("%s:%d" % kv for kv in sorted(districts.items())))
        bad = [o.name for o in objs if o.name.startswith(("Cube", "Sphere", "Cylinder",
                                                          "Plane", "Icosphere"))]
        if bad:
            print("QA default-named objects:", bad[:12])
    return {"objects": len(objs), "tris": tri, "lights": len(lights),
            "cameras": len(cams), "animated": len(animated)}


def build_look():
    build_lights()
    cam = build_cameras()
    build_foreground_framed()
    qa_report()
    return cam
