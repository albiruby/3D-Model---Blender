"""
NEON_RITUAL - final render and VSE encode helpers.
"""

import bpy
import os
import glob
import subprocess

BASE = r"D:\Tes Animasi-Motion-Blender\NEON_RITUAL"
FRAMES = os.path.join(BASE, "frames")
AUDIO = os.path.join(BASE, "audio", "NEON_RITUAL_AUDIO.wav")
FINAL = os.path.join(BASE, "NEON_RITUAL_FINAL.mp4")
FFMPEG = r"D:\Tes Animasi-Motion-Blender\karhutla animation\node_modules\ffmpeg-static\ffmpeg.exe"


def configure_final(samples=24):
    sc = bpy.context.scene
    sc.name = "NEON_RITUAL"
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    sc.frame_start = 1
    sc.frame_end = 450
    sc.eevee.taa_render_samples = samples
    sc.render.image_settings.media_type = "IMAGE"
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.render.image_settings.compression = 15
    sc.render.filepath = FRAMES + os.sep
    sc.render.use_file_extension = True
    sc.render.film_transparent = False
    sc.render.use_sequencer = False
    sc.render.use_compositing = True
    sc.camera = bpy.data.objects.get("CAM_01_CORRIDOR")
    sc.frame_set(1)
    os.makedirs(FRAMES, exist_ok=True)
    return sc


def render_range(start, end):
    sc = bpy.context.scene
    sc.frame_start = start
    sc.frame_end = end
    sc.render.filepath = FRAMES + os.sep
    bpy.ops.render.render(animation=True)
    print("RENDERED", start, end)


def frame_paths(start=1, end=450):
    out = []
    for f in range(start, end + 1):
        p = os.path.join(FRAMES, "%04d.png" % f)
        if os.path.exists(p):
            out.append(p)
    return out


def build_encode_scene(name="NEON_RITUAL_ENCODE", start=1, end=450,
                       audio=AUDIO, out=FINAL):
    paths = frame_paths(start, end)
    if len(paths) != (end - start + 1):
        raise RuntimeError("missing frames: %d / %d" % (len(paths), end - start + 1))
    sc = bpy.data.scenes.new(name)
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = 100
    sc.render.fps = 30
    sc.render.fps_base = 1.0
    sc.frame_start = start
    sc.frame_end = end
    sc.view_settings.view_transform = "Standard"
    try:
        sc.view_settings.look = "None"
    except Exception:
        pass
    sc.view_settings.exposure = 0.0
    sc.view_settings.gamma = 1.0
    sc.use_nodes = False
    sc.render.use_sequencer = True
    sc.render.use_compositing = False
    se = sc.sequence_editor_create()
    strip = se.strips.new_image("FRAMES", paths[0], 1, start)
    for p in paths[1:]:
        strip.elements.append(p)
    strip.frame_final_start = start
    strip.frame_final_duration = end - start + 1
    snd = se.strips.new_sound("AUDIO", audio, 2, start)
    snd.frame_final_start = start
    # keep the sound at its natural 15 s duration
    sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.ffmpeg.ffmpeg_preset = "GOOD"
    sc.render.ffmpeg.audio_codec = "AAC"
    sc.render.ffmpeg.audio_bitrate = 192
    sc.render.ffmpeg.audio_mixrate = 48000
    try:
        sc.render.ffmpeg.audio_channels = "STEREO"
    except Exception:
        pass
    sc.render.filepath = out
    sc.render.use_file_extension = False
    print("ENCODE SCENE", name, "images", len(paths), "audio", os.path.basename(audio))
    return sc


def encode_video(enc):
    orig = bpy.context.window.scene
    bpy.context.window.scene = enc
    try:
        bpy.ops.render.render(animation=True)
    finally:
        bpy.context.window.scene = orig
    print("ENCODED", enc.render.filepath)


def encode_with_ffmpeg(out=FINAL, audio=AUDIO, crf=18):
    """Robust H.264/AAC encode from the PNG sequence.

    The Blender 5.2 VSE image-strip path crashed on a 450-element strip in
    this environment, so the delivered MP4 is encoded with the ffmpeg-static
    binary already present on the machine.
    """
    paths = frame_paths(1, 450)
    if len(paths) != 450:
        raise RuntimeError("missing frames: %d / 450" % len(paths))
    if not os.path.exists(FFMPEG):
        raise FileNotFoundError(FFMPEG)
    cmd = [
        FFMPEG, "-y",
        "-framerate", "30", "-start_number", "1",
        "-i", os.path.join(FRAMES, "%04d.png"),
        "-i", audio,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(crf), "-preset", "medium",
        "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart",
        out,
    ]
    print("FFMPEG", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("ENCODED", out, os.path.getsize(out))
    return out


def verify_video(path):
    print("VERIFY FILE", path, os.path.getsize(path) if os.path.exists(path) else "MISSING")
    if not os.path.exists(path):
        return
    with open(path, "rb") as fh:
        head = fh.read(2_000_000)
    print("MP4 avc1", b"avc1" in head, "mp4a", b"mp4a" in head)
    try:
        clip = bpy.data.movieclips.load(path)
        print("CLIP", clip.size[:], "frames", clip.frame_duration,
              "fps", clip.fps, "duration", clip.frame_duration / max(clip.fps, 1))
    except Exception as e:
        print("CLIP ERR", e)


if __name__ == "__main__":
    configure_final()
    render_range(1, 450)
