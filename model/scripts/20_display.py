"""Workspace layout — a copy of every removable part laid out on the table in front of the server, grouped
and labelled. The server stays intact. Copies share mesh data, live in the 'display' collection (not
exported) and have their metadata stripped so QA ignores them."""
import bpy, math
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
from mathutils import Vector, Euler

DSP = coll("display"); wipe(DSP)
FLAT = (0, math.radians(90), 0)          # lay thin upright parts flat
GAP = 0.020

def copy_tree(o, parent=None):
    c = o.copy()                         # linked duplicate (shares mesh/curve data)
    for k in list(c.keys()):
        del c[k]
    DSP.objects.link(c)
    if parent:
        c.parent = parent; c.matrix_parent_inverse = o.matrix_parent_inverse.copy()
    else:
        c.parent = None; c.matrix_world = o.matrix_world.copy()
    for ch in o.children:
        copy_tree(ch, c)
    return c

def bbox(root):
    bpy.context.view_layer.update()
    pts = []
    for o in [root] + list(root.children_recursive):
        if o.type in ("MESH", "CURVE"):
            pts += [o.matrix_world @ Vector(v) for v in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])

def lay_row(names, y_top, x_start, rot=None, label=None, pitch=None):
    x = x_start
    for n in names:
        src = bpy.data.objects.get(n)
        if not src: continue
        c = copy_tree(src)
        if rot: c.rotation_euler = Euler(rot)
        lo, hi = bbox(c)
        c.location += Vector((x - lo.x, y_top - hi.y, -lo.z))
        x += (pitch if pitch else (hi.x - lo.x)) + GAP
    if label:
        text_obj(f"display_label_{label.lower().replace(' ', '_')}", label, 0.012, M("M_LabelWhite"),
                 (x_start, y_top + 0.012, 0.0002), DSP, None, align="LEFT")
    return x

A = lambda pat, n: [pat.format(i) for i in range(1, n + 1)]
lay_row(A("asset_caddy_{:02d}", 24), -0.10, -0.24, label="DRIVE CADDIES (with drives)")
x = lay_row(A("asset_fan_{:02d}", 3), -0.32, -0.24, label="FANS")
x = lay_row(["asset_hs_1", "asset_hs_2"], -0.32, x + 0.03, label="HEATSINKS")
x = lay_row(["asset_cpu_1", "asset_cpu_2"], -0.32, x + 0.03, label="CPUS")
x = lay_row(A("asset_dimm_{:02d}", 8), -0.32, x + 0.03, rot=FLAT, label="DIMMS")
x = lay_row(A("asset_blank_{}", 7)[2:], -0.50, -0.24, rot=FLAT, label="BLANK BRACKETS")
x = lay_row(["asset_nic"], -0.50, x + 0.03, rot=FLAT, label="NIC")
x = lay_row(["asset_accel"], -0.50, x + 0.03, rot=FLAT, label="K2T-QB CARD")
x = lay_row(["asset_psu_1", "asset_psu_2"], -0.50, x + 0.03, label="PSUS")
x = lay_row(["asset_cord_1", "asset_cord_2"], -0.50, x + 0.03, label="POWER CORDS")
x = lay_row(["asset_board"], -0.92, -0.24, label="MOTHERBOARD")
x = lay_row(["asset_backplane"], -0.92, x + 0.03, rot=(math.radians(90), 0, 0), label="BACKPLANE")
x = lay_row(["asset_shroud"], -0.92, x + 0.03, rot=FLAT, label="AIR SHROUD")
x = lay_row(["asset_cable_sata"], -0.92, x + 0.03, label="SATA CABLES")
print("DISPLAY", {"objects": len(DSP.all_objects)})
save()
