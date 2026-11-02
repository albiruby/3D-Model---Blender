"""
NEON_RITUAL_BUILD.py - main scene generation entry point.

Usage inside Blender:
    exec(open(r"...\\NEON_RITUAL_BUILD.py").read())
    build()
"""

import bpy
import os
import sys

BASE = r"D:\Tes Animasi-Motion-Blender\NEON_RITUAL"
SCRIPTS = os.path.join(BASE, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import nr_build


def build():
    return nr_build.build(save=True)


def stats():
    nr_build.stats()


if __name__ == "__main__":
    build()
