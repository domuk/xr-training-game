"""Hall export -> assets/glb/datahall.glb + assets/glb/datahall_manifest.json (as 60_lab_export.py does for the lab).
Run headless after the hall scripts + qa_hall:  python -c "import runpy; runpy.run_path('assets/blender/scripts/79_hall_export.py')"
Everything in the `datahall` collection, custom properties as glTF extras, +Y up, modifiers applied.
Manifest: every node with a role, its world position, and for moving parts the axis in WORLD Blender axes
(X east, Y north, Z up); glTF = (x, z, -y) of these."""
import bpy, json, os
from mathutils import Vector, Matrix
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "assets", "blender", "datahall.blend"))
OUT = os.path.join(ROOT, "assets", "glb"); os.makedirs(OUT, exist_ok=True)
GLB, MAN = os.path.join(OUT, "datahall.glb"), os.path.join(OUT, "datahall_manifest.json")
hall = bpy.data.collections["datahall"]
objs = list(hall.all_objects)
for o in objs: o.hide_set(False); o.hide_viewport = False; o.hide_render = False
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["hall_root"]
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
lay = json.load(open(os.path.join(ROOT, "assets", "blender", "datahall_layout.json")))
man = {"file": "datahall.glb", "units": "metres", "up": "+Y (glTF); Blender source is Z-up",
       "note": "positions/axes below are WORLD Blender axes (X east, Y north, Z up); glTF = (x, z, -y)",
       "room": {"size": [lay["room"]["W"], lay["room"]["L"]], "wall_h": lay["room"]["wall_h"], "roof": lay["room"]["roof"],
                "origin": "centre of the room, floor level"},
       "layout": {k: lay[k] for k in ("rows", "hot_aisles", "pdc", "incoming_feed", "devices", "empty_positions") if k in lay},
       "nodes": {}}
for o in objs:
    r = o.get("role")
    if not r: continue
    d = {k: conv(v) for k, v in o.items() if not k.startswith(("_", "cycles"))}
    d["parent"] = o.parent.name if o.parent else None
    d["pos"] = [round(x, 5) for x in o.matrix_world.translation]
    if r == "moving" and "axis" in d:
        a = d["axis"]; s = -1 if a.startswith("-") else 1
        m = o.parent.matrix_world.to_3x3() if o.parent else Matrix.Identity(3)
        d["axis_world"] = [round(x * s, 5) for x in (m @ AX[a[-1]])]
    man["nodes"][o.name] = d
json.dump(man, open(MAN, "w"), indent=1)
counts = {}
for v in man["nodes"].values(): counts[v["role"]] = counts.get(v["role"], 0) + 1
dg = bpy.context.evaluated_depsgraph_get(); T = 0
for o in objs:
    if o.type == "MESH":
        me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); T += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
mats = {m.name for o in objs if o.type == "MESH" for m in o.data.materials if m}
print("HALL_EXPORT", {"glb_mb": round(os.path.getsize(GLB) / 1e6, 2), "objects": len(objs), "tris": T, "materials": len(mats), **counts})
