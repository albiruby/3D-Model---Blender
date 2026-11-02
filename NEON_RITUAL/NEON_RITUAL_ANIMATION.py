"""
NEON_RITUAL_ANIMATION.py - camera / object / material animation setup.

This is the animation entry point for a freshly built scene.  The delivered
NEON_RITUAL.blend already contains the animation; running this again on that
file will duplicate keyframes.  Intended flow:

    exec(open(r"...\\NEON_RITUAL_BUILD.py").read())
    build()
    exec(open(r"...\\NEON_RITUAL_ANIMATION.py").read())
    apply()
"""

import bpy
import os
import sys

BASE = r"D:\Tes Animasi-Motion-Blender\NEON_RITUAL"
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import nr_anim


def apply():
    nr_anim.animate_all()
    print("ANIMATION APPLIED")


if __name__ == "__main__":
    apply()
