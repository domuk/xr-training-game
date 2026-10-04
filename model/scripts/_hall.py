"""Data hall helpers (on top of _lib.py + the lab materials). Load with:  exec(open(os.path.join(HERE, "_hall.py")).read())
Conventions as the lab (LAB-HANDOFF): metres, Z up, X = east, Y = north, origin = centre of the room at floor level.
Everything under `hall_root`; scenery under `fixed_*`; grabbable `asset_*`; moving parts carry motion/axis/limits.
Lab parts (rack, door, card reader, materials) are copied from lab.blend, not redrawn. Saved to assets/blender/datahall.blend.
Plan (research/reference/LOG.md): 6 rows x 10 racks, rows run N-S, hot aisle containment (3 pods), doors on the south wall."""
import bpy, math, os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_lab.py")).read())       # _lib.py + lab materials, tex_material, save_png, tquad
from mathutils import Matrix, Vector
BLEND = os.path.join(ROOT, "assets", "blender", "datahall.blend")
LAB_BLEND = os.path.join(ROOT, "assets", "blender", "lab.blend")
TEX = os.path.join(ROOT, "assets", "blender", "tex")
HALL_LAYOUT = os.path.join(ROOT, "assets", "blender", "datahall_layout.json")

def hall_layout(key=None, value=None):
    """Read (and with key/value, update) assets/blender/datahall_layout.json (the lab's layout.json is not touched)."""
    d = json.load(open(HALL_LAYOUT)) if os.path.exists(HALL_LAYOUT) else {}
    if key is not None:
        d[key] = value; json.dump(d, open(HALL_LAYOUT, "w"), indent=1)
    return d

# ---------- plan (all from the SW inside corner, metres) ----------
TILE = 0.60
RACK_W, RACK_D, RACK_H = 0.60, 1.20, 2.00     # lab rack_2 (600 W x 1200 D, 42U)
N_ROWS, N_RACKS = 6, 10
HOT = 1.20                                    # hot aisle (between the rack backs of a pod)
COLD = 1.80                                   # cold aisle between pods
POD = 2 * RACK_D + HOT                        # 3.6
SIDE = 3.00                                   # west / east walkway incl. things against the wall
NORTH = 3.00                                  # north walkway
SOUTH = 3.40                                  # south walkway (doors) ...
PDC_ZONE = 0.80                               # ... plus the PDC at the south end of every row
ROW_LEN = N_RACKS * RACK_W                    # 6.0
W = 2 * SIDE + 3 * POD + 2 * COLD             # 20.4 (west-east)
L = SOUTH + PDC_ZONE + ROW_LEN + NORTH        # 13.2 (south-north)
RH, CEIL = 3.60, 4.20                         # lab wall height / roof
OX, OY = -W / 2, -L / 2
ROW_Y0 = SOUTH + PDC_ZONE                     # plan y of the south end of the racks
def P(x, y): return (OX + x, OY + y)
def pod_x0(i): return SIDE + i * (POD + COLD)  # plan x of the west face of pod i
COL_X = [SIDE + POD + COLD / 2 + i * (POD + COLD) for i in range(2)]   # free columns in the 2 cold aisles
COL_Y = [SOUTH / 2, ROW_Y0 + ROW_LEN / 2, ROW_Y0 + ROW_LEN + NORTH / 2]

_MAT_DEFS.update({
    "M_LabWall": ("#E9E8E1", 0.7, 0), "M_LabSeam": ("#BDBCB4", 0.7, 0), "M_LabCeil": ("#D9D9D6", 0.8, 0),
    "M_Galv": ("#A9ADB0", 0.45, 1.0), "M_ColumnWhite": ("#F2F2F0", 0.6, 0), "M_LEDDiffuser": ("#F4F4F4", 0.4, 0),
    "M_SteelGrey": ("#7C8084", 0.5, 0.6),
})

def roof_under(x, y):
    """World z of the underside of the roof steel above world point (x, y): main beam, joist or the roof deck.
    Hanger rods stop here (they fix to the steel, they do not pass through it). Matches 70_hall_room.py."""
    px, py = x - OX, y - OY
    if any(abs(px - c) < 0.125 for c in COL_X) or any(abs(py - c) < 0.125 for c in COL_Y): return CEIL - 0.45
    if any(abs(px - j) < 0.04 for j in [k * 1.5 for k in range(1, int(W / 1.5) + 1)] if min(abs(j - c) for c in COL_X) >= 0.4):
        return CEIL - 0.25
    return CEIL

def hall_coll(name):
    return coll(name, coll("datahall"))

def hall_root():
    r = bpy.data.objects.get("hall_root")
    if not r:
        r = bpy.data.objects.new("hall_root", None); coll("datahall").objects.link(r); r.empty_display_size = 0.3
    return r

def hnode(name, loc, c, parent=None, **props):
    e = bpy.data.objects.get(name)
    if e: bpy.data.objects.remove(e, do_unlink=True)
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.05; c.objects.link(e)
    place(e, loc, parent or hall_root()); setp(e, **props); return e

def hfixed(name, c):
    return hnode(f"fixed_{name}", (0, 0, 0), c, role="fixed")

def fix_image_paths():
    """Point every image at assets/blender/tex relative to the .blend (lab.blend stores PC paths)."""
    for im in bpy.data.images:
        if im.source == "FILE" and im.filepath:
            im.filepath = "//tex/" + os.path.basename(im.filepath.replace("\\", "/"))

def from_lab(objects=(), meshes=(), materials=()):
    """Append objects / meshes / materials from lab.blend (once). Returns {name: datablock}."""
    want_o = [n for n in objects if n not in bpy.data.objects]
    want_m = [n for n in meshes if n not in bpy.data.meshes]
    want_t = [n for n in materials if n not in bpy.data.materials]
    if want_o or want_m or want_t:
        with bpy.data.libraries.load(LAB_BLEND, link=False) as (src, dst):
            dst.objects = want_o; dst.meshes = want_m; dst.materials = want_t
        fix_image_paths()
    out = {}
    for n in objects: out[n] = bpy.data.objects[n]
    for n in meshes: out[n] = bpy.data.meshes[n]
    for n in materials: out[n] = bpy.data.materials[n]
    return out

def uv_world(o, scale, ox=0.0, oy=0.0):
    """Box-project UVs in world metres * scale (tiling textures), offset so joints start at (ox, oy)."""
    me = o.data; uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co + o.location
            u, v = [(co.y - oy, co.z), (co.x - ox, co.z), (co.x - ox, co.y - oy)][ax]
            uvl.data[li].uv = (u * scale, v * scale)

def hall_open():
    if os.path.exists(BLEND): bpy.ops.wm.open_mainfile(filepath=BLEND)
    else: bpy.ops.wm.read_factory_settings(use_empty=True)

def hall_save():
    fix_image_paths()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND, relative_remap=True)
