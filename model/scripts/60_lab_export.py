"""Lab export -> assets/glb/lab.glb + assets/glb/lab_manifest.json (run in the live Blender after the lab scripts + qa_lab).
Everything in the `lab` collection, custom properties as glTF extras, +Y up, modifiers applied.
Manifest: every node with a role, its world position, and (for moving parts / pulls) the axis and pull steps converted to
WORLD Blender axes, so the app never has to know about the rotated rack-row frame. glTF = (x, z, -y) of these."""
import bpy, json, os
from mathutils import Vector, Matrix
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))   # repo root
OUT = os.path.join(ROOT, "assets", "glb"); os.makedirs(OUT, exist_ok=True)
GLB, MAN = os.path.join(OUT, "lab.glb"), os.path.join(OUT, "lab_manifest.json")
lab = bpy.data.collections["lab"]
objs = [o for o in lab.all_objects]
for o in objs: o.hide_set(False); o.hide_viewport = False
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["lab_root"]
bpy.ops.export_scene.gltf(filepath=GLB, use_selection=True, export_extras=True, export_yup=True, export_apply=True,
                          export_cameras=False, export_lights=False, export_materials="EXPORT")
bpy.ops.object.select_all(action="DESELECT")

def conv(v):
    if hasattr(v, "to_dict"): return {k: conv(x) for k, x in v.to_dict().items()}
    if hasattr(v, "to_list"): return [conv(x) for x in v.to_list()]
    if isinstance(v, (list, tuple)): return [conv(x) for x in v]
    if isinstance(v, float): return round(v, 6)
    return v
AX = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}
def world_dir(o, local):
    """Direction given in the object's parent frame -> world."""
    m = o.parent.matrix_world.to_3x3() if o.parent else Matrix.Identity(3)
    v = m @ Vector(local); return [round(x, 5) for x in v]
def frame_of(o):
    f = o.get("pull_frame"); return bpy.data.objects[f] if f and f in bpy.data.objects else o.parent
man = {"file": "lab.glb", "units": "metres", "up": "+Y (glTF); Blender source is Z-up",
       "note": "positions/axes/pulls below are WORLD Blender axes (X east, Y north, Z up); glTF = (x, z, -y)",
       "room": {"size": [8.4, 8.4], "wall_h": 3.6, "origin": "centre of the room's bounding box, floor level"},
       "nodes": {}}
for o in objs:
    r = o.get("role")
    if not r: continue
    d = {k: conv(v) for k, v in o.items() if not k.startswith(("_", "cycles"))}
    d["parent"] = o.parent.name if o.parent else None
    d["pos"] = [round(x, 5) for x in o.matrix_world.translation]
    if r == "moving" and "axis" in d:
        a = d["axis"]; s = -1 if a.startswith("-") else 1
        d["axis_world"] = [x * s for x in world_dir(o, AX[a[-1]])]
    if "pull" in d and d["pull"]:
        f = frame_of(o); m = f.matrix_world.to_3x3() if f else Matrix.Identity(3)
        d["pull_world"] = [[round(x, 5) for x in (m @ Vector(step))] for step in d["pull"]]
    man["nodes"][o.name] = d
json.dump(man, open(MAN, "w"), indent=1)
counts = {}
for v in man["nodes"].values(): counts[v["role"]] = counts.get(v["role"], 0) + 1
dg = bpy.context.evaluated_depsgraph_get(); T = 0
for o in objs:
    if o.type == "MESH":
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); T += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
mats = {m.name for o in objs if o.type == "MESH" for m in o.data.materials if m}
print("LAB_EXPORT", {"glb_mb": round(os.path.getsize(GLB) / 1e6, 2), "objects": len(objs), "tris": T, "materials": len(mats), **counts})
