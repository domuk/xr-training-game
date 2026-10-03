"""Shared helpers for all asset scripts. Load with:  exec(open(LIB).read())
Conventions (MODEL-SPEC §5, §12.3c, §12.3d):
  - metres, Z up, front faces -Y, origin front-bottom-middle
  - every replaceable part = one empty `asset_<name>` (grab pivot) with its meshes as children
  - fixed scenery under empties `fixed_<name>`; everything under `server_root`
  - motion metadata as custom properties (exported to glTF extras)"""
import bpy, bmesh, json, math, os
from mathutils import Matrix, Vector

# Paths are relative to model/server.blend (open it before running scripts).
MODEL = bpy.path.abspath("//")
ROOT = os.path.dirname(os.path.normpath(MODEL))
LAYOUT = os.path.join(MODEL, "layout.json")
BLEND = os.path.join(MODEL, "server.blend")

def load_layout():
    return json.load(open(LAYOUT)) if os.path.exists(LAYOUT) else {"slots": {}}

def save_layout(d):
    os.makedirs(os.path.dirname(LAYOUT), exist_ok=True)
    json.dump(d, open(LAYOUT, "w"), indent=1)

# ---------- collections ----------
def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]:
        p.children.link(c)
    return c

def server_coll():
    return coll("server")

def wipe(c):
    for o in list(c.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)

def server_root():
    r = bpy.data.objects.get("server_root")
    if not r:
        r = bpy.data.objects.new("server_root", None); server_coll().objects.link(r)
        r.empty_display_size = 0.05
    return r

# ---------- materials ----------
_MAT_DEFS = {
    "M_ShellGrey": ("#6E6F71", 0.5, 0.6), "M_Zinc": ("#B9BBBD", 0.45, 1.0), "M_EarAlu": ("#CFD1D3", 0.25, 1.0),
    "M_CaddyBlack": ("#1B1B1C", 0.55, 0), "M_CaddyRed": ("#D2504A", 0.5, 0), "M_DriveGrey": ("#3A3B3D", 0.4, 0.5),
    "M_PCBGreen": ("#2F5A3A", 0.5, 0), "M_ChipBlack": ("#141414", 0.4, 0), "M_FanBlack": ("#1F1F20", 0.6, 0),
    "M_FanTan": ("#B39E78", 0.6, 0), "M_HeatsinkFin": ("#4A4541", 0.4, 1.0), "M_Copper": ("#B87333", 0.35, 1.0),
    "M_SocketSilver": ("#C4C6C8", 0.3, 1.0), "M_SlotBlack": ("#151515", 0.5, 0), "M_PlugWhite": ("#E6E2D6", 0.5, 0),
    "M_SATARed": ("#C8383A", 0.5, 0), "M_ZipTie": ("#EDEDED", 0.5, 0), "M_IOShield": ("#B9BBBD", 0.45, 1.0),
    "M_Screw": ("#AEB0B2", 0.35, 1.0), "M_ClipGrey": ("#C9C9C6", 0.5, 0), "M_Gold": ("#C9A14A", 0.3, 1.0),
    "M_Wire_Black": ("#1A1A1A", 0.5, 0), "M_Wire_Red": ("#C8383A", 0.5, 0), "M_Wire_Yellow": ("#E2C23A", 0.5, 0),
    "M_Wire_Blue": ("#3D6FC2", 0.5, 0), "M_IO_Purple": ("#7B5BA6", 0.5, 0), "M_IO_Green": ("#4FA35A", 0.5, 0),
    "M_IO_Blue": ("#3D7FC2", 0.5, 0), "M_IO_Yellow": ("#E2C23A", 0.5, 0), "M_IO_Pink": ("#D9809A", 0.5, 0),
    "M_USB3Blue": ("#1E5BC6", 0.5, 0), "M_TabMaroon": ("#7A1F2B", 0.5, 0), "M_VGABlue": ("#2B4FA0", 0.5, 0), "M_UIDBlue": ("#2F6FE0", 0.4, 0),
    "M_ScrewDark": ("#4E5052", 0.5, 1.0), "M_Choke": ("#4B4B4E", 0.6, 0.2), "M_CapBody": ("#1E2A22", 0.4, 0.3),
    "M_LabelWhite": ("#F2F2F2", 0.6, 0), "M_LabelBlack": ("#101010", 0.6, 0), "M_CordBlack": ("#202020", 0.6, 0),
}
_EMIT = {"M_LEDGreen": "#3CCB5A", "M_LEDRed": "#E0302A", "M_LEDAmber": "#F0A020", "M_LEDBlue": "#3A7BFF"}

def _lin(hexcol):
    h = hexcol.lstrip("#")
    return [(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
            for c in (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))]

def M(name):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    if name in _EMIT:
        lin = _lin(_EMIT[name]); rough, metal = 0.4, 0
        bsdf.inputs["Emission Color"].default_value = (*lin, 1)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    else:
        hexcol, rough, metal = _MAT_DEFS[name]; lin = _lin(hexcol)
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*lin, 1)
    return m

# ---------- mesh builder (world coordinates in, local mesh out) ----------
class Part:
    def __init__(self, name, origin=(0, 0, 0)):
        self.name, self.o, self.bm, self.mats = name, Vector(origin), bmesh.new(), []
    def _mi(self, m):
        if m not in self.mats: self.mats.append(m)
        return self.mats.index(m)
    def _tag(self, verts, m):
        i = self._mi(m)
        for f in {f for v in verts for f in v.link_faces}: f.material_index = i
    def box(self, x0, x1, y0, y1, z0, z1, m, mtx=None):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        for v in r["verts"]:
            p = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0),
                        (z0 + z1) / 2 + v.co.z * (z1 - z0)))
            v.co = (mtx @ p if mtx else p) - self.o
        self._tag(r["verts"], m)
    def cyl(self, c, axis, a0, a1, r, m, segs=12):
        """Cylinder centred on point c (2 coords used), along axis 'X'|'Y'|'Z' from a0 to a1."""
        rot = {"X": Matrix.Rotation(math.radians(90), 4, "Y"), "Y": Matrix.Rotation(math.radians(90), 4, "X"),
               "Z": Matrix.Identity(4)}[axis]
        mid = Vector(c); idx = "XYZ".index(axis); mid[idx] = (a0 + a1) / 2
        res = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=segs, radius1=r, radius2=r,
                                    depth=abs(a1 - a0), matrix=Matrix.Translation(mid - self.o) @ rot)
        self._tag(res["verts"], m)
    def tri(self, pts, m):
        vs = [self.bm.verts.new(Vector(p) - self.o) for p in pts]
        self.bm.faces.new(vs).material_index = self._mi(m)
    def mesh(self):
        me = bpy.data.meshes.get(self.name)
        if me: bpy.data.meshes.remove(me)
        me = bpy.data.meshes.new(self.name); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats: me.materials.append(m)
        return me
    def build(self, c, parent=None, name=None, me=None):
        me = me or self.mesh()
        o = bpy.data.objects.new(name or self.name, me); c.objects.link(o)
        place(o, self.o, parent)
        return o

def place(o, world_loc, parent=None):
    """Put object at a world location, optionally parented (no rotation/scale on parents)."""
    if parent:
        o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
        pw, q = Vector(), parent                      # parent world position (matrix_world may be stale)
        while q: pw += q.location; q = q.parent
        o.location = Vector(world_loc) - pw
    else:
        o.location = Vector(world_loc)

def text_mesh(name, txt, size, m, align="CENTER"):
    cu = bpy.data.curves.new("tmp_txt", "FONT"); cu.body = txt; cu.size = size
    cu.align_x = align; cu.align_y = "CENTER"
    o = bpy.data.objects.new("tmp_txt", cu); bpy.context.scene.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o); bpy.data.curves.remove(cu)
    old = bpy.data.meshes.get(name)
    if old: bpy.data.meshes.remove(old)
    me.name = name; me.materials.clear(); me.materials.append(m)
    return me

def text_obj(name, txt, size, m, loc, c, parent=None, rot=(0, 0, 0), align="CENTER"):
    o = bpy.data.objects.new(name, text_mesh(name, txt, size, m, align)); c.objects.link(o)
    o.rotation_euler = rot; place(o, loc, parent); return o

# ---------- screws with real drive recesses ----------
def screw_mesh(name, r, h, kind="phillips", mat="M_Screw", shaft=None, segs=20):
    """Shared screw mesh, origin at the head's underside centre, axis +Z (head above, shaft below).
    kind: 'phillips' (cross recess) | 'torx' (6-point star) | 'slot'. shaft=(radius, length) or None.
    The recess is a real boolean cut; its faces get the darker M_ScrewDark."""
    me = bpy.data.meshes.get(name)
    if me and me.get("built") == 2: return me
    p = Part(name + "_tmp"); p.cyl((0, 0, 0), "Z", 0, h, r, M(mat), segs)
    if shaft: p.cyl((0, 0, 0), "Z", -shaft[1], 0, shaft[0], M(mat), 6)
    head = p.build(bpy.context.scene.collection)
    d = h * 0.55; w = r * (0.32 if kind != "torx" else 0.38); L = r * (1.30 if kind != "torx" else 1.15)
    for a in {"phillips": (0, 90), "torx": (0, 60, 120), "slot": (0,)}[kind]:     # one cutter per arm (no self-overlap)
        k = Part(name + "_cut"); k.box(-L / 2, L / 2, -w / 2, w / 2, h - d, h + 0.001, M("M_ScrewDark"),
                                       Matrix.Rotation(math.radians(a), 4, "Z"))
        cut = k.build(bpy.context.scene.collection)
        md = head.modifiers.new("recess", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut; md.solver = "EXACT"
        md.material_mode = "TRANSFER"
        for o in bpy.context.selected_objects: o.select_set(False)
        bpy.context.view_layer.objects.active = head; head.select_set(True)
        bpy.ops.object.modifier_apply(modifier=md.name); bpy.data.objects.remove(cut, do_unlink=True)
    new = head.data; bpy.data.objects.remove(head, do_unlink=True)
    old = bpy.data.meshes.get(name)
    if old and old != new: old.name = name + "_old"
    new.name = name; new["built"] = 2
    return new

def screw(name, me, loc, c, parent, axis="+Z"):
    """Place a shared screw mesh; axis = direction the head faces ('+Z', '-X', '+Y', ...)."""
    o = inst(name, me, loc, c, parent)
    o.rotation_euler = {"+Z": (0, 0, 0), "-Z": (math.pi, 0, 0), "+X": (0, math.pi / 2, 0), "-X": (0, -math.pi / 2, 0),
                        "+Y": (-math.pi / 2, 0, 0), "-Y": (math.pi / 2, 0, 0)}[axis]
    return o

# ---------- grouping + metadata ----------
def empty(name, loc, c, parent=None, size=0.01):
    e = bpy.data.objects.new(name, None); e.empty_display_type = "PLAIN_AXES"; e.empty_display_size = size
    c.objects.link(e); place(e, loc, parent or server_root()); return e

def asset(name, loc, c, parent=None, **props):
    """Grabbable root for a replaceable part. props: pull=[[dx,dy,dz],...] (steps, metres),
    requires='obj_a,obj_b' (moving parts/fasteners that must be actioned first), tip=..."""
    e = empty(f"asset_{name}", loc, c, parent); setp(e, role="asset", **props); return e

def inst(name, me, loc, c, parent):
    """Object sharing mesh `me` (instancing), placed at a world location."""
    o = bpy.data.objects.new(name, me); c.objects.link(o); place(o, loc, parent); return o

def fixed(name, c):
    e = empty(f"fixed_{name}", (0, 0, 0), c); setp(e, role="fixed"); return e

def setp(o, **kw):
    for k, v in kw.items():
        o[k] = v
    return o

def moving(o, motion, axis, limits, **kw):
    """motion: hinge|press|slide|screw|lift. limits: [a,b] (deg for hinge/screw turn, m for press/slide)."""
    return setp(o, role="moving", motion=motion, axis=axis, limits=list(limits), **kw)

def fastener(o, tool, turns=4, rise=0.004, **kw):
    return setp(o, role="fastener", motion="screw", axis=kw.pop("axis", "Z"), tool=tool,
                limits=[0.0, 360.0 * turns], rise=rise, **kw)

# ---------- report ----------
def tris(c):
    dg = bpy.context.evaluated_depsgraph_get(); t = 0
    for o in c.all_objects:
        if o.type in ("MESH", "CURVE"):
            ev = o.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles(); t += len(me.loop_triangles)
            ev.to_mesh_clear()
    return t

def save():
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
