"""Lab 56 — cardboard boxes from the lab photo: tall flat TV box standing beside the big door cabinet (long side
north-south, just north of the rack row) with two long boxes on top, and a box on top of the tool cabinet."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("boxes"); wipe(C); root = lfixed("boxes", C)
R = load_layout()["lab_room"]; W, L, XI = R["W"], R["L"], R["inset_x"]; OX, OY = -W / 2, -L / 2
row = load_layout()["lab_racks"]["_row"]["origin"]                      # north end of the rack row (rear plane)
_MAT_DEFS.update({"M_CardDark": ("#9C7448", 0.8, 0), "M_CardPrint": ("#2B2B2B", 0.7, 0)})
CB, CD, PR = M("M_Card"), M("M_CardDark"), M("M_CardPrint")
b = Part("lab_boxes")
cx = OX + XI - 0.33; cy = OY + 2.20                                       # box on top of the tool cabinet
b.box(cx - 0.25, cx + 0.25, cy - 0.30, cy + 0.20, 1.95, 2.25, CB)
b.box(cx - 0.20, cx + 0.10, cy - 0.25, cy + 0.10, 2.25, 2.37, CD)
setp(b.build(C, root), role="fixed", tip="boxes")
print("BOX_REPORT", {"tris": tris(C)})
lab_save()
