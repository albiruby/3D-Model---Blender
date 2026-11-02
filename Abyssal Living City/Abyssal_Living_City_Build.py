"""
PROJECT 10 - THE ABYSSAL LIVING CITY
Abyssal_Living_City_Build.py : single entry point.

Loads the procedural modules into one shared namespace, builds the world, then
renders the review set.  Every stage is idempotent: rerunning rebuilds the scene
from nothing rather than accumulating duplicates.

Usage inside Blender:
    exec(open(r"...\\Abyssal_Living_City_Build.py").read())
    main(mode="m1")
"""

import bpy
import os
import time
import traceback

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _HERE = r"D:\Tes Animasi-Motion-Blender\Abyssal Living City"
if not os.path.isdir(os.path.join(_HERE, "scripts")):
    _HERE = r"D:\Tes Animasi-Motion-Blender\Abyssal Living City"

BASE_DIR = _HERE
SCRIPTS = os.path.join(BASE_DIR, "scripts")
RENDERS = os.path.join(BASE_DIR, "renders")

MODULES = [
    "abyss_core",
    "abyss_kit",
    "abyss_arch",
    "abyss_seabed",
    "abyss_water",
    "abyss_domes",
    "abyss_layout",
    "abyss_look",
    "abyss_vessels",
    "abyss_eco",
    "abyss_fauna",
    "abyss_people",
    "abyss_detail",
]

NS = {"__name__": "abyss", "BASE_DIR": BASE_DIR, "SCRIPTS": SCRIPTS}


def load_modules():
    for m in MODULES:
        p = os.path.join(SCRIPTS, m + ".py")
        with open(p, "r", encoding="utf-8") as fh:
            src = fh.read()
        exec(compile(src, p, "exec"), NS)
    print("MODULES LOADED %d" % len(MODULES))


def build_world():
    NS["bootstrap"]()
    NS["build_world_layout"]()
    NS["build_fleet"]()
    NS["build_ecosystem"]()
    NS["build_fauna"]()
    NS["build_population"]()
    NS["build_foreground_shelf"]()
    NS["build_detailing"]()
    NS["build_water"]()
    cam = NS["build_look"]()
    return cam


def _out(name):
    os.makedirs(RENDERS, exist_ok=True)
    return os.path.join(RENDERS, name)


def review_m1():
    """Clay first (silhouette + composition), then the lit look."""
    cam = build_world()
    NS["render_clay"](_out("M1_clay.png"), 900, 24, cam)
    NS["render_hero"](_out("M1_hero_1280.png"), 1280, 40)
    NS["qa_report"]()
    NS["save_checkpoint"]("M1_blockout")
    return cam


def review_atmosphere():
    """A/B the two depth cues at a cheap resolution before committing."""
    cam = bpy.data.objects.get("CAMERA_ABYSSAL_HERO")
    if cam is None:
        cam = build_world()
    for mode in ("fog", "volume", "both"):
        NS["set_atmosphere"](mode)
        NS["render_to"](cam, _out("M1_water_%s.png" % mode), 760, 24)
        print("WATER TEST", mode, "done")


def _asset_centre(name):
    """World-space centre of a master-backed instance.

    Master geometry is baked at world coordinates with the object at the origin,
    so ob.location is useless for framing.  The bound box is the truth.
    """
    ob = bpy.data.objects.get(name)
    if ob is None:
        return None
    from mathutils import Vector
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
    hi = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
    return (lo + hi) * 0.5, (hi - lo)


def bench_assets(kind="arch"):
    """Asset Quality Gate: build one master, render it, inspect, then duplicate."""
    NS["bootstrap"]()
    NS["define_pads"]()
    NS["build_seabed"]()
    NS["build_lights"]()
    sc = bpy.context.scene
    sc.render.film_transparent = False

    made = []
    if kind == "arch":
        NS["apartment"]("BENCH_APT", -14.0, 0.0, 9.0, 7.0, 4,
                        coll="RESIDENTIAL", seed=1)
        NS["shophouse"]("BENCH_SHOP", 0.0, 0.0, 7.0, 6.0, 3,
                        coll="COMMERCIAL", shop=(3, "COFFEE", "#F0975A"))
        NS["office_tower"]("BENCH_TOWER", 14.0, 0.0, 6.0, 22.0, 8,
                           coll="COMMERCIAL")
        NS["lab_block"]("BENCH_LAB", 28.0, 0.0, 10.0, 7.0, 3, coll="RESEARCH")
        made = ["BENCH_APT", "BENCH_SHOP", "BENCH_TOWER", "BENCH_LAB"]
    elif kind == "civic":
        NS["civic_block"]("BENCH_HOSP", -18.0, 0.0, 18.0, 10.0, 3,
                          coll="PUBLIC", accent=MAT["emit_teal"])
        NS["hotel_stack"]("BENCH_HOTEL", 6.0, 0.0, 16.0, 10.0, 6, coll="RESORT")
        NS["industrial_hall"]("BENCH_IND", 30.0, 0.0, 16.0, 10.0, 7.0,
                              coll="INDUSTRIAL")
        made = ["BENCH_HOSP", "BENCH_HOTEL", "BENCH_IND"]
    else:
        NS["pod_house"]("BENCH_POD", 0.0, 0.0, 3.2, coll="RESIDENTIAL")
        made = ["BENCH_POD"]

    for i, nm in enumerate(made):
        c = _asset_centre(nm)
        if c is None:
            continue
        cen, size = c
        ext = max(size.x, size.y, size.z) * 1.55 + 2.0
        cam = NS["make_camera"](
            "BENCHCAM_%d" % i,
            (cen.x + ext * 0.68, cen.y - ext * 0.78, cen.z + ext * 0.42),
            (cen.x, cen.y, cen.z), lens=62.0)
        NS["render_to"](cam, os.path.join(RENDERS, "M2_bench_%s.png" % nm.lower()),
                        820, 32)
        print("BENCH", nm, "ext=%.1f" % ext, "ok")

    # one wide lineup: the fastest way to judge a family together
    xs = [(_asset_centre(n)[0].x, n) for n in made if _asset_centre(n)]
    if xs:
        mid = sum(x for x, _ in xs) / len(xs)
        span = max(x for x, _ in xs) - min(x for x, _ in xs)
        NS["make_camera"]("BENCH_LINEUP",
                          (mid + span * 0.55, -span * 0.95 - 18.0, 34.0),
                          (mid, 0.0, 8.0), lens=48.0)
        NS["render_to"](bpy.data.objects["BENCH_LINEUP"],
                        os.path.join(RENDERS, "M2_bench_LINEUP_%s.png" % kind),
                        1500, 40)
        print("LINEUP", kind, "ok span=%.1f" % span)
    return made


def bench_render_asset(name, out, lens=62.0, scale=1.55):
    c = _asset_centre(name)
    if c is None:
        print("bench asset missing", name)
        return None
    cen, size = c
    ext = max(size.x, size.y, size.z) * scale + 2.0
    cam = NS["make_camera"](
        "BENCHCAM_" + name,
        (cen.x + ext * 0.68, cen.y - ext * 0.78, cen.z + ext * 0.42),
        (cen.x, cen.y, cen.z), lens=lens)
    return NS["render_to"](cam, os.path.join(RENDERS, out), 820, 32)


def main(mode="m1"):
    t0 = time.time()
    try:
        load_modules()
        if mode == "m1":
            review_m1()
        elif mode == "water":
            load_modules()
            review_m1()
            review_atmosphere()
        elif mode == "build":
            build_world()
            NS["save_checkpoint"]("M1_blockout")
        elif mode == "bench":
            bench_assets("arch")
        elif mode == "bench2":
            bench_assets("civic")
        else:
            print("unknown mode", mode)
    except BaseException:
        print("FATAL")
        print(traceback.format_exc()[-3500:])
    print("ELAPSED %.1fs" % (time.time() - t0))


if __name__ == "__main__":
    main("m1")
