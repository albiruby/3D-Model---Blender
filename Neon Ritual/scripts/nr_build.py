"""
NEON_RITUAL - orchestrator.  Call build() from the entry point.
"""

import bpy
import sys
import os

BASE = r"D:\Tes Animasi-Motion-Blender\Neon Ritual"
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def _fresh_import():
    for name in list(sys.modules):
        if name.startswith("nr_"):
            del sys.modules[name]
    import nr_core
    import nr_world
    import nr_hero
    import nr_look
    import nr_anim
    return nr_core, nr_world, nr_hero, nr_look, nr_anim


def build(save=True):
    C, W, H, L, A = _fresh_import()
    C.clear_scene()
    C.setup_scene()
    C.make_collections()
    C.make_materials()

    W.build_world()
    H.build_sculpture()
    H.build_typography()
    H.build_event_info()
    L.build_lights()
    L.build_cameras()
    L.setup_compositor()
    A.animate_all()

    sc = bpy.context.scene
    sc.frame_set(1)
    sc.camera = bpy.data.objects.get("CAM_01_CORRIDOR")
    if save:
        C.save_blend(os.path.join(BASE, "NEON_RITUAL.blend"))

    tris = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            tris += len(ob.data.loop_triangles)
    print("BUILD objs=%d tris=%d mats=%d colls=%d actions=%d markers=%d"
          % (len(bpy.data.objects), tris, len(bpy.data.materials),
             len(bpy.data.collections), len(bpy.data.actions),
             len(sc.timeline_markers)))
    return sc


def stats():
    sc = bpy.context.scene
    tris = 0
    for ob in bpy.data.objects:
        if ob.type == "MESH":
            ob.data.calc_loop_triangles()
            tris += len(ob.data.loop_triangles)
    print("STATS objs=%d tris=%d cams=%d lights=%d actions=%d frames=%d-%d"
          % (len(bpy.data.objects), tris,
             len([o for o in bpy.data.objects if o.type == "CAMERA"]),
             len([o for o in bpy.data.objects if o.type == "LIGHT"]),
             len(bpy.data.actions), sc.frame_start, sc.frame_end))
    print("COLLS", sorted(c.name for c in bpy.data.collections))
    print("MATS", sorted(m.name for m in bpy.data.materials))
