"""Verify the encoded MP4 and extract three check frames."""
import bpy
import os

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
SRC = os.path.join(BASE, "PARADISE_AFTER_DARK_15s.mp4")
OUT = os.path.join(BASE, "renders")

clip = bpy.data.movieclips.load(SRC)
print("CLIP", clip.name, "frames", clip.frame_duration,
      "size", tuple(clip.size), "fps", clip.fps)

sc = bpy.context.scene
sc.sequence_editor_create()
for s in list(sc.sequence_editor.strips_all):
    sc.sequence_editor.strips.remove(s)
seq = sc.sequence_editor.strips.new_movie(
    name="VIDEO", filepath=SRC, channel=1, frame_start=1)
seq.transform.scale_x = 0.5
seq.transform.scale_y = 0.5
print("STRIP", seq.frame_final_start, seq.frame_final_end,
      seq.frame_final_duration, "elements", len(seq.elements))

sc.render.resolution_x = 960
sc.render.resolution_y = 540
sc.render.resolution_percentage = 100
sc.render.use_sequencer = True
sc.render.use_compositing = False
sc.render.image_settings.media_type = "IMAGE"
sc.render.image_settings.file_format = "PNG"
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
sc.view_settings.exposure = 0.0
sc.view_settings.gamma = 1.0

for f in (1, 225, 450):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, "video_check_f%03d.png" % f)
    bpy.ops.render.render(write_still=True)
    print("CHECK", f)

# full-resolution poster from the encoded video
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
seq.transform.scale_x = 1.0
seq.transform.scale_y = 1.0
sc.frame_set(225)
sc.render.filepath = os.path.join(BASE, "PARADISE_AFTER_DARK_15s_poster.png")
bpy.ops.render.render(write_still=True)
print("POSTER DONE")
print("VIDEO CHECK DONE")
