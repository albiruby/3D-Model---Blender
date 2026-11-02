import bpy
import os

BASE = r"D:\Tes Animasi-Motion-Blender\Neon Ritual"
FONTS = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1000
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(BASE, "PREVIEW", "00_font_specimen2.png")
scene.eevee.taa_render_samples = 24
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.005, 0.005, 0.006, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.15

mat = bpy.data.materials.new("CHROME")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.85, 0.87, 0.9, 1)
b.inputs["Metallic"].default_value = 1.0
b.inputs["Roughness"].default_value = 0.12
b.inputs["Anisotropic"].default_value = 0.35
b.inputs["Emission Color"].default_value = (0.8, 0.01, 0.02, 1)
b.inputs["Emission Strength"].default_value = 0.15

def get_font(name):
    for d in (FONTS, r"C:\Windows\Fonts"):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return bpy.data.fonts.load(p, check_existing=True)
    raise FileNotFoundError(name)

def add_text(name, body, fname, size, loc, offset=0.0, extrude=0.06, bevel=0.012):
    f = get_font(fname)
    cu = bpy.data.curves.new(name + "_C", type="FONT")
    cu.body = body
    cu.font = f
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 3
    cu.offset = offset
    cu.materials.append(mat)
    ob = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(ob)
    ob.location = loc
    return ob

# rows: font name, file, offset, gap
rows = [
    ("BLACKADDER", "ITCBLKAD.TTF", 0.0, 3.7),
    ("CANTERBURY .02", "Canterbury.ttf", 0.02, 1.3),
    ("CANTERBURY .04", "Canterbury.ttf", 0.04, -1.1),
    ("BN CRINGE", "BNCringeSerifBlack.ttf", 0.0, -3.7),
]

for label, fname, off, y in rows:
    f = get_font(fname)
    cu = bpy.data.curves.new(label + "_C", type="FONT")
    cu.body = "NEON\nRITUAL"
    cu.font = f
    cu.size = 0.95
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 0.78
    cu.extrude = 0.09
    cu.bevel_depth = 0.014
    cu.bevel_resolution = 3
    cu.offset = off
    cu.materials.append(mat)
    ob = bpy.data.objects.new(label, cu)
    scene.collection.objects.link(ob)
    ob.location = (0, y, 0)

    lcu = bpy.data.curves.new(label + "_LC", type="FONT")
    lcu.body = label
    lcu.font = get_font("LeagueSpartan-Bold.otf")
    lcu.size = 0.12
    lcu.align_x = "CENTER"
    lcu.materials.append(mat)
    lob = bpy.data.objects.new(label + "_LABEL", lcu)
    scene.collection.objects.link(lob)
    lob.location = (-3.55, y, 0)

cam_data = bpy.data.cameras.new("CAM")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 9.6
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, 0, 10)
scene.camera = cam

for x, e, col in ((-4.0, 600, (1,1,1)), (4.0, 600, (1,0.02,0.02)), (0, 900, (1,1,1))):
    ld = bpy.data.lights.new("L", type="AREA")
    ld.energy = e
    ld.size = 3.0
    ld.color = col
    lo = bpy.data.objects.new("L", ld)
    scene.collection.objects.link(lo)
    lo.location = (x, 0, 5)
    lo.rotation_euler = (0, 0, 0)

bpy.ops.render.render(write_still=True)
print("FONT SPECIMEN 2", scene.render.filepath)
