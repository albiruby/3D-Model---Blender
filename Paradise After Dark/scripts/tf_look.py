"""
PARADISE AFTER DARK — daylight, sky, camera and compositor.
"""

import bpy
import math
import os

from mathutils import Vector

import tf_core as C

CAMERA = None
SUN_DIR = Vector((0.46, 0.60, -0.66)).normalized()   # where light travels


def build_world():
    sc = bpy.context.scene
    world = bpy.data.worlds.new("PARADISE_SKY")
    sc.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (900, 0)

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    geom.location = (-1000, 200)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-800, 200)
    nt.links.new(geom.outputs["Incoming"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-620, 200)
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-420, 200)
    ramp.color_ramp.elements[0].position = 0.01
    ramp.color_ramp.elements[0].color = (0.84, 0.92, 0.92, 1)
    ramp.color_ramp.elements[1].position = 0.95
    ramp.color_ramp.elements[1].color = (0.002, 0.030, 0.26, 1)
    for pos, col in ((0.07, (0.46, 0.72, 0.90, 1)),
                     (0.18, (0.13, 0.43, 0.92, 1)),
                     (0.38, (0.025, 0.20, 0.76, 1)),
                     (0.62, (0.006, 0.09, 0.50, 1))):
        e = ramp.color_ramp.elements.new(pos)
        e.color = col
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])

    # warm halo around the sun
    sun_pos = -SUN_DIR
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.location = (-800, -260)
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = sun_pos
    nt.links.new(geom.outputs["Incoming"], dot.inputs[0])
    sglow = nt.nodes.new("ShaderNodeMapRange")
    sglow.location = (-620, -260)
    sglow.inputs["From Min"].default_value = 0.72
    sglow.inputs["From Max"].default_value = 1.0
    nt.links.new(dot.outputs["Value"], sglow.inputs["Value"])
    glow_ramp = nt.nodes.new("ShaderNodeValToRGB")
    glow_ramp.location = (-420, -260)
    glow_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    glow_ramp.color_ramp.elements[1].color = (0.55, 0.94, 1.0, 1)
    e = glow_ramp.color_ramp.elements.new(0.55)
    e.color = (0.30, 0.62, 0.90, 1)
    nt.links.new(sglow.outputs["Result"], glow_ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.location = (-120, 100)
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 0.55
    nt.links.new(ramp.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(glow_ramp.outputs["Color"], mix.inputs["Color2"])

    # soft cumulus layer
    cl_noise = nt.nodes.new("ShaderNodeTexNoise")
    cl_noise.location = (-620, -520)
    cl_noise.inputs["Scale"].default_value = 2.4
    cl_noise.inputs["Detail"].default_value = 7.0
    cl_noise.inputs["Roughness"].default_value = 0.58
    cl_noise.inputs["Distortion"].default_value = 0.25
    nt.links.new(geom.outputs["Incoming"], cl_noise.inputs["Vector"])
    cl_ramp = nt.nodes.new("ShaderNodeValToRGB")
    cl_ramp.location = (-400, -520)
    cl_ramp.color_ramp.elements[0].position = 0.47
    cl_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
    cl_ramp.color_ramp.elements[1].position = 0.60
    cl_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1)
    nt.links.new(cl_noise.outputs["Fac"], cl_ramp.inputs["Fac"])
    cl_mask = nt.nodes.new("ShaderNodeMapRange")
    cl_mask.location = (-620, -740)
    cl_mask.inputs["From Min"].default_value = -0.95
    cl_mask.inputs["From Max"].default_value = -0.02
    cl_mask.inputs["To Min"].default_value = 0.20
    cl_mask.inputs["To Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], cl_mask.inputs["Value"])
    cl_mul = nt.nodes.new("ShaderNodeMath")
    cl_mul.location = (-180, -600)
    cl_mul.operation = "MULTIPLY"
    cl_mul.inputs[1].default_value = 0.62
    nt.links.new(cl_ramp.outputs["Color"], cl_mul.inputs[0])
    cl_mul2 = nt.nodes.new("ShaderNodeMath")
    cl_mul2.location = (0, -600)
    cl_mul2.operation = "MULTIPLY"
    nt.links.new(cl_mul.outputs[0], cl_mul2.inputs[0])
    nt.links.new(cl_mask.outputs["Result"], cl_mul2.inputs[1])
    cl_mix = nt.nodes.new("ShaderNodeMixRGB")
    cl_mix.location = (160, 60)
    cl_mix.blend_type = "MIX"
    cl_mix.inputs["Color2"].default_value = (0.95, 0.97, 1.0, 1)
    nt.links.new(mix.outputs["Color"], cl_mix.inputs["Color1"])
    nt.links.new(cl_mul2.outputs[0], cl_mix.inputs["Fac"])

    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (380, 80)
    bg.inputs["Strength"].default_value = 0.38
    nt.links.new(cl_mix.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def build_lights():
    rot = SUN_DIR.to_track_quat("-Z", "Y").to_euler()
    # warm tropical key from the front-left
    sun = C.sun_light("SUN_KEY", tuple(rot),
                      energy=8.8, angle=math.radians(1.1),
                      color=(1.0, 0.92, 0.82))
    # broad sky fill from the camera side
    C.area_light("FILL_FRONT", (0, -11.0, 7.5), (0, 3.0, 4.6),
                 20, 14.0, (0.55, 0.72, 1.0), C.COLL["FILL"],
                 shape="RECTANGLE")
    # warm bounce from the left garden
    C.area_light("FILL_LEFT", (-10.0, -5.0, 5.0), (-2.0, 4.0, 3.6),
                 15, 9.0, (1.0, 0.76, 0.56), C.COLL["FILL"],
                 shape="RECTANGLE")
    # rim behind the pavilion, separates the white petals from the sky
    C.area_light("RIM_BACK", (0, 11.5, 8.5), (0, 4.0, 5.0),
                 120, 9.0, (0.78, 0.88, 1.0), C.COLL["FILL"],
                 shape="RECTANGLE")
    # cool bounce from the lagoon
    C.area_light("POOL_BOUNCE", (0, -5.0, 1.4), (0, 2.0, 2.6),
                 18, 7.0, (0.22, 0.86, 0.86), C.COLL["FILL"],
                 shape="RECTANGLE")
    # soft top light under the canopy so the stage is not a cave
    C.area_light("STAGE_TOP", (0, 5.0, 8.4), (0, 4.6, 1.0),
                 40, 8.0, (1.0, 0.96, 0.90), C.COLL["FILL"],
                 shape="RECTANGLE")
    return sun


def build_camera():
    global CAMERA
    CAMERA = C.make_camera("CAM_MAIN", (-1.80, -10.5, 1.35), (0.40, 2.6, 2.6),
                           lens=19.0, coll=C.COLL["CAMERAS"])
    cd = CAMERA.data
    cd.dof.use_dof = True
    cd.dof.focus_distance = 12.5
    cd.dof.aperture_fstop = 8.0
    cd.dof.aperture_blades = 7
    bpy.context.scene.camera = CAMERA
    return CAMERA


def build_probes():
    """Planar probe for the lagoon so the pavilion lands in the water."""
    for ob in list(bpy.data.objects):
        if ob.type == "LIGHT_PROBE":
            bpy.data.objects.remove(ob, do_unlink=True)
    lp = bpy.data.lightprobes.new("POOL_REFLECTION", "PLANE")
    ob = bpy.data.objects.new("POOL_REFLECTION", lp)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = (0.0, -4.45, -0.155)
    ob.scale = (7.0, 2.5, 1.0)
    try:
        lp.influence_distance = 5.0
        lp.clip_start = 0.05
        lp.parallax_distance = 12.0
    except Exception as e:
        print("PROBE WARN", e)
    try:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.context.view_layer.update()
        bpy.ops.object.lightprobe_cache_bake(subset="ACTIVE")
        print("PROBE BAKED")
    except Exception as e:
        print("PROBE BAKE WARN", e)
    print("PROBE OK")


def setup_compositor():
    sc = bpy.context.scene
    sc.use_nodes = True
    old = bpy.data.node_groups.get("PARADISE_COMPOSITOR")
    if old:
        bpy.data.node_groups.remove(old)
    nt = bpy.data.node_groups.new("PARADISE_COMPOSITOR", "CompositorNodeTree")
    nt.interface.new_socket(name="Image", in_out="OUTPUT",
                            socket_type="NodeSocketColor")
    sc.compositing_node_group = nt
    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.location = (-700, 0)
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.location = (-450, 0)
    glare.inputs["Type"].default_value = "Bloom"
    glare.inputs["Quality"].default_value = "High"
    glare.inputs["Threshold"].default_value = 1.35
    glare.inputs["Smoothness"].default_value = 0.12
    glare.inputs["Strength"].default_value = 0.10
    glare.inputs["Size"].default_value = 0.42
    lens = nt.nodes.new("CompositorNodeLensdist")
    lens.location = (-200, 0)
    lens.inputs["Distortion"].default_value = 0.004
    lens.inputs["Dispersion"].default_value = 0.006
    out = nt.nodes.new("NodeGroupOutput")
    out.location = (120, 0)
    out.is_active_output = True
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], lens.inputs["Image"])
    nt.links.new(lens.outputs["Image"], out.inputs[0])
    print("COMPOSITOR OK")


def build_look():
    build_world()
    build_lights()
    build_camera()
    build_probes()
    setup_compositor()
    print("LOOK OK")
