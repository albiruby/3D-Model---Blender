"""
TROPICAL ISLAND CIVILIZATION - THE LIVING PARADISE
island_core.py : world field, terrain, ocean, materials, scene, primitives

Blender 5.2 / EEVEE.  Every module is exec()'d into one shared namespace by
build_island.py, so functions defined here are visible to all later modules.
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector

BASE_DIR = r"D:\Tes Animasi-Motion-Blender\TROPICAL_ISLAND_CIVILIZATION"
TAU = math.pi * 2.0
RNG = random.Random(20261101)

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


# ---------------------------------------------------------------- island field
# Gaussian land masses (x, y, rx, ry, strength) and bays (negative).
S0 = 1.20
LAND = [
    (-2.0, 1.0, 35.0 * S0, 27.0 * S0, 1.00),    # main mass
    (14.0, 9.0, 19.0 * S0, 15.0 * S0, 0.88),    # NE forest lobe
    (-15.0, 11.0, 15.0 * S0, 13.0 * S0, 0.80),  # NW agriculture plateau
    (-22.0, -4.0, 13.0 * S0, 11.0 * S0, 0.72),  # west point / lighthouse
    (5.0, -13.0, 17.0 * S0, 13.0 * S0, 0.86),   # south coast / harbour land
    (21.0, -12.0, 13.0 * S0, 11.0 * S0, 0.80),  # SE resort coast
]
BAYS = [
    (-5.0, -24.0, 11.0, 7.0, 1.15),   # harbour bay notch
    (-33.0, -18.0, 11.0, 9.0, 0.60),  # west cove
    (31.0, 14.0, 9.0, 8.0, 0.30),     # east cove
]
T_ISLAND = 0.90

# Baked field grid: signed distance to the coastline is computed once and
# sampled bilinearly, so terrain / colours / placement are all O(1) lookups.
GX0, GY0, GSTEP = -64.0, -56.0, 0.5
G_NX = int((64.0 - GX0) / GSTEP) + 1
G_NY = int((56.0 - GY0) / GSTEP) + 1
G_LAND = None
G_DW = None
G_DL = None


def gauss(x, y, cx, cy, rx, ry):
    dx = (x - cx) / rx
    dy = (y - cy) / ry
    return math.exp(-(dx * dx + dy * dy))


def field_eval(x, y):
    f = 0.0
    for cx, cy, rx, ry, s in LAND:
        f += s * gauss(x, y, cx, cy, rx, ry)
    for cx, cy, rx, ry, s in BAYS:
        f -= s * gauss(x, y, cx, cy, rx, ry)
    f += (fbm(x * 0.085, y * 0.085, 11, 3) - 0.5) * 0.10
    return f


def _chamfer(mask, target, nx, ny):
    INF = 1e9
    d = [0.0 if m == target else INF for m in mask]
    w1, w2 = 1.0, 1.41421356
    for j in range(ny):
        base = j * nx
        for i in range(nx):
            k = base + i
            v = d[k]
            if v == 0.0:
                continue
            if i > 0:
                v = min(v, d[k - 1] + w1)
            if j > 0:
                v = min(v, d[k - nx] + w1)
                if i > 0:
                    v = min(v, d[k - nx - 1] + w2)
                if i < nx - 1:
                    v = min(v, d[k - nx + 1] + w2)
            d[k] = v
    for j in range(ny - 1, -1, -1):
        base = j * nx
        for i in range(nx - 1, -1, -1):
            k = base + i
            v = d[k]
            if v == 0.0:
                continue
            if i < nx - 1:
                v = min(v, d[k + 1] + w1)
            if j < ny - 1:
                v = min(v, d[k + nx] + w1)
                if i < nx - 1:
                    v = min(v, d[k + nx + 1] + w2)
                if i > 0:
                    v = min(v, d[k + nx - 1] + w2)
            d[k] = v
    return d


def bake_field():
    global G_LAND, G_DW, G_DL
    nx, ny, step = G_NX, G_NY, GSTEP
    f = [0.0] * (nx * ny)
    for j in range(ny):
        y = GY0 + j * step
        base = j * nx
        for i in range(nx):
            f[base + i] = field_eval(GX0 + i * step, y)
    land = [v > T_ISLAND for v in f]
    G_LAND = land
    G_DW = _chamfer(land, False, nx, ny)
    G_DL = _chamfer(land, True, nx, ny)
    area = sum(land) * step * step
    print("FIELD baked %dx%d land_area=%.0f BU2" % (nx, ny, area))


def _sample(arr, x, y):
    fx = (x - GX0) / GSTEP
    fy = (y - GY0) / GSTEP
    i = int(math.floor(fx))
    j = int(math.floor(fy))
    if i < 0:
        i = 0
    elif i > G_NX - 2:
        i = G_NX - 2
    if j < 0:
        j = 0
    elif j > G_NY - 2:
        j = G_NY - 2
    tx = clamp(fx - i)
    ty = clamp(fy - j)
    k = j * G_NX + i
    a = arr[k] * (1 - tx) + arr[k + 1] * tx
    b = arr[k + G_NX] * (1 - tx) + arr[k + G_NX + 1] * tx
    return a * (1 - ty) + b * ty


def coast_dist(x, y):
    """Signed distance to the coastline in BU: positive inland, negative in water."""
    d = (_sample(G_DW, x, y) - _sample(G_DL, x, y)) * GSTEP
    # organic wobble near the shoreline; also hides the chamfer grid quantisation
    w = math.exp(-(d / 9.0) * (d / 9.0))
    d += (fbm(x * 0.23, y * 0.23, 71, 3) - 0.5) * 1.30 * w
    return d


def cliff_amount(x, y):
    """1 on the rocky western / northern coast, 0 on the gentle beaches."""
    west = smoothstep(-13.0, -26.0, x)
    north = smoothstep(19.0, 26.0, y)
    return max(west, north * 0.85)


def terrain_raw(x, y):
    d = coast_dist(x, y)
    if d >= 0.0:
        cliff = cliff_amount(x, y)
        beach_w = lerp(4.2, 1.2, cliff)
        beach_h = lerp(1.15, 4.60, cliff)
        z = -0.30
        z += beach_h * smoothstep(0.0, beach_w, d)
        z += 2.20 * smoothstep(3.0, 11.0, d)
        z += 5.20 * smoothstep(9.0, 29.0, d)
        hm = smoothstep(2.0, 9.0, d)
        z += hm * 4.60 * gauss(x, y, -7.0, 8.0, 10.0, 9.0)    # main peak
        z += hm * 2.20 * gauss(x, y, -17.0, 14.0, 7.5, 6.0)   # agriculture terrace
        z += hm * 2.40 * gauss(x, y, 12.0, 15.0, 8.5, 6.5)    # NE forest rise
        z += hm * 1.60 * gauss(x, y, 19.0, -2.0, 7.0, 9.0)    # east ridge
        z += hm * 1.20 * gauss(x, y, 2.0, -11.0, 12.0, 5.5)   # south ridge
        z += (fbm(x * 0.075, y * 0.075, 3, 4) - 0.5) * 1.30 * smoothstep(2.5, 10.0, d)
        return z
    w = -d
    return (-0.30 - 1.60 * smoothstep(0.0, 3.0, w) - 5.00 * smoothstep(2.0, 14.0, w)
            - 6.00 * smoothstep(10.0, 40.0, w))


# Flat construction pads. Filled by the layout module BEFORE terrain is built.
PADS = []


def add_pad(x, y, r, z=None, falloff=0.55):
    PADS.append([x, y, r, terrain_raw(x, y) if z is None else z, falloff])


def terrain_h(x, y):
    z = terrain_raw(x, y)
    for px, py, r, pz, fo in PADS:
        d = math.hypot(x - px, y - py)
        if d < r:
            w = 1.0 - smoothstep(r * fo, r, d)
            z += (pz - z) * w
    return z


def terrain_slope(x, y, h=0.8):
    dx = terrain_h(x + h, y) - terrain_h(x - h, y)
    dy = terrain_h(x, y + h) - terrain_h(x, y - h)
    return math.hypot(dx, dy) / (2.0 * h)


def is_land(x, y):
    return coast_dist(x, y) > 0.0


def shore_distance(x, y):
    return max(0.0, -coast_dist(x, y))


# ---------------------------------------------------------------- palette
PAL = {
    "ocean_shallow": "#57E3D8",
    "ocean_mid": "#20C9C3",
    "ocean_deep": "#087F91",
    "ocean_abyss": "#07596F",
    "sand": "#E9D3A0",
    "sand_wet": "#C9AF80",
    "sand_dry": "#F0DCB0",
    "grass_mid": "#3C9B58",
    "grass_dark": "#246B43",
    "grass_light": "#58AD63",
    "rock": "#7E7A70",
    "rock_dark": "#57544E",
    "wood_warm": "#A96F43",
    "wood_light": "#D3A878",
    "wood_dark": "#6E462A",
    "paint_white": "#F2F0E8",
    "paint_coral": "#F08076",
    "paint_teal": "#2FA8A0",
    "paint_yellow": "#F5CB65",
    "paint_blue": "#4C86C6",
    "paint_mint": "#9FD8C0",
    "roof_terra": "#C86D4B",
    "roof_thatch": "#B0894F",
    "roof_metal": "#5A6B6E",
    "concrete": "#CFC9BC",
    "concrete_dark": "#8E8A80",
    "stone": "#8A857B",
    "stone_dark": "#5F5B54",
    "glass": "#CFE6E8",
    "metal": "#9AA3A8",
    "metal_dark": "#3A4045",
    "fabric_white": "#F6F1E4",
    "fabric_coral": "#F08076",
    "fabric_teal": "#2FA8A0",
    "asphalt": "#4A4F52",
    "paving": "#C7BFAE",
    "line": "#EDE6CF",
    "leaf_dark": "#246B43",
    "leaf_mid": "#3C9B58",
    "leaf_light": "#62B96A",
    "leaf_banana": "#4E9E52",
    "leaf_dry": "#8FA84A",
    "trunk": "#8A6A4C",
    "trunk_palm": "#9C7B55",
    "coconut": "#6E5A32",
    "coral_pink": "#F08076",
    "coral_orange": "#F09A5A",
    "coral_purple": "#B07AC8",
    "skin_1": "#F2C9A0",
    "skin_2": "#D9A377",
    "skin_3": "#A9714A",
    "skin_4": "#7A4B2E",
    "hair_dark": "#2A211C",
    "hair_brown": "#4A3222",
    "glow_warm": "#FFD9A0",
}

MAT = {}


def make_mat(name, hexv, metallic=0.0, rough=0.6, emit=None, estr=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    col = hexcol(hexv)
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*hexcol(emit), 1.0)
        bsdf.inputs["Emission Strength"].default_value = estr
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
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


def build_materials():
    mk = make_mat
    MAT["wood"] = mk("MAT_WOOD_WARM", PAL["wood_warm"], 0.0, 0.62)
    MAT["wood_light"] = mk("MAT_WOOD_LIGHT", PAL["wood_light"], 0.0, 0.60)
    MAT["wood_dark"] = mk("MAT_WOOD_DARK", PAL["wood_dark"], 0.0, 0.66)
    MAT["paint_w"] = mk("MAT_PAINT_WHITE", PAL["paint_white"], 0.0, 0.48)
    MAT["paint_coral"] = mk("MAT_PAINT_CORAL", PAL["paint_coral"], 0.0, 0.50)
    MAT["paint_teal"] = mk("MAT_PAINT_TEAL", PAL["paint_teal"], 0.0, 0.50)
    MAT["paint_yellow"] = mk("MAT_PAINT_YELLOW", PAL["paint_yellow"], 0.0, 0.50)
    MAT["paint_blue"] = mk("MAT_PAINT_BLUE", PAL["paint_blue"], 0.0, 0.50)
    MAT["paint_mint"] = mk("MAT_PAINT_MINT", PAL["paint_mint"], 0.0, 0.50)
    MAT["roof_terra"] = mk("MAT_ROOF_TERRACOTTA", PAL["roof_terra"], 0.0, 0.72)
    MAT["roof_thatch"] = mk("MAT_ROOF_THATCH", PAL["roof_thatch"], 0.0, 0.94)
    MAT["roof_metal"] = mk("MAT_ROOF_METAL", PAL["roof_metal"], 0.85, 0.42)
    MAT["concrete"] = mk("MAT_CONCRETE", "#E4DFD2", 0.0, 0.86)
    MAT["concrete_dark"] = mk("MAT_CONCRETE_DARK", "#B0AAA0", 0.0, 0.88)
    MAT["stone"] = mk("MAT_STONE", PAL["stone"], 0.0, 0.90)
    MAT["stone_dark"] = mk("MAT_STONE_DARK", PAL["stone_dark"], 0.0, 0.90)
    MAT["glass"] = mk("MAT_GLASS", PAL["glass"], 0.0, 0.06, alpha=0.30)
    MAT["glass_dark"] = mk("MAT_GLASS_DARK", "#2A3B42", 0.0, 0.10, alpha=0.55)
    MAT["metal"] = mk("MAT_METAL", PAL["metal"], 1.0, 0.34)
    MAT["metal_dark"] = mk("MAT_METAL_DARK", PAL["metal_dark"], 1.0, 0.44)
    MAT["fabric_w"] = mk("MAT_FABRIC_WHITE", PAL["fabric_white"], 0.0, 0.92)
    MAT["fabric_coral"] = mk("MAT_FABRIC_CORAL", PAL["fabric_coral"], 0.0, 0.92)
    MAT["fabric_teal"] = mk("MAT_FABRIC_TEAL", PAL["fabric_teal"], 0.0, 0.92)
    MAT["asphalt"] = mk("MAT_ASPHALT", PAL["asphalt"], 0.0, 0.92)
    MAT["paving"] = mk("MAT_PAVING", PAL["paving"], 0.0, 0.88)
    MAT["line"] = mk("MAT_ROAD_LINE", PAL["line"], 0.0, 0.80)
    MAT["leaf_dark"] = mk("MAT_LEAF_DARK", PAL["leaf_dark"], 0.0, 0.80)
    MAT["leaf_mid"] = mk("MAT_LEAF_MID", PAL["leaf_mid"], 0.0, 0.78)
    MAT["leaf_light"] = mk("MAT_LEAF_LIGHT", PAL["leaf_light"], 0.0, 0.76)
    MAT["leaf_banana"] = mk("MAT_LEAF_BANANA", PAL["leaf_banana"], 0.0, 0.78)
    MAT["leaf_dry"] = mk("MAT_LEAF_DRY", PAL["leaf_dry"], 0.0, 0.82)
    MAT["grass_blade"] = mk("MAT_GRASS_BLADE", "#7FA24E", 0.0, 0.86)
    MAT["bench"] = mk("MAT_BENCH_GREY", "#B4B2AC", 0.0, 0.75)
    MAT["cream"] = mk("MAT_WALL_CREAM", "#EADFC8", 0.0, 0.70)
    MAT["cream2"] = mk("MAT_WALL_CREAM_WARM", "#E7D3B4", 0.0, 0.70)
    MAT["interior"] = mk("MAT_INTERIOR_SHADOW", "#241C17", 0.0, 0.95)
    MAT["pool_water"] = mk("MAT_POOL_WATER", "#3FD3CC", 0.0, 0.08, alpha=0.55)
    MAT["trunk"] = mk("MAT_TRUNK", PAL["trunk"], 0.0, 0.88)
    MAT["trunk_palm"] = mk("MAT_TRUNK_PALM", PAL["trunk_palm"], 0.0, 0.86)
    MAT["coconut"] = mk("MAT_COCONUT", PAL["coconut"], 0.0, 0.70)
    MAT["coral_pink"] = mk("MAT_CORAL_PINK", PAL["coral_pink"], 0.0, 0.62)
    MAT["coral_orange"] = mk("MAT_CORAL_ORANGE", PAL["coral_orange"], 0.0, 0.62)
    MAT["coral_purple"] = mk("MAT_CORAL_PURPLE", PAL["coral_purple"], 0.0, 0.62)
    MAT["glow"] = mk("MAT_LAMP_GLOW", "#FFF0D2", 0.0, 0.3, PAL["glow_warm"], 8.0)
    MAT["glow_soft"] = mk("MAT_LAMP_GLOW_SOFT", "#FFE9C8", 0.0, 0.3, PAL["glow_warm"], 3.0)
    for i, h in enumerate(("#F2C9A0", "#D9A377", "#A9714A", "#7A4B2E"), 1):
        MAT["skin_%d" % i] = mk("MAT_SKIN_%d" % i, h, 0.0, 0.62)
    MAT["hair_dark"] = mk("MAT_HAIR_DARK", PAL["hair_dark"], 0.0, 0.72)
    MAT["hair_brown"] = mk("MAT_HAIR_BROWN", PAL["hair_brown"], 0.0, 0.72)
    # character clothing variants (shared, swapped per instance)
    for i, h in enumerate(("#F2F0E8", "#F08076", "#2FA8A0", "#F5CB65",
                            "#4C86C6", "#9FD8C0", "#E0644F", "#5E7FA8",
                            "#D9A878", "#7E6BA8")):
        MAT["cloth_%d" % i] = mk("MAT_CLOTH_%02d" % i, h, 0.0, 0.88)
    for i, h in enumerate(("#4A5A68", "#7A6A52", "#3E5A48", "#8E7A5E", "#5E4A6E")):
        MAT["pants_%d" % i] = mk("MAT_PANTS_%02d" % i, h, 0.0, 0.90)
    build_terrain_mat()
    build_ocean_mat()


def build_terrain_mat():
    m = bpy.data.materials.get("MAT_TERRAIN") or bpy.data.materials.new("MAT_TERRAIN")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "terr_col"
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 42.0
    noise.inputs["Detail"].default_value = 6.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.06
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.90
    bsdf.inputs["Metallic"].default_value = 0.0
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    MAT["terrain"] = m


def build_ocean_mat():
    m = bpy.data.materials.get("MAT_OCEAN") or bpy.data.materials.new("MAT_OCEAN")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.055
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.33

    shore = nt.nodes.new("ShaderNodeAttribute")
    shore.attribute_name = "shore_dist"
    # attribute is in BU: normalise 0..30 BU to 0..1 for the ramp
    norm = nt.nodes.new("ShaderNodeMath")
    norm.operation = "DIVIDE"
    norm.inputs[1].default_value = 30.0
    nt.links.new(shore.outputs["Fac"], norm.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position = 0.0
    el[0].color = (*hexcol(PAL["ocean_shallow"]), 1.0)
    el[1].position = 1.0
    el[1].color = (*hexcol(PAL["ocean_abyss"]), 1.0)
    for pos, key in ((0.10, "ocean_mid"), (0.34, "ocean_deep")):
        e = el.new(pos)
        e.color = (*hexcol(PAL[key]), 1.0)
    nt.links.new(norm.outputs[0], ramp.inputs["Fac"])

    # foam band right at the shoreline
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 3.2
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 0.0
    nt.links.new(shore.outputs["Fac"], mr.inputs["Value"])
    foam_noise = nt.nodes.new("ShaderNodeTexNoise")
    foam_noise.inputs["Scale"].default_value = 6.0
    foam_noise.inputs["Detail"].default_value = 5.0
    foam_noise.inputs["Roughness"].default_value = 0.6
    foam_mul = nt.nodes.new("ShaderNodeMath")
    foam_mul.operation = "MULTIPLY"
    nt.links.new(mr.outputs["Result"], foam_mul.inputs[0])
    nt.links.new(foam_noise.outputs["Fac"], foam_mul.inputs[1])
    foam_pow = nt.nodes.new("ShaderNodeMath")
    foam_pow.operation = "POWER"
    foam_pow.inputs[1].default_value = 1.6
    nt.links.new(foam_mul.outputs[0], foam_pow.inputs[0])
    foam_col = nt.nodes.new("ShaderNodeMixRGB")
    foam_col.inputs["Color2"].default_value = (0.86, 0.96, 0.95, 1.0)
    nt.links.new(ramp.outputs["Color"], foam_col.inputs["Color1"])
    nt.links.new(foam_pow.outputs[0], foam_col.inputs["Fac"])
    nt.links.new(foam_col.outputs["Color"], bsdf.inputs["Base Color"])

    # alpha: clear shallows, opaque deep
    amap = nt.nodes.new("ShaderNodeMapRange")
    amap.inputs["From Min"].default_value = 0.0
    amap.inputs["From Max"].default_value = 9.0
    amap.inputs["To Min"].default_value = 0.62
    amap.inputs["To Max"].default_value = 0.97
    nt.links.new(shore.outputs["Fac"], amap.inputs["Value"])
    nt.links.new(amap.outputs["Result"], bsdf.inputs["Alpha"])

    # wave normals: two scales of noise
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 3.2
    n1.inputs["Detail"].default_value = 4.0
    n1.inputs["Roughness"].default_value = 0.55
    n1.inputs["Distortion"].default_value = 0.4
    b1 = nt.nodes.new("ShaderNodeBump")
    b1.inputs["Strength"].default_value = 0.30
    b1.inputs["Distance"].default_value = 0.35
    nt.links.new(n1.outputs["Fac"], b1.inputs["Height"])
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 18.0
    n2.inputs["Detail"].default_value = 6.0
    b2 = nt.nodes.new("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.16
    b2.inputs["Distance"].default_value = 0.10
    nt.links.new(n2.outputs["Fac"], b2.inputs["Height"])
    nt.links.new(b1.outputs["Normal"], b2.inputs["Normal"])
    nt.links.new(b2.outputs["Normal"], bsdf.inputs["Normal"])

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except Exception:
            pass
    try:
        m.use_transparent_shadow = False
    except Exception:
        pass
    MAT["ocean"] = m


# ---------------------------------------------------------------- scene / collections
COLLS = {}
ROOT = None


def build_collections():
    global ROOT
    names = [
        "01_TERRAIN", "02_OCEAN", "03_RESIDENTIAL", "04_COMMERCIAL", "05_RESORT",
        "06_HARBOR", "07_PUBLIC_FACILITIES", "08_HUMAN_CHARACTERS", "09_ANIMALS",
        "10_VEGETATION", "11_AGRICULTURE", "12_VEHICLES", "13_ENVIRONMENTAL_PROPS",
        "14_LIGHTING", "15_CAMERAS",
    ]
    root = bpy.data.collections.get("TROPICAL_ISLAND_CIVILIZATION")
    if root is None:
        root = bpy.data.collections.new("TROPICAL_ISLAND_CIVILIZATION")
    if root.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(root)
    ROOT = root
    for n in names:
        c = bpy.data.collections.get(n)
        if c is None:
            c = bpy.data.collections.new(n)
            root.children.link(c)
        COLLS[n[3:]] = c
    lib = bpy.data.collections.get("00_ASSET_LIBRARY")
    if lib is None:
        lib = bpy.data.collections.new("00_ASSET_LIBRARY")
        root.children.link(lib)
    lib.hide_render = True
    lib.hide_viewport = True
    COLLS["LIB"] = lib
    work = bpy.data.collections.get("00_WORKSPACE")
    if work is None:
        work = bpy.data.collections.new("00_WORKSPACE")
        root.children.link(work)
    work.hide_render = True
    COLLS["WORK"] = work
    # purge() destroys the collection tree; reset the active layer collection so
    # bpy.ops.mesh.primitive_* can register their result in context.object again.
    try:
        vl = bpy.context.view_layer
        vl.active_layer_collection = vl.layer_collection
        vl.update()
    except Exception as e:
        print("layer collection reset failed", repr(e))


def C(key):
    return COLLS[key]


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
    try:
        sc.eevee.taa_render_samples = 64
    except Exception:
        pass
    try:
        sc.eevee.use_raytracing = True
    except Exception:
        pass
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Punchy"
    except Exception:
        try:
            sc.view_settings.view_transform = "AgX"
        except Exception:
            pass
    sc.view_settings.exposure = 0.0
    return sc


def build_world():
    w = bpy.data.worlds.get("TI_World") or bpy.data.worlds.new("TI_World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    # visible sky: vertical gradient
    incoming = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(incoming.outputs["Incoming"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.85
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position = 0.0
    el[0].color = (*hexcol("#CDE9F2"), 1.0)
    el[1].position = 1.0
    el[1].color = (*hexcol("#2F7FC4"), 1.0)
    e = el.new(0.35)
    e.color = (*hexcol("#8FC9E8"), 1.0)
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])

    visible = nt.nodes.new("ShaderNodeBackground")
    visible.inputs["Strength"].default_value = 1.0
    nt.links.new(ramp.outputs["Color"], visible.inputs["Color"])
    ambient = nt.nodes.new("ShaderNodeBackground")
    ambient.inputs["Strength"].default_value = 0.42
    nt.links.new(ramp.outputs["Color"], ambient.inputs["Color"])
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(ambient.outputs["Background"], mix.inputs[1])
    nt.links.new(visible.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    MAT["world"] = w


def build_compositor():
    sc = bpy.context.scene
    try:
        old = bpy.data.node_groups.get("TI_Compositing")
        if old:
            bpy.data.node_groups.remove(old)
        ng = bpy.data.node_groups.new("TI_Compositing", "CompositorNodeTree")
        try:
            ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        except Exception:
            pass
        sc.compositing_node_group = ng
        sc.use_nodes = True
        rl = ng.nodes.new("CompositorNodeRLayers")
        glare = ng.nodes.new("CompositorNodeGlare")
        try:
            glare.inputs["Type"].default_value = "Bloom"
        except Exception:
            pass
        try:
            glare.inputs["Quality"].default_value = "High"
        except Exception:
            pass
        glare.inputs["Threshold"].default_value = 1.35
        glare.inputs["Strength"].default_value = 0.22
        glare.inputs["Size"].default_value = 0.35
        outn = ng.nodes.new("NodeGroupOutput")
        ng.links.new(rl.outputs["Image"], glare.inputs["Image"])
        ng.links.new(glare.outputs["Image"], outn.inputs[0])
        print("COMPOSITOR OK")
    except Exception as e:
        print("COMPOSITOR SKIPPED:", repr(e))


# ---------------------------------------------------------------- primitive helpers
# All geometry is built with bmesh.  No bpy.ops and no bpy.context.* is used for
# modelling, so the builders behave identically inside the MCP sandbox (which
# exposes a restricted context) and in a normal Blender session.

def _obj(name, bm, mat, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1),
         smooth=True, smooth_cut=None):
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


def smooth_round(ob, cutoff=0.72):
    for p in ob.data.polygons:
        p.use_smooth = abs(p.normal.z) < cutoff
    return ob


def all_smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def _bm_tube(r1, r2, d, sides):
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


def _bm_torus(major, minor, mseg, nseg):
    bm = bmesh.new()
    rows = []
    for i in range(mseg):
        a = i * TAU / mseg
        c, s = math.cos(a), math.sin(a)
        ring = []
        for j in range(nseg):
            b = j * TAU / nseg
            rr = major + math.cos(b) * minor
            ring.append(bm.verts.new((c * rr, s * rr, math.sin(b) * minor)))
        rows.append(ring)
    for i in range(mseg):
        a = rows[i]
        b = rows[(i + 1) % mseg]
        for j in range(nseg):
            k = (j + 1) % nseg
            bm.faces.new((a[j], a[k], b[k], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def box(name, size, loc, mat, coll, rot=(0, 0, 0), bev=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _obj(name, bm, mat, coll, loc, rot, smooth=False)


def cyl(name, r, d, loc, mat, coll, rot=(0, 0, 0), verts=16, smooth=True):
    ob = _obj(name, _bm_tube(r, r, d, verts), mat, coll, loc, rot,
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


def ico(name, r, loc, mat, coll, sub=1, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    except TypeError:
        bmesh.ops.create_icosphere(bm, subdivisions=sub, diameter=r * 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _obj(name, bm, mat, coll, loc, rot, scale, smooth=True)


def torus(name, major, minor, loc, mat, coll, rot=(0, 0, 0), mseg=32, nseg=8):
    return _obj(name, _bm_torus(major, minor, mseg, nseg), mat, coll, loc, rot,
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
    """rings: list of equal-length point lists."""
    bm = bmesh.new()
    vrings = []
    for ring in rings:
        vrings.append([bm.verts.new(Vector(p)) for p in ring])
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


def loft_path(name, pts, radii, mat, coll, sides=8, up=(0, 0, 1), smooth=True):
    """Loft a tube along a polyline with per-point radius."""
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
        ring = []
        for k in range(sides):
            a = k * TAU / sides
            ring.append(p + side * (math.cos(a) * r) + up2 * (math.sin(a) * r))
        rings.append(ring)
    return loft(name, rings, mat, coll, smooth=smooth)


def ring_pts(center, rx, ry, sides, phase=0.0):
    cx, cy, cz = center
    return [Vector((cx + math.cos(phase + i * TAU / sides) * rx,
                    cy + math.sin(phase + i * TAU / sides) * ry, cz)) for i in range(sides)]


# ---------------------------------------------------------------- asset masters
POOL = {}


def merge_parts(name, parts):
    """Merge objects into one mesh, baking each object's transform and materials."""
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


def make_master(name, parts, bevel=0.018, weighted=True, coll=None, keep_parts=False):
    """Merge parts into one asset mesh, apply bevel + weighted normals, register."""
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


def place(name, x, y, rot=0.0, s=1.0, coll="ENVIRONMENTAL_PROPS", z=None,
          matset=None, tag=None, sink=0.0):
    m = POOL[name]
    ob = bpy.data.objects.new(name, m["mesh"])
    gz = terrain_h(x, y) if z is None else z
    ob.location = (x, y, gz - sink)
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (s, s, s)
    C(coll).objects.link(ob)
    if matset:
        for idx, mat in matset.items():
            try:
                ob.material_slots[idx].link = "OBJECT"
                ob.material_slots[idx].material = mat
            except Exception:
                pass
    if tag:
        ob["ti_tag"] = tag
    return ob


# ---------------------------------------------------------------- terrain
C_SAND = hexcol(PAL["sand"])
C_SAND_WET = hexcol(PAL["sand_wet"])
C_SAND_DRY = hexcol(PAL["sand_dry"])
C_GRASS_MID = hexcol(PAL["grass_mid"])
C_GRASS_DARK = hexcol(PAL["grass_dark"])
C_GRASS_LIGHT = hexcol(PAL["grass_light"])
C_ROCK = hexcol(PAL["rock"])
C_ROCK_DARK = hexcol(PAL["rock_dark"])


def _mix(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def terrain_color(x, y, z):
    if z < -0.05:
        depth = -z
        base = _mix(C_SAND_DRY, hexcol("#A8CFC0"), smoothstep(0.4, 3.5, depth))
        base = _mix(base, hexcol("#2F7078"), smoothstep(2.5, 9.0, depth))
        return (base[0] * 0.95, base[1] * 0.95, base[2] * 0.95)
    n = fbm(x * 0.17, y * 0.17, 21, 3)
    d = coast_dist(x, y)
    wet = 1.0 - smoothstep(0.4, 2.2, d)
    sand = _mix(C_SAND, C_SAND_WET, wet)
    sand = _mix(sand, C_SAND_DRY, (1.0 - wet) * n * 0.55)
    gn = fbm(x * 0.11, y * 0.11, 33, 4)
    grass = _mix(C_GRASS_DARK, C_GRASS_MID, gn)
    grass = _mix(grass, C_GRASS_LIGHT, smoothstep(0.55, 1.0, gn) * 0.55)
    sand_w = 1.0 - smoothstep(2.4 + n * 1.6, 4.8 + n * 1.6, d)
    col = _mix(grass, sand, sand_w)
    rock = _mix(C_ROCK_DARK, C_ROCK, fbm(x * 0.3, y * 0.3, 44, 2))
    sl = terrain_slope(x, y, 0.9)
    col = _mix(col, rock, smoothstep(0.62, 1.10, sl))
    k = 0.94 + 0.12 * fbm(x * 0.55, y * 0.55, 55, 2)
    return (clamp(col[0] * k, 0, 1), clamp(col[1] * k, 0, 1), clamp(col[2] * k, 0, 1))


def build_terrain(coll):
    step = 0.62
    x0, x1, y0, y1 = -60.0, 60.0, -50.0, 50.0
    nx = int((x1 - x0) / step) + 1
    ny = int((y1 - y0) / step) + 1
    verts, cols = [], []
    zmin, zmax = 99.0, -99.0
    for j in range(ny):
        y = y0 + j * step
        for i in range(nx):
            x = x0 + i * step
            z = terrain_h(x, y)
            zmin = min(zmin, z)
            zmax = max(zmax, z)
            verts.append((x, y, z))
            cols.append(terrain_color(x, y, z))
    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    me = bpy.data.meshes.new("TERRAIN")
    me.from_pydata(verts, [], faces)
    me.update()
    attr = me.color_attributes.new("terr_col", "FLOAT_COLOR", "POINT")
    for i, c in enumerate(cols):
        attr.data[i].color = (c[0], c[1], c[2], 1.0)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(MAT["terrain"])
    ob = bpy.data.objects.new("TERRAIN_ISLAND", me)
    coll.objects.link(ob)
    print("TERRAIN verts=%d faces=%d  z=[%.2f, %.2f]" % (len(verts), len(faces), zmin, zmax))
    return ob


def _ocean_axis(a, b, step, ext, growth=1.32):
    n = int((b - a) / step)
    xs = [a + i * step for i in range(n + 1)]
    left, v, cur = [], step * 1.5, xs[0]
    while cur > -ext:
        v *= growth
        cur -= v
        left.append(cur)
    xs = list(reversed(left)) + xs
    right, v, cur = [], step * 1.5, xs[-1]
    while cur < ext:
        v *= growth
        cur += v
        right.append(cur)
    return xs + right


def build_ocean(coll):
    xs = _ocean_axis(-46.0, 46.0, 0.85, 900.0)
    ys = _ocean_axis(-40.0, 40.0, 0.85, 900.0)
    nx, ny = len(xs), len(ys)
    verts, dists = [], []
    for y in ys:
        for x in xs:
            verts.append((x, y, 0.0))
            dists.append(shore_distance(x, y))
    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i
            faces.append((a, a + 1, a + nx + 1, a + nx))
    me = bpy.data.meshes.new("OCEAN")
    me.from_pydata(verts, [], faces)
    me.update()
    attr = me.attributes.new("shore_dist", "FLOAT", "POINT")
    for i, d in enumerate(dists):
        attr.data[i].value = d
    me.materials.append(MAT["ocean"])
    ob = bpy.data.objects.new("OCEAN_SURFACE", me)
    coll.objects.link(ob)
    try:
        ob.visible_shadow = False
    except Exception:
        pass
    print("OCEAN verts=%d faces=%d" % (len(verts), len(faces)))
    return ob


# ---------------------------------------------------------------- cameras / render
def make_camera(name, loc, target, lens=50.0, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    ob = bpy.data.objects.new(name, cd)
    C("CAMERAS").objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def render_to(cam, path, res=960, samples=32):
    sc = bpy.context.scene
    prev = sc.camera
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
    sc.camera = prev
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
    bake_field()
    print("BOOTSTRAP OK engine=%s view=%s look=%s" % (
        bpy.context.scene.render.engine,
        bpy.context.scene.view_settings.view_transform,
        bpy.context.scene.view_settings.look))


def test_sun():
    """Temporary key light used for terrain / layout inspection renders."""
    li = bpy.data.lights.new("TEMP_SUN", "SUN")
    li.energy = 4.2
    li.angle = math.radians(1.6)
    li.color = (1.0, 0.93, 0.82)
    ob = bpy.data.objects.new("TEMP_SUN", li)
    C("LIGHTING").objects.link(ob)
    d = Vector((0.62, 0.42, -0.66)).normalized()
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob


def build_ground():
    build_terrain(C("TERRAIN"))
    build_ocean(C("OCEAN"))


def map_camera():
    return make_camera("CAM_MAP", (0, 0, 160), (0, 0, 0), ortho=92.0)


# ---------------------------------------------------------------- asset bench
BENCH_O = Vector((1200.0, 1200.0, 0.0))
_BENCH = {}


def _bench_scene():
    if _BENCH:
        return _BENCH
    c = bpy.data.collections.new("TMP_BENCH")
    bpy.context.scene.collection.children.link(c)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=80.0)
    g = _obj("BENCH_GROUND", bm, MAT["bench"], c, loc=(BENCH_O.x, BENCH_O.y, -0.03), smooth=False)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=90.0)
    _obj("BENCH_WALL", bm, MAT["bench"], c, loc=(BENCH_O.x, BENCH_O.y + 22.0, 30.0),
         rot=(math.radians(90), 0, 0), smooth=False)
    lights = []
    for nm, loc, energy, size, col in (
        ("BENCH_KEY", (-9, -11, 14), 2600, 10, (1.0, 0.95, 0.88)),
        ("BENCH_FILL", (12, -8, 6), 700, 9, (0.72, 0.84, 1.0)),
        ("BENCH_RIM", (7, 12, 10), 1700, 8, (1.0, 0.86, 0.70)),
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
    cd.lens = 62
    cam = bpy.data.objects.new("BENCH_CAM", cd)
    c.objects.link(cam)
    _BENCH.update({"coll": c, "cam": cam, "lights": lights, "ground": g})
    return _BENCH


def bench_render(name, path, res=720, samples=24, angle=0.62, target_frac=0.52):
    b = _bench_scene()
    ob = bpy.data.objects.new("BENCH_ASSET", POOL[name]["mesh"])
    b["coll"].objects.link(ob)
    ob.location = BENCH_O
    bb = [Vector(c) for c in ob.bound_box]
    h = max(v.z for v in bb) - min(v.z for v in bb)
    w = max(max(v.x for v in bb) - min(v.x for v in bb),
            max(v.y for v in bb) - min(v.y for v in bb))
    ext = max(h, w * 1.15, 0.6)
    dist = ext * 2.35 + 2.0
    tz = BENCH_O.z + h * target_frac
    cam = b["cam"]
    cam.location = (BENCH_O.x + math.cos(angle) * dist,
                    BENCH_O.y - math.sin(angle) * dist,
                    tz + ext * 0.42)
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
