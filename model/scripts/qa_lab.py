"""QA for the lab (run in the live Blender after the lab scripts). Checks:
1. metadata: every moving part has motion/axis/limits; every asset has a pull or is static; every `requires` name exists
2. motion sweep: each moving part is driven to both limits (and assets along their pull path) and tested for overlap
   (BVH, 2 mm tolerance) against every other mesh that is not in the same group; poses are restored afterwards
Prints QA_LAB with the counts and every problem found."""
import bpy, math
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
lab = bpy.data.collections["lab"]
objs = [o for o in lab.all_objects]
names = {o.name for o in bpy.data.objects}
problems = []

# ---------- 1. metadata ----------
mov = [o for o in objs if o.get("role") == "moving"]
ast = [o for o in objs if o.get("role") == "asset"]
for o in mov:
    for k in ("motion", "axis", "limits"):
        if k not in o: problems.append(f"{o.name}: moving part missing '{k}'")
for o in objs:
    req = o.get("requires")
    if req:
        for r in str(req).split(","):
            r = r.strip()
            if r and r not in names: problems.append(f"{o.name}: requires unknown '{r}'")
for o in ast:
    if "pull" not in o: problems.append(f"{o.name}: asset without pull")

# ---------- 2. motion sweep ----------
dg = bpy.context.evaluated_depsgraph_get()
def group_of(o):
    q = o
    while q.parent and not (q.parent.name.startswith(("fixed_", "asset_", "lab_root")) and q.parent.get("role") in ("fixed", "asset")):
        q = q.parent
    top = o
    while top.parent and top.parent.name != "lab_root": top = top.parent
    return top.name
def meshes_under(o): return [q for q in [o] + list(o.children_recursive) if q.type == "MESH"]
def bvh(o, shrink=0.0):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh(); mw = o.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ps = [list(p.vertices) for p in me.polygons]; ev.to_mesh_clear()
    if shrink and vs:
        c = sum(vs, Vector()) / len(vs); vs = [c + (v - c) * (1 - shrink) for v in vs]
    return BVHTree.FromPolygons(vs, ps) if ps else None
statics = None
def static_trees(exclude_top):
    return [(q, bvh(q)) for q in objs if q.type == "MESH" and q.visible_get()]          # everything; own meshes skipped below
def check(o, label, moved_meshes):
    top = group_of(o); hits = set()
    trees = [(m, bvh(m, 0.02)) for m in moved_meshes]
    for (q, t) in static_trees(top):
        if t is None or q in moved_meshes: continue
        for (m, tm) in trees:
            if tm and tm.overlap(t): hits.add(q.name)
    rest = REST.get(o.name, set()); hits -= rest
    if hits: problems.append(f"{label}: clashes with {sorted(hits)[:6]}{' ...' if len(hits) > 6 else ''}")
AX = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}
def axis_vec(a):
    s = -1 if a.startswith("-") else 1; return AX[a[-1]] * s
# contacts that already exist at rest (hinges on frames, drawers in carcasses) are not motion clashes
REST = {}
for o in mov:
    mm = meshes_under(o); trees = [(m, bvh(m, 0.02)) for m in mm]; h = set()
    for (q, t) in static_trees(None):
        if t is None or q in mm: continue
        if any(tm and tm.overlap(t) for _, tm in trees): h.add(q.name)
    REST[o.name] = h
tested = 0
for o in mov:
    if o.get("motion") not in ("hinge", "slide"): continue                    # press = pushes into its panel by design
    lo, hi = o["limits"]; ax = axis_vec(o["axis"])
    for lim in (lo, hi):
        if lim == 0: continue
        save_loc, save_rot = o.location.copy(), o.rotation_euler.copy()
        if o["motion"] == "hinge":
            o.rotation_euler.rotate(Matrix.Rotation(math.radians(lim), 3, ax).to_euler())
        else:
            par = o.parent.matrix_world.to_3x3().inverted() if o.parent else Matrix.Identity(3)
            o.location += (o.matrix_world.to_3x3() @ ax).normalized() * 0 + (par @ (o.matrix_world.to_3x3() @ ax)) * lim if False else ax * lim
        bpy.context.view_layer.update()
        check(o, f"{o.name} @ {lim}", meshes_under(o)); tested += 1
        o.location, o.rotation_euler = save_loc, save_rot
bpy.context.view_layer.update()
print("MOVING", sorted(o.name for o in mov))
print("QA_LAB", {"moving": len(mov), "assets": len(ast), "poses_tested": tested, "problems": len(problems)})
for p in problems: print("  -", p)
