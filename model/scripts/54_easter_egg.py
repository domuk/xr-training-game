"""Lab 54 — easter egg: framed "supreme trainer" portrait (user's joke image, assets/blender/images/supremetrainer.png).
North wall, spare space west of the TVs/bench, centre 1.70 m up. Picture 0.60 x 0.80 (image 1086 x 1448, 3:4),
plain black frame 30 mm wide x 20 mm deep, 20 mm off the wall. Texture resized to 1024 px -> tex/lab_supremetrainer.png.
Node `easter_supremetrainer` has role="easter_egg" so the app can react when it's found."""
import bpy
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("easter_egg"); wipe(C); root = lfixed("easter_egg", C)
R = load_layout()["lab_room"]; W, L = R["W"], R["L"]; OX, OY = -W / 2, -L / 2
_MAT_DEFS.update({"M_FrameBlack": ("#141414", 0.45, 0)})

SRC = os.path.join(ROOT, "assets", "blender", "images", "supremetrainer.png")      # 3:4 portrait (owner, 2026-10-04)
img = bpy.data.images.load(SRC, check_existing=False); w0, h0 = img.size
img.scale(int(1024 * w0 / h0) if h0 > w0 else 1024, 1024 if h0 > w0 else int(1024 * h0 / w0))
DST = os.path.join(TEX, "lab_supremetrainer.png"); img.filepath_raw = DST; img.file_format = "PNG"; img.save()
bpy.data.images.remove(img)
mat = tex_material("M_SupremeTrainer", DST, rough=0.6)

PW = 0.60; PH = PW * h0 / w0; FW, FD = 0.03, 0.02
cx, cz = OX + 2.4, 1.70; yw = OY + L                  # wall face (north wall, facing -Y into the room)
x0, x1, z0, z1 = cx - PW / 2, cx + PW / 2, cz - PH / 2, cz + PH / 2
e = lnode("easter_supremetrainer", (cx, yw - FD, cz), C, root, role="easter_egg", tip="supreme_trainer",
          note="hidden joke portrait; framed on the north wall")
p = Part("supremetrainer_portrait", (cx, yw - FD, cz))
yp = yw - FD + 0.004                                   # picture just behind the frame front
tquad(p, [(x0, yp, z0), (x1, yp, z0), (x1, yp, z1), (x0, yp, z1)], [(0, 0), (1, 0), (1, 1), (0, 1)], mat)
FB = M("M_FrameBlack")
p.box(x0 - FW, x1 + FW, yw - FD, yw, z1, z1 + FW, FB); p.box(x0 - FW, x1 + FW, yw - FD, yw, z0 - FW, z0, FB)   # top, bottom
p.box(x0 - FW, x0, yw - FD, yw, z0, z1, FB); p.box(x1, x1 + FW, yw - FD, yw, z0, z1, FB)                       # sides
p.box(x0, x1, yw - 0.004, yw, z0, z1, FB)                                                                       # backing
p.build(C, e)
print("EGG_REPORT", {"tris": tris(C), "size": [round(PW, 3), round(PH, 3)]})
lab_save()
