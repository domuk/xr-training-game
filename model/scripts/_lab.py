"""Lab helpers (on top of _lib.py). Load with:  exec(open(LAB).read())
Conventions (MODEL-SPEC §14): metres, Z up, origin = floor centre of the room, X across (door wall at -Y).
Everything under `lab_root`; grabbable things as `asset_*`, scenery under `fixed_*`; slot markers `slot_*`.
Built in the live Blender session; saved to assets/blender/lab.blend."""
import bpy, bmesh, math, os, json
exec(open(os.path.join(HERE, "_lib.py")).read())
from mathutils import Matrix, Vector
BLEND = os.path.join(ROOT, "assets", "blender", "lab.blend")
TEX = os.path.join(ROOT, "assets", "blender", "tex"); os.makedirs(TEX, exist_ok=True)

# ---------- room dimensions (shared by all lab scripts) ----------
RW, RD, RH = 9.0, 7.2, 3.6          # room inside: width X, depth Y, wall height
CEIL = 4.0                          # structural ceiling (above the strut grid)
STRUT_Z = 3.2                       # unistrut grid height
TILE = 0.6                          # raised-floor tile

_MAT_DEFS.update({
    "M_LabWall": ("#E9E8E1", 0.7, 0), "M_LabSeam": ("#BDBCB4", 0.7, 0), "M_LabCeil": ("#D9D9D6", 0.8, 0),
    "M_Galv": ("#A9ADB0", 0.45, 1.0), "M_SocketGrey": ("#8E9296", 0.4, 0.8), "M_SocketDark": ("#2A2A2A", 0.5, 0),
    "M_DoorGrey": ("#B4B8BA", 0.5, 0.2), "M_DoorFrame": ("#A5A9AB", 0.5, 0.3), "M_Glass": ("#B8D0D8", 0.05, 0), "M_FrostGlass": ("#E4E8EA", 0.55, 0),
    "M_Chequer": ("#BFC2C4", 0.45, 0.3), "M_SteelHandle": ("#C9CBCD", 0.25, 1.0), "M_CallGreen": ("#1E9E4A", 0.5, 0),
    "M_DeskWhite": ("#F1F1EE", 0.55, 0), "M_PedWhite": ("#ECEBE6", 0.5, 0), "M_ColumnWhite": ("#F2F2F0", 0.6, 0),
    "M_LEDDiffuser": ("#F4F4F4", 0.4, 0), "M_RackBlack": ("#18191A", 0.55, 0.3), "M_RackRail": ("#2A2B2D", 0.5, 0.6),
    "M_BottBlue": ("#1F48B8", 0.4, 0.3), "M_BottGrey": ("#D9DAD6", 0.5, 0.2), "M_Card": ("#B98E5A", 0.8, 0),
    "M_TVBlack": ("#0D0D0E", 0.15, 0), "M_CommandoBlue": ("#1F5FD6", 0.5, 0), "M_CableBlack": ("#151515", 0.6, 0),
    "M_Rubber": ("#202020", 0.8, 0), "M_PDURed": ("#B0202A", 0.5, 0),
})

def lab_coll(name):
    return coll(name, coll("lab"))

def lab_root():
    r = bpy.data.objects.get("lab_root")
    if not r:
        r = bpy.data.objects.new("lab_root", None); coll("lab").objects.link(r); r.empty_display_size = 0.3
    return r

def lnode(name, loc, c, parent=None, **props):
    """Empty under lab_root (or parent) with metadata."""
    e = bpy.data.objects.get(name)
    if e: bpy.data.objects.remove(e, do_unlink=True)
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.05; c.objects.link(e)
    place(e, loc, parent or lab_root()); setp(e, **props); return e

def lfixed(name, c):
    return lnode(f"fixed_{name}", (0, 0, 0), c, role="fixed")

def tex_material(name, img_path, rough=0.6, metal=0.0, alpha_clip=False, normal=None, repeat_note=""):
    """Image-textured material (glTF friendly). alpha_clip uses a Round node -> exported as alphaMode MASK."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    img = bpy.data.images.load(img_path, check_existing=True); img.reload()
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if alpha_clip:
        r = nt.nodes.new("ShaderNodeMath"); r.operation = "ROUND"
        nt.links.new(t.outputs["Alpha"], r.inputs[0]); nt.links.new(r.outputs[0], b.inputs["Alpha"])
        try: m.surface_render_method = "DITHERED"
        except Exception: pass
    if normal:
        ni = bpy.data.images.load(normal, check_existing=True); ni.colorspace_settings.name = "Non-Color"
        tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = ni; nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (0.5, 0.5, 0.5, 1)
    return m

def save_png(name, rgba):
    """rgba: numpy HxWx4 float 0..1, top row first."""
    import numpy as np
    h, w = rgba.shape[:2]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h, alpha=True)
    if tuple(img.size) != (w, h): img.scale(w, h)
    img.pixels = np.ascontiguousarray(rgba[::-1]).ravel().tolist()
    path = os.path.join(TEX, name + ".png"); img.filepath_raw = path; img.file_format = "PNG"; img.save()
    return path

def uv_box(o, scale=1.0):
    """Box-project UVs in world-ish metres (u,v = metres * scale) for tiling textures."""
    me = o.data; uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co + o.location
            u, v = [(co.y, co.z), (co.x, co.z), (co.x, co.y)][ax]
            uvl.data[li].uv = (u * scale, v * scale)

def lab_save():
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)

def tquad(p, pts, uvs, m):
    """Textured quad into Part p: pts = 4 world points (CCW seen from the front), uvs = 4 (u, v)."""
    bm = p.bm; uvl = bm.loops.layers.uv.verify()
    vs = [bm.verts.new(Vector(q) - p.o) for q in pts]
    f = bm.faces.new(vs); f.material_index = p._mi(m)
    for l, uv in zip(f.loops, uvs): l[uvl].uv = uv
    return f
