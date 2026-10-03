"""QA helper — exact mesh clash test (BVH). Usage inside Blender:
    exec(open(r'...\\qa_clash.py').read()); print(clash(['dimms'], ['board','chassis'], lift=0.0001))
`lift` offsets the tested geometry upward (in the BVH only, nothing is moved), so parts resting on a
surface don't count. Pairs inside the same asset/fixed group are skipped."""
import bpy, bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

def _bvh(o, off=Vector()):
    dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear(); bm.transform(Matrix.Translation(off) @ o.matrix_world)
    t = BVHTree.FromBMesh(bm); bm.free(); return t

def _objs(colls):
    out = []
    for c in colls:
        out += [o for o in bpy.data.collections[c].all_objects if o.type in ("MESH", "CURVE")]
    return out

def _group(o):
    while o.parent and o.parent.name != "server_root": o = o.parent
    return o.name

def clash(test_colls, against_colls, lift=0.0, skip=("tray_bottom",)):
    for c in bpy.data.collections["server"].children_recursive: c.hide_viewport = False
    bpy.context.view_layer.update()
    against = {o.name: _bvh(o) for o in _objs(against_colls) if o.name not in skip}
    hits = []
    for o in _objs(test_colls):
        if o.name in skip: continue
        t = _bvh(o, Vector((0, 0, lift))); g = _group(o)
        hits += [(o.name, k) for k, b in against.items() if k != o.name and _group(bpy.data.objects[k]) != g and t.overlap(b)]
    return hits
