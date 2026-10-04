"""Lab 51 — tables only (no chairs, no pedestals yet): L-shaped wall desks (north wall + east wall down to the step)
and the tall white island table with A-frame legs, from the user's plan sketch + photos (assets/reference/lab).
Desks: white top 0.90 high, 0.75 deep, white end-frame legs. Island: 2.0 x 1.0, top at 1.00, long side north-south."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("tables"); wipe(C); root = lfixed("tables", C)
R = load_layout()["lab_room"]; W, L, XI, YS = R["W"], R["L"], R["inset_x"], R["step_y"]
OX, OY = -W / 2, -L / 2
def P(x, y): return (OX + x, OY + y)
WH = M("M_DeskWhite"); BH, BD, BT, t = 0.90, 0.75, 0.025, 0.02

# ---------- L desks ----------
d = Part("desks")
(xa, ya), (xb, yb) = P(3.7, L - BD), P(W - 0.30, L); d.box(xa, xb, ya, yb, BH - BT, BH, WH)          # north run (to the column)
(xa, ya), (xb, yb) = P(W - BD, 3.20), P(W, L - 0.30); d.box(xa, xb, ya, yb, BH - BT, BH, WH)    # east run (to the step)
def frame_y(x, y0, y1):          # end frame spanning y0..y1 at x (north run)
    d.box(x - t, x + t, y0 + 0.03, y0 + 0.07, 0, BH - BT, WH); d.box(x - t, x + t, y1 - 0.07, y1 - 0.03, 0, BH - BT, WH)
    d.box(x - t, x + t, y0 + 0.03, y1 - 0.03, BH - BT - 0.05, BH - BT, WH); d.box(x - t, x + t, y0 + 0.03, y1 - 0.03, 0, 0.03, WH)
def frame_x(y, x0, x1):          # end frame spanning x0..x1 at y (east run)
    d.box(x0 + 0.03, x0 + 0.07, y - t, y + t, 0, BH - BT, WH); d.box(x1 - 0.07, x1 - 0.03, y - t, y + t, 0, BH - BT, WH)
    d.box(x0 + 0.03, x1 - 0.03, y - t, y + t, BH - BT - 0.05, BH - BT, WH); d.box(x0 + 0.03, x1 - 0.03, y - t, y + t, 0, 0.03, WH)
for px in (3.75, 5.25, 6.75):
    x, _ = P(px, 0); frame_y(x, OY + L - BD, OY + L)
for py in (3.25, 4.75, 6.25):
    _, y = P(0, py); frame_x(y, OX + W - BD, OX + W)
(xa, ya), (xb, yb) = P(3.7, L - 0.06), P(W - 0.30, L - 0.04); d.box(xa, xb, ya, yb, BH - BT - 0.10, BH - BT, WH)   # wall rails
(xa, ya), (xb, yb) = P(W - 0.06, 3.20), P(W - 0.04, L - 0.30); d.box(xa, xb, ya, yb, BH - BT - 0.10, BH - BT, WH)
d.build(C, root)

# ---------- island table: 2.0 (N-S) x 1.0, top at 1.00, A-frame legs at each end ----------
TX, TY = P(5.1, 4.5); TW, TD, TH = 1.00, 2.00, 1.00
tb = Part("island_table", (TX, TY, 0))
tb.box(TX - TW / 2, TX + TW / 2, TY - TD / 2, TY + TD / 2, TH - 0.03, TH, WH)
q = 0.02
for ey in (TY - TD / 2 + 0.18, TY + TD / 2 - 0.18):
    for s in (-1, 1):                                         # A legs: close together under the top, splayed at the floor
        top = Vector((TX + s * 0.06, ey, TH - 0.03)); bot = Vector((TX + s * 0.42, ey, 0.0)); mid = (top + bot) / 2
        Ln = (top - bot).length; ang = math.atan2(top.x - bot.x, top.z - bot.z)
        mtx = Matrix.Translation(mid) @ Matrix.Rotation(ang, 4, "Y") @ Matrix.Translation(-mid)
        tb.box(mid.x - q, mid.x + q, ey - q, ey + q, mid.z - Ln / 2, mid.z + Ln / 2, WH, mtx)
    tb.box(TX - 0.42, TX + 0.42, ey - q, ey + q, 0, 0.04, WH)   # floor foot
    tb.box(TX - 0.31, TX + 0.31, ey - q, ey + q, 0.33, 0.37, WH)  # crossbar
tb.box(TX - q, TX + q, TY - TD / 2 + 0.18, TY + TD / 2 - 0.18, 0.33, 0.37, WH)   # stretcher
tb.build(C, root)
lnode("slot_island_server", (TX, TY - 0.30, TH), C, root, role="slot", accepts="server", note="server rests here, front towards -Y")
lnode("slot_island_screwdriver", (TX + 0.30, TY + 0.70, TH + 0.0175), C, root, role="slot", accepts="screwdriver")
print("TABLES_REPORT", {"tris": tris(C)})
lab_save()
