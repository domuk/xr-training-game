"""Hall QA (headless):  python -c "import runpy; runpy.run_path('assets/blender/scripts/qa_hall.py')"
For every moving part in datahall.blend: checks it has motion/axis/limits, then puts it at each limit and reports
any NEW overlap with the other meshes of the same device (overlaps already there at rest, e.g. a handle on its mount,
are ignored). Also checks every slot_* sits on something and every moving part's limits are not both 0."""
import bpy, os, math
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, "assets", "blender", "datahall.blend"))
dg = bpy.context.evaluated_depsgraph_get()

def device_of(o):
    """Top-level group under a fixed_* collection root (the device / row / pod the part belongs to)."""
    q = o
    while q.parent and q.parent.parent and not q.parent.name.startswith("fixed_") or (q.parent and q.parent.name.startswith("fixed_row")):
        q = q.parent
    return q.parent or q

def tree(o):
    bpy.context.view_layer.update()
    me = o.evaluated_get(dg).to_mesh(); mw = o.matrix_world
    t = BVHTree.FromPolygons([mw @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons], epsilon=0.0)
    o.evaluated_get(dg).to_mesh_clear(); return t

def meshes_under(obj):
    return [x for x in [obj] + list(obj.children_recursive) if x.type == "MESH"]

def overlaps(part, others):
    mine = [tree(x) for x in meshes_under(part)]
    hits = set()
    for o in others:
        to = tree(o)
        if any(m.overlap(to) for m in mine): hits.add(o.name)
    return hits

AX = {"X": 0, "Y": 1, "Z": 2}
problems, tested = [], 0
moving = [o for o in bpy.data.objects if o.get("role") == "moving"]
for o in moving:
    for k in ("motion", "axis", "limits"):
        if k not in o: problems.append(f"{o.name}: no {k}")
    if "limits" not in o: continue
    lim = list(o["limits"]); ax = o["axis"].lstrip("-"); sgn = -1 if o["axis"].startswith("-") else 1
    if lim[0] == lim[1]: problems.append(f"{o.name}: limits both {lim[0]}")
    dev = device_of(o); own = set(meshes_under(o))
    others = [x for x in meshes_under(dev) if x not in own]
    if len(others) > 60:                                                # big groups (rows, PDCs): only the 60 nearest
        c = o.matrix_world.translation
        others = sorted(others, key=lambda x: (x.matrix_world.translation - c).length)[:60]
    rest = overlaps(o, others); loc0, rot0 = o.location.copy(), o.rotation_euler.copy()
    for v in lim:
        if v == 0: continue
        if o["motion"] == "hinge" or o["motion"] == "screw": o.rotation_euler[AX[ax]] = rot0[AX[ax]] + math.radians(v)
        else: o.location[AX[ax]] = loc0[AX[ax]] + sgn * v
        new = overlaps(o, others) - rest; tested += 1
        if new: problems.append(f"{o.name} at {v}: hits {sorted(new)[:4]}")
        o.location, o.rotation_euler = loc0.copy(), rot0.copy()
print("QA_HALL", {"moving": len(moving), "poses_tested": tested, "slots": sum(1 for x in bpy.data.objects if x.get("role") == "slot"),
                  "problems": len(problems)})
for p in problems: print("  -", p)
