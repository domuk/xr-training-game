"""Export — app/public/gltf/server/server.glb + server_manifest.json.
Everything under server_root (fixed scenery, grabbable assets, moving parts, fasteners, slot markers) with custom
properties as glTF extras, +Y up. Excludes the 'display' layout copies, cameras and lights. The lid is fitted
for the export and put back aside afterwards."""
import bpy, json, os
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())

OUT = os.path.join(ROOT, "app", "public", "gltf", "server"); os.makedirs(OUT, exist_ok=True)
GLB, MAN = os.path.join(OUT, "server.glb"), os.path.join(OUT, "server_manifest.json")

for c in bpy.data.collections["server"].children_recursive: c.hide_viewport = False
lid = bpy.data.objects["asset_lid"]; aside = tuple(lid.location)
lid.location = (0.0, 0.0, 0.0892)                          # fitted for the export
bpy.context.view_layer.update()

root = bpy.data.objects["server_root"]
objs = [root] + list(root.children_recursive)
bpy.ops.object.select_all(action="DESELECT")
for o in objs:
    o.hide_set(False); o.hide_viewport = False; o.select_set(True)
bpy.context.view_layer.objects.active = root

bpy.ops.export_scene.gltf(filepath=GLB, use_selection=True, export_extras=True, export_yup=True, export_apply=True,
                          export_cameras=False, export_lights=False, export_materials="EXPORT")

# ---------- manifest: everything the app needs to drive the parts ----------
def conv(v):
    if hasattr(v, "to_dict"): return {k: conv(x) for k, x in v.to_dict().items()}
    if hasattr(v, "to_list"): return [conv(x) for x in v.to_list()]
    if isinstance(v, (list, tuple)): return [conv(x) for x in v]
    if isinstance(v, float): return round(v, 6)
    return v
def props(o):
    return {k: conv(v) for k, v in o.items() if k not in ("_RNA_UI",) and not k.startswith("cycles")}
def parent_asset(o):
    q = o.parent
    while q and q.get("role") != "asset": q = q.parent
    return q.name if q else None
man = {"file": "server.glb", "units": "metres", "up": "+Y (glTF); Blender source is Z-up",
       "note": "pull steps / axes / slot positions below are in Blender axes (X right, Y back, Z up). "
               "glTF conversion: (x, y, z)_blender -> (x, z, -y)_gltf",
       "assets": {}, "moving": {}, "fasteners": {}, "indicators": {}, "slots": {}}
for o in objs:
    r = o.get("role")
    if r == "asset":
        man["assets"][o.name] = {"parent_asset": parent_asset(o), **props(o)}
    elif r == "moving":
        man["moving"][o.name] = {"asset": parent_asset(o), **props(o)}
    elif r == "fastener":
        man["fasteners"][o.name] = {"asset": parent_asset(o), **props(o)}
    elif r == "indicator":
        man["indicators"][o.name] = {"asset": parent_asset(o), **props(o)}
    if o.name.startswith("slot_") and o.type == "EMPTY":
        man["slots"][o.name] = [round(v, 5) for v in o.matrix_world.translation]
json.dump(man, open(MAN, "w"), indent=1)

lid.location = aside; bpy.ops.object.select_all(action="DESELECT"); save()
print("EXPORT", {"glb_mb": round(os.path.getsize(GLB) / 1e6, 2), "objects": len(objs),
                 "assets": len(man["assets"]), "moving": len(man["moving"]), "fasteners": len(man["fasteners"]),
                 "slots": len(man["slots"])})
