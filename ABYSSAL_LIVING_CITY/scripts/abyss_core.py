"""
THE ABYSSAL LIVING CITY - PROJECT 10
abyss_core.py : scene, collections, material library, primitive kit, asset pipeline

Blender 5.2 / EEVEE Next.  Every module is exec()'d into one shared namespace by
Abyssal_Living_City_Build.py, so functions defined here are visible everywhere.

All modelling is bmesh-only: no bpy.ops and no bpy.context.object / selected_objects.
The MCP sandbox does not expose those reliably, and this keeps builds deterministic.
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector

BASE_DIR = globals().get("BASE_DIR") or r"D:\Tes Animasi-Motion-Blender\ABYSSAL_LIVING_CITY"
TAU = math.pi * 2.0
RNG = random.Random(20261101)

# World scale --------------------------------------------------------------
CITY_W = 100.0          # east-west span of the plateau
CITY_D = 85.0           # north-south span
PLATEAU_RX = 52.0
PLATEAU_RY = 44.0
ABYSS_Z = -30.0         # open abyssal plain beyond the drop-off
FLOOR_Z = -1.0          # nominal city floor level


# ---------------------------------------------------------------- math
def clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(a, b, x):
    if a == b:
        return 0.0 if x < a else 1.0
    t = clamp((x - a) / (b - a))
    return t * t * (3.0 - 2.0 * t)


def _hash2(i, j, seed=0):
    h = (i * 374761393 + j * 668265263 + seed * 144665) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0xFFFFFF)


def vnoise(x, y, seed=0):
    xi, yi = math.floor(x), math.floor(y)
    xf, yf = x - xi, y - yi
    u = xf * xf * (3.0 - 2.0 * xf)
    v = yf * yf * (3.0 - 2.0 * yf)
    a = _hash2(xi, yi, seed)
    b = _hash2(xi + 1, yi, seed)
    c = _hash2(xi, yi + 1, seed)
    d = _hash2(xi + 1, yi + 1, seed)
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v


def fbm(x, y, seed=0, octaves=4):
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for o in range(octaves):
        total += vnoise(x * freq, y * freq, seed + o * 17) * amp
        norm += amp
        amp *= 0.5
        freq *= 2.03
    return total / norm


def _s2l(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip("#")
    return tuple(_s2l(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4))


# ---------------------------------------------------------------- palette
PAL = {
    # engineered
    "navy":        "#16233A",
    "navy_lt":     "#25375B",
    "titanium":    "#9BA8B4",
    "alu":         "#C3CBD2",
    "steel":       "#2B3540",
    "steel_lt":    "#55636F",
    "ceramic":     "#E8EDEC",
    "composite":   "#2F4F6B",
    "composite_lt": "#4E7391",
    "deck":        "#38424C",
    "rubber":      "#1A1E22",
    # emissive
    "cyan":        "#48E9FF",
    "teal":        "#2FD9C4",
    "amber":       "#FFAE43",
    "green":       "#86F08A",
    "warm":        "#FFD2A0",
    "magenta":     "#FF6BC8",
    # natural
    "sand_dk":     "#6A6355",
    "sand_lt":     "#8C8271",
    "rock_dk":     "#262C33",
    "rock_mid":    "#3C444D",
    "rock_lt":     "#565F69",
    "kelp":        "#2C6B47",
    "kelp_lt":     "#469A5E",
    "seagrass":    "#3B7A4F",
    "algae":       "#4E7A5C",
    "coral_pink":  "#F2738F",
    "coral_orange": "#F0975A",
    "coral_purple": "#9C79C8",
    "coral_blue":  "#4FA8D8",
    "coral_lime":  "#93D95C",
    "bio_cyan":    "#63F0E0",
    "bio_violet":  "#9A7BFF",
    # people
    "skin_1":      "#F2C9A0",
    "skin_2":      "#D9A377",
    "skin_3":      "#A9714A",
    "skin_4":      "#7A4B2E",
    "hair_dark":   "#2A211C",
    "hair_brown":  "#4A3222",
    "hair_grey":   "#8E8A85",
}

MAT = {}
FOG_COLOR = "#0D2C42"


# ---------------------------------------------------------------- materials
def _bsdf(m):
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def make_mat(name, hexv, metallic=0.0, rough=0.6, emit=None, estr=0.0, alpha=1.0,
             coat=0.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = _bsdf(m)
    col = hexcol(hexv)
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*hexcol(emit), 1.0)
        b.inputs["Emission Strength"].default_value = estr
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try:
                setattr(m, attr, val)
            except Exception:
                pass
        try:
            m.use_transparent_shadow = True
        except Exception:
            pass
    m.diffuse_color = (*col, 1.0)
    return m


def make_glass(name, hexv, a_front=0.08, a_edge=0.60, rough=0.05, rim=0.0,
               rim_col="#48E9FF"):
    """Fresnel-driven alpha: nearly clear head-on, tinted and reflective at grazing.

    This is what makes a transparent dome read as glass instead of plastic wrap.
    Refraction is deliberately off - a stack of refracting domes is unreadable.
    """
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tf = nt.nodes.new("ShaderNodeBsdfTransparent")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.30
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["From Min"].default_value = 0.0
    rng.inputs["From Max"].default_value = 1.0
    rng.inputs["To Min"].default_value = a_front
    rng.inputs["To Max"].default_value = a_edge
    nt.links.new(lw.outputs["Facing"], rng.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(rng.outputs["Result"], mix.inputs["Fac"])
    nt.links.new(tf.outputs["BSDF"], mix.inputs[1])
    b.inputs["Base Color"].default_value = (*hexcol(hexv), 1.0)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = 1.45
    if rim > 0.0 and "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value = (*hexcol(rim_col), 1.0)
        # glow only where the shell turns edge-on
        erng = nt.nodes.new("ShaderNodeMapRange")
        erng.inputs["From Min"].default_value = 0.55
        erng.inputs["From Max"].default_value = 1.0
        erng.inputs["To Min"].default_value = 0.0
        erng.inputs["To Max"].default_value = rim
        nt.links.new(lw.outputs["Facing"], erng.inputs["Value"])
        nt.links.new(erng.outputs["Result"], b.inputs["Emission Strength"])
    nt.links.new(b.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    for attr, val in (("show_transparent_back", False),
                      ("use_transparent_shadow", False),
                      ("use_backface_culling", False),
                      ("use_screen_refraction", False),
                      ("use_raytrace_refraction", False)):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    m.diffuse_color = (*hexcol(hexv), 0.25)
    return m


def build_materials():
    mk = make_mat
    # --- structural metals ------------------------------------------------
    MAT["navy"] = mk("MAT_METAL_NAVY", PAL["navy"], 0.85, 0.42)
    MAT["navy_lt"] = mk("MAT_METAL_NAVY_LIGHT", PAL["navy_lt"], 0.80, 0.38)
    MAT["titanium"] = mk("MAT_TITANIUM", PAL["titanium"], 1.0, 0.28)
    MAT["alu"] = mk("MAT_ALUMINIUM", PAL["alu"], 1.0, 0.34)
    MAT["steel"] = mk("MAT_STEEL_DARK", PAL["steel"], 0.90, 0.46)
    MAT["steel_lt"] = mk("MAT_STEEL_LIGHT", PAL["steel_lt"], 0.92, 0.38)
    MAT["ceramic"] = mk("MAT_CERAMIC_WHITE", PAL["ceramic"], 0.0, 0.34, coat=0.4)
    MAT["composite"] = mk("MAT_COMPOSITE_BLUE", "#3C5F82", 0.25, 0.46)
    # district accents: the city was reading as one grey material
    MAT["ceramic_warm"] = mk("MAT_CERAMIC_WARM", "#C6A077", 0.0, 0.54)
    MAT["paint_ochre"] = mk("MAT_PAINT_OCHRE", "#B98A3E", 0.30, 0.40)
    MAT["paint_teal"] = mk("MAT_PAINT_TEAL", "#2E7E85", 0.25, 0.44)
    MAT["composite_lt"] = mk("MAT_COMPOSITE_BLUE_LT", PAL["composite_lt"], 0.20, 0.44)
    MAT["deck"] = mk("MAT_DECK_PLATE", PAL["deck"], 0.70, 0.52)
    MAT["rubber"] = mk("MAT_RUBBER", PAL["rubber"], 0.0, 0.88)
    MAT["concrete"] = mk("MAT_CONCRETE_SUBSEA", "#7C7B72", 0.0, 0.86)
    MAT["floor_hab"] = mk("MAT_FLOOR_HABITAT", "#8A8578", 0.0, 0.78,
                          PAL["warm"], 0.55)
    MAT["paint_w"] = mk("MAT_PAINT_WHITE", "#E9EDEA", 0.0, 0.44)
    MAT["paint_safe"] = mk("MAT_PAINT_SAFETY", "#D8A32F", 0.0, 0.50)
    # --- glass ------------------------------------------------------------
    MAT["glass_dome"] = make_glass("MAT_GLASS_DOME", "#9FDDE6", 0.042, 0.46, 0.05,
                                   0.45, PAL["cyan"])
    MAT["glass_win"] = make_glass("MAT_GLASS_WINDOW", "#5FA6B8", 0.16, 0.72, 0.08)
    MAT["glass_tube"] = make_glass("MAT_GLASS_TUNNEL", "#7FCFDA", 0.11, 0.62, 0.06,
                                   0.35, PAL["teal"])
    MAT["glass_dark"] = make_glass("MAT_GLASS_VEHICLE", "#31596B", 0.42, 0.88, 0.10)
    # --- emissive ---------------------------------------------------------
    def em(key, hexv, strength):
        MAT[key] = mk("MAT_EMIT_" + key.upper(), hexv, 0.0, 0.30, hexv, strength)
    em("emit_cyan", PAL["cyan"], 9.0)
    em("emit_teal", PAL["teal"], 7.0)
    em("emit_amber", PAL["amber"], 8.0)
    em("emit_green", PAL["green"], 6.0)
    em("emit_warm", PAL["warm"], 5.0)
    em("emit_magenta", PAL["magenta"], 7.0)
    em("emit_white", "#F2FBFF", 12.0)
    em("bio_cyan", PAL["bio_cyan"], 3.2)
    em("bio_violet", PAL["bio_violet"], 2.8)
    MAT["snow"] = mk("MAT_MARINE_SNOW", "#B9D6DE", 0.0, 0.70, "#9FD8E0", 0.22)
    # --- natural ----------------------------------------------------------
    MAT["sand"] = mk("MAT_SEABED_SAND", PAL["sand_lt"], 0.0, 0.90)
    MAT["sand_dk"] = mk("MAT_SEABED_SAND_DARK", PAL["sand_dk"], 0.0, 0.92)
    MAT["rock"] = mk("MAT_ROCK_MID", PAL["rock_mid"], 0.0, 0.88)
    MAT["rock_dk"] = mk("MAT_ROCK_DARK", PAL["rock_dk"], 0.0, 0.90)
    MAT["rock_lt"] = mk("MAT_ROCK_LIGHT", PAL["rock_lt"], 0.0, 0.86)
    MAT["kelp"] = mk("MAT_KELP", PAL["kelp"], 0.0, 0.72)
    MAT["kelp_lt"] = mk("MAT_KELP_LIGHT", PAL["kelp_lt"], 0.0, 0.70)
    MAT["seagrass"] = mk("MAT_SEAGRASS", PAL["seagrass"], 0.0, 0.78)
    MAT["algae"] = mk("MAT_ALGAE", PAL["algae"], 0.0, 0.84)
    MAT["coral_pink"] = mk("MAT_CORAL_PINK", PAL["coral_pink"], 0.0, 0.58)
    MAT["coral_orange"] = mk("MAT_CORAL_ORANGE", PAL["coral_orange"], 0.0, 0.58)
    MAT["coral_purple"] = mk("MAT_CORAL_PURPLE", PAL["coral_purple"], 0.0, 0.58)
    MAT["coral_blue"] = mk("MAT_CORAL_BLUE", PAL["coral_blue"], 0.0, 0.58)
    MAT["coral_lime"] = mk("MAT_CORAL_LIME", PAL["coral_lime"], 0.0, 0.58)
    # --- people -----------------------------------------------------------
    for i, h in enumerate(("#F2C9A0", "#D9A377", "#A9714A", "#7A4B2E"), 1):
        MAT["skin_%d" % i] = mk("MAT_SKIN_%d" % i, h, 0.0, 0.62)
    MAT["hair_dark"] = mk("MAT_HAIR_DARK", PAL["hair_dark"], 0.0, 0.72)
    MAT["hair_brown"] = mk("MAT_HAIR_BROWN", PAL["hair_brown"], 0.0, 0.72)
    MAT["hair_grey"] = mk("MAT_HAIR_GREY", PAL["hair_grey"], 0.0, 0.72)
    for i, h in enumerate(("#E7EDF2", "#4C7396", "#2F8C86", "#D9A03C",
                           "#B8553F", "#3E4E60", "#7A6BA8", "#5E8A5A",
                           "#C26E8E", "#8A94A0")):
        MAT["cloth_%d" % i] = mk("MAT_CLOTH_%02d" % i, h, 0.0, 0.88)
    for i, h in enumerate(("#2B3440", "#3E4652", "#4A4438", "#243038", "#514A56")):
        MAT["pants_%d" % i] = mk("MAT_PANTS_%02d" % i, h, 0.0, 0.90)
    # --- interior / furnishing -------------------------------------------
    MAT["wood"] = mk("MAT_WOOD_HABITAT", "#A0703F", 0.0, 0.62)
    MAT["wood_lt"] = mk("MAT_WOOD_LIGHT_HAB", "#C99A64", 0.0, 0.60)
    MAT["fabric_red"] = mk("MAT_FABRIC_RED", "#B4524A", 0.0, 0.90)
    MAT["fabric_blue"] = mk("MAT_FABRIC_BLUE", "#3F5E82", 0.0, 0.90)
    MAT["fabric_grey"] = mk("MAT_FABRIC_GREY", "#8A9199", 0.0, 0.90)
    MAT["plant"] = mk("MAT_PLANT_GREEN", "#3E8A52", 0.0, 0.74)
    MAT["plant_dk"] = mk("MAT_PLANT_DARK", "#2A5F3C", 0.0, 0.78)
    MAT["emit_shop"] = mk("MAT_EMIT_SHOP_WARM", "#FFD9A6", 0.0, 0.30,
                          "#FFD9A6", 3.2)
    MAT["emit_shop2"] = mk("MAT_EMIT_SHOP_BRIGHT", "#FFE0B0", 0.0, 0.28,
                          "#FFE0B0", 2.2)
    MAT["emit_room"] = mk("MAT_EMIT_ROOM", "#FFE6C4", 0.0, 0.30,
                          "#FFE6C4", 1.8)
    MAT["emit_screen"] = mk("MAT_EMIT_SCREEN", "#7FD8FF", 0.0, 0.22,
                            "#7FD8FF", 2.6)
    MAT["glow_strip"] = mk("MAT_GLOW_STRIP", "#BFEFFF", 0.0, 0.25,
                           "#BFEFFF", 4.0)
    build_seabed_mat()
    build_water_mat()


def build_seabed_mat():
    """Vertex-colour seabed + procedural caustics + fine sediment bump."""
    m = bpy.data.materials.get("MAT_SEABED") or bpy.data.materials.new("MAT_SEABED")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "terr_col"
    nt.links.new(attr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Metallic"].default_value = 0.0

    # caustics: voronoi cell edges, only on upward faces NEAR THE CITY.
    # Without the height mask the pattern also lands on the abyssal plain, where
    # there is no light to make caustics - it reads as a hex grid painted on the
    # floor and destroys the sense of depth.
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.voronoi_dimensions = "3D"
    try:
        vor.feature = "DISTANCE_TO_EDGE"
    except Exception:
        pass
    vor.inputs["Scale"].default_value = 0.30
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    tex = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tex.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], vor.inputs["Vector"])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(vor.outputs["Distance"], inv.inputs[1])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 11.0
    nt.links.new(inv.outputs[0], pw.inputs[0])
    # mask 1: upward facing only
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs["Vector"])
    mask = nt.nodes.new("ShaderNodeMapRange")
    mask.inputs["From Min"].default_value = 0.45
    mask.inputs["From Max"].default_value = 0.95
    mask.inputs["To Min"].default_value = 0.0
    mask.inputs["To Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], mask.inputs["Value"])
    # mask 2: only where light actually reaches the floor
    psep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], psep.inputs["Vector"])
    hmask = nt.nodes.new("ShaderNodeMapRange")
    hmask.inputs["From Min"].default_value = -22.0
    hmask.inputs["From Max"].default_value = -5.0
    hmask.inputs["To Min"].default_value = 0.0
    hmask.inputs["To Max"].default_value = 1.0
    nt.links.new(psep.outputs["Z"], hmask.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(pw.outputs[0], m1.inputs[0])
    nt.links.new(mask.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(hmask.outputs["Result"], m2.inputs[1])
    gain = nt.nodes.new("ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 0.055
    nt.links.new(m2.outputs[0], gain.inputs[0])
    ccol = nt.nodes.new("ShaderNodeMixRGB")
    ccol.blend_type = "ADD"
    ccol.inputs["Color2"].default_value = (*hexcol("#BFE8E4"), 1.0)
    nt.links.new(attr.outputs["Color"], ccol.inputs["Color1"])
    nt.links.new(gain.outputs[0], ccol.inputs["Fac"])
    nt.links.new(ccol.outputs["Color"], b.inputs["Base Color"])

    # sediment bump
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 6.5
    n1.inputs["Detail"].default_value = 7.0
    n1.inputs["Roughness"].default_value = 0.62
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 34.0
    n2.inputs["Detail"].default_value = 5.0
    b1 = nt.nodes.new("ShaderNodeBump")
    b1.inputs["Strength"].default_value = 0.30
    b1.inputs["Distance"].default_value = 0.22
    nt.links.new(n1.outputs["Fac"], b1.inputs["Height"])
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.14
    b2.inputs["Distance"].default_value = 0.06
    nt.links.new(n2.outputs["Fac"], b2.inputs["Height"])
    nt.links.new(b1.outputs["Normal"], b2.inputs["Normal"])
    nt.links.new(b2.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    MAT["seabed"] = m


def build_water_mat():
    """A distant water-surface plane seen from below, if the camera ever tilts up."""
    m = bpy.data.materials.get("MAT_WATER_SURFACE") or bpy.data.materials.new("MAT_WATER_SURFACE")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*hexcol("#2A7FA8"), 1.0)
    b.inputs["Roughness"].default_value = 0.12
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    MAT["water_surface"] = m


# ---------------------------------------------------------------- collections
COLLS = {}
ROOT = None

COLL_NAMES = [
    ("01_TERRAIN_SEABED", "TERRAIN"),
    ("02_OCEAN_ENVIRONMENT", "OCEAN"),
    ("03_CENTRAL_HABITAT", "CENTRAL"),
    ("04_RESIDENTIAL_DISTRICT", "RESIDENTIAL"),
    ("05_COMMERCIAL_DISTRICT", "COMMERCIAL"),
    ("06_UNDERWATER_RESORT", "RESORT"),
    ("07_RESEARCH_DISTRICT", "RESEARCH"),
    ("08_INDUSTRIAL_DISTRICT", "INDUSTRIAL"),
    ("09_SUBMARINE_HARBOR", "HARBOR"),
    ("10_AGRICULTURE_DISTRICT", "AGRI"),
    ("11_PUBLIC_FACILITIES", "PUBLIC"),
    ("12_HUMAN_POPULATION", "PEOPLE"),
    ("13_MARINE_WILDLIFE", "WILDLIFE"),
    ("14_CORAL_REEFS", "CORAL"),
    ("15_MARINE_VEGETATION", "VEG"),
    ("16_TRANSPORT_INFRASTRUCTURE", "TRANSPORT"),
    ("17_ENVIRONMENTAL_PROPS", "PROPS"),
    ("18_LIGHTING", "LIGHT"),
    ("19_CAMERAS", "CAMERAS"),
    ("20_REFERENCE_AND_HELPERS", "HELPERS"),
]


def build_collections():
    global ROOT
    root = bpy.data.collections.get("ABYSSAL_LIVING_CITY")
    if root is None:
        root = bpy.data.collections.new("ABYSSAL_LIVING_CITY")
    if root.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(root)
    ROOT = root
    for full, key in COLL_NAMES:
        c = bpy.data.collections.get(full)
        if c is None:
            c = bpy.data.collections.new(full)
            root.children.link(c)
        COLLS[key] = c
    for full, key in (("00_ASSET_LIBRARY", "LIB"), ("00_WORKSPACE", "WORK")):
        c = bpy.data.collections.get(full)
        if c is None:
            c = bpy.data.collections.new(full)
            root.children.link(c)
        c.hide_render = True
        if key == "LIB":
            c.hide_viewport = True
        COLLS[key] = c
    try:
        vl = bpy.context.view_layer
        vl.active_layer_collection = vl.layer_collection
        vl.update()
    except Exception as e:
        print("layer collection reset failed", repr(e))


def C(key):
    return COLLS[key]


# ---------------------------------------------------------------- scene
def setup_scene():
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            continue
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False
    for attr, val in (("taa_render_samples", 64), ("use_raytracing", True),
                      ("use_shadows", True), ("volumetric_tile_size", "8"),
                      ("volumetric_samples", 64), ("volumetric_end", 420.0),
                      ("volumetric_start", 4.0),
                      ("volumetric_sample_distribution", 0.92)):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        pass
    sc.view_settings.exposure = 0.35
    # static world: one frame, always
    sc.frame_start = 1
    sc.frame_end = 1
    sc.frame_set(1)
    return sc


def build_world():
    w = bpy.data.worlds.get("AB_World") or bpy.data.worlds.new("AB_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    # vertical gradient: light from above, black water below
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Incoming"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.95
    mr.inputs["From Max"].default_value = 0.15
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position = 0.0
    el[0].color = (*hexcol("#0A2130"), 1.0)
    el[1].position = 1.0
    el[1].color = (*hexcol("#63C6E2"), 1.0)
    e = el.new(0.46)
    e.color = (*hexcol("#1B4E66"), 1.0)
    e2 = el.new(0.72)
    e2.color = (*hexcol("#2E86A9"), 1.0)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.15
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    MAT["world"] = w
    return w


def build_compositor():
    """Depth fog + bloom.  The fog is what sells an underwater medium."""
    sc = bpy.context.scene
    try:
        old = bpy.data.node_groups.get("AB_Compositing")
        if old:
            bpy.data.node_groups.remove(old)
        ng = bpy.data.node_groups.new("AB_Compositing", "CompositorNodeTree")
        try:
            ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        except Exception:
            pass
        sc.compositing_node_group = ng
        sc.use_nodes = True
        try:
            bpy.context.view_layer.use_pass_z = True
        except Exception:
            pass
        rl = ng.nodes.new("CompositorNodeRLayers")
        # --- depth fog from the MIST pass.
        # The Z pass is not reliably in world units across engines; Mist is driven
        # by world.mist_settings, whose start/depth are unambiguously in BU.
        try:
            bpy.context.view_layer.use_pass_mist = True
        except Exception:
            pass
        mr = ng.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 0.0
        mr.inputs["To Max"].default_value = 1.0
        try:
            mr.interpolation_type = "SMOOTHSTEP"
        except Exception:
            pass
        ng.links.new(rl.outputs["Mist"], mr.inputs["Value"])
        fogc = ng.nodes.new("ShaderNodeMixRGB")
        fogc.blend_type = "MIX"
        fogc.inputs["Color2"].default_value = (*hexcol(FOG_COLOR), 1.0)
        ng.links.new(rl.outputs["Image"], fogc.inputs["Color1"])
        ng.links.new(mr.outputs["Result"], fogc.inputs["Fac"])
        # --- bloom for emissives
        glare = ng.nodes.new("CompositorNodeGlare")
        try:
            glare.inputs["Type"].default_value = "Bloom"
            glare.inputs["Quality"].default_value = "High"
        except Exception:
            pass
        glare.inputs["Threshold"].default_value = 1.10
        glare.inputs["Strength"].default_value = 0.30
        glare.inputs["Size"].default_value = 0.42
        ng.links.new(fogc.outputs["Color"], glare.inputs["Image"])
        # --- grade
        cb = ng.nodes.new("CompositorNodeColorBalance")
        try:
            cb.inputs["Lift"].default_value = (0.97, 1.00, 1.06, 1.0)
            cb.inputs["Gamma"].default_value = (1.00, 1.00, 1.00, 1.0)
            cb.inputs["Gain"].default_value = (1.05, 1.00, 0.94, 1.0)
        except Exception:
            pass
        ng.links.new(glare.outputs["Image"], cb.inputs["Image"])
        # --- vignette
        em = ng.nodes.new("CompositorNodeEllipseMask")
        try:
            em.inputs["Size"].default_value = (0.90, 0.90)
        except Exception:
            pass
        blur = ng.nodes.new("CompositorNodeBlur")
        try:
            blur.inputs["Size"].default_value = (260, 260)
        except Exception:
            pass
        ng.links.new(em.outputs["Mask"], blur.inputs["Image"])
        # invert: mask is 1 inside the ellipse, we want the corners darkened
        inv = ng.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        ng.links.new(blur.outputs["Image"], inv.inputs[1])
        vig = ng.nodes.new("ShaderNodeMixRGB")
        vig.blend_type = "MULTIPLY"
        vig.inputs["Color2"].default_value = (0.58, 0.58, 0.62, 1.0)
        ng.links.new(cb.outputs["Image"], vig.inputs["Color1"])
        ng.links.new(inv.outputs[0], vig.inputs["Fac"])
        outn = ng.nodes.new("NodeGroupOutput")
        ng.links.new(vig.outputs["Color"], outn.inputs[0])
        print("COMPOSITOR OK")
    except Exception as e:
        import traceback
        print("COMPOSITOR SKIPPED:", repr(e))
        print(traceback.format_exc()[-1200:])


# ---------------------------------------------------------------- primitives
def _res(coll):
    """Accept either a collection object or its short key ('WORK', 'CENTRAL')."""
    return C(coll) if isinstance(coll, str) else coll


def _obj(name, bm, mat, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
         smooth=True, smooth_cut=None):
    coll = _res(coll)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    if smooth_cut is not None:
        for p in me.polygons:
            p.use_smooth = abs(p.normal.z) < smooth_cut
    elif smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def _bm_tube(r1, r2, d, sides, cap=True):
    bm = bmesh.new()
    lo, hi = [], []
    for i in range(sides):
        a = i * TAU / sides
        c, s = math.cos(a), math.sin(a)
        lo.append(bm.verts.new((c * r1, s * r1, -d * 0.5)))
        hi.append(bm.verts.new((c * r2, s * r2, d * 0.5)))
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if cap:
        if r1 > 1e-5:
            bm.faces.new(list(reversed(lo)))
        if r2 > 1e-5:
            bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _bm_sphere(r, seg, rings):
    bm = bmesh.new()
    rows = []
    for j in range(1, rings):
        phi = math.pi * j / rings
        rr = math.sin(phi) * r
        z = math.cos(phi) * r
        rows.append([bm.verts.new((math.cos(i * TAU / seg) * rr,
                                   math.sin(i * TAU / seg) * rr, z))
                     for i in range(seg)])
    top = bm.verts.new((0, 0, r))
    bot = bm.verts.new((0, 0, -r))
    for a, b in zip(rows, rows[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((top, rows[0][j], rows[0][i]))
        bm.faces.new((bot, rows[-1][i], rows[-1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def _bm_torus(major, minor, mseg, nseg, arc=TAU, phase=0.0):
    bm = bmesh.new()
    rows = []
    closed = abs(arc - TAU) < 1e-6
    count = mseg if closed else mseg + 1
    for i in range(count):
        a = phase + i * arc / mseg
        c, s = math.cos(a), math.sin(a)
        ring = []
        for j in range(nseg):
            b = j * TAU / nseg
            rr = major + math.cos(b) * minor
            ring.append(bm.verts.new((c * rr, s * rr, math.sin(b) * minor)))
        rows.append(ring)
    span = len(rows) if closed else len(rows) - 1
    for i in range(span):
        a = rows[i]
        b = rows[(i + 1) % len(rows)]
        for j in range(nseg):
            k = (j + 1) % nseg
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def box(name, size, loc, mat, coll, rot=(0, 0, 0), smooth=False):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _obj(name, bm, mat, coll, loc, rot, smooth=smooth)


def cyl(name, r, d, loc, mat, coll, rot=(0, 0, 0), verts=16, smooth=True, r2=None):
    ob = _obj(name, _bm_tube(r, r if r2 is None else r2, d, verts), mat, coll, loc, rot,
              smooth_cut=0.72 if smooth else None)
    if not smooth:
        for p in ob.data.polygons:
            p.use_smooth = False
    return ob


def cone(name, r1, r2, d, loc, mat, coll, rot=(0, 0, 0), verts=16, smooth=True):
    ob = _obj(name, _bm_tube(r1, r2, d, verts), mat, coll, loc, rot,
              smooth_cut=0.72 if smooth else None)
    if not smooth:
        for p in ob.data.polygons:
            p.use_smooth = False
    return ob


def sphere(name, r, loc, mat, coll, seg=16, rings=10, scale=(1, 1, 1), rot=(0, 0, 0)):
    return _obj(name, _bm_sphere(r, seg, rings), mat, coll, loc, rot, scale, smooth=True)


def ico(name, r, loc, mat, coll, sub=1, scale=(1, 1, 1), rot=(0, 0, 0), flat=False):
    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    except TypeError:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, diameter=r * 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _obj(name, bm, mat, coll, loc, rot, scale, smooth=not flat)


def torus(name, major, minor, loc, mat, coll, rot=(0, 0, 0), mseg=32, nseg=8,
          arc=TAU, phase=0.0):
    return _obj(name, _bm_torus(major, minor, mseg, nseg, arc, phase), mat, coll, loc, rot,
                smooth=True)


def align_z(ob, direction):
    ob.rotation_euler = Vector(direction).normalized().to_track_quat("Z", "Y").to_euler()


def tube_between(name, p0, p1, r0, r1, mat, coll, sides=8):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ln = d.length
    if ln < 1e-5:
        return None
    ob = cone(name, r0, r1, ln, (p0 + p1) * 0.5, mat, coll, verts=sides, smooth=True)
    align_z(ob, d)
    return ob


def loft(name, rings, mat, coll, close_start=True, close_end=True, smooth=True):
    coll = _res(coll)
    bm = bmesh.new()
    vrings = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    bm.verts.ensure_lookup_table()
    n = len(vrings[0])
    for a, b in zip(vrings, vrings[1:]):
        for i in range(n):
            j = (i + 1) % n
            try:
                bm.faces.new((a[i], a[j], b[j], b[i]))
            except ValueError:
                pass
    if close_start:
        try:
            bm.faces.new(list(reversed(vrings[0])))
        except ValueError:
            pass
    if close_end:
        try:
            bm.faces.new(vrings[-1])
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    me.materials.append(mat)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def loft_path(name, pts, radii, mat, coll, sides=8, up=(0, 0, 1), smooth=True,
              close=False):
    pts = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        t.normalize()
        upv = Vector(up)
        if abs(t.dot(upv)) > 0.95:
            upv = Vector((1, 0, 0))
        side = t.cross(upv).normalized()
        up2 = side.cross(t).normalized()
        r = radii[i]
        rings.append([p + side * (math.cos(k * TAU / sides) * r)
                      + up2 * (math.sin(k * TAU / sides) * r) for k in range(sides)])
    if close:
        rings.append(rings[0])
    return loft(name, rings, mat, coll, smooth=smooth,
                close_start=not close, close_end=not close)


def ring_pts(center, rx, ry, sides, phase=0.0, z=None):
    cx, cy, cz = center
    zz = cz if z is None else z
    return [Vector((cx + math.cos(phase + i * TAU / sides) * rx,
                    cy + math.sin(phase + i * TAU / sides) * ry, zz)) for i in range(sides)]


def ring_bm(bm, center, axis, major, minor, mseg=12, nseg=5):
    """Append one torus ring into an existing bmesh, oriented to `axis`.

    Used to build tunnel stiffeners as one merged mesh instead of dozens of
    single-object toruses.
    """
    ax = Vector(axis).normalized()
    tmp = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(tmp).normalized()
    v = ax.cross(u).normalized()
    c = Vector(center)
    base = len(bm.verts)
    for i in range(mseg):
        a = i * TAU / mseg
        rad = u * math.cos(a) + v * math.sin(a)
        cc = c + rad * major
        for j in range(nseg):
            b = j * TAU / nseg
            bm.verts.new(cc + rad * (math.cos(b) * minor) + ax * (math.sin(b) * minor))
    bm.verts.ensure_lookup_table()
    vv = bm.verts
    for i in range(mseg):
        i2 = (i + 1) % mseg
        for j in range(nseg):
            j2 = (j + 1) % nseg
            try:
                bm.faces.new((vv[base + i * nseg + j], vv[base + i * nseg + j2],
                              vv[base + i2 * nseg + j2], vv[base + i2 * nseg + j]))
            except ValueError:
                pass


def beam_bm(bm, p0, p1, w, h=None, off=0.0):
    """Append a rectangular beam between two points into an existing bmesh.

    Used to build merged structural frames (geodesic ribs) as ONE mesh instead of
    hundreds of objects.
    """
    h = w if h is None else h
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ln = d.length
    if ln < 1e-6:
        return
    d.normalize()
    up = Vector((0, 0, 1))
    if abs(d.dot(up)) > 0.94:
        up = Vector((1, 0, 0))
    side = d.cross(up).normalized()
    up2 = side.cross(d).normalized()
    base = len(bm.verts)
    for p in (p0, p1):
        c = p + up2 * off
        bm.verts.new(c + side * (w * 0.5) + up2 * (h * 0.5))
        bm.verts.new(c - side * (w * 0.5) + up2 * (h * 0.5))
        bm.verts.new(c - side * (w * 0.5) - up2 * (h * 0.5))
        bm.verts.new(c + side * (w * 0.5) - up2 * (h * 0.5))
    bm.verts.ensure_lookup_table()
    v = bm.verts
    quads = ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1),
             (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))
    for a, b_, c_, d_ in quads:
        try:
            bm.faces.new((v[base + a], v[base + b_], v[base + c_], v[base + d_]))
        except ValueError:
            pass


# ---------------------------------------------------------------- asset masters
POOL = {}


def merge_parts(name, parts, coll=None):
    mats, mat_index = [], {}
    verts, faces, face_mat, face_smooth = [], [], [], []
    for ob in parts:
        me = ob.data
        mw = ob.matrix_basis
        local_map = []
        for m in me.materials:
            key = m.name if m else "NONE"
            if key not in mat_index:
                mat_index[key] = len(mats)
                mats.append(m)
            local_map.append(mat_index[key])
        if not local_map:
            if "NONE" not in mat_index:
                mat_index["NONE"] = len(mats)
                mats.append(None)
            local_map = [mat_index["NONE"]]
        base = len(verts)
        verts.extend([tuple(mw @ v.co) for v in me.vertices])
        for p in me.polygons:
            faces.append(tuple(base + i for i in p.vertices))
            mi = p.material_index
            face_mat.append(local_map[mi] if mi < len(local_map) else local_map[0])
            face_smooth.append(p.use_smooth)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for m in mats:
        me.materials.append(m)
    for i, p in enumerate(me.polygons):
        p.material_index = face_mat[i]
        p.use_smooth = face_smooth[i]
    ob = bpy.data.objects.new(name, me)
    C("WORK").objects.link(ob)
    for p in parts:
        old = p.data
        bpy.data.objects.remove(p, do_unlink=True)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    return ob


def apply_modifiers(ob):
    if not ob.modifiers:
        return ob
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    new_me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True,
                                             depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob


def make_master(name, parts, bevel=0.012, weighted=True, keep_parts=False):
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    ob = merge_parts(name, parts)
    if bevel > 0:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(38)
    if weighted:
        m = ob.modifiers.new("WN", "WEIGHTED_NORMAL")
        m.keep_sharp = True
    apply_modifiers(ob)
    me = ob.data
    me.name = name
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    C("WORK").objects.unlink(ob)
    C("LIB").objects.link(ob)
    ob.location = (0, 0, 0)
    ob.hide_render = True
    ob.hide_viewport = True
    POOL[name] = {"mesh": me, "tris": tris, "obj": ob, "parts": len(parts)}
    return ob


def place(name, x, y, rot=0.0, s=1.0, coll="PROPS", z=None, tag=None, sink=0.0,
          scale3=None, tilt=(0.0, 0.0)):
    m = POOL[name]
    ob = bpy.data.objects.new(name, m["mesh"])
    gz = seabed_h(x, y) if z is None else z
    ob.location = (x, y, gz - sink)
    ob.rotation_euler = (tilt[0], tilt[1], rot)
    if scale3:
        ob.scale = scale3
    else:
        ob.scale = (s, s, s)
    C(coll).objects.link(ob)
    if tag:
        ob["ab_tag"] = tag
    return ob


def instance(name, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), tag=None):
    m = POOL[name]
    ob = bpy.data.objects.new(name, m["mesh"])
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    C(coll).objects.link(ob)
    if tag:
        ob["ab_tag"] = tag
    return ob


# ---------------------------------------------------------------- cameras / render
def make_camera(name, loc, target, lens=50.0, ortho=None, coll="CAMERAS"):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    cd.clip_start = 0.5
    cd.clip_end = 900.0
    ob = bpy.data.objects.new(name, cd)
    C(coll).objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def render_to(cam, path, res=960, samples=32):
    sc = bpy.context.scene
    prev = sc.camera
    prev_x, prev_y = sc.render.resolution_x, sc.render.resolution_y
    try:
        prev_samples = sc.eevee.taa_render_samples
    except Exception:
        prev_samples = 64
    sc.camera = cam
    sc.render.resolution_x = res
    sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    try:
        sc.eevee.taa_render_samples = samples
    except Exception:
        pass
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # inspection renders must not leak their settings into the saved project
    sc.camera = prev
    sc.render.resolution_x = prev_x
    sc.render.resolution_y = prev_y
    try:
        sc.eevee.taa_render_samples = prev_samples
    except Exception:
        pass
    return path


def save_checkpoint(tag):
    path = os.path.join(BASE_DIR, "checkpoints", tag + ".blend")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("CHECKPOINT", path, os.path.getsize(path))
    return path


def purge():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def bootstrap():
    global RNG
    RNG = random.Random(20261101)
    purge()
    setup_scene()
    build_collections()
    build_materials()
    build_world()
    build_compositor()
    print("BOOTSTRAP OK engine=%s view=%s look=%s" % (
        bpy.context.scene.render.engine,
        bpy.context.scene.view_settings.view_transform,
        bpy.context.scene.view_settings.look))


# ---------------------------------------------------------------- asset bench
BENCH_O = Vector((900.0, 900.0, 0.0))
_BENCH = {}


def _bench_scene():
    if _BENCH:
        return _BENCH
    c = bpy.data.collections.new("TMP_BENCH")
    bpy.context.scene.collection.children.link(c)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60.0)
    g = _obj("BENCH_GROUND", bm, MAT["steel"], c, loc=(BENCH_O.x, BENCH_O.y, -0.03))
    lights = []
    for nm, loc, energy, size, col in (
        ("BENCH_KEY", (-9, -11, 14), 3000, 10, (0.92, 0.97, 1.0)),
        ("BENCH_FILL", (12, -8, 6), 900, 9, (0.55, 0.85, 1.0)),
        ("BENCH_RIM", (7, 12, 10), 1800, 8, (0.55, 1.0, 0.95)),
    ):
        li = bpy.data.lights.new(nm, "AREA")
        li.energy = energy
        li.size = size
        li.color = col
        ob = bpy.data.objects.new(nm, li)
        ob.location = (BENCH_O.x + loc[0], BENCH_O.y + loc[1], loc[2])
        d = Vector((BENCH_O.x, BENCH_O.y, 3.0)) - Vector(ob.location)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        c.objects.link(ob)
        lights.append(ob)
    cd = bpy.data.cameras.new("BENCH_CAM")
    cd.lens = 70
    cam = bpy.data.objects.new("BENCH_CAM", cd)
    c.objects.link(cam)
    _BENCH.update({"coll": c, "cam": cam, "lights": lights, "ground": g})
    return _BENCH


def bench_render(name, path, res=720, samples=24, angle=0.72, target_frac=0.52):
    b = _bench_scene()
    ob = bpy.data.objects.new("BENCH_ASSET", POOL[name]["mesh"])
    b["coll"].objects.link(ob)
    ob.location = BENCH_O
    bb = [Vector(c) for c in ob.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    w = max(max(v.x for v in bb) - min(v.x for v in bb),
            max(v.y for v in bb) - min(v.y for v in bb))
    ext = max(h, w * 1.1, 0.6)
    dist = ext * 2.30 + 2.0
    tz = BENCH_O.z + h * target_frac
    cam = b["cam"]
    cam.location = (BENCH_O.x + math.cos(angle) * dist,
                    BENCH_O.y - math.sin(angle) * dist,
                    tz + ext * 0.36)
    d = Vector((BENCH_O.x, BENCH_O.y, tz)) - Vector(cam.location)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    path_out = render_to(cam, path, res, samples)
    bpy.data.objects.remove(ob, do_unlink=True)
    return path_out


def bench_cleanup():
    b = _BENCH
    if not b:
        return
    for ob in list(b["coll"].objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(b["coll"])
    _BENCH.clear()
