"""
island_orbit.py : camera-only orbit for the review video.

Every object stays static - the camera is the only thing keyframed, so the
"all world objects are static" rule still holds.
"""

import bpy
import math
from mathutils import Vector


def setup_orbit(frames=240, elev_start=38.0, elev_end=26.0, target=(0.0, 0.0, 5.0),
                start_deg=-56.0, turns=1.0):
    cam = bpy.data.objects.get("CAMERA_ISLAND_HERO")
    if cam is None:
        cam = bpy.data.objects["CAMERA_ISLAND_HERO"]
    for c in list(cam.constraints):
        cam.constraints.remove(c)
    tgt = bpy.data.objects.get("ORBIT_TARGET")
    if tgt is None:
        tgt = bpy.data.objects.new("ORBIT_TARGET", None)
        C("CAMERAS").objects.link(tgt)
    tgt.location = target
    tgt.empty_display_size = 1.0
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    d0 = Vector(cam.location) - Vector(target)
    radius = d0.length
    for f in range(1, frames + 1):
        t = (f - 1) / float(frames)
        ang = math.radians(start_deg) + t * math.tau * turns
        el = math.radians(elev_start + (elev_end - elev_start) * t)
        dist = radius * (1.0 + 0.035 * math.sin(t * math.tau))
        loc = Vector(target) + Vector((math.cos(ang) * math.cos(el),
                                       math.sin(ang) * math.cos(el),
                                       math.sin(el))) * dist
        cam.location = loc
        cam.keyframe_insert("location", frame=f)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames
    sc.render.fps = 24
    sc.frame_set(1)
    bpy.context.view_layer.update()
    print("ORBIT frames=%d radius=%.1f" % (frames, radius))
    return cam


def render_orbit(path, res=1280, samples=40, frames=240):
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = frames
    sc.render.fps = 24
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    try:
        sc.render.ffmpeg.constant_rate_factor = "HIGH"
        sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    except Exception:
        pass
    sc.render.filepath = path
    bpy.ops.render.render(animation=True)
    print("ORBIT RENDER", path)
    return path


def clear_orbit(save_path=None):
    """Remove the camera animation and put the scene back to a static still."""
    cam = bpy.data.objects.get("CAMERA_ISLAND_HERO")
    if cam:
        cam.animation_data_clear()
        for c in list(cam.constraints):
            cam.constraints.remove(c)
    tgt = bpy.data.objects.get("ORBIT_TARGET")
    if tgt:
        bpy.data.objects.remove(tgt, do_unlink=True)
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = 1
    sc.frame_set(1)
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1920
    sc.eevee.taa_render_samples = 64
    if save_path:
        bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print("ORBIT cleared, scene back to static")
