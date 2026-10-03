"""QA v2 — serviceability, driven by the metadata on the objects (MODEL-SPEC §12.3c/d).
  SCREW_ACCESS : straight ray out of every fastener head (its axis); in-place screws must be clear of everything
                 except the lid; drive screws (caddy_*) are checked with the caddy out (own asset only).
  REMOVAL      : every asset moves along its `pull` steps after its `requires` are done (those objects/assets are
                 ignored) and with its `carries` moving along; anything else it touches is a blocker.
  REQUIRES     : every name in `requires`/`carries` must exist."""
import bpy, bmesh, fnmatch
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

for c in bpy.data.collections["server"].children_recursive: c.hide_viewport = False
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()

def bvh(o, off=Vector()):
    ev = o.evaluated_get(dg); me = ev.to_mesh(); bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear()
    bm.transform(Matrix.Translation(off) @ o.matrix_world); t = BVHTree.FromBMesh(bm); bm.free(); return t

def fam(o): return {o.name} | {c.name for c in o.children_recursive}
def root_asset(o):
    q, r = o, None
    while q:
        if q.get("role") == "asset": r = q
        q = q.parent
    return r
def own_asset(o):
    q = o
    while q:
        if q.get("role") == "asset": return q
        q = q.parent

GEO = [o for o in bpy.data.collections["server"].all_objects if o.type in ("MESH", "CURVE") and o.name != "tray_bottom"]
LID = fam(bpy.data.objects["asset_lid"])
BV = {o.name: bvh(o) for o in GEO if o.name not in LID}
names = {o.name for o in bpy.data.objects}

# ---- REQUIRES sanity ----
missing = []
for o in bpy.data.objects:
    for key in ("requires", "carries"):
        for r in [x for x in str(o.get(key, "")).split(",") if x]:
            if not fnmatch.filter(names, r): missing.append((o.name, key, r))
print("REQUIRES_MISSING", missing)

# ---- SCREW ACCESS ----
AX = {"X": Vector((-1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}
bad = {}; n_ok = 0
for s in [o for o in bpy.data.objects if o.get("role") == "fastener" and o.name not in LID]:
    d = AX[s.get("axis", "Z")]; start = s.matrix_world.translation + d * 0.0025
    pool = fam(own_asset(s)) if s.name.startswith("caddy_") else BV.keys()
    hits = [k for k in pool if k in BV and k != s.name and BV[k].ray_cast(start, d, 0.15)[0] is not None]
    if hits: bad[s.name] = hits[:4]
    else: n_ok += 1
print("SCREW_ACCESS ok:", n_ok, "blocked:", bad)

# ---- REMOVAL ----
def expand(lst):
    out = set()
    for r in [x for x in lst.split(",") if x]:
        for n in fnmatch.filter(names, r):
            out |= fam(bpy.data.objects[n])
    return out
res = {}
for a in [o for o in bpy.data.objects if o.get("role") == "asset" and o.name != "asset_lid"]:
    moving_set = fam(a) | expand(str(a.get("carries", "")))
    ignore = moving_set | expand(str(a.get("requires", ""))) | LID
    if a.parent and a.parent.get("role") == "asset":   # sub-asset (drive): tested with its parent out of the server
        ignore |= set(BV.keys()) - fam(root_asset(a))
    steps = [Vector(v) for v in a.get("pull", [])]; acc = Vector(); block = set()
    for st in steps:
        for f in (0.25, 0.5, 0.75, 1.0):
            off = acc + st * f
            for m in [bpy.data.objects[n] for n in moving_set if n in BV]:
                t = bvh(m, off); block |= {k for k, b in BV.items() if k not in ignore and t.overlap(b)}
        acc += st
    res[a.name] = sorted(block)
ok = [k for k, v in res.items() if not v]
print("REMOVAL ok:", len(ok), "of", len(res))
print("REMOVAL blocked:", {k: v[:5] for k, v in res.items() if v})
