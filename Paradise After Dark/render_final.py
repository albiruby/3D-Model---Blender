"""Final still previews: Cycles hero + EEVEE comparison, 1920x1080."""
import bpy
import os
import time

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
sc = bpy.context.scene
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"
sc.render.image_settings.compression = 15

# EEVEE first (fast, checks the authored engine)
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 64
sc.render.filepath = os.path.join(BASE, "render_preview_eevee.png")
bpy.ops.render.render(write_still=True)
print("EEVEE PREVIEW DONE")

# Cycles hero
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 96
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 8
sc.cycles.diffuse_bounces = 3
sc.cycles.glossy_bounces = 4
sc.cycles.transmission_bounces = 8
sc.cycles.transparent_max_bounces = 8
sc.render.filepath = os.path.join(BASE, "render_preview.png")
bpy.ops.render.render(write_still=True)
print("CYCLES PREVIEW DONE")
