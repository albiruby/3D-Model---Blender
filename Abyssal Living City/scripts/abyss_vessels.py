"""
abyss_vessels.py : the submarine fleet.

Six masters, each authored once and placed.  Every hull is built along local +X
so "forward" is unambiguous, and every vessel follows the same vocabulary - hull,
canopy, thruster pods, dorsal light bar, keel fins - which is what makes them read
as one fleet instead of six unrelated objects.

Static: no animation, no rotation over time.  They are posed, not driven.
"""

import bpy
import bmesh
import math
from mathutils import Vector

VESSELS = {}


def _v_m(name, parts, bevel=0.008):
    ob = make_master(name, parts, bevel=bevel, weighted=True)
    VESSELS[name] = ob
    return ob


def _v_hull(name, length, r0, r1, loc, mat, verts=20, rot=(0, math.pi * 0.5, 0)):
    return cyl(name, r0, length, loc, mat, C("WORK"), rot=rot, verts=verts,
               smooth=True, r2=r1)


def _v_thruster(parts, name, x, y, z, r=0.30, ln=0.9, tilt=0.0):
    """One ducted pod: cowl, spinning disc recess, emissive ring."""
    parts.append(cyl(name + "_c", r, ln, (x, y, z), MAT["steel_lt"], C("WORK"),
                     rot=(0, math.pi * 0.5 + tilt, 0), verts=14, smooth=True,
                     r2=r * 1.12))
    parts.append(cyl(name + "_d", r * 0.72, 0.10, (x - ln * 0.52, y, z),
                     MAT["navy"], C("WORK"),
                     rot=(0, math.pi * 0.5 + tilt, 0), verts=12, smooth=True))
    parts.append(torus(name + "_r", r * 1.02, r * 0.11, (x - ln * 0.10, y, z),
                       MAT["emit_cyan"], C("WORK"),
                       rot=(0, math.pi * 0.5 + tilt, 0), mseg=16, nseg=4))


def _v_dorsal(parts, name, x0, x1, z, w=0.16, h=0.34):
    parts.append(box(name + "_fin", (x1 - x0, w, h),
                     ((x0 + x1) * 0.5, 0, z), MAT["titanium"], C("WORK")))
    parts.append(box(name + "_bar", (x1 - x0 - 0.25, w * 0.55, 0.07),
                     ((x0 + x1) * 0.5, 0, z + h * 0.5 + 0.03),
                     MAT["emit_white"], C("WORK")))


def _v_keel(parts, name, x, z, span=1.0, mat=None):
    mat = mat or MAT["steel_lt"]
    parts.append(box(name + "_k", (1.1, 0.10, 0.28), (x, 0, z), mat, C("WORK")))
    for s in (-1, 1):
        parts.append(box(name + "_p%d" % s, (0.9, span, 0.08),
                         (x - 0.2, s * span * 0.5, z), mat, C("WORK")))


# ---------------------------------------------------------------- masters
def vessel_passenger():
    """Long pressurised shuttle: the harbour workhorse."""
    parts = []
    L = 11.0
    parts.append(_v_hull("VP_MAIN", L, 1.55, 1.05, (0, 0, 0), MAT["ceramic"], verts=22))
    parts.append(sphere("VP_NOSE", 1.12, (L * 0.5, 0, 0), MAT["ceramic"],
                        C("WORK"), seg=20, rings=12, scale=(0.85, 1.0, 1.0)))
    parts.append(sphere("VP_TAIL", 1.02, (-L * 0.5, 0, 0), MAT["ceramic"],
                        C("WORK"), seg=18, rings=10, scale=(0.70, 1.0, 1.0)))
    # canopy band
    parts.append(cyl("VP_CAN", 1.06, 2.6, (L * 0.20, 0, 0.10),
                     MAT["glass_dark"], C("WORK"), rot=(0, math.pi * 0.5, 0),
                     verts=22, smooth=True, r2=1.30))
    # six portholes, three per side
    for s in (-1, 1):
        for i in range(3):
            parts.append(sphere("VP_PH%d%d" % (s, i), 0.24,
                                (-2.4 + i * 2.1, s * 1.36, 0.28),
                                MAT["glass_win"], C("WORK"), seg=12, rings=7,
                                scale=(1.0, 0.55, 1.0)))
    for s in (-1, 1):
        _v_thruster(parts, "VP_T%d" % s, -L * 0.52, s * 1.05, -0.15, 0.34, 1.0)
    _v_dorsal(parts, "VP", -3.6, 1.2, 1.34)
    _v_keel(parts, "VP", -1.0, -1.28, 1.25)
    parts.append(box("VP_DOCK", (2.2, 0.55, 0.16), (1.2, 0, 1.42),
                     MAT["titanium"], C("WORK")))
    parts.append(sphere("VP_BEACON", 0.14, (-L * 0.5 + 0.4, 0, 1.10),
                        MAT["emit_amber"], C("WORK"), seg=10, rings=6))
    return _v_m("VSL_PASSENGER", parts)


def vessel_research():
    """Squat submersible with a full frontal viewport and working arms."""
    parts = []
    parts.append(sphere("VR_BODY", 1.85, (0, 0, 0), MAT["ceramic"], C("WORK"),
                        seg=24, rings=14, scale=(1.25, 1.0, 0.92)))
    parts.append(cyl("VR_FRAME", 0.16, 3.9, (0.3, 0, 0.10), MAT["titanium"],
                     C("WORK"), rot=(0, math.pi * 0.5, 0), verts=8))
    # frontal viewport
    parts.append(sphere("VR_EYE", 1.10, (2.05, 0, 0.16), MAT["glass_win"],
                        C("WORK"), seg=20, rings=11, scale=(0.55, 1.0, 1.0)))
    parts.append(torus("VR_EYER", 1.12, 0.10, (1.92, 0, 0.16), MAT["titanium"],
                       C("WORK"), rot=(0, math.pi * 0.5, 0), mseg=24, nseg=5))
    # sample basket
    for s in (-1, 1):
        parts.append(box("VR_BASK%d" % s, (1.5, 0.10, 0.9),
                         (-0.6, s * 1.45, -0.55), MAT["steel"], C("WORK")))
    parts.append(box("VR_BASKB", (1.5, 3.0, 0.10), (-0.6, 0, -1.0),
                     MAT["steel"], C("WORK")))
    # manipulator arms
    for s in (-1, 1):
        parts.append(cyl("VR_UA%d" % s, 0.09, 1.2, (1.5, s * 0.95, -0.85),
                         MAT["steel_lt"], C("WORK"),
                         rot=(0, math.pi * 0.42, s * 0.22), verts=6))
        parts.append(cyl("VR_FA%d" % s, 0.07, 1.0, (2.35, s * 0.80, -1.25),
                         MAT["steel_lt"], C("WORK"),
                         rot=(0, math.pi * 0.62, s * 0.30), verts=6))
    # floodlights on a crossbar
    for s in (-1, 1):
        parts.append(box("VR_LAMPB%d" % s, (0.34, 0.40, 0.30),
                         (1.90, s * 1.25, 0.95), MAT["titanium"], C("WORK")))
        parts.append(cyl("VR_LAMP%d" % s, 0.16, 0.16, (2.12, s * 1.25, 0.95),
                         MAT["emit_white"], C("WORK"),
                         rot=(0, math.pi * 0.5, 0), verts=12))
    parts.append(_v_thruster(parts, "VR_T", -2.15, 0.0, 0.55, 0.40, 1.0))
    for s in (-1, 1):
        _v_thruster(parts, "VR_TS%d" % s, -1.5, s * 1.55, -0.55, 0.24, 0.7)
    parts.append(cyl("VR_MAST", 0.05, 1.5, (-0.9, 0, 1.55), MAT["titanium"],
                     C("WORK"), verts=5))
    parts.append(sphere("VR_BEACON", 0.11, (-0.9, 0, 2.32), MAT["emit_cyan"],
                        C("WORK"), seg=8, rings=5))
    return _v_m("VSL_RESEARCH", parts)


def vessel_cargo():
    """Boxy hauler with a container deck."""
    parts = []
    L = 12.0
    parts.append(box("VC_HULL", (L, 3.0, 2.0), (0, 0, 0), MAT["steel"],
                     C("WORK")))
    parts.append(box("VC_BOW", (1.3, 2.4, 1.6), (L * 0.5 + 0.55, 0, 0.1),
                     MAT["steel_lt"], C("WORK")))
    parts.append(box("VC_DECK", (L * 0.92, 3.2, 0.22), (0, 0, 1.11),
                     MAT["steel_lt"], C("WORK")))
    # container stacks
    cols = ((MAT["paint_safe"], "VC_C1"), (MAT["paint_w"], "VC_C2"),
            (MAT["composite"], "VC_C3"))
    for i, (mat, nm) in enumerate(cols):
        x = -4.0 + i * 2.9
        parts.append(box(nm + "a", (2.5, 2.4, 1.1), (x, 0, 1.78), mat,
                         C("WORK")))
        parts.append(box(nm + "b", (2.5, 2.4, 1.1), (x, 0, 2.93),
                         MAT["composite_lt"] if i % 2 else MAT["paint_w"],
                         C("WORK")))
        for k in range(3):
            parts.append(box("%s_r%d" % (nm, k), (2.52, 2.44, 0.06),
                             (x, 0, 1.28 + k * 1.15), MAT["steel"],
                             C("WORK")))
    # bridge
    parts.append(box("VC_BRIDGE", (2.4, 2.2, 1.5), (L * 0.30, 0, 2.0),
                     MAT["ceramic"], C("WORK")))
    parts.append(box("VC_BGLASS", (0.10, 1.9, 0.70), (L * 0.30 + 1.22, 0,
                     2.18), MAT["glass_win"], C("WORK")))
    for s in (-1, 1):
        _v_thruster(parts, "VC_T%d" % s, -L * 0.55, s * 1.0, -0.35, 0.42, 1.2)
    _v_keel(parts, "VC", -0.5, -1.20, 1.4)
    parts.append(box("VC_RAMP", (0.4, 2.6, 1.5), (L * 0.5 + 1.15, 0, -0.35),
                     MAT["steel_lt"], C("WORK")))
    parts.append(sphere("VC_BEACON", 0.16, (L * 0.30, 0, 2.85),
                        MAT["emit_amber"], C("WORK"), seg=10, rings=6))
    return _v_m("VSL_CARGO", parts)


def vessel_pod():
    """Single-person runabout - small enough to be parked on a balcony."""
    parts = []
    parts.append(sphere("VPD_BODY", 0.95, (0, 0, 0), MAT["composite_lt"],
                        C("WORK"), seg=20, rings=12, scale=(1.55, 1.0, 0.95)))
    parts.append(sphere("VPD_CAN", 0.72, (0.62, 0, 0.30), MAT["glass_dark"],
                        C("WORK"), seg=18, rings=10, scale=(0.95, 0.95, 0.80)))
    parts.append(torus("VPD_RIM", 0.74, 0.06, (0.55, 0, 0.26),
                       MAT["titanium"], C("WORK"),
                       rot=(0, math.pi * 0.5, 0), mseg=20, nseg=4))
    for s in (-1, 1):
        _v_thruster(parts, "VPD_T%d" % s, -1.42, s * 0.62, -0.20, 0.22, 0.6)
    _v_keel(parts, "VPD", -0.2, -0.85, 0.65)
    parts.append(box("VPD_BAR", (0.10, 0.55, 0.10), (0.30, 0, 0.90),
                     MAT["emit_white"], C("WORK")))
    return _v_m("VSL_POD", parts)


def vessel_tourist():
    """Wide, slow sightseer: the largest glass area in the fleet."""
    parts = []
    L = 9.5
    parts.append(cyl("VT_HULL", 1.95, L, (0, 0, 0), MAT["ceramic"], C("WORK"),
                     rot=(0, math.pi * 0.5, 0), verts=24, smooth=True, r2=1.35))
    parts.append(sphere("VT_NOSE", 1.40, (L * 0.5, 0, 0), MAT["ceramic"],
                        C("WORK"), seg=20, rings=12, scale=(0.80, 1.0, 0.92)))
    # top and bottom panorama domes
    parts.append(sphere("VT_TOPDOME", 1.74, (0.2, 0, 1.15), MAT["glass_win"],
                        C("WORK"), seg=24, rings=12, scale=(1.55, 1.0, 0.62)))
    parts.append(sphere("VT_BOTDOME", 1.40, (0.2, 0, -1.05), MAT["glass_win"],
                        C("WORK"), seg=20, rings=10, scale=(1.50, 1.0, 0.55)))
    parts.append(torus("VT_TRIM", 1.78, 0.08, (0.2, 0, 0.18),
                       MAT["titanium"], C("WORK"), mseg=28, nseg=5))
    for i in range(12):
        a = i * TAU / 12.0
        parts.append(cyl("VT_RIB%d" % i, 0.05, 0.95,
                         (0.2 + math.cos(a) * 1.74, math.sin(a) * 1.74, 1.42),
                         MAT["titanium"], C("WORK"), verts=5,
                         rot=(0, math.pi * 0.5, a)))
    for s in (-1, 1):
        _v_thruster(parts, "VT_T%d" % s, -L * 0.55, s * 1.35, -0.25, 0.36, 0.9)
    _v_keel(parts, "VT", -0.6, -1.45, 1.5)
    _v_dorsal(parts, "VT", -4.2, -1.6, 1.60, 0.18, 0.30)
    parts.append(sphere("VT_BEACON", 0.15, (-L * 0.5 + 0.3, 0, 0.95),
                        MAT["emit_cyan"], C("WORK"), seg=10, rings=6))
    return _v_m("VSL_TOURIST", parts)


def vessel_drone():
    """Maintenance drone: an open frame, four ducted fans, one tool arm."""
    parts = []
    parts.append(box("VD_FRAME", (1.5, 1.3, 0.30), (0, 0, 0), MAT["titanium"],
                     C("WORK")))
    parts.append(sphere("VD_EYE", 0.30, (0.80, 0, 0.16), MAT["glass_win"],
                        C("WORK"), seg=14, rings=8))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 0.95, sy * 0.90
            parts.append(cyl("VD_D%d%d" % (sx, sy), 0.46, 0.14, (cx, cy, 0.18),
                             MAT["steel"], C("WORK"), verts=14))
            parts.append(cyl("VD_DI%d%d" % (sx, sy), 0.20, 0.18, (cx, cy, 0.20),
                             MAT["steel_lt"], C("WORK"), verts=10))
            parts.append(box("VD_A%d%d" % (sx, sy), (0.95, 0.14, 0.10),
                             (cx * 0.5, cy, 0.02), MAT["titanium"],
                             C("WORK")))
    parts.append(cyl("VD_ARM", 0.06, 0.9, (0.85, 0, -0.45), MAT["steel_lt"],
                     C("WORK"), rot=(0, 0.5, 0), verts=6))
    parts.append(box("VD_TOOL", (0.30, 0.26, 0.26), (1.15, 0, -0.85),
                     MAT["paint_safe"], C("WORK")))
    parts.append(sphere("VD_WARN", 0.10, (0, 0, 0.30), MAT["emit_amber"],
                        C("WORK"), seg=8, rings=5))
    return _v_m("VSL_DRONE", parts)


# ---------------------------------------------------------------- fleet
def build_fleet():
    for fn in (vessel_passenger, vessel_research, vessel_cargo, vessel_pod,
               vessel_tourist, vessel_drone):
        fn()

    quay = seabed_h(-7.0, -34.0) + 1.10

    def put(name, x, y, z, rot, s=1.0, tilt=(0.0, 0.0)):
        place(name, x, y, rot=rot, s=s, coll="HARBOR", z=z, tilt=tilt,
              tag="vessel")

    # harbour berths
    put("VSL_PASSENGER", -12.0, -38.5, quay + 2.2, 0.35)
    put("VSL_CARGO", -2.0, -41.0, quay + 1.6, 3.02)
    put("VSL_RESEARCH", 9.5, -36.0, quay + 3.0, 2.55)
    put("VSL_POD", 12.5, -29.0, seabed_h(12.5, -29.0) + 3.4, 1.15)
    # tourist run over the resort
    put("VSL_TOURIST", 13.0, 30.0, seabed_h(13.0, 30.0) + 12.0, 4.10,
        tilt=(0.05, 0.04))
    # maintenance drones at the industrial intake
    put("VSL_DRONE", 24.0, -28.5, seabed_h(24.0, -28.5) + 5.5, 0.80)
    put("VSL_DRONE", 31.0, -25.0, seabed_h(31.0, -25.0) + 6.4, 2.20)
    # a second shuttle on the plaza approach
    put("VSL_PASSENGER", 6.0, -34.0, quay + 2.6, 0.12, s=0.86)

    print("FLEET %d masters, 8 placed" % len(VESSELS))
