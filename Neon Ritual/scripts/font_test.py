import bpy
import os

BASE = r"D:\Tes Animasi-Motion-Blender\Neon Ritual"
FONTS = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft", "Windows", "Fonts")

bpy.ops.wm.read_homefile(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(BASE, "PREVIEW", "00_font_specimen.png")
scene.eevee.taa_render_samples = 24
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.005, 0.005, 0.006, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.2

mat = bpy.data.materials.new("SPECIMEN")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.8, 0.82, 0.85, 1)
bsdf.inputs["Metallic"].default_value = 0.9
bsdf.inputs["Roughness"].default_value = 0.18
bsdf.inputs["Emission Color"].default_value = (1, 0.02, 0.02, 1)
bsdf.inputs["Emission Strength"].default_value = 0.0

label_mat = bpy.data.materials.new("LABEL")
label_mat.use_nodes = True
lb = label_mat.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.6, 0.6, 0.6, 1)
lb.inputs["Emission Color"].default_value = (0.8, 0.8, 0.8, 1)
lb.inputs["Emission Strength"].default_value = 2.0

rows = [
    ("ABADDON", "Abaddon Bold.ttf"),
    ("THESTRAL", "ThestralNeue-Bold.otf"),
    ("CRINGE", "BNCringeSerifBlack.ttf"),
    ("CANTERBURY", "Canterbury.ttf"),
]
ys = [3.0, 1.0, -1.0, -3.0]

for (label, fname), y in zip(rows, ys):
    path = os.path.join(FONTS, fname)
    font = bpy.data.fonts.load(path, check_existing=True)
    cu = bpy.data.curves.new(label + "_CURVE", type="FONT")
    cu.body = "NEON RITUAL"
    cu.font = font
    cu.size = 1.05
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.04
    cu.bevel_depth = 0.008
    cu.bevel_resolution = 2
    cu.materials.append(mat)
    ob = bpy.data.objects.new(label + "_TEXT", cu)
    scene.collection.objects.link(ob)
    ob.location = (0, y, 0)

    lcu = bpy.data.curves.new(label + "_LC", type="FONT")
    lcu.body = label
    lcu.font = bpy.data.fonts.load(os.path.join(FONTS, "LeagueSpartan-Bold.otf"), check_existing=True)
    lcu.size = 0.16
    lcu.align_x = "CENTER"
    lcu.materials.append(label_mat)
    lob = bpy.data.objects.new(label + "_LABEL", lcu)
    scene.collection.objects.link(lob)
    lob.location = (-4.6, y, 0.0)

# camera
cam_data = bpy.data.cameras.new("CAM")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 10.5
cam = bpy.data.objects.new("CAM", cam_data)
scene.collection.objects.link(cam)
cam.location = (0, 0, 10)
scene.camera = cam

# lights
for x, e in ((-4, 500), (4, 500), (0, 700)):
    ld = bpy.data.lights.new("L", type="AREA")
    ld.energy = e
    ld.size = 4
    lo = bpy.data.objects.new("L", ld)
    scene.collection.objects.link(lo)
    lo.location = (x, 0, 6)
    lo.rotation_euler = (0, 0, 0)

bpy.ops.render.render(write_still=True)
print("FONT SPECIMEN", scene.render.filepath)
