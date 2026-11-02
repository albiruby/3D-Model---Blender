"""
PARADISE AFTER DARK — 15 s animation setup.
Adds a slow camera push-in and subtle life to water, LED, neon, lanterns,
palms and the DJ. Saves a separate .blend and renders three key previews.
"""

import bpy
import math
import os
from mathutils import Vector

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
BLEND_OUT = os.path.join(BASE, "tropical_festival_courtyard_15s.blend")
PREVIEW_DIR = os.path.join(BASE, "renders")

sc = bpy.context.scene
sc.frame_start = 1
sc.frame_end = 450
sc.render.fps = 30
sc.render.fps_base = 1.0
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.resolution_percentage = 100
sc.render.use_motion_blur = False


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# Default Blender keyframes are Bezier with auto-clamped handles, which is
# exactly what a slow camera move needs. The 5.2 slotted-action API no longer
# exposes action.fcurves directly, so no manual handle pass is needed.


# ------------------------------------------------------------------ camera
cam = bpy.data.objects["CAM_MAIN"]
cam.data.dof.use_dof = True
cam.data.dof.aperture_fstop = 8.0
cam.data.dof.aperture_blades = 7

cam_keys = [
    (1,   (-5.20, -10.60, 1.50), (0.30, 2.80, 2.90)),
    (150, (-3.00, -10.40, 1.52), (0.25, 2.80, 2.85)),
    (300, (0.20, -10.10, 1.58), (0.20, 2.85, 2.95)),
    (450, (3.20, -9.90, 1.62), (0.10, 2.90, 3.00)),
]
for f, loc, tgt in cam_keys:
    cam.location = loc
    look_at(cam, tgt)
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)

for f, dist in ((1, 15.0), (450, 14.0)):
    cam.data.dof.focus_distance = dist
    cam.data.dof.keyframe_insert("focus_distance", frame=f)

# ------------------------------------------------------------------ water
for mat_name in ("POOL_WATER", "POOL_FLOOR"):
    m = bpy.data.materials.get(mat_name)
    if not m:
        continue
    for i, n in enumerate([n for n in m.node_tree.nodes
                           if n.type == "TEX_NOISE"]):
        n.noise_dimensions = "4D"
        w = n.inputs["W"]
        start = 0.7 * i
        w.default_value = start
        w.keyframe_insert("default_value", frame=1)
        w.default_value = start + 2.2
        w.keyframe_insert("default_value", frame=450)

# ------------------------------------------------------------------ LED
m = bpy.data.materials.get("LED_SCREEN")
if m:
    for n in m.node_tree.nodes:
        if n.type == "TEX_WAVE":
            ph = n.inputs["Phase Offset"]
            ph.default_value = 0.0
            ph.keyframe_insert("default_value", frame=1)
            ph.default_value = 6.0
            ph.keyframe_insert("default_value", frame=450)

# ------------------------------------------------------------------ neon pulse
m = bpy.data.materials.get("SIGN_NEON")
if m:
    b = next((n for n in m.node_tree.nodes
              if n.type == "BSDF_PRINCIPLED"), None)
    if b:
        inp = b.inputs["Emission Strength"]
        for f, val in ((1, 2.2), (112, 3.2), (225, 2.2),
                       (337, 3.2), (450, 2.2)):
            inp.default_value = val
            inp.keyframe_insert("default_value", frame=f)

# ------------------------------------------------------------------ lanterns
for i in range(10):
    ob = bpy.data.objects.get("LANTERN_%02d" % i)
    if not ob:
        continue
    base = ob.location.copy()
    phase = i * 0.73
    for f in range(1, 451, 12):
        t = (f - 1) / 30.0
        ob.location = (base.x + 0.012 * math.sin(t * 0.9 + phase),
                       base.y + 0.009 * math.cos(t * 0.7 + phase),
                       base.z + 0.026 * math.sin(t * 1.7 + phase))
        ob.keyframe_insert("location", frame=f)

# ------------------------------------------------------------------ palms
palms = [o for o in bpy.data.objects
         if o.name.startswith(("BG_PALM", "BED_PALM", "FAN_PALM",
                               "BG_HERO", "STAGE_BAN"))]
for i, ob in enumerate(palms):
    base = ob.rotation_euler.copy()
    phase = i * 0.81
    for f in range(1, 451, 24):
        t = (f - 1) / 30.0
        ob.rotation_euler[0] = base[0] + 0.0035 * math.sin(t * 0.65 + phase * 1.3)
        ob.rotation_euler[1] = base[1] + 0.0060 * math.sin(t * 0.80 + phase)
        ob.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ DJ
dj = bpy.data.objects.get("CROWD_DJ")
if dj:
    base = dj.location.copy()
    for f in range(1, 451, 15):
        t = (f - 1) / 30.0
        dj.location = (base.x, base.y, base.z + 0.012 * math.sin(t * 2.4))
        dj.rotation_euler[2] = 0.035 * math.sin(t * 1.2)
        dj.keyframe_insert("location", frame=f)
        dj.keyframe_insert("rotation_euler", frame=f)

# ------------------------------------------------------------------ save
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print("ANIM BLEND SAVED", BLEND_OUT)

# ------------------------------------------------------------------ key previews
sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.eevee.taa_render_samples = 16
os.makedirs(PREVIEW_DIR, exist_ok=True)
for f in (1, 225, 450):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(PREVIEW_DIR, "anim_preview_f%03d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", f)
print("ANIM SETUP DONE")
