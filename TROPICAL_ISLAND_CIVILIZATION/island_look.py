"""
island_look.py : sun, sky, atmosphere, hero camera with numeric framing.
"""

import bpy
import math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def build_sun():
    coll = C("LIGHTING")
    for ob in list(coll.objects):
        if ob.type == "LIGHT":
            bpy.data.objects.remove(ob, do_unlink=True)
    li = bpy.data.lights.new("SUN_TROPICAL", "SUN")
    li.energy = 4.6
    li.angle = math.radians(1.4)
    li.color = (1.0, 0.925, 0.815)
    sun = bpy.data.objects.new("SUN_TROPICAL", li)
    coll.objects.link(sun)
    d = Vector((-0.58, -0.36, -0.72)).normalized()
    sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    # soft fill from the ocean side so shaded facades still read
    li2 = bpy.data.lights.new("FILL_SKY", "AREA")
    li2.energy = 4200
    li2.size = 42
    li2.color = (0.55, 0.72, 0.95)
    fill = bpy.data.objects.new("FILL_SKY", li2)
    coll.objects.link(fill)
    fill.location = (58, -66, 46)
    d2 = Vector((0, 0, 5)) - Vector(fill.location)
    fill.rotation_euler = d2.to_track_quat("-Z", "Y").to_euler()
    # warm bounce from the sand
    li3 = bpy.data.lights.new("BOUNCE_WARM", "AREA")
    li3.energy = 2600
    li3.size = 30
    li3.color = (1.0, 0.80, 0.60)
    b = bpy.data.objects.new("BOUNCE_WARM", li3)
    coll.objects.link(b)
    b.location = (-26, -30, 12)
    b.rotation_euler = (Vector((0, 0, 6)) - Vector(b.location)).to_track_quat("-Z", "Y").to_euler()
    return sun


def tune_world():
    w = bpy.context.scene.world
    nt = w.node_tree
    ramp = None
    for n in nt.nodes:
        if n.type == "VALTORGB":
            ramp = n
    if ramp:
        el = ramp.color_ramp.elements
        el[0].color = (*hexcol("#E6F4F6"), 1.0)
        el[1].color = (*hexcol("#2E7CC2"), 1.0)
        if len(el) > 2:
            el[1].color = (*hexcol("#88C6E6"), 1.0)
            el[2].color = (*hexcol("#2E7CC2"), 1.0)
    for n in nt.nodes:
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value = 0.55 if n.inputs["Strength"].default_value < 1.0 else 1.0


def island_bounds():
    pts = []
    for x in (-37.0, -26.0, -12.0, 0.0, 12.0, 24.0, 34.0):
        for y in (-27.0, -14.0, 0.0, 14.0, 25.0):
            if is_land(x, y):
                z = terrain_h(x, y)
                pts.append(Vector((x, y, z)))
    pts.append(Vector((0, 0, 14)))
    return pts


def fit_camera(cam, target_frac=0.80, iters=6):
    sc = bpy.context.scene
    pts = island_bounds()
    for _ in range(iters):
        bpy.context.view_layer.update()
        xs = []
        for p in pts:
            co = world_to_camera_view(sc, cam, p)
            xs.append(co.x)
        frac = max(xs) - min(xs)
        if frac < 1e-4:
            break
        k = frac / target_frac
        d = Vector(cam.location) - Vector((0, 0, 5.0))
        d = d * (0.4 + 0.6 * k)
        cam.location = Vector((0, 0, 5.0)) + d
        bpy.context.view_layer.update()
    return cam


def build_hero_camera():
    cam = bpy.data.objects.get("CAMERA_ISLAND_HERO")
    if cam:
        bpy.data.objects.remove(cam, do_unlink=True)
    cam = make_camera("CAMERA_ISLAND_HERO", (46, -70, 56), (0, 0, 5.0), 50)
    fit_camera(cam, 0.80)
    bpy.context.scene.camera = cam
    # secondary inspection camera over the town
    cam2 = bpy.data.objects.get("CAMERA_TOWN_CLOSE")
    if cam2:
        bpy.data.objects.remove(cam2, do_unlink=True)
    make_camera("CAMERA_TOWN_CLOSE", (6, -26, 16), (-4, 4, 8), 40)
    return cam


def build_look():
    build_sun()
    tune_world()
    cam = build_hero_camera()
    sc = bpy.context.scene
    sc.view_settings.exposure = 0.0
    sc.eevee.taa_render_samples = 64
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1920
    return cam
