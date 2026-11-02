"""
TROPICAL ISLAND CIVILIZATION - THE LIVING PARADISE
build_island.py : entry point.

Run inside Blender (Scripting workspace or MCP execute_blender_code):

    exec(compile(open(r"D:\\Tes Animasi-Motion-Blender\\Tropical Island Civilization\\build_island.py",
                      encoding="utf-8").read(), "build_island.py", "exec"))

Everything is procedural: no external assets, no textures, no simulations,
no armatures and no keyframes.  Re-running rebuilds the island from scratch.
"""

import os
import time

BASE_DIR = r"D:\Tes Animasi-Motion-Blender\Tropical Island Civilization"
FINAL_PNG = os.path.join(BASE_DIR, "TROPICAL_ISLAND_FINAL.png")
BLEND = os.path.join(BASE_DIR, "TROPICAL_ISLAND_CIVILIZATION.blend")
RES = 1920
SAMPLES = 64
RENDER = True

MODULES = ("island_core", "island_nature", "island_arch", "island_people",
           "island_animals", "island_vehicles", "island_boats", "island_layout",
           "island_look")

NS = {"__name__": "island_build", "__file__": os.path.join(BASE_DIR, "build_island.py")}
for _m in MODULES:
    _p = os.path.join(BASE_DIR, _m + ".py")
    exec(compile(open(_p, "r", encoding="utf-8").read(), _p, "exec"), NS)

bpy = NS["bpy"]


def verify():
    """Programmatic QA. Fails loudly rather than reporting unverified success."""
    sc = bpy.context.scene
    objs = list(bpy.data.objects)
    report = {}
    report["objects"] = len(objs)
    report["meshes"] = len([o for o in objs if o.type == "MESH"])
    report["lights"] = len([o for o in objs if o.type == "LIGHT"])
    report["cameras"] = len([o for o in objs if o.type == "CAMERA"])
    report["collections"] = len([c for c in bpy.data.collections])
    report["actions"] = len(bpy.data.actions)
    report["armatures"] = len([o for o in objs if o.type == "ARMATURE"])
    report["animated"] = len([o for o in objs if o.animation_data is not None])
    report["sim_modifiers"] = len([o for o in objs for m in o.modifiers
                                   if m.type in ("FLUID", "CLOTH", "SOFT_BODY",
                                                 "PARTICLE_SYSTEM", "DYNAMIC_PAINT")])
    tris = 0
    for o in objs:
        if o.type == "MESH":
            o.data.calc_loop_triangles()
            tris += len(o.data.loop_triangles)
    report["tris"] = tris
    counts = {}
    idx = {"RESIDENTIAL": "03", "COMMERCIAL": "04", "RESORT": "05", "HARBOR": "06",
           "PUBLIC_FACILITIES": "07", "HUMAN_CHARACTERS": "08", "ANIMALS": "09",
           "VEGETATION": "10", "AGRICULTURE": "11", "VEHICLES": "12",
           "ENVIRONMENTAL_PROPS": "13", "LIGHTING": "14", "TERRAIN": "01",
           "OCEAN": "02"}
    for key, num in idx.items():
        c = bpy.data.collections.get(num + "_" + key)
        counts[key] = len(c.objects) if c else 0
    report["districts"] = counts
    print("QA " + " ".join("%s=%s" % (k, v) for k, v in report.items() if k != "districts"))
    print("QA districts " + " ".join("%s:%d" % kv for kv in counts.items()))
    assert report["actions"] == 0, "animation actions present"
    assert report["armatures"] == 0, "armatures present"
    assert report["animated"] == 0, "animated objects present"
    assert report["sim_modifiers"] == 0, "simulation modifiers present"
    assert report["cameras"] == 2, "expected 2 cameras"
    assert sc.camera is not None, "no active camera"
    return report


def floating_check(limit=12):
    """Every placed instance must sit on the terrain surface."""
    bad = []
    for o in bpy.data.objects:
        tag = o.get("ti_tag")
        if tag != "grounded":
            continue
        x, y = o.location.x, o.location.y
        z = NS["terrain_h"](x, y)
        if abs(o.location.z - z) > 0.6:
            bad.append((o.name, round(o.location.z - z, 2)))
    print("QA floating offenders:", bad[:limit], "total", len(bad))
    return bad


def main(preview=False):
    t0 = time.time()
    NS["bootstrap"]()
    NS["build_island_layout"]()
    cam = NS["build_look"]()
    sc = bpy.context.scene
    sc.render.resolution_x = RES
    sc.render.resolution_y = RES
    sc.eevee.taa_render_samples = SAMPLES
    verify()
    print("BUILD+LOOK %.1fs" % (time.time() - t0))
    if RENDER:
        NS["render_to"](cam, FINAL_PNG, RES, SAMPLES if not preview else 32)
        print("RENDER", FINAL_PNG, os.path.getsize(FINAL_PNG))
    sc.camera = cam
    sc.render.filepath = FINAL_PNG
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("SAVED", BLEND, os.path.getsize(BLEND))
    print("TOTAL %.1fs" % (time.time() - t0))
    return cam


if __name__ == "island_build":
    main(preview=False)
