"""Hall 75 — 3 parts cabinets side by side: the lab's blue tool cabinet (doors + 7 drawers + 3 shelves), copied from
lab.blend with its moving-part data (LOG.md sections 7, 11). Placed against the north wall, between the two wall
columns, facing south into the north walkway."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
hall_open()
NAMES = ["fixed_tool_cabinet", "lab_cabinet_body", "lab_cabinet_door_L", "lab_cabinet_door_R"] + \
        [f"lab_cabinet_drawer_{k}" for k in range(1, 8)] + [f"lab_cabinet_shelf_{k}" for k in range(1, 4)]
C = hall_coll("cabinets"); wipe(C); root = hfixed("cabinets", C)
LAB = from_lab(objects=NAMES)
src_root = LAB["fixed_tool_cabinet"]
CAB_W, BACK = 1.00, 0.65                    # lab cabinet: 1.0 wide (local Y), back 0.65 behind the root (local X), front = -X
for k, x in enumerate((-CAB_W, 0.0, CAB_W)):
    n = k + 1
    r = hnode(f"fixed_parts_cabinet_{n}", (x, OY + L - BACK - 0.02, 0), C, root, role="fixed", tip="tool_cabinet", number=n)
    r.rotation_euler = (0, 0, math.pi / 2)  # front (-X) faces south
    for ch in src_root.children:
        o = ch.copy(); o.name = ch.name.replace("lab_cabinet", f"parts_cabinet_{n}"); C.objects.link(o)
        o.parent = r; o.matrix_parent_inverse = Matrix.Identity(4); o.location = ch.location.copy()
for o in list(LAB.values()): bpy.data.objects.remove(o, do_unlink=True)
hall_layout("cabinets", {"x": [-1.5 * CAB_W, 1.5 * CAB_W], "back_y": OY + L - 0.02, "faces": "south"})
print("HALL_CABINETS_REPORT", {"tris": tris(C)})
hall_save()
