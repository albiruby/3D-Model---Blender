"""
NEON_RITUAL - core scene, materials, primitives, collections.
Blender 5.2.3 LTS / EEVEE.
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Euler

BASE = r"D:\Tes Animasi-Motion-Blender\Neon Ritual"
SCRIPTS = os.path.join(BASE, "scripts")
PREVIEW = os.path.join(BASE, "PREVIEW")
RENDERS = os.path.join(BASE, "renders")
FRAMES = os.path.join(BASE, "frames")
AUDIO = os.path.join(BASE, "audio")
FONT_DIRS = (
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
    r"C:\Windows\Fonts",
)

SCENE = None
ROOT = None
COLL = {}
MAT = {}
FONTS = {}


# ------------------------------------------------------------------ scene

def clear_scene():
    bpy.ops.wm.read_homefile(use_empty=True)


def make_collections():
    global ROOT, COLL
    SCENE = bpy.context.scene
    ROOT = bpy.data.collections.new("NEON_RITUAL_SCENE")
    SCENE.collection.children.link(ROOT)
    COLL.clear()

    def sub(key, name, parent):
        c = bpy.data.collections.new(name)
        parent.children.link(c)
        COLL[key] = c
        return c

    env = sub("ENV", "01_ENVIRONMENT", ROOT)
    sub("MAIN_HALL", "Main_Hall", env)
    sub("ARCHITECTURE", "Architecture", env)
    sub("PILLARS", "Pillars", env)
    sub("RUINS", "Concrete_Ruins", env)
    sub("BEAMS", "Structural_Beams", env)

    stage = sub("STAGE", "02_STAGE", ROOT)
    sub("STAGE_PLATFORM", "Stage_Platform", stage)
    sub("STAIRCASE", "Staircase", stage)
    sub("DJ_BOOTH", "DJ_Booth", stage)
    sub("SPEAKERS", "Speakers", stage)
    sub("LED", "LED_Screens", stage)

    hero = sub("HERO", "03_HERO_ASSETS", ROOT)
    sub("SCULPTURE", "Chrome_Sculpture", hero)
    sub("RINGS", "Orbital_Rings", hero)
    sub("FRAGMENTS", "Floating_Fragments", hero)

    typo = sub("TYPO", "04_TYPOGRAPHY", ROOT)
    sub("LOGO", "Main_Logo", typo)
    sub("SECONDARY", "Secondary_Text", typo)
    sub("INFO", "Event_Information", typo)

    props = sub("PROPS", "05_INDUSTRIAL_PROPS", ROOT)
    sub("CHAINS", "Chains", props)
    sub("CRATES", "Crates", props)
    sub("PIPES", "Pipes", props)
    sub("MACHINERY", "Machinery", props)
    sub("DECOR", "Decorative_Objects", props)

    lights = sub("LIGHTS", "06_LIGHTING", ROOT)
    sub("RED_NEON", "Red_Neon", lights)
    sub("WHITE_SPOT", "White_Spotlights", lights)
    sub("RIM", "Rim_Lights", lights)
    sub("ATMOS_LIGHT", "Atmospheric_Lighting", lights)

    atmo = sub("ATMO", "07_ATMOSPHERE", ROOT)
    sub("FOG", "Fog", atmo)
    sub("PARTICLES", "Particles", atmo)
    sub("SMOKE", "Smoke", atmo)

    cams = sub("CAMS", "08_CAMERAS", ROOT)
    for i in range(1, 9):
        sub("CAM_%02d" % i, "Camera_%02d" % i, cams)

    sub("CTRL", "09_ANIMATION_CONTROLS", ROOT)
    sub("MASTERS", "MASTERS", ROOT)
    return COLL


def setup_scene():
    global SCENE
    SCENE = bpy.context.scene
    SCENE.render.engine = "BLENDER_EEVEE"
    SCENE.render.resolution_x = 1080
    SCENE.render.resolution_y = 1920
    SCENE.render.resolution_percentage = 100
    SCENE.render.fps = 30
    SCENE.frame_start = 1
    SCENE.frame_end = 450
    SCENE.render.image_settings.file_format = "PNG"
    SCENE.render.image_settings.color_mode = "RGB"
    SCENE.render.image_settings.compression = 15
    SCENE.render.film_transparent = False
    SCENE.render.use_file_extension = True
    SCENE.view_settings.view_transform = "AgX"
    SCENE.view_settings.look = "AgX - Punchy"
    SCENE.view_settings.exposure = 0.70
    SCENE.view_settings.gamma = 1.0
    SCENE.eevee.taa_render_samples = 32
    SCENE.eevee.taa_samples = 16
    SCENE.eevee.use_raytracing = True
    SCENE.eevee.ray_tracing_method = "SCREEN"
    SCENE.eevee.use_shadows = True
    SCENE.eevee.shadow_ray_count = 2
    SCENE.eevee.shadow_step_count = 6
    SCENE.eevee.volumetric_tile_size = "8"
    SCENE.eevee.volumetric_samples = 32
    SCENE.eevee.volumetric_start = 0.1
    SCENE.eevee.volumetric_end = 80.0
    SCENE.eevee.use_volumetric_shadows = True
    SCENE.eevee.volumetric_shadow_samples = 16
    SCENE.render.use_motion_blur = False
    SCENE.unit_settings.system = "METRIC"
    return SCENE


# ------------------------------------------------------------------ materials

def _new_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf


def _noise(nt, scale=5.0, detail=6.0, rough=0.6, loc=(-500, 0)):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.location = loc
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    return n


def _maprange(nt, lo, hi, loc=(-250, 0)):
    m = nt.nodes.new("ShaderNodeMapRange")
    m.location = loc
    m.inputs["From Min"].default_value = 0.0
    m.inputs["From Max"].default_value = 1.0
    m.inputs["To Min"].default_value = lo
    m.inputs["To Max"].default_value = hi
    return m


def _ramp(nt, c0, c1, loc=(-250, 200)):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.location = loc
    r.color_ramp.elements[0].color = c0
    r.color_ramp.elements[1].color = c1
    return r


def make_materials():
    global MAT
    MAT.clear()

    # chrome
    m, nt, b = _new_mat("CHROME_MIRROR")
    b.inputs["Base Color"].default_value = (0.86, 0.88, 0.92, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.09
    b.inputs["Anisotropic"].default_value = 0.4
    n = _noise(nt, 7.0, 6.0, 0.55, (-520, 80))
    mr = _maprange(nt, 0.10, 0.20, (-260, 80))
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    nb = _noise(nt, 90.0, 4.0, 0.5, (-520, -220))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (0, -200)
    bump.inputs["Strength"].default_value = 0.035
    bump.inputs["Distance"].default_value = 0.05
    nt.links.new(nb.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MAT["chrome"] = m

    # dark gunmetal
    m, nt, b = _new_mat("DARK_GUNMETAL")
    b.inputs["Base Color"].default_value = (0.018, 0.020, 0.024, 1)
    b.inputs["Metallic"].default_value = 0.92
    b.inputs["Roughness"].default_value = 0.30
    b.inputs["Anisotropic"].default_value = 0.15
    n = _noise(nt, 12.0, 5.0, 0.6, (-520, 100))
    mr = _maprange(nt, 0.22, 0.42, (-260, 100))
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    MAT["gunmetal"] = m

    # concrete
    m, nt, b = _new_mat("AGED_CONCRETE")
    b.inputs["Roughness"].default_value = 0.82
    b.inputs["Metallic"].default_value = 0.0
    n = _noise(nt, 5.5, 8.0, 0.72, (-620, 160))
    r = _ramp(nt, (0.040, 0.037, 0.034, 1), (0.180, 0.160, 0.135, 1), (-280, 160))
    nt.links.new(n.outputs["Fac"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Base Color"])
    n2 = _noise(nt, 38.0, 7.0, 0.65, (-620, -180))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (0, -220)
    bump.inputs["Strength"].default_value = 0.28
    bump.inputs["Distance"].default_value = 0.10
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MAT["concrete"] = m

    # darker concrete for ruins
    m, nt, b = _new_mat("CONCRETE_DARK")
    b.inputs["Base Color"].default_value = (0.030, 0.028, 0.026, 1)
    b.inputs["Roughness"].default_value = 0.88
    n = _noise(nt, 8.0, 7.0, 0.7, (-520, 80))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (0, -200)
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.12
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MAT["concrete_dark"] = m

    # wet floor
    m, nt, b = _new_mat("WET_FLOOR")
    b.inputs["Base Color"].default_value = (0.006, 0.0055, 0.005, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.12
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.03
    n = _noise(nt, 2.6, 7.0, 0.6, (-620, 140))
    mr = _maprange(nt, 0.035, 0.30, (-280, 140))
    nt.links.new(n.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    n2 = _noise(nt, 32.0, 5.0, 0.55, (-620, -160))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (0, -200)
    bump.inputs["Strength"].default_value = 0.06
    bump.inputs["Distance"].default_value = 0.08
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MAT["floor"] = m

    # red emissive
    m, nt, b = _new_mat("RED_EMISSIVE")
    b.inputs["Base Color"].default_value = (0.10, 0.0, 0.005, 1)
    b.inputs["Roughness"].default_value = 0.25
    b.inputs["Emission Color"].default_value = (1.0, 0.005, 0.012, 1)
    b.inputs["Emission Strength"].default_value = 12.0
    MAT["red"] = m

    m, nt, b = _new_mat("RED_HOT")
    b.inputs["Base Color"].default_value = (0.2, 0.01, 0.005, 1)
    b.inputs["Roughness"].default_value = 0.2
    b.inputs["Emission Color"].default_value = (1.0, 0.12, 0.06, 1)
    b.inputs["Emission Strength"].default_value = 22.0
    MAT["red_hot"] = m

    # white practical / small emitter
    m, nt, b = _new_mat("WHITE_EMIT")
    b.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.95, 0.9, 1)
    b.inputs["Emission Strength"].default_value = 8.0
    MAT["white_emit"] = m

    # fabric
    m, nt, b = _new_mat("RED_FABRIC")
    b.inputs["Base Color"].default_value = (0.14, 0.004, 0.008, 1)
    b.inputs["Roughness"].default_value = 0.86
    b.inputs["Sheen Weight"].default_value = 0.55
    b.inputs["Sheen Tint"].default_value = (1.0, 0.05, 0.05, 1)
    n = _noise(nt, 30.0, 6.0, 0.6, (-520, 0))
    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (0, -200)
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.06
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    MAT["fabric"] = m

    # black glass
    m, nt, b = _new_mat("BLACK_GLASS")
    b.inputs["Base Color"].default_value = (0.002, 0.0025, 0.003, 1)
    b.inputs["Metallic"].default_value = 0.15
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Coat Weight"].default_value = 0.6
    b.inputs["Coat Roughness"].default_value = 0.03
    MAT["glass"] = m

    # LED screen
    m, nt, b = _new_mat("LED_RED")
    b.inputs["Base Color"].default_value = (0.01, 0.0, 0.0, 1)
    b.inputs["Roughness"].default_value = 0.22
    b.inputs["Emission Strength"].default_value = 1.2
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.location = (-650, 100)
    wave.wave_type = "BANDS"
    wave.bands_direction = "DIAGONAL"
    wave.inputs["Scale"].default_value = 3.2
    wave.inputs["Distortion"].default_value = 2.0
    wave.inputs["Detail"].default_value = 3.0
    n = _noise(nt, 6.0, 6.0, 0.6, (-650, -160))
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.location = (-380, 0)
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.55
    nt.links.new(wave.outputs["Color"], mix.inputs["Color1"])
    nt.links.new(n.outputs["Color"], mix.inputs["Color2"])
    r = _ramp(nt, (0.002, 0.0, 0.0, 1), (0.55, 0.005, 0.01, 1), (-150, 20))
    nt.links.new(mix.outputs["Color"], r.inputs["Fac"])
    nt.links.new(r.outputs["Color"], b.inputs["Emission Color"])
    MAT["led"] = m

    # dust / ember
    m, nt, b = _new_mat("DUST")
    b.inputs["Base Color"].default_value = (0.2, 0.05, 0.03, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.18, 0.10, 1)
    b.inputs["Emission Strength"].default_value = 2.5
    MAT["dust"] = m

    # star sigil dark red
    m, nt, b = _new_mat("SIGIL")
    b.inputs["Base Color"].default_value = (0.35, 0.01, 0.02, 1)
    b.inputs["Metallic"].default_value = 0.5
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Emission Color"].default_value = (0.8, 0.01, 0.02, 1)
    b.inputs["Emission Strength"].default_value = 0.8
    MAT["sigil"] = m

    # black backing
    m, nt, b = _new_mat("BLACK_METAL")
    b.inputs["Base Color"].default_value = (0.008, 0.008, 0.009, 1)
    b.inputs["Metallic"].default_value = 0.6
    b.inputs["Roughness"].default_value = 0.38
    MAT["black_metal"] = m

    for m in MAT.values():
        m.use_fake_user = True
    return MAT


# ------------------------------------------------------------------ geometry helpers

def _link(ob, coll):
    c = coll or COLL.get("MAIN_HALL") or bpy.context.scene.collection
    c.objects.link(ob)
    return ob


def _finish(ob, name, mat, coll, bevel=0.0, smooth=False):
    ob.name = name
    if mat:
        ob.data.materials.append(mat)
    _link(ob, coll)
    if bevel > 0:
        md = ob.modifiers.new("BEVEL", "BEVEL")
        md.width = bevel
        md.segments = 2
        md.limit_method = "ANGLE"
        md.angle_limit = math.radians(40)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    return ob


def box(name, size, loc, mat, coll=None, rot=(0, 0, 0), bevel=0.0):
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
    return _finish(ob, name, mat, coll, bevel)


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


def sphere(name, radius, loc, mat, coll=None, seg=16, rings=8, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co.x *= scale[0]
        v.co.y *= scale[1]
        v.co.z *= scale[2]
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    return _finish(ob, name, mat, coll, 0.0, True)


def ico(name, radius, loc, mat, coll=None, sub=1, scale=(1, 1, 1), rot=(0, 0, 0)):
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


def torus(name, major, minor, loc, mat, coll=None, mseg=48, nseg=12,
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


def curve_tube(name, points, radius, mat, coll=None, res=8, bevel_res=2,
               cyclic=False):
    cu = bpy.data.curves.new(name + "_C", "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = res
    cu.bevel_depth = radius
    cu.bevel_resolution = bevel_res
    cu.fill_mode = "FULL"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (co[0], co[1], co[2], 1.0)
    sp.use_cyclic_u = cyclic
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    _link(ob, coll)
    return ob


def text_obj(name, body, font, size, loc, rot, mat, coll=None,
             extrude=0.06, bevel=0.008, offset=0.0, align="CENTER",
             line=1.0):
    cu = bpy.data.curves.new(name + "_C", type="FONT")
    cu.body = body
    cu.font = font
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.offset = offset
    cu.space_line = line
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = Euler(rot)
    _link(ob, coll)
    return ob


def text_to_mesh(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    me.materials.clear()
    for slot in ob.material_slots:
        if slot.material:
            me.materials.append(slot.material)
    new = bpy.data.objects.new(ob.name + "_MESH", me)
    new.matrix_world = ob.matrix_world.copy()
    colls = list(ob.users_collection)
    for c in colls:
        c.objects.link(new)
    bpy.data.objects.remove(ob, do_unlink=True)
    return new


def join_objects(objs, name):
    """Join meshes without bpy.ops, preserving world placement and materials.

    The joined mesh is expressed in the first object's local space, so the
    resulting object keeps that object's matrix_world.  This makes the result
    safe to move afterwards.
    """
    objs = [o for o in objs if o and o.name in bpy.data.objects
            and o.type == "MESH"]
    if not objs:
        return None
    bpy.context.view_layer.update()
    target = objs[0]
    M = target.matrix_world.copy()
    Minv = M.inverted()
    mats = []
    bm = bmesh.new()
    for ob in objs:
        mat_map = []
        for slot in ob.material_slots:
            m = slot.material
            if m is not None and m not in mats:
                mats.append(m)
            mat_map.append(mats.index(m) if m is not None else 0)
        src = bmesh.new()
        src.from_mesh(ob.data)
        src.transform(Minv @ ob.matrix_world)
        vmap = {}
        for v in src.verts:
            vmap[v] = bm.verts.new(v.co)
        for f in src.faces:
            try:
                nf = bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                continue
            if mat_map:
                try:
                    nf.material_index = mat_map[f.material_index]
                except Exception:
                    nf.material_index = 0
            nf.smooth = f.smooth
        src.free()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_M")
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    new = bpy.data.objects.new(name, me)
    new.matrix_world = M
    colls = list(target.users_collection)
    if colls:
        colls[0].objects.link(new)
    else:
        bpy.context.scene.collection.objects.link(new)
    for ob in objs:
        bpy.data.objects.remove(ob, do_unlink=True)
    return new


def origin_to_world(ob):
    """Bake the object transform into the mesh and reset it to identity."""
    bpy.context.view_layer.update()
    M = ob.matrix_world.copy()
    for v in ob.data.vertices:
        v.co = M @ v.co
    ob.matrix_world.identity()
    ob.data.update()


def apply_modifiers(ob):
    """Apply the modifier stack without bpy.ops (context-safe)."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.data = me
    ob.modifiers.clear()
    if old.users == 0:
        bpy.data.meshes.remove(old)
    ob.data.update()
    return ob


def load_font(fname):
    if fname in FONTS:
        return FONTS[fname]
    for d in FONT_DIRS:
        p = os.path.join(d, fname)
        if os.path.exists(p):
            f = bpy.data.fonts.load(p, check_existing=True)
            FONTS[fname] = f
            return f
    raise FileNotFoundError(fname)


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def make_camera(name, loc, target, lens=35.0, coll=None):
    cd = bpy.data.cameras.new(name + "_D")
    cd.lens = lens
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.1
    cd.clip_end = 500
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    look_at(ob, target)
    _link(ob, coll or COLL.get("CAMS"))
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
    _link(ob, coll or COLL.get("WHITE_SPOT"))
    return ob


def spot_light(name, loc, target, energy, angle=25.0, blend=0.35,
               color=(1, 1, 1), coll=None):
    ld = bpy.data.lights.new(name + "_D", "SPOT")
    ld.energy = energy
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.color = color
    ld.shadow_soft_size = 0.3
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    look_at(ob, target)
    _link(ob, coll or COLL.get("WHITE_SPOT"))
    return ob


def point_light(name, loc, energy, color=(1, 1, 1), radius=0.2, coll=None):
    ld = bpy.data.lights.new(name + "_D", "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ld.use_shadow = False
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    _link(ob, coll or COLL.get("RED_NEON"))
    return ob


def save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)


def render_still(path, cam, res=(540, 960), samples=16, frame=None):
    sc = bpy.context.scene
    old = (sc.camera, sc.render.resolution_x, sc.render.resolution_y,
           sc.eevee.taa_render_samples, sc.render.filepath)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.eevee.taa_render_samples = samples
    sc.render.filepath = path
    if frame is not None:
        sc.frame_set(frame)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    sc.camera, sc.render.resolution_x, sc.render.resolution_y, \
        sc.eevee.taa_render_samples, sc.render.filepath = old
    print("RENDER", path)
