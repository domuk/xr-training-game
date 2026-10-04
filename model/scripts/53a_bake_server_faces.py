"""Lab 53a (headless) — render the detailed server's front and rear faces to textures for the low-poly rack server.
Opens server.blend, fits the lid, renders orthographic front/rear (transparent background) to tex/rack_server_*.png.
Run:  blender --background assets/blender/server.blend --python 53a_bake_server_faces.py"""
import bpy, os
from mathutils import Vector, Euler
TEX = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tex"))
sc = bpy.context.scene
for c in bpy.data.collections:
    if c.name == "display": c.hide_render = True
lid = bpy.data.objects["asset_lid"]; lid.location = (0, 0, 0.0892)
for o in bpy.data.objects:                                     # cords plug into the rack PDU instead
    if o.name.startswith("asset_cord"):
        for q in [o] + list(o.children_recursive): q.hide_render = True
for o in sc.objects:
    if o.type in ("CAMERA", "LIGHT"): o.hide_render = True
try: sc.render.engine = "BLENDER_EEVEE"
except TypeError: pass
for k in dir(sc.render):                                    # no metadata in the PNGs (Blender writes the .blend path otherwise)
    if k.startswith("use_stamp"):
        try: setattr(sc.render, k, False)
        except Exception: pass
sc.render.film_transparent = True; sc.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("bake"); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND"); bg.inputs[0].default_value = (1, 1, 1, 1); bg.inputs[1].default_value = 0.55
cam = bpy.data.cameras.new("bc"); cam.type = "ORTHO"; cam.ortho_scale = 0.48; cam.clip_end = 5
co = bpy.data.objects.new("bc", cam); sc.collection.objects.link(co); sc.camera = co
sun = bpy.data.lights.new("bs", "SUN"); sun.energy = 1.4; so = bpy.data.objects.new("bs", sun); sc.collection.objects.link(so)
sc.render.resolution_x, sc.render.resolution_y = 1024, 192
for name, loc, rot, srot in (("front", (0, -1.0, 0.0446), (1.5708, 0, 0), (1.3, 0, 0.3)),
                             ("rear", (0, 2.0, 0.0446), (1.5708, 0, 3.14159), (1.3, 0, 2.8))):
    co.location = loc; co.rotation_euler = Euler(rot); so.rotation_euler = Euler(srot)
    sc.render.filepath = os.path.join(TEX, f"rack_server_{name}.png"); bpy.ops.render.render(write_still=True)
print("BAKED")
