"""Render the 15 s animation to H.264.

Usage:
  blender -b tropical_festival_courtyard_15s.blend --python render_animation.py
  blender -b tropical_festival_courtyard_15s.blend --python render_animation.py -- --test
"""
import bpy
import os
import sys
import time

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
TEST = "--test" in sys.argv

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.resolution_percentage = 100
sc.eevee.taa_render_samples = 16
sc.frame_start = 1
sc.frame_end = 10 if TEST else 450

# The planar probe is beautiful for stills but re-bakes every frame and
# multiplies animation render time by roughly ten. Screen-space raytracing
# still gives the lagoon its reflection.
for o in bpy.data.objects:
    if o.type == "LIGHT_PROBE":
        o.hide_render = True
# Sun shadows only; the area fills do not need shadow maps.
for l in bpy.data.lights:
    if l.name != "SUN_KEY":
        l.use_shadow = False
sc.eevee.ray_tracing_options.resolution_scale = "2"
sc.eevee.ray_tracing_options.trace_max_roughness = 0.35
sc.render.use_compositing = True
sc.render.use_motion_blur = False

sc.render.image_settings.media_type = "VIDEO"
sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.constant_rate_factor = "HIGH"
sc.render.ffmpeg.ffmpeg_preset = "GOOD"
sc.render.ffmpeg.gopsize = 15
sc.render.ffmpeg.audio_codec = "NONE"

name = "anim_test_10f" if TEST else "PARADISE_AFTER_DARK_15s"
sc.render.filepath = os.path.join(BASE, name)

t0 = time.time()
bpy.ops.render.render(animation=True)
print("ANIM RENDER DONE %.1f s -> %s" % (time.time() - t0, sc.render.filepath))
