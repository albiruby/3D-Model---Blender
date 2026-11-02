"""
NEON_RITUAL_RENDER.py - render frames and encode the final MP4.

Usage inside Blender:
    exec(open(r"...\\NEON_RITUAL_RENDER.py").read())
    render_all()          # configure + 450 frames
    encode_final()        # VSE encode with audio
"""

import bpy
import os
import sys

BASE = r"D:\Tes Animasi-Motion-Blender\NEON_RITUAL"
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import nr_render


def configure():
    return nr_render.configure_final()


def render_all(start=1, end=450):
    nr_render.configure_final()
    nr_render.render_range(start, end)


def encode_final():
    nr_render.encode_with_ffmpeg()
    nr_render.verify_video(nr_render.FINAL)


if __name__ == "__main__":
    render_all()
