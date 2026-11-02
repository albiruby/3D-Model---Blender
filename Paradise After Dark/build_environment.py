"""
PARADISE AFTER DARK — build_environment.py
Reproducible environment construction for the Tropical Futuristic Festival
Courtyard. Run headless:

  blender.exe -b --python build_environment.py

The scene is intentionally compact: 24 x 18 m, pavilion 16 x 8 x 9 m.
"""

import bpy
import os
import sys
import time

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import tf_core as C
import tf_arch as A
import tf_look as L


def build(with_plants=False, render=True, quick=True):
    t0 = time.time()
    C.reset_scene()
    C.setup_scene()
    C.make_collections()
    C.make_materials()
    A.build_all()
    if with_plants:
        try:
            import tf_nature as N
            N.build_all()
        except Exception as e:
            print("NATURE WARN", e)
    L.build_look()
    C.save_blend(os.path.join(BASE, "tropical_festival_courtyard.blend"))
    if render:
        cam = bpy.data.objects["CAM_MAIN"]
        if quick:
            C.render_to(os.path.join(BASE, "renders", "blockout.png"),
                        cam, (960, 540), 32, 1)
        else:
            C.render_to(os.path.join(BASE, "render_preview.png"),
                        cam, (1920, 1080), 64, 1)
    print("BUILD DONE %.1fs objects=%d" % (time.time() - t0,
                                           len(bpy.data.objects)))


if __name__ == "__main__":
    build(with_plants=True, render=True, quick=True)
