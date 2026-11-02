"""
NEON_RITUAL - lighting, cameras, compositor, probes.
"""

import bpy
import math
import os

from mathutils import Vector

from nr_core import (
    COLL, MAT, SCENE, make_camera, area_light, spot_light, point_light,
    look_at, box, torus, PREVIEW, RENDERS,
)

CAMERAS = {}
MARKERS = []


def build_lights():
    # halo materials must exist before the bars that use them
    halo_w = MAT["white_emit"].copy()
    halo_w.name = "HALO_WHITE"
    halo_r = MAT["red_hot"].copy()
    halo_r.name = "HALO_RED"
    for m in (halo_w, halo_r):
        m.use_fake_user = True
        for n in m.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    MAT["halo_white"] = halo_w
    MAT["halo_red"] = halo_r

    # main overhead key
    spot_light("LIGHT_KEY_OVERHEAD", (0, 4, 33.0), (0, 8, 14.0),
               3200, angle=28, blend=0.4, color=(1.0, 0.96, 0.92),
               coll=COLL["WHITE_SPOT"])

    # white rim from behind the sculpture
    area_light("LIGHT_RIM_L", (-5.5, 14.5, 18.0), (0, 8, 14.0),
               1200, 3.0, (1.0, 0.97, 0.93), COLL["RIM"], shape="RECTANGLE")
    area_light("LIGHT_RIM_R", (5.5, 14.5, 18.0), (0, 8, 14.0),
               1200, 3.0, (1.0, 0.97, 0.93), COLL["RIM"], shape="RECTANGLE")
    # broad softbox overhead-front for chrome highlights
    area_light("LIGHT_CHROME_TOP", (0, -6, 24.0), (0, 6, 15.0),
               600, 9.0, (0.9, 0.93, 1.0), COLL["RIM"], shape="RECTANGLE")

    # stage wash and ring uplight
    spot_light("LIGHT_STAGE_WASH", (0, 8, 17.0), (0, 8, 1.4),
               3000, angle=55, blend=0.5, color=(1.0, 0.92, 0.85),
               coll=COLL["WHITE_SPOT"])
    spot_light("LIGHT_RING_UP", (0, 4, 5.0), (0, 4, 22.0),
               2200, angle=50, blend=0.55, color=(1.0, 0.88, 0.82),
               coll=COLL["RIM"])

    # red architecture wash
    for i, (x, y, z) in enumerate(((-8.5, -18, 7), (8.5, -18, 7),
                                    (-8.5, -2, 7), (8.5, -2, 7),
                                    (-8.5, 14, 7), (8.5, 14, 7),
                                    (-8.5, -12, 22), (8.5, -12, 22),
                                    (-8.5, 12, 22), (8.5, 12, 22))):
        area_light("LIGHT_RED_WASH_%02d" % i, (x, y, z),
                   (0, y, 6 if z < 15 else 18),
                   450, 2.2, (1.0, 0.01, 0.012), COLL["RED_NEON"],
                   shape="RECTANGLE")

    # neutral wall / pillar reveals
    for i, (x, y) in enumerate(((-16, -14), (16, -14), (-16, 8), (16, 8))):
        area_light("LIGHT_WALL_%02d" % i, (x, y, 11.0),
                   (x * 0.55, y, 10.0), 1800, 4.0,
                   (0.95, 0.84, 0.74), COLL["ATMOS_LIGHT"],
                   shape="RECTANGLE")
    # front fill on the nave pillars, from near the audience
    for i, x in enumerate((-12.0, 12.0)):
        area_light("LIGHT_PILLAR_FILL_%d" % i, (x, -26.0, 12.0),
                   (x * 0.72, -4.0, 11.0), 1200, 5.0,
                   (0.90, 0.80, 0.68), COLL["ATMOS_LIGHT"],
                   shape="RECTANGLE")
    # broad cool top light for the whole nave
    area_light("LIGHT_NAVE_TOP", (0, 0, 29.0), (0, 5, 0.0),
               5000, 18.0, (0.82, 0.88, 1.0), COLL["ATMOS_LIGHT"],
               shape="RECTANGLE")
    # cool grazing wash on the arches and upper stone
    for i, x in enumerate((-11, 11)):
        area_light("LIGHT_ARCH_%d" % i, (x, -16, 15.0), (x * 0.7, 4, 21.0),
                   1600, 4.0, (0.65, 0.74, 1.0), COLL["ATMOS_LIGHT"],
                   shape="RECTANGLE")
    for i, (x, y) in enumerate(((-18.3, -12), (18.3, -12),
                                 (-18.3, 8), (18.3, 8))):
        area_light("LIGHT_WALL_WASH_%d" % i, (x, y, 16.0),
                   (x, y, 8.0), 800, 2.4,
                   (0.95, 0.82, 0.70), COLL["ATMOS_LIGHT"],
                   shape="RECTANGLE")

    # vertical ritual light bars behind the sculpture: these are what the
    # chrome actually reflects, and they give the upper hall its depth.
    for i, x in enumerate((-7.2, 7.2)):
        box("RITUAL_BAR_FRAME_R_%d" % i, (0.36, 0.36, 12.6),
            (x, 15.8, 15.2), MAT["gunmetal"], COLL["ATMOS_LIGHT"])
        box("RITUAL_BAR_R_%d" % i, (0.16, 0.16, 12.0),
            (x, 15.55, 15.2), halo_r, COLL["ATMOS_LIGHT"])
    for i, x in enumerate((-4.2, 4.2)):
        box("RITUAL_BAR_FRAME_W_%d" % i, (0.34, 0.34, 12.2),
            (x, 15.6, 15.0), MAT["gunmetal"], COLL["ATMOS_LIGHT"])
        box("RITUAL_BAR_W_%d" % i, (0.14, 0.14, 11.6),
            (x, 15.35, 15.0), halo_w, COLL["ATMOS_LIGHT"])

    # a physical white light bar in front of the stage; it gives the chrome
    # a reflection at camera height that the top title line can catch.
    lb = MAT["white_emit"].copy()
    lb.name = "STAGE_LIGHTBAR"
    for n in lb.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
            n.inputs["Emission Strength"].default_value = 4.0
    lb.use_fake_user = True
    MAT["stage_lightbar"] = lb
    box("STAGE_LIGHTBAR_FRAME", (6.5, 0.20, 0.20), (0, -7.0, 2.2),
        MAT["gunmetal"], COLL["DECOR"])
    box("STAGE_LIGHTBAR", (6.0, 0.10, 0.10), (0, -6.88, 2.2),
        lb, COLL["ATMOS_LIGHT"])
    spot_light("LIGHT_BEAM", (0, 4, 31.0), (0, 8, 14.0),
               15000, angle=12, blend=0.22, color=(1.0, 0.97, 0.94),
               coll=COLL["WHITE_SPOT"])
    # a large ceremonial halo directly behind the sculpture: it is both a
    # set piece and the broad chrome reflection the hero needs.  It turns on
    # with the title reveal, not before.
    torus("HALO_FRAME", 6.05, 0.22, (0, 16.7, 16.7), MAT["gunmetal"],
          COLL["ATMOS_LIGHT"], 96, 10, rot=(math.radians(90), 0, 0))
    torus("HALO_RED", 4.95, 0.06, (0, 16.3, 16.3), halo_r,
          COLL["ATMOS_LIGHT"], 96, 6, rot=(math.radians(90), 0, 0))
    for i, x in enumerate((-4.5, 4.5)):
        box("FLOOR_STRIP_%d" % i, (0.08, 12.0, 0.02),
            (x, -6.0, 0.035), MAT["red"], COLL["DECOR"])
    box("FLOOR_STRIP_CENTER", (0.06, 4.0, 0.02), (0, -8.0, 0.035),
        MAT["red"], COLL["DECOR"])
    area_light("LIGHT_STAGE_FRONT", (0, -8.0, 2.0), (0, -1.0, 0.6),
               450, 4.0, (1.0, 0.9, 0.8), COLL["WHITE_SPOT"],
               shape="RECTANGLE")
    spot_light("LIGHT_STAGE_TOP", (0, 8, 10.0), (0, 8, 1.4),
               700, angle=50, blend=0.5, color=(1.0, 0.9, 0.8),
               coll=COLL["WHITE_SPOT"])
    area_light("LIGHT_SCULPT_FRONT", (0, -6.0, 15.0), (0, 8, 15.0),
               700, 4.0, (1.0, 0.95, 0.9), COLL["RIM"],
               shape="RECTANGLE")
    for i, (x, y) in enumerate(((-9, -7), (9, -7), (-9, 7), (9, 7))):
        point_light("LIGHT_PILLAR_UP_%d" % i, (x, y, 1.2), 220,
                    (1.0, 0.55, 0.35), 0.8, COLL["RED_NEON"])

    # stage practicals
    for i, (x, y, z) in enumerate(((-4.0, 2.0, 2.2), (4.0, 2.0, 2.2),
                                    (-4.0, 12.0, 2.2), (4.0, 12.0, 2.2))):
        point_light("LIGHT_STAGE_RED_%02d" % i, (x, y, z), 180,
                    (1.0, 0.01, 0.012), 0.4, COLL["RED_NEON"])

    # title backlight and sweep
    back = area_light("LIGHT_TITLE_BACK", (0, 0.8, 8.8), (0, -2, 8.6),
                      0.0, 4.0, (1.0, 0.01, 0.012), COLL["RED_NEON"],
                      shape="RECTANGLE")
    key = area_light("LIGHT_TITLE_KEY", (-7.5, -7.5, 10.8), (0, -2, 9.6),
                     450, 0.8, (1.0, 0.94, 0.88), COLL["WHITE_SPOT"],
                     shape="RECTANGLE")
    key.data.size_y = 1.5
    key2 = area_light("LIGHT_TITLE_KEY_R", (7.5, -7.0, 10.4), (0, -2, 9.8),
                      300, 1.0, (1.0, 0.95, 0.9), COLL["WHITE_SPOT"],
                      shape="RECTANGLE")
    key2.data.size_y = 1.6
    rim = area_light("LIGHT_TITLE_RIM", (6.0, -5.0, 10.5), (0, -2, 8.6),
                     160, 0.45, (1.0, 0.96, 0.92), COLL["RIM"],
                     shape="RECTANGLE")
    rim.data.size_y = 2.0
    soft = area_light("LIGHT_TITLE_SOFT", (0, -19.0, 10.5), (0, -2, 9.6),
                      900, 6.0, (1.0, 0.97, 0.94), COLL["WHITE_SPOT"],
                      shape="RECTANGLE")
    soft.data.size_y = 2.0
    low = area_light("LIGHT_TITLE_LOW", (0, -9.0, 2.8), (0, -2, 9.8),
                     300, 3.0, (1.0, 0.9, 0.85), COLL["WHITE_SPOT"],
                     shape="RECTANGLE")
    low.data.size_y = 1.2
    low.data.use_shadow = False
    # on-axis chrome fill: at the camera height, so the reflection is seen
    onaxis = area_light("LIGHT_TITLE_ONAXIS", (0, -16.0, 3.0), (0, -2, 9.0),
                        900, 9.0, (1.0, 0.97, 0.95), COLL["WHITE_SPOT"],
                        shape="RECTANGLE")
    onaxis.data.size_y = 4.0
    onaxis.data.use_shadow = False
    sweep = area_light("LIGHT_TITLE_SWEEP", (-5.5, -4.8, 10.6), (0, -2, 8.6),
                       0.0, 0.35, (1.0, 0.98, 0.94), COLL["WHITE_SPOT"],
                       shape="RECTANGLE")
    sweep.data.size_y = 2.6

    # low fill from the entrance, cool
    area_light("LIGHT_FILL_ENTRANCE", (0, -24, 9.0), (0, 8, 12.0),
               500, 12.0, (0.55, 0.65, 1.0), COLL["ATMOS_LIGHT"])
    area_light("LIGHT_FILL_HIGH", (0, -8, 24.0), (0, 8, 10.0),
               320, 14.0, (0.55, 0.65, 0.85), COLL["ATMOS_LIGHT"])

    # corridor
    area_light("LIGHT_CORRIDOR", (0, -45, 5.0), (0, -30, 3.0),
               500, 2.0, (1.0, 0.82, 0.76), COLL["WHITE_SPOT"])
    point_light("LIGHT_CORRIDOR_RED", (0, -40, 3.5), 120,
                (1.0, 0.01, 0.01), 0.4, COLL["RED_NEON"])
    point_light("LIGHT_CORRIDOR_FILL", (0, -43, 2.6), 160,
                (1.0, 0.65, 0.55), 1.0, COLL["WHITE_SPOT"])

    # a few practicals in the apse / side aisles
    for i, (x, y) in enumerate(((-16, 24), (16, 24), (-18, -2), (18, -2))):
        point_light("LIGHT_PRACTICAL_%02d" % i, (x, y, 4.0), 90,
                    (1.0, 0.02, 0.02), 0.3, COLL["RED_NEON"])

    # return handles for animation
    return {
        "title_back": back,
        "title_key": key,
        "title_sweep": sweep,
        "key": bpy.data.objects["LIGHT_KEY_OVERHEAD"],
    }


def build_cameras():
    global CAMERAS, MARKERS
    specs = [
        ("CAM_01_CORRIDOR", 24, (0, -46, 1.7), (0, -30, 4.2),
         (0, -32.0, 2.4), (0, -24, 7.5), 1, 90),
        ("CAM_02_REVEAL", 35, (0, -30, 2.4), (0, 2, 10.0),
         (0, -19, 3.2), (0, 5, 12.0), 91, 180),
        ("CAM_03_TITLE", 32, (-1.0, -18, 2.6), (0, 0, 9.5),
         (-0.6, -15.5, 2.9), (0, 1, 10.5), 181, 240),
        ("CAM_04_HERO", 28, (-0.5, -15, 2.6), (0, 0, 9.8),
         (0.0, -13.5, 2.4), (0, 1, 9.8), 241, 300),
        ("CAM_05_INFO", 32, (0, -10.5, 4.8), (0, -2, 5.0),
         (0, -9.0, 4.6), (0, -2, 5.0), 301, 360),
        ("CAM_06_WIDE", 18, (0, -24, 9.0), (0, 4, 12.0),
         (0, -28, 10.5), (0, 4, 12.0), 361, 390),
        ("CAM_07_IMPACT", 35, (8.0, -4.0, 2.0), (0, 8, 15.0),
         (7.0, -2.0, 2.5), (0, 8, 15.5), 391, 420),
        ("CAM_08_END", 28, (0, -18, 2.2), (0, 3, 10.2),
         (0, -17, 2.3), (0, 3, 10.4), 421, 450),
    ]
    CAMERAS = {}
    for name, lens, loc0, tgt0, loc1, tgt1, f0, f1 in specs:
        cam = make_camera(name, loc0, tgt0, lens=lens,
                          coll=COLL["CAM_%02d" % (len(CAMERAS) + 1)])
        cam["shot_start"] = f0
        cam["shot_end"] = f1
        # end pose
        cam.location = loc1
        look_at(cam, tgt1)
        cam.keyframe_insert("location", frame=f1)
        cam.keyframe_insert("rotation_euler", frame=f1)
        # start pose
        cam.location = loc0
        look_at(cam, tgt0)
        cam.keyframe_insert("location", frame=f0)
        cam.keyframe_insert("rotation_euler", frame=f0)
        # smooth interpolation
        for fc in _fcurves(cam):
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.handle_left_type = "AUTO_CLAMPED"
                kp.handle_right_type = "AUTO_CLAMPED"
        CAMERAS[name] = cam

    sc = bpy.context.scene
    sc.camera = CAMERAS["CAM_01_CORRIDOR"]
    # markers
    for m in list(sc.timeline_markers):
        sc.timeline_markers.remove(m, do_unlink=True)
    for i, name in enumerate(("CAM_01_CORRIDOR", "CAM_02_REVEAL",
                              "CAM_03_TITLE", "CAM_04_HERO", "CAM_05_INFO",
                              "CAM_06_WIDE", "CAM_07_IMPACT", "CAM_08_END")):
        f = (1, 91, 181, 241, 301, 361, 391, 421)[i]
        mk = sc.timeline_markers.new("SHOT_%02d" % (i + 1), frame=f)
        mk.camera = CAMERAS[name]
    print("CAMERAS", len(CAMERAS), "markers", len(sc.timeline_markers))
    return CAMERAS


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


def setup_compositor():
    sc = bpy.context.scene
    sc.use_nodes = True
    old = bpy.data.node_groups.get("NEON_COMPOSITOR")
    if old:
        bpy.data.node_groups.remove(old)
    nt = bpy.data.node_groups.new("NEON_COMPOSITOR", "CompositorNodeTree")
    nt.interface.new_socket(name="Image", in_out="OUTPUT",
                            socket_type="NodeSocketColor")
    sc.compositing_node_group = nt
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.location = (-800, 0)
    exp = nt.nodes.new("CompositorNodeExposure")
    exp.location = (-580, 0)
    exp.inputs["Exposure"].default_value = 0.0
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.location = (-360, 0)
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = 1.2
    glare.inputs["Smoothness"].default_value = 0.1
    glare.inputs["Maximum"].default_value = 10.0
    glare.inputs["Strength"].default_value = 0.18
    glare.inputs["Size"].default_value = 0.45
    lens = nt.nodes.new("CompositorNodeLensdist")
    lens.location = (-140, 0)
    lens.inputs["Distortion"].default_value = 0.006
    lens.inputs["Dispersion"].default_value = 0.008
    # vignette: black over image at the edges
    mask = nt.nodes.new("CompositorNodeEllipseMask")
    mask.location = (-360, -300)
    mask.inputs["Position"].default_value = (0.5, 0.5)
    mask.inputs["Size"].default_value = (1.08, 1.12)
    blur = nt.nodes.new("CompositorNodeBlur")
    blur.location = (-140, -300)
    blur.inputs["Type"].default_value = "Gaussian"
    blur.inputs["Size"].default_value = (140.0, 140.0)
    inv = nt.nodes.new("CompositorNodeInvert")
    inv.location = (80, -300)
    inv.inputs["Factor"].default_value = 1.0
    inv.inputs["Invert Color"].default_value = True
    black = nt.nodes.new("CompositorNodeRGB")
    black.location = (80, -500)
    black.outputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
    over = nt.nodes.new("CompositorNodeAlphaOver")
    over.location = (320, -120)
    comp = nt.nodes.new("NodeGroupOutput")
    comp.location = (560, 0)
    comp.is_active_output = True

    nt.links.new(rl.outputs["Image"], exp.inputs["Image"])
    nt.links.new(exp.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], lens.inputs["Image"])
    nt.links.new(lens.outputs["Image"], over.inputs["Background"])
    nt.links.new(black.outputs[0], over.inputs["Foreground"])
    nt.links.new(mask.outputs["Mask"], blur.inputs["Image"])
    nt.links.new(blur.outputs["Image"], inv.inputs["Color"])
    nt.links.new(inv.outputs["Color"], over.inputs["Factor"])
    nt.links.new(over.outputs["Image"], comp.inputs[0])
    # intro fade via exposure
    exp.inputs["Exposure"].default_value = -7.0
    exp.inputs["Exposure"].keyframe_insert("default_value", frame=1)
    exp.inputs["Exposure"].default_value = 0.0
    exp.inputs["Exposure"].keyframe_insert("default_value", frame=12)
    print("COMPOSITOR OK")


def add_probes():
    """Add probes; bake later if the bake operation works in this build."""
    sc = bpy.context.scene
    try:
        bpy.ops.object.lightprobe_add(type="SPHERE", location=(0, 8, 12))
        p = bpy.context.object
        p.name = "PROBE_HALL"
        p.data.influence_distance = 30
        for c in list(p.users_collection):
            c.objects.unlink(p)
        COLL["LIGHTING"] if "LIGHTING" in COLL else COLL["ATMOS_LIGHT"]
        COLL["ATMOS_LIGHT"].objects.link(p)
        bpy.ops.object.lightprobe_add(type="PLANE", location=(0, 1, 0.02))
        q = bpy.context.object
        q.name = "PROBE_FLOOR"
        q.scale = (18, 28, 1)
        q.data.influence_distance = 40
        for c in list(q.users_collection):
            c.objects.unlink(q)
        COLL["ATMOS_LIGHT"].objects.link(q)
        print("PROBES ADDED")
    except Exception as e:
        print("PROBE ERR", e)


def preview(cam, frame, path, res=(540, 960), samples=16):
    sc = bpy.context.scene
    markers = list(sc.timeline_markers)
    saved = [(m, m.camera) for m in markers]
    for m in markers:
        m.camera = None
    old_cam = sc.camera
    old_res = (sc.render.resolution_x, sc.render.resolution_y)
    old_s = sc.eevee.taa_render_samples
    old_path = sc.render.filepath
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.eevee.taa_render_samples = samples
    sc.render.filepath = path
    sc.frame_set(frame)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    sc.camera = old_cam
    sc.render.resolution_x, sc.render.resolution_y = old_res
    sc.eevee.taa_render_samples = old_s
    sc.render.filepath = old_path
    for m, c in saved:
        m.camera = c
    print("PREVIEW", path)
