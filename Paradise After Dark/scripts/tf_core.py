"""
PARADISE AFTER DARK — Tropical Futuristic Festival Courtyard
Core scene, collections, materials, geometry helpers.
Blender 5.2.3 LTS / EEVEE.
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Euler, Matrix

BASE = r"D:\Tes Animasi-Motion-Blender\Paradise After Dark"
SCRIPTS = os.path.join(BASE, "scripts")
RENDERS = os.path.join(BASE, "renders")
ASSETS = os.path.join(BASE, "assets")
FONT_DIRS = (
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    r"C:\Windows\Fonts",
)

SCENE = None
COLL = {}
MAT = {}
RNG = random.Random(20261102)


# ------------------------------------------------------------------ scene

def reset_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


def setup_scene():
    global SCENE
    SCENE = bpy.context.scene
    SCENE.name = "PARADISE_AFTER_DARK"
    SCENE.render.engine = "BLENDER_EEVEE"
    SCENE.render.resolution_x = 1920
    SCENE.render.resolution_y = 1080
    SCENE.render.resolution_percentage = 100
    SCENE.render.fps = 30
    SCENE.frame_start = 1
    SCENE.frame_end = 1
    SCENE.render.image_settings.media_type = "IMAGE"
    SCENE.render.image_settings.file_format = "PNG"
    SCENE.render.image_settings.color_mode = "RGB"
    SCENE.render.image_settings.compression = 15
    SCENE.render.film_transparent = False
    SCENE.view_settings.view_transform = "AgX"
    SCENE.view_settings.look = "AgX - Medium High Contrast"
    SCENE.view_settings.exposure = -0.45
    SCENE.view_settings.gamma = 1.0
    SCENE.eevee.taa_render_samples = 64
    SCENE.eevee.taa_samples = 16
    SCENE.eevee.use_raytracing = True
    SCENE.eevee.ray_tracing_method = "SCREEN"
    SCENE.eevee.ray_tracing_options.resolution_scale = "1"
    SCENE.eevee.ray_tracing_options.trace_max_roughness = 0.55
    SCENE.eevee.ray_tracing_options.screen_trace_quality = 0.85
    SCENE.eevee.use_fast_gi = True
    SCENE.eevee.fast_gi_method = "GLOBAL_ILLUMINATION"
    SCENE.eevee.fast_gi_distance = 6.0
    SCENE.eevee.fast_gi_ray_count = 4
    SCENE.eevee.fast_gi_step_count = 8
    SCENE.eevee.use_shadows = True
    SCENE.eevee.shadow_ray_count = 3
    SCENE.eevee.shadow_step_count = 10
    SCENE.eevee.shadow_resolution_scale = 1.0
    SCENE.eevee.volumetric_tile_size = "8"
    SCENE.eevee.volumetric_samples = 32
    SCENE.eevee.volumetric_start = 0.1
    SCENE.eevee.volumetric_end = 100.0
    SCENE.eevee.use_volumetric_shadows = True
    SCENE.render.use_motion_blur = False
    SCENE.unit_settings.system = "METRIC"
    return SCENE


def make_collections():
    global COLL
    COLL.clear()
    root = bpy.data.collections.new("PARADISE_AFTER_DARK")
    bpy.context.scene.collection.children.link(root)
    COLL["ROOT"] = root

    def sub(key, name, parent=None):
        c = bpy.data.collections.new(name)
        (parent or root).children.link(c)
        COLL[key] = c
        return c

    sub("SETUP", "00_SCENE_SETUP")
    a = sub("ARCH", "01_MAIN_ARCHITECTURE")
    sub("PETALS", "Petals", a)
    sub("DOME", "Central_Dome", a)
    sub("ARCH_RIBS", "Structural_Ribs", a)
    sub("BALCONIES", "Balconies_And_Stairs", a)
    s = sub("STAGE", "02_STAGE_SYSTEM")
    sub("STAGE_PLATFORM", "Stage_Platform", s)
    sub("DJ", "DJ_Booth", s)
    sub("SPEAKERS", "Speakers", s)
    sub("LED", "LED_Screens", s)
    sub("STAGE_LIGHTS", "Stage_Lights", s)
    r = sub("ROOF", "03_ROOF_AND_PANELS")
    sub("CANOPY", "Canopy", r)
    sub("PANELS", "Iridescent_Panels", r)
    sub("TREES", "04_TROPICAL_TREES")
    sub("PLANTS", "05_TROPICAL_PLANTS")
    sub("FLOWERS", "FLOWERS", COLL["PLANTS"])
    sub("GROUNDCOVER", "Groundcover", COLL["PLANTS"])
    sub("CROWD", "05b_CROWD")
    w = sub("WATER", "06_POOL_AND_WATER")
    sub("POOL", "Pool", w)
    sub("WATERFALL", "Waterfall", w)
    l = sub("LANDSCAPE", "07_STONE_AND_LANDSCAPE")
    sub("PLANTERS", "Planters", l)
    sub("ROCKS", "Rocks", l)
    d = sub("DECOR", "08_FESTIVAL_DECORATIONS")
    sub("SIGNAGE", "Signage", d)
    sub("BUNTING", "Bunting", d)
    sub("PORTAL", "Portal_Installation", d)
    li = sub("LIGHTS", "09_LIGHTING")
    sub("SUN", "Sun", li)
    sub("FILL", "Fill_Lights", li)
    sub("PRACTICALS", "Practicals", li)
    sub("CAMERAS", "10_CAMERAS")
    sub("REFERENCE", "11_REFERENCE_OBJECTS")
    sub("MASTERS", "MASTERS")
    return COLL


def _new_mat(name):
    old = bpy.data.materials.get(name)
    if old:
        bpy.data.materials.remove(old)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (300, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, b


def _noise(nt, scale=5.0, detail=6.0, rough=0.6, loc=(-500, 0)):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.location = loc
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    return n


def _bump(nt, height, strength=0.2, distance=0.1, loc=(0, -220)):
    b = nt.nodes.new("ShaderNodeBump")
    b.location = loc
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height, b.inputs["Height"])
    return b


def _ramp(nt, c0, c1, loc=(-250, 200)):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = loc
    r.color_ramp.elements[0].color = c0
    r.color_ramp.elements[1].color = c1
    return r


def make_materials():
    global MAT
    MAT.clear()

    # white ceramic / plaster
    m, nt, b = _new_mat("WHITE_CERAMIC")
    b.inputs["Base Color"].default_value = (0.80, 0.77, 0.72, 1)
    b.inputs["Roughness"].default_value = 0.34
    b.inputs["Coat Weight"].default_value = 0.18
    b.inputs["Coat Roughness"].default_value = 0.12
    n = _noise(nt, 28.0, 5.0, 0.55, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.05, 0.04).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["white"] = m

    m, nt, b = _new_mat("WHITE_STONE")
    b.inputs["Base Color"].default_value = (0.46, 0.41, 0.34, 1)
    b.inputs["Roughness"].default_value = 0.58
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.location = (-700, 180)
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.8
    sr = _ramp(nt, (0.28, 0.24, 0.19, 1), (0.60, 0.54, 0.45, 1), (-450, 180))
    sr.color_ramp.elements[0].position = 0.0
    sr.color_ramp.elements[1].position = 0.035
    nt.links.new(vor.outputs["Distance"], sr.inputs["Fac"])
    nt.links.new(sr.outputs["Color"], b.inputs["Base Color"])
    n = _noise(nt, 16.0, 7.0, 0.65, (-520, -80))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.12, 0.06).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["stone"] = m

    m, nt, b = _new_mat("SAND")
    b.inputs["Base Color"].default_value = (0.56, 0.44, 0.30, 1)
    b.inputs["Roughness"].default_value = 0.92
    n = _noise(nt, 40.0, 8.0, 0.7, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.16, 0.05).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["sand"] = m

    # pearlescent / iridescent panel
    m, nt, b = _new_mat("IRIDESCENT")
    b.inputs["Base Color"].default_value = (0.78, 0.90, 0.90, 1)
    b.inputs["Metallic"].default_value = 0.18
    b.inputs["Roughness"].default_value = 0.14
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.06
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.location = (-650, 250)
    lw.inputs["Blend"].default_value = 0.48
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = (-420, 250)
    r.color_ramp.elements[0].position = 0.0
    r.color_ramp.elements[0].color = (0.68, 0.84, 0.88, 1)
    r.color_ramp.elements[1].position = 0.92
    r.color_ramp.elements[1].color = (0.30, 0.55, 0.98, 1)
    for pos, col in ((0.18, (0.95, 0.72, 0.84, 1)),
                     (0.40, (0.98, 0.88, 0.70, 1)),
                     (0.62, (0.38, 0.92, 0.80, 1)),
                     (0.80, (0.70, 0.56, 0.98, 1))):
        e = r.color_ramp.elements.new(pos)
        e.color = col
    nt.links.new(lw.outputs["Facing"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    MAT["irid"] = m

    # softer pearl ceramic for the big petals/dome
    m, nt, b = _new_mat("PEARL_WHITE")
    b.inputs["Base Color"].default_value = (0.84, 0.82, 0.78, 1)
    b.inputs["Metallic"].default_value = 0.04
    b.inputs["Roughness"].default_value = 0.30
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.10
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.location = (-650, 250)
    lw.inputs["Blend"].default_value = 0.26
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = (-420, 250)
    r.color_ramp.elements[0].position = 0.25
    r.color_ramp.elements[0].color = (0.90, 0.87, 0.98, 1)
    r.color_ramp.elements[1].position = 0.82
    r.color_ramp.elements[1].color = (0.90, 0.98, 0.95, 1)
    e = r.color_ramp.elements.new(0.55)
    e.color = (1.0, 0.90, 0.94, 1)
    nt.links.new(lw.outputs["Facing"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    MAT["pearl"] = m

    # turquoise glass
    m, nt, b = _new_mat("TURQUOISE_GLASS")
    b.inputs["Base Color"].default_value = (0.10, 0.55, 0.52, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["IOR"].default_value = 1.45
    b.inputs["Transmission Weight"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.4
    try:
        m.use_screen_refraction = True
    except Exception:
        pass
    MAT["turquoise_glass"] = m

    # pool water — saturated lagoon turquoise with a soft sky reflection
    m, nt, b = _new_mat("POOL_WATER")
    b.inputs["Base Color"].default_value = (0.0, 0.32, 0.34, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["IOR"].default_value = 1.333
    b.inputs["Specular IOR Level"].default_value = 0.45
    b.inputs["Transmission Weight"].default_value = 0.55
    b.inputs["Coat Weight"].default_value = 0.55
    b.inputs["Coat Roughness"].default_value = 0.025
    b.inputs["Emission Color"].default_value = (0.0, 0.06, 0.08, 1)
    b.inputs["Emission Strength"].default_value = 0.10
    # depth gradient: deep teal at the far edge, bright lagoon near camera
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, 300)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-720, 300)
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.location = (-540, 300)
    mr.inputs["From Min"].default_value = -6.8
    mr.inputs["From Max"].default_value = -2.1
    nt.links.new(sep.outputs["Y"], mr.inputs["Value"])
    wr = nt.nodes.new("ShaderNodeValToRGB")
    wr.location = (-340, 300)
    wr.color_ramp.elements[0].position = 0.0
    wr.color_ramp.elements[0].color = (0.001, 0.12, 0.18, 1)
    wr.color_ramp.elements[1].position = 1.0
    wr.color_ramp.elements[1].color = (0.02, 0.50, 0.52, 1)
    e = wr.color_ramp.elements.new(0.55)
    e.color = (0.005, 0.28, 0.34, 1)
    nt.links.new(mr.outputs["Result"], wr.inputs["Fac"])
    nt.links.new(wr.outputs["Color"], b.inputs["Base Color"])

    n = _noise(nt, 6.0, 7.0, 0.55, (-520, -80))
    n2 = _noise(nt, 34.0, 4.0, 0.5, (-520, -300))
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 0.30
    nt.links.new(n.outputs["Fac"], mix.inputs["Color1"])
    nt.links.new(n2.outputs["Fac"], mix.inputs["Color2"])
    nt.links.new(_bump(nt, mix.outputs["Color"], 0.03, 0.04).outputs["Normal"],
                 b.inputs["Normal"])

    # blend a little transparency so the caustic floor reads through
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    for lk in list(out.inputs["Surface"].links):
        nt.links.remove(lk)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.location = (300, -240)
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.location = (460, 0)
    mx.inputs[0].default_value = 0.16
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
        m.use_transparency_overlap = False
        m.use_raytrace_refraction = True
        m.thickness_mode = "SLAB"
    except Exception:
        pass
    MAT["water"] = m

    # pool floor / pale tiles with a caustic web
    m, nt, b = _new_mat("POOL_FLOOR")
    b.inputs["Base Color"].default_value = (0.20, 0.66, 0.62, 1)
    b.inputs["Roughness"].default_value = 0.34
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1000, 0)
    nz = _noise(nt, 0.9, 3.0, 0.50, (-820, 120))
    nz2 = _noise(nt, 1.8, 3.0, 0.50, (-820, -120))
    mixv = nt.nodes.new("ShaderNodeMixRGB")
    mixv.location = (-650, 0)
    mixv.blend_type = "ADD"
    mixv.inputs["Fac"].default_value = 0.45
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], nz2.inputs["Vector"])
    nt.links.new(nz.outputs["Color"], mixv.inputs["Color1"])
    nt.links.new(nz2.outputs["Color"], mixv.inputs["Color2"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.location = (-650, -300)
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 0.55
    nt.links.new(mixv.outputs["Color"], vor.inputs["Vector"])
    r = _ramp(nt, (0.32, 0.80, 0.76, 1), (0.01, 0.22, 0.27, 1), (-400, -260))
    r.color_ramp.elements[0].position = 0.0
    r.color_ramp.elements[1].position = 0.16
    nt.links.new(vor.outputs["Distance"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(_bump(nt, vor.outputs["Distance"], 0.05, 0.04).outputs["Normal"],
                 b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (0.03, 0.26, 0.26, 1)
    b.inputs["Emission Strength"].default_value = 0.06
    MAT["pool_floor"] = m

    # translucent canopy glass, pastel iridescent
    m, nt, b = _new_mat("CANOPY_GLASS")
    b.inputs["Base Color"].default_value = (0.86, 0.94, 0.96, 1)
    b.inputs["Metallic"].default_value = 0.20
    b.inputs["Roughness"].default_value = 0.09
    b.inputs["Coat Weight"].default_value = 0.40
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.location = (-650, 250)
    lw.inputs["Blend"].default_value = 0.45
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = (-420, 250)
    r.color_ramp.elements[0].position = 0.0
    r.color_ramp.elements[0].color = (0.90, 0.97, 0.98, 1)
    r.color_ramp.elements[1].position = 0.92
    r.color_ramp.elements[1].color = (0.55, 0.75, 0.98, 1)
    for pos, col in ((0.25, (1.0, 0.85, 0.92, 1)),
                     (0.50, (1.0, 0.96, 0.82, 1)),
                     (0.68, (0.64, 0.98, 0.90, 1)),
                     (0.82, (0.82, 0.66, 0.98, 1))):
        e = r.color_ramp.elements.new(pos)
        e.color = col
    nt.links.new(lw.outputs["Facing"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.location = (300, -220)
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.location = (460, 0)
    mx.inputs[0].default_value = 0.45
    nt.links.new(tr.outputs[0], mx.inputs[1])
    nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    try:
        m.surface_render_method = "BLENDED"
        m.use_transparency_overlap = False
    except Exception as e:
        print("CANOPY MAT WARN", e)
    MAT["canopy_glass"] = m

    m, nt, b = _new_mat("FOAM")
    b.inputs["Base Color"].default_value = (0.92, 0.98, 1.0, 1)
    b.inputs["Roughness"].default_value = 0.28
    b.inputs["Transmission Weight"].default_value = 0.15
    b.inputs["Emission Color"].default_value = (0.55, 0.92, 0.98, 1)
    b.inputs["Emission Strength"].default_value = 0.25
    MAT["foam"] = m

    # basalt / river rock
    m, nt, b = _new_mat("ROCK")
    b.inputs["Base Color"].default_value = (0.20, 0.18, 0.15, 1)
    b.inputs["Roughness"].default_value = 0.86
    n = _noise(nt, 9.0, 7.0, 0.7, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.55, 0.18).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["rock"] = m
    MAT["lava"] = m

    m, nt, b = _new_mat("HAZE")
    b.inputs["Base Color"].default_value = (0.020, 0.070, 0.060, 1)
    b.inputs["Roughness"].default_value = 0.98
    n = _noise(nt, 3.0, 6.0, 0.65, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.35, 0.30).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["haze"] = m

    m, nt, b = _new_mat("BERM")
    b.inputs["Base Color"].default_value = (0.008, 0.055, 0.024, 1)
    b.inputs["Roughness"].default_value = 0.98
    n = _noise(nt, 5.0, 7.0, 0.65, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.55, 0.25).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["berm"] = m

    m, nt, b = _new_mat("LANTERN")
    b.inputs["Base Color"].default_value = (0.35, 0.10, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.45
    b.inputs["Emission Color"].default_value = (1.0, 0.42, 0.12, 1)
    b.inputs["Emission Strength"].default_value = 2.0
    MAT["lantern"] = m

    m, nt, b = _new_mat("WOOD")
    b.inputs["Base Color"].default_value = (0.43, 0.23, 0.10, 1)
    b.inputs["Roughness"].default_value = 0.5
    n = _noise(nt, 4.0, 4.0, 0.65, (-520, -100))
    r = _ramp(nt, (0.12, 0.05, 0.02, 1), (0.55, 0.30, 0.13, 1), (-260, 0))
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    MAT["wood"] = m

    m, nt, b = _new_mat("PALM_BARK")
    b.inputs["Base Color"].default_value = (0.33, 0.30, 0.25, 1)
    b.inputs["Roughness"].default_value = 0.82
    n = _noise(nt, 7.0, 6.0, 0.7, (-520, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.30, 0.08).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["bark"] = m

    m, nt, b = _new_mat("COCONUT")
    b.inputs["Base Color"].default_value = (0.24, 0.15, 0.06, 1)
    b.inputs["Roughness"].default_value = 0.62
    MAT["coconut"] = m

    m, nt, b = _new_mat("DARK_METAL")
    b.inputs["Base Color"].default_value = (0.015, 0.018, 0.022, 1)
    b.inputs["Metallic"].default_value = 0.8
    b.inputs["Roughness"].default_value = 0.28
    MAT["dark_metal"] = m

    m, nt, b = _new_mat("SIGN_PANEL")
    b.inputs["Base Color"].default_value = (0.010, 0.012, 0.014, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.72
    MAT["sign_panel"] = m

    # botanical greens
    greens = {
        "leaf_deep": (0.012, 0.115, 0.045),
        "leaf_mid": (0.030, 0.255, 0.075),
        "leaf_bright": (0.075, 0.410, 0.115),
        "leaf_lime": (0.180, 0.520, 0.130),
    }
    for key, col in greens.items():
        m, nt, b = _new_mat("LEAF_" + key.upper())
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Roughness"].default_value = 0.52
        b.inputs["Subsurface Weight"].default_value = 0.035
        b.inputs["Subsurface Radius"].default_value = (0.8, 1.0, 0.4)
        n = _noise(nt, 45.0, 4.0, 0.5, (-450, -100))
        nt.links.new(_bump(nt, n.outputs["Fac"], 0.06, 0.02).outputs["Normal"],
                     b.inputs["Normal"])
        MAT[key] = m

    # flowers
    flowers = {
        "flower_pink": (1.0, 0.20, 0.36),
        "flower_coral": (1.0, 0.32, 0.22),
        "flower_orange": (1.0, 0.42, 0.10),
        "flower_yellow": (1.0, 0.78, 0.18),
        "flower_lav": (0.62, 0.48, 0.95),
    }
    for key, col in flowers.items():
        m, nt, b = _new_mat(key.upper())
        b.inputs["Base Color"].default_value = (*col, 1)
        b.inputs["Roughness"].default_value = 0.42
        b.inputs["Subsurface Weight"].default_value = 0.06
        MAT[key] = m

    # dark soil / planter
    m, nt, b = _new_mat("SOIL")
    b.inputs["Base Color"].default_value = (0.10, 0.055, 0.03, 1)
    b.inputs["Roughness"].default_value = 0.95
    n = _noise(nt, 35.0, 6.0, 0.6, (-450, -100))
    nt.links.new(_bump(nt, n.outputs["Fac"], 0.3, 0.05).outputs["Normal"],
                 b.inputs["Normal"])
    MAT["soil"] = m

    # LED screen — vertical turquoise/magenta light bars with dark gaps
    m, nt, b = _new_mat("LED_SCREEN")
    b.inputs["Base Color"].default_value = (0.005, 0.008, 0.012, 1)
    b.inputs["Roughness"].default_value = 0.34
    b.inputs["Emission Strength"].default_value = 0.75
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-900, 0)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (-700, 120)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 2.3
    wave.inputs["Distortion"].default_value = 0.55
    wave.inputs["Detail"].default_value = 2.0
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.location = (-400, 0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.0, 0.020, 0.035, 1)
    ramp.color_ramp.elements[1].position = 0.88
    ramp.color_ramp.elements[1].color = (0.02, 0.62, 0.56, 1)
    for pos, col in ((0.16, (0.0, 0.26, 0.28, 1)),
                     (0.30, (0.0, 0.05, 0.07, 1)),
                     (0.44, (0.36, 0.01, 0.14, 1)),
                     (0.55, (0.72, 0.04, 0.26, 1)),
                     (0.64, (0.02, 0.01, 0.06, 1)),
                     (0.76, (0.0, 0.40, 0.42, 1)),
                     (0.84, (0.0, 0.06, 0.08, 1))):
        e = ramp.color_ramp.elements.new(pos)
        e.color = col
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Emission Color"])
    MAT["led"] = m

    m, nt, b = _new_mat("SIGN_NEON")
    b.inputs["Base Color"].default_value = (0.02, 0.05, 0.06, 1)
    b.inputs["Emission Color"].default_value = (0.2, 1.0, 0.9, 1)
    b.inputs["Emission Strength"].default_value = 2.2
    MAT["neon"] = m

    m, nt, b = _new_mat("WARM_EMIT")
    b.inputs["Base Color"].default_value = (1.0, 0.85, 0.60, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.78, 0.48, 1)
    b.inputs["Emission Strength"].default_value = 3.0
    MAT["white_emit"] = m

    m, nt, b = _new_mat("SIGN_PINK")
    b.inputs["Base Color"].default_value = (0.08, 0.01, 0.04, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.18, 0.45, 1)
    b.inputs["Emission Strength"].default_value = 2.5
    MAT["neon_pink"] = m

    for m in MAT.values():
        m.use_fake_user = True
    return MAT


# ------------------------------------------------------------------ geometry

def _link(ob, coll):
    c = coll or COLL.get("SETUP") or bpy.context.scene.collection
    c.objects.link(ob)
    return ob


def _finish(ob, name, mat, coll, bevel=0.0, smooth=False, bevel_seg=2):
    ob.name = name
    if mat:
        ob.data.materials.append(mat)
    _link(ob, coll)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    if bevel > 0:
        md = ob.modifiers.new("BEVEL", "BEVEL")
        md.width = bevel
        md.segments = bevel_seg
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(35)
        md.harden_normals = True
        wn = ob.modifiers.new("WEIGHTED_NORMAL", "WEIGHTED_NORMAL")
        wn.keep_sharp = True
    return ob


def box(name, size, loc, mat, coll=None, rot=(0, 0, 0), bevel=0.0,
        smooth=False, bevel_seg=2):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return _finish(ob, name, mat, coll, bevel, smooth, bevel_seg)


def cyl(name, radius, depth, loc, mat, coll=None, verts=24, rot=(0, 0, 0),
        r2=None, smooth=True):
    bm = bmesh.new()
    r2 = radius if r2 is None else r2
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=radius, radius2=r2, depth=depth)
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return _finish(ob, name, mat, coll, 0.0, smooth)


def sphere(name, radius, loc, mat, coll=None, seg=20, rings=12,
           scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings,
                              radius=radius)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return _finish(ob, name, mat, coll, 0.0, True)


def ico(name, radius, loc, mat, coll=None, sub=1, scale=(1, 1, 1),
        rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=radius)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return _finish(ob, name, mat, coll, 0.0, False)


def torus(name, major, minor, loc, mat, coll=None, mseg=48, nseg=10,
          rot=(0, 0, 0)):
    bm = bmesh.new()
    for i in range(mseg):
        a = math.tau * i / mseg
        ca, sa = math.cos(a), math.sin(a)
        for j in range(nseg):
            b = math.tau * j / nseg
            rr = major + minor * math.cos(b)
            bm.verts.new((rr * ca, rr * sa, minor * math.sin(b)))
    bm.verts.ensure_lookup_table()
    for i in range(mseg):
        for j in range(nseg):
            v0 = i * nseg + j
            v1 = ((i + 1) % mseg) * nseg + j
            v2 = ((i + 1) % mseg) * nseg + (j + 1) % nseg
            v3 = i * nseg + (j + 1) % nseg
            bm.faces.new((bm.verts[v0], bm.verts[v1],
                          bm.verts[v2], bm.verts[v3]))
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    ob.data.materials.append(mat)
    _link(ob, coll)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def curve_tube(name, points, radius, mat, coll=None, cyclic=False,
               res=6, bevel_res=2, location=(0, 0, 0), rotation=(0, 0, 0)):
    cu = bpy.data.curves.new(name + "_C", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.fill_mode = "FULL"
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    ob.location = location
    ob.rotation_euler = Euler(rotation)
    _link(ob, coll)
    return ob


def mesh_obj(name, verts, faces, mat, coll=None, loc=(0, 0, 0),
             rot=(0, 0, 0), smooth=True, bevel=0.0):
    me = bpy.data.meshes.new(name + "_M")
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    return _finish(ob, name, mat, coll, bevel, smooth)


def parametric_surface(name, func, u_range, v_range, nu, nv, mat, coll,
                       loc=(0, 0, 0), rot=(0, 0, 0), smooth=True,
                       bevel=0.0):
    verts = []
    for i in range(nu + 1):
        u = u_range[0] + (u_range[1] - u_range[0]) * i / nu
        for j in range(nv + 1):
            v = v_range[0] + (v_range[1] - v_range[0]) * j / nv
            verts.append(func(u, v))
    faces = []
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            b = (i + 1) * (nv + 1) + j
            c = (i + 1) * (nv + 1) + j + 1
            d = i * (nv + 1) + j + 1
            faces.append((a, b, c, d))
    return mesh_obj(name, verts, faces, mat, coll, loc, rot, smooth, bevel)


def load_font(name):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return bpy.data.fonts.load(p, check_existing=True)
    return None


def text_mesh(name, body, font_name, size, loc, rot, mat, coll=None,
              extrude=0.03, bevel=0.006, align="CENTER", spacing=1.0):
    font = load_font(font_name)
    cu = bpy.data.curves.new(name + "_C", type="FONT")
    cu.body = body
    if font:
        cu.font = font
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.space_character = spacing
    cu.materials.append(mat)
    tmp = bpy.data.objects.new(name + "_TMP", cu)
    coll = coll or COLL.get("SIGNAGE")
    coll.objects.link(tmp)
    tmp.location = loc
    tmp.rotation_euler = Euler(rot)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = tmp.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    me.materials.clear()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    _link(ob, coll)
    bpy.data.objects.remove(tmp, do_unlink=True)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def make_camera(name, loc, target, lens=28.0, coll=None):
    cd = bpy.data.cameras.new(name + "_D")
    cd.lens = lens
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.05
    cd.clip_end = 300
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    look_at(ob, target)
    _link(ob, coll or COLL.get("CAMERAS"))
    return ob


def area_light(name, loc, target, energy, size, color=(1, 1, 1),
               coll=None, shape="SQUARE"):
    ld = bpy.data.lights.new(name + "_D", "AREA")
    ld.energy = energy
    ld.shape = shape
    ld.size = size
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    look_at(ob, target)
    _link(ob, coll or COLL.get("FILL"))
    return ob


def sun_light(name, rotation, energy=4.0, angle=0.1, color=(1, 0.95, 0.86)):
    ld = bpy.data.lights.new(name + "_D", "SUN")
    ld.energy = energy
    ld.angle = angle
    ld.color = color
    ob = bpy.data.objects.new(name, ld)
    ob.rotation_euler = Euler(rotation)
    _link(ob, COLL.get("SUN"))
    return ob


def save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)


def render_to(path, cam, res=(1920, 1080), samples=64, frame=1):
    sc = bpy.context.scene
    old = (sc.camera, sc.render.resolution_x, sc.render.resolution_y,
           sc.eevee.taa_render_samples, sc.render.filepath)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.eevee.taa_render_samples = samples
    sc.render.filepath = path
    sc.frame_set(frame)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    sc.camera, sc.render.resolution_x, sc.render.resolution_y, \
        sc.eevee.taa_render_samples, sc.render.filepath = old
    print("RENDER", path)
