"""
abyss_domes.py : geodesic habitat kit.

The dome is the project's signature asset, so it is built properly rather than
approximated with a sphere:

  * a real geodesic shell (icosphere bisected at the equator, clean rim loop)
  * every strut modelled as a beam oriented radially, so ribs sit proud of the glass
  * node hubs at each vertex - the joints read as cast connectors, not intersections
  * horizontal stiffener rings at two latitudes
  * foundation collar that meets the sediment (nothing floats)
  * airlock with frame, two door leaves and hazard chevrons
  * interior: floor, plaza, ring of building massing, light strips

Glass and frame are separate objects on purpose: one is alpha-blended, the other
is opaque, and keeping them apart makes transparency sorting predictable.
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector

DOME_INFO = []


# ---------------------------------------------------------------- geodesic base
def _dome_geo(r, sub):
    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    except TypeError:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, diameter=r * 2.0)
    bmesh.ops.bisect_plane(
        bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-4,
        plane_co=(0.0, 0.0, 0.0), plane_no=(0.0, 0.0, 1.0), clear_inner=True)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    verts = [tuple(v.co) for v in bm.verts]
    vmap = {v: i for i, v in enumerate(bm.verts)}
    edges = [(vmap[e.verts[0]], vmap[e.verts[1]]) for e in bm.edges]
    faces = [tuple(vmap[v] for v in f.verts) for f in bm.faces]
    bm.free()
    return verts, edges, faces


def _beam_radial(bm, p0, p1, w, h):
    """Rectangular strut whose 'height' axis points away from the dome centre."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ln = d.length
    if ln < 1e-6:
        return
    d.normalize()
    mid = (p0 + p1) * 0.5
    rad = mid.normalized()
    rad_p = rad - d * rad.dot(d)
    if rad_p.length < 1e-5:
        rad_p = Vector((0.0, 0.0, 1.0))
    up = rad_p.normalized()
    side = up.cross(d).normalized()
    base = len(bm.verts)
    for p in (p0, p1):
        bm.verts.new(p + side * (w * 0.5) + up * (h * 0.5))
        bm.verts.new(p - side * (w * 0.5) + up * (h * 0.5))
        bm.verts.new(p - side * (w * 0.5) - up * (h * 0.5))
        bm.verts.new(p + side * (w * 0.5) - up * (h * 0.5))
    bm.verts.ensure_lookup_table()
    v = bm.verts
    for a, b, c, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        try:
            bm.faces.new((v[base + a], v[base + b], v[base + c], v[base + e]))
        except ValueError:
            pass


def _node_hub(bm, p, size):
    p = Vector(p)
    up = p.normalized() if p.length > 1e-5 else Vector((0, 0, 1))
    tmp = Vector((0, 0, 1)) if abs(up.z) < 0.9 else Vector((1, 0, 0))
    side = up.cross(tmp).normalized()
    fwd = side.cross(up).normalized()
    h = size * 0.5
    base = len(bm.verts)
    for sz in (-1, 1):
        for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            bm.verts.new(p + side * (a * h) + fwd * (b * h) + up * (sz * h))
    v = bm.verts
    bm.verts.ensure_lookup_table()
    for a, b, c, e in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
                       (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        try:
            bm.faces.new((v[base + a], v[base + b], v[base + c], v[base + e]))
        except ValueError:
            pass


def _bm_to_obj(name, bm, mat, coll, smooth=False):
    coll = _res(coll)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# ---------------------------------------------------------------- parts
def _airlock(parts, name, r, ang, w=1.05, h=2.3, coll=None):
    coll = coll or C("WORK")
    ca, sa = math.cos(ang), math.sin(ang)
    out = Vector((ca, sa, 0.0))
    p0 = out * (r * 0.80)
    p1 = out * (r * 1.12)
    parts.append(tube_between(name + "_tube", p0 + Vector((0, 0, h * 0.5)),
                              p1 + Vector((0, 0, h * 0.5)), w, w,
                              MAT["navy_lt"], coll, sides=12))
    # door frame
    fw = w * 2.15
    parts.append(box(name + "_frame", (0.30, fw, h * 1.18), (0, 0, 0),
                     MAT["titanium"], coll))
    frm = parts[-1]
    frm.location = p1 + Vector((0, 0, h * 0.5))
    frm.rotation_euler = (0, 0, ang + math.pi * 0.5)
    # two door leaves, slightly proud of the frame
    for s in (-1, 1):
        leaf = box(name + "_leaf%d" % s, (0.14, w * 0.92, h * 0.92),
                   p1 + out * 0.12 + Vector((0, 0, h * 0.52)), MAT["steel"], coll)
        leaf.rotation_euler = (0, 0, ang + math.pi * 0.5)
        leaf.location = leaf.location + Vector((-sa, ca, 0)) * (s * w * 0.50)
        parts.append(leaf)
    # hazard chevrons above the door
    for i in range(3):
        ch = box(name + "_hz%d" % i, (0.10, w * 1.9, 0.14),
                 p1 + out * 0.14 + Vector((0, 0, h * 1.14 + i * 0.20)),
                 MAT["paint_safe"] if i % 2 == 0 else MAT["steel"], coll)
        ch.rotation_euler = (0, 0, ang + math.pi * 0.5)
        parts.append(ch)
    # landing step
    st = box(name + "_step", (w * 2.2, w * 2.2, 0.22),
             p1 + out * 0.30 + Vector((0, 0, 0.11)), MAT["deck"], coll)
    st.rotation_euler = (0, 0, ang + math.pi * 0.5)
    parts.append(st)


def _foundation(parts, name, r, coll, height=2.6):
    parts.append(cyl(name + "_collar", r * 1.045, height,
                     (0, 0, -height * 0.5 + 0.06), MAT["concrete"], coll,
                     verts=48, smooth=True))
    parts.append(cyl(name + "_lip", r * 1.075, 0.30, (0, 0, 0.16),
                     MAT["steel"], coll, verts=48, smooth=True))
    # maintenance walkway ring at the base
    parts.append(torus(name + "_walk", r * 1.11, 0.16, (0, 0, 0.30),
                       MAT["deck"], coll, mseg=48, nseg=6))
    # buttresses, evenly spaced
    for i in range(8):
        a = i * TAU / 8.0 + 0.19
        ca, sa = math.cos(a), math.sin(a)
        b = box(name + "_but%d" % i, (0.55, 0.85, 2.3),
                (ca * r * 1.01, sa * r * 1.01, -0.95), MAT["navy"], coll)
        b.rotation_euler = (0, 0, a + math.pi * 0.5)
        parts.append(b)


def build_dome(name, cx, cy, r, sub=2, style="geodesic", coll="CENTRAL",
               rot=0.0, airlock_deg=90.0, rings=(0.42, 0.74),
               rib_scale=1.0, interior=True, density=1.0, seed=0,
               lights=1, glass_mat=None, sink=0.0, tag=None):
    """Build one habitat dome at (cx, cy).

    Everything is modelled in LOCAL space with the base plane at z=0, then the
    merged master is instanced at the site.  This keeps the master reusable and
    means the interior, foundation and shell can never drift apart.
    """
    rng = random.Random(seed)
    cz = seabed_h(cx, cy) - sink
    rib = max(0.085, r * 0.0205) * rib_scale
    glass_mat = glass_mat or MAT["glass_dome"]
    work = C("WORK")

    verts, edges, faces = _dome_geo(r, sub)
    if style == "ribbed":
        keep = [(a, b) for a, b in edges if abs(verts[a][2] - verts[b][2]) > r * 0.10]
        if len(keep) < 12:
            keep = edges
        edges = keep
    elif style == "faceted":
        rib = max(0.11, r * 0.029)

    # ---- frame: every strut as a radial beam plus a cast node hub
    fbm_ = bmesh.new()
    for a, b in edges:
        _beam_radial(fbm_, verts[a], verts[b], rib, rib * 1.25)
    hub = rib * 2.4 if style != "faceted" else rib * 2.0
    for p in verts:
        _node_hub(fbm_, p, hub)
    parts = [_bm_to_obj(name + "_FRAME", fbm_, MAT["titanium"], work)]

    # ---- stiffener rings
    for f in rings:
        rr = r * math.sqrt(max(0.0, 1.0 - f * f))
        parts.append(torus(name + "_ring%.2f" % f, rr, rib * 1.05,
                           (0, 0, r * f), MAT["navy_lt"], work,
                           mseg=40, nseg=6))

    # ---- foundation + airlocks
    _foundation(parts, name, r, work)
    n_air = 2 if r > 9.0 else 1
    for i in range(n_air):
        _airlock(parts, "%s_AIR%d" % (name, i), r,
                 math.radians(airlock_deg) + i * math.pi * 1.15, coll=work)

    # ---- observation balcony
    if r > 6.5:
        a = math.radians(airlock_deg) + math.pi * 0.62
        f = 0.58
        rr = r * math.sqrt(1.0 - f * f)
        bx, by = math.cos(a) * rr * 0.86, math.sin(a) * rr * 0.86
        bal = box(name + "_balcony", (rr * 0.42, 2.2, 0.20), (bx, by, r * f),
                  MAT["deck"], work)
        bal.rotation_euler = (0, 0, a)
        parts.append(bal)
        rail = box(name + "_balrail", (rr * 0.42, 0.08, 0.55),
                   (bx, by, r * f + 0.34), MAT["steel_lt"], work)
        rail.rotation_euler = (0, 0, a)
        parts.append(rail)
        for s in (-1, 1):
            parts.append(cyl(name + "_balp%d" % s, 0.07, 0.8,
                             (bx + math.sin(a) * s * rr * 0.19,
                              by - math.cos(a) * s * rr * 0.19, r * f - 0.45),
                             MAT["steel"], work, verts=6))

    # ---- interior
    if interior:
        build_dome_interior(parts, name, r, rng, density=density, coll=work)

    frame_master = make_master(name + "_FRAME", parts, bevel=0.010, weighted=True)

    # ---- glass shell (separate object: alpha-blended draws must not be merged
    #      into the opaque frame mesh)
    me = bpy.data.meshes.new(name + "_GLASS")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(glass_mat)
    g = bpy.data.objects.new(name + "_GLASS", me)
    work.objects.link(g)
    C("WORK").objects.unlink(g)
    C("LIB").objects.link(g)
    g.hide_render = True
    g.hide_viewport = True
    g.location = (0, 0, 0)
    POOL[name + "_GLASS"] = {"mesh": g.data, "tris": len(faces), "obj": g, "parts": 1}

    # ---- place both instances
    instance(name + "_FRAME", coll, loc=(cx, cy, cz), rot=(0, 0, rot), tag=tag)
    gi = instance(name + "_GLASS", coll, loc=(cx, cy, cz), rot=(0, 0, rot), tag=tag)
    try:
        gi.visible_shadow = False
    except Exception:
        pass

    for i in range(lights):
        add_dome_light("%s_L%d" % (name, i), cx, cy, cz + r * (0.35 + 0.25 * i),
                       r, i)

    DOME_INFO.append({"name": name, "x": cx, "y": cy, "z": cz, "r": r,
                      "style": style, "coll": coll})
    print("DOME %-14s r=%.1f style=%-8s tris=%d" % (
        name, r, style, POOL[name + "_FRAME"]["tris"]))
    return gi


def add_dome_light(name, x, y, z, r, idx=0):
    li = bpy.data.lights.new(name, "POINT")
    li.energy = 760.0 * max(1.0, r * 0.15)
    li.color = (1.0, 0.80, 0.58) if idx % 2 == 0 else (0.55, 0.86, 1.0)
    li.shadow_soft_size = max(1.2, r * 0.22)
    ob = bpy.data.objects.new(name, li)
    ob.location = (x, y, z)
    C("LIGHT").objects.link(ob)
    return ob


def build_dome_interior(parts, name, r, rng, density=1.0, coll=None):
    """A terraced plaza, not a ring of lit cylinders.

    The first version stood towers in the middle of the floor.  From the hero camera
    that read as a field of glowing drums with no circulation.  This is an
    amphitheatre: four stepped terraces rising to a lit basin, radial stairs, and the
    buildings pushed out to the shell where buildings belong.
    """
    coll = coll or C("WORK")
    parts.append(cyl(name + "_floor", r * 0.985, 0.22, (0, 0, -0.02),
                     MAT["deck"], coll, verts=56, smooth=True))

    # --- four terraces, rising toward the centre
    tiers = ((0.760, 0.42), (0.590, 0.86), (0.430, 1.30), (0.280, 1.74))
    for i, (rr, hh) in enumerate(tiers):
        parts.append(cyl(name + "_ter%d" % i, r * rr, hh, (0, 0, hh * 0.5),
                         MAT["deck"] if i % 2 == 0 else MAT["concrete"], coll,
                         verts=48, smooth=True))
        parts.append(torus(name + "_nos%d" % i, r * rr - 0.06, 0.045,
                           (0, 0, hh), MAT["glow_strip"], coll, mseg=44,
                           nseg=4))

    # --- radial stairs: three landings per spoke, cut through the terraces
    for i in range(6):
        a = i * TAU / 6.0 + 0.26
        ca, sa = math.cos(a), math.sin(a)
        for k, (rad, hh, wd) in enumerate(((0.845, 0.44, 1.30),
                                           (0.672, 0.88, 1.15),
                                           (0.505, 1.32, 1.00),
                                           (0.352, 1.76, 0.90))):
            ob = box(name + "_st%d_%d" % (i, k), (r * 0.115, wd, hh * 0.5),
                     (ca * r * rad, sa * r * rad, hh * 0.25 + 0.06),
                     MAT["deck"], coll)
            ob.rotation_euler = (0.0, 0.0, a)
            parts.append(ob)
        # handrail along the spoke
        for k in range(3):
            rad = 0.70 - k * 0.15
            parts.append(cyl(name + "_rp%d_%d" % (i, k), 0.05, 1.05,
                             (ca * r * rad, sa * r * rad,
                              r * 0.0 + 0.42 + k * 0.44 + 0.52),
                             MAT["steel_lt"], coll, verts=5))

    # --- basin and monument at the centre
    parts.append(cyl(name + "_pool", r * 0.175, 0.14, (0, 0, 1.80),
                     MAT["glass_win"], coll, verts=32, smooth=True))
    parts.append(cyl(name + "_poolin", r * 0.105, 0.06, (0, 0, 1.86),
                     MAT["emit_teal"], coll, verts=32, smooth=True))
    parts.append(cyl(name + "_mono", r * 0.052, r * 0.30, (0, 0, 2.02 + r * 0.15),
                     MAT["titanium"], coll, verts=12, smooth=True,
                     r2=r * 0.018))
    parts.append(torus(name + "_mring", r * 0.068, 0.018,
                       (0, 0, 2.10 + r * 0.12), MAT["emit_cyan"], coll,
                       mseg=20, nseg=4))
    parts.append(sphere(name + "_mbea", 0.10, (0, 0, 2.04 + r * 0.30),
                        MAT["emit_white"], coll, seg=10, rings=6))

    # --- buildings against the shell, with real facades
    nb = max(7, int(10 * density))
    for i in range(nb):
        a = i * TAU / nb + 0.18
        px, py = math.cos(a) * r * 0.885, math.sin(a) * r * 0.885
        w, d = r * 0.235, r * 0.150
        hh = r * rng.uniform(0.32, 0.58)
        body = MAT["ceramic"] if i % 2 else MAT["composite_lt"]
        ob = box(name + "_pb%d" % i, (w, d, hh), (px, py, hh * 0.5), body, coll)
        ob.rotation_euler = (0.0, 0.0, a)
        parts.append(ob)
        # glazing bands and a lit ground floor, so the shell reads as inhabited
        for k in range(3):
            bz = hh * (0.28 + k * 0.26)
            g = box(name + "_pg%d_%d" % (i, k), (w * 0.82, 0.05, hh * 0.11),
                    (px - math.sin(a) * 0, py - math.cos(a) * 0, bz), body, coll)
            # offset toward the plaza side
            g.location.x = px - math.sin(a) * (d * 0.52)
            g.location.y = py + math.cos(a) * (d * 0.52)
            g.rotation_euler = (0.0, 0.0, a)
            parts.append(g)
            band = box(name + "_pbnd%d_%d" % (i, k), (w * 0.86, 0.03, hh * 0.05),
                       (0, 0, bz + hh * 0.07), MAT["emit_room"], coll)
            band.location.x = px - math.sin(a) * (d * 0.54)
            band.location.y = py + math.cos(a) * (d * 0.54)
            band.rotation_euler = (0.0, 0.0, a)
            parts.append(band)
        cap = box(name + "_pc%d" % i, (w * 1.06, d * 1.06, 0.16),
                  (px, py, hh + 0.08), MAT["titanium"], coll)
        cap.rotation_euler = (0.0, 0.0, a)
        parts.append(cap)
        # balcony rail facing the plaza
        rail = box(name + "_pr%d" % i, (w * 0.9, 0.05, 0.05),
                   (px - math.sin(a) * (d * 0.60),
                    py + math.cos(a) * (d * 0.60), hh * 0.56),
                   MAT["steel_lt"], coll)
        rail.rotation_euler = (0.0, 0.0, a)
        parts.append(rail)

    # --- planting and furniture on the terraces
    for ring, (rr, hh, count) in enumerate(((0.665, 0.86, 6), (0.500, 1.30, 5))):
        for i in range(count):
            a = i * TAU / count + 0.42 + ring * 0.3
            px, py = math.cos(a) * r * rr, math.sin(a) * r * rr
            parts.append(cyl(name + "_pit%d_%d" % (ring, i), r * 0.036, 0.16,
                             (px, py, hh + 0.08), MAT["concrete"], coll,
                             verts=10, smooth=True))
            for k in range(3):
                b = k * TAU / 3.0 + a
                parts.append(ico(name + "_sh%d_%d_%d" % (ring, i, k), r * 0.026,
                                 (px + math.cos(b) * r * 0.026,
                                  py + math.sin(b) * r * 0.026, hh + 0.30),
                                 MAT["plant"] if k % 2 else MAT["plant_dk"],
                                 coll, sub=1, scale=(0.9, 0.9, 1.4)))
    for i in range(8):
        a = i * TAU / 8.0 + 0.4
        prop_bench(parts, name + "_bn%d" % i, Frame(0, 0, 0, 0),
                   math.cos(a) * r * 0.70, math.sin(a) * r * 0.70, 0.44,
                   r * 0.13, math.pi * 0.5 + a)
# ---------------------------------------------------------------- district domes
def build_central_dome():
    build_dome("DOME_CENTRAL", 0.0, 0.0, 13.5, sub=2, style="geodesic",
               coll="CENTRAL", airlock_deg=196.0, rings=(0.30, 0.52, 0.75),
               density=1.25, seed=101, lights=3, tag="central")


def build_support_domes():
    specs = [
        # name,      x,      y,     r,   sub, style,      coll,          seed, dens
        ("DOME_RES1", -30.0, 4.0, 6.0, 2, "geodesic", "RESIDENTIAL", 201, 1.0),
        ("DOME_RES2", -23.0, 20.0, 4.2, 1, "ribbed", "RESIDENTIAL", 202, 0.8),
        ("DOME_RES3", -38.0, -12.0, 4.8, 2, "faceted", "RESIDENTIAL", 203, 0.7),
        ("DOME_COM1", -23.0, -8.0, 4.4, 2, "geodesic", "COMMERCIAL", 204, 1.0),
        ("DOME_RESEARCH", 33.0, 3.0, 5.4, 2, "geodesic", "RESEARCH", 206, 1.0),
        ("DOME_RESORT", 9.0, 29.0, 6.5, 2, "geodesic", "RESORT", 207, 1.15),
        ("DOME_AGRI", -26.0, -19.0, 6.0, 2, "ribbed", "AGRI", 208, 1.2),
        ("DOME_MED", -11.0, 22.0, 3.6, 1, "faceted", "PUBLIC", 209, 0.6),
        ("DOME_IND", 26.0, -24.0, 4.0, 1, "faceted", "INDUSTRIAL", 210, 0.5),
    ]
    for nm, x, y, r, sub, style, col, seed, dens in specs:
        build_dome(nm, x, y, r, sub=sub, style=style, coll=col,
                   airlock_deg=250.0 + seed * 7.0, seed=seed, density=dens,
                   lights=1, tag=col.lower())
    print("SUPPORT DOMES %d" % len(specs))


def build_domes():
    build_central_dome()
    build_support_domes()