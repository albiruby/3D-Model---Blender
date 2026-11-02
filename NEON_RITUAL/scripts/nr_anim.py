"""
NEON_RITUAL - all object, material, light and camera animation.
450 frames @ 30 fps.  Eight shots, hard cuts at markers.
"""

import bpy
import math

from nr_core import COLL


def _fcurves(id_data):
    ad = id_data.animation_data
    if not ad or not ad.action:
        return []
    a = ad.action
    out = []
    for layer in a.layers:
        for strip in layer.strips:
            for slot in a.slots:
                try:
                    cb = strip.channelbag(slot)
                except Exception:
                    cb = None
                if cb:
                    out.extend(cb.fcurves)
    return out


def _smooth(id_data):
    for fc in _fcurves(id_data):
        for kp in fc.keyframe_points:
            kp.interpolation = "BEZIER"
            kp.handle_left_type = "AUTO_CLAMPED"
            kp.handle_right_type = "AUTO_CLAMPED"


def _key_emission(mat, keys):
    if mat is None or not mat.use_nodes:
        return
    node = None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            node = n
            break
    if node is None:
        return
    inp = node.inputs["Emission Strength"]
    for f, v in keys:
        inp.default_value = v
        inp.keyframe_insert("default_value", frame=f)
    _smooth(mat.node_tree)


def _key_energy(light, keys):
    if light is None:
        return
    for f, v in keys:
        light.data.energy = v
        light.data.keyframe_insert("energy", frame=f)
    _smooth(light.data)


def _key_rot_z(ob, keys):
    if ob is None:
        return
    for f, v in keys:
        ob.rotation_euler[2] = v
        ob.keyframe_insert("rotation_euler", index=2, frame=f)
    _smooth(ob)


def animate_all():
    sc = bpy.context.scene
    sc.frame_start = 1
    sc.frame_end = 450

    # hero sculpture: slow rotation, extra turn on the impact
    body = bpy.data.objects.get("HERO_SCULPTURE")
    _key_rot_z(body, [(1, 0.0), (240, 0.10), (390, 0.16),
                      (411, 0.24), (450, 0.28)])

    # orbital rings: counter-rotating
    for name, amount in (("ORBITAL_RING_00", 0.36),
                         ("ORBITAL_RING_01", -0.22),
                         ("ORBITAL_RING_02", 0.15)):
        _key_rot_z(bpy.data.objects.get(name),
                   [(1, 0.0), (450, amount)])

    # banner sway, phase offset
    for i in range(6):
        ob = bpy.data.objects.get("BANNER_%02d" % i)
        if ob is None:
            continue
        phase = i * 0.9
        keys = []
        for f in (1, 90, 180, 270, 360, 450):
            keys.append((f, 0.018 * math.sin(f * 0.012 + phase)))
        _key_rot_z(ob, keys)

    # floating fragments rig
    rig = bpy.data.objects.get("RIG_FRAGMENTS")
    if rig:
        _key_rot_z(rig, [(1, 0.0), (450, 0.20)])
        for f, z in ((1, 0.0), (240, 0.10), (450, 0.22)):
            rig.location[2] = 14.4 + z
            rig.keyframe_insert("location", index=2, frame=f)
        _smooth(rig)

    # dust drift
    dust = bpy.data.objects.get("DUST_FIELD")
    if dust:
        _key_rot_z(dust, [(1, 0.0), (450, 0.018)])

    # title lighting / reveal
    back = bpy.data.objects.get("LIGHT_TITLE_BACK")
    _key_energy(back, [(1, 0), (180, 0), (225, 700), (240, 500),
                       (260, 800), (280, 600), (300, 700), (450, 600)])
    key = bpy.data.objects.get("LIGHT_TITLE_KEY")
    _key_energy(key, [(1, 0), (180, 0), (195, 450), (210, 450),
                      (300, 450), (450, 350)])
    sweep = bpy.data.objects.get("LIGHT_TITLE_SWEEP")
    if sweep:
        _key_energy(sweep, [(1, 0), (195, 0), (205, 350), (235, 350),
                            (240, 0), (450, 0)])
        for f, x in ((195, -5.5), (205, -4.0), (235, 5.0), (240, 5.5)):
            sweep.location[0] = x
            sweep.keyframe_insert("location", index=0, frame=f)
        _smooth(sweep)

    # global red pulse + key spot
    _key_energy(bpy.data.objects.get("LIGHT_KEY_OVERHEAD"),
                [(1, 3200), (390, 3200), (405, 4500), (450, 3800)])
    _key_emission(bpy.data.materials.get("RED_EMISSIVE"),
                  [(1, 10), (390, 10), (405, 18), (430, 12), (450, 10)])
    _key_emission(bpy.data.materials.get("RED_HOT"),
                  [(1, 18), (390, 18), (405, 24), (450, 20)])
    # LED screens go dark for the event-info shot
    _key_emission(bpy.data.materials.get("LED_RED"),
                  [(1, 0.25), (300, 0.25), (301, 0.10), (360, 0.10), (361, 0.25)])

    # title / info text emitters
    _key_emission(bpy.data.materials.get("HALO_WHITE"),
                  [(1, 0), (180, 0), (200, 2.5), (450, 2.5)])
    _key_emission(bpy.data.materials.get("HALO_RED"),
                  [(1, 0), (180, 0), (200, 8.0), (405, 12.0), (450, 8.0)])
    _key_energy(bpy.data.objects.get("LIGHT_TITLE_SOFT"),
                [(1, 0), (180, 0), (200, 900), (450, 900)])
    _key_energy(bpy.data.objects.get("LIGHT_TITLE_RIM"),
                [(1, 0), (180, 0), (200, 120), (450, 120)])
    _key_energy(bpy.data.objects.get("LIGHT_TITLE_KEY_R"),
                [(1, 0), (180, 0), (200, 300), (450, 300)])
    _key_energy(bpy.data.objects.get("LIGHT_TITLE_LOW"),
                [(1, 0), (180, 0), (200, 300), (450, 300)])
    _key_energy(bpy.data.objects.get("LIGHT_TITLE_ONAXIS"),
                [(1, 0), (180, 0), (200, 900), (450, 900)])
    _key_emission(bpy.data.materials.get("SECONDARY_EMIT"),
                  [(1, 0), (190, 0), (200, 3.0), (450, 3.0)])
    _key_emission(bpy.data.materials.get("INFO_EMIT"),
                  [(300, 0), (301, 0), (302, 6), (303, 1), (305, 4),
                   (320, 3), (360, 3), (361, 0), (450, 0)])
    _key_emission(bpy.data.materials.get("INFO_FRAME"),
                  [(300, 0), (301, 0), (305, 2.0), (360, 2.0),
                   (361, 0.0), (450, 0.0)])
    _key_emission(bpy.data.materials.get("TAG_EMIT"),
                  [(421, 0), (429, 0), (432, 3.0), (450, 3.0)])

    # info lines rise slightly as they power on
    for i in range(3):
        ob = bpy.data.objects.get("INFO_LINE_%d" % i)
        if ob is None:
            continue
        base = ob.location.z
        ob.location.z = base - 0.12
        ob.keyframe_insert("location", index=2, frame=301)
        ob.location.z = base
        ob.keyframe_insert("location", index=2, frame=330)
        _smooth(ob)

    # hard visibility gates so ghost text never shows through chrome
    for i in range(3):
        ob = bpy.data.objects.get("INFO_LINE_%d" % i)
        if ob is None:
            continue
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=301)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=361)
    for i in range(2):
        ob = bpy.data.objects.get("INFO_FRAME_%d" % i)
        if ob is None:
            continue
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=301)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=361)
    for i in range(2):
        ob = bpy.data.objects.get("INFO_FRAME_V_%d" % i)
        if ob is None:
            continue
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=1)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=301)
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=361)
    tag = bpy.data.objects.get("TAGLINE")
    if tag:
        tag.hide_render = True
        tag.keyframe_insert("hide_render", frame=1)
        tag.hide_render = False
        tag.keyframe_insert("hide_render", frame=431)
    sec = bpy.data.objects.get("TYPO_SECONDARY")
    if sec:
        sec.hide_render = True
        sec.keyframe_insert("hide_render", frame=1)
        sec.hide_render = False
        sec.keyframe_insert("hide_render", frame=199)

    # make sure all object fcurves are smooth
    for ob in bpy.data.objects:
        if ob.animation_data and ob.animation_data.action:
            _smooth(ob)

    print("ANIMATION DONE actions=%d" % len(bpy.data.actions))
