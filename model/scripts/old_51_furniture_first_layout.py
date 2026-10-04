"""Lab 51 — furniture from assets/reference/lab (no chairs, per the user).
White wall benches on white frame legs with 3-drawer pedestals (on castors, D-handles, lock); tall white centre
table with A-frame legs (slot markers for the server and the screwdriver); two wall TVs; blue steel tool cabinet
(light-grey body, blue doors, shelves, drawer stack); blue tool trolley with pegboard; cardboard boxes."""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("furniture"); wipe(C); root = lfixed("furniture", C)
X0, X1, Y0, Y1 = -RW / 2, RW / 2, -RD / 2, RD / 2
WH, PW = M("M_DeskWhite"), M("M_PedWhite")

# ---------- wall benches (L: +Y wall and -X wall), top 0.90, depth 0.75 ----------
BH, BD, BT = 0.90, 0.75, 0.025
b = Part("benches")
b.box(X0, 1.20, Y1 - BD, Y1, BH - BT, BH, WH)                       # +Y run (stops at the column)
b.box(X0, X0 + BD, -0.40, Y1 - BD, BH - BT, BH, WH)                  # -X run (north half)
def leg_frame(x, y0, y1, along="Y"):                                  # white rectangular end frame, 40x40 tube
    t = 0.02
    if along == "Y":
        b.box(x - t, x + t, y0 + 0.03, y0 + 0.07, 0, BH - BT, WH); b.box(x - t, x + t, y1 - 0.07, y1 - 0.03, 0, BH - BT, WH)
        b.box(x - t, x + t, y0 + 0.03, y1 - 0.03, BH - BT - 0.05, BH - BT, WH); b.box(x - t, x + t, y0 + 0.03, y1 - 0.03, 0, 0.03, WH)
    else:
        b.box(y0 + 0.03, y0 + 0.07, x - t, x + t, 0, BH - BT, WH); b.box(y1 - 0.07, y1 - 0.03, x - t, x + t, 0, BH - BT, WH)
        b.box(y0 + 0.03, y1 - 0.03, x - t, x + t, BH - BT - 0.05, BH - BT, WH); b.box(y0 + 0.03, y1 - 0.03, x - t, x + t, 0, 0.03, WH)
for x in (X0 + BD + 0.05, -2.2, -0.5, 1.15): leg_frame(x, Y1 - BD, Y1, "Y")
for y in (-0.35, 1.30): leg_frame(y, X0, X0 + BD, "X")
b.box(X0, 1.20, Y1 - 0.06, Y1 - 0.04, BH - BT - 0.10, BH - BT, WH)  # rear modesty rail
b.build(C, root)

# ---------- pedestals: 0.42 W x 0.60 D x 0.68 H, 2 shallow + 1 file drawer, castors ----------
def pedestal(name, x, y, face):
    """face = direction the drawers face ('-Y' or '+X')."""
    W, D, H = 0.42, 0.60, 0.68
    a = lnode(f"asset_{name}", (x, y, 0), C, root, role="asset", tip="pedestal", pull=[[0, 0, 0]], note="scenery; drawers open")
    rot = 0 if face == "-Y" else math.pi / 2
    p = Part(f"{name}_body", (x, y, 0)); R = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Translation((-x, -y, 0))
    p.box(x - W / 2, x + W / 2, y - D / 2 + 0.02, y + D / 2, 0.05, 0.05 + H - 0.05, PW, R)
    for cx in (-1, 1):
        for cy in (-1, 1):
            p.box(x + cx * 0.16 - 0.015, x + cx * 0.16 + 0.015, y + cy * 0.24 - 0.015, y + cy * 0.24 + 0.015, 0, 0.05, M("M_Rubber"), R)
    p.build(C, a)
    z = 0.06
    for k, hgt in enumerate((0.15, 0.15, 0.32)):
        d = Part(f"{name}_drawer_{k + 1}", (x, y, z))
        d.box(x - W / 2 + 0.005, x + W / 2 - 0.005, y - D / 2, y - D / 2 + 0.02, z + 0.004, z + hgt - 0.004, PW, R)
        hz = z + hgt - 0.05                                            # D-handle near the top of each front
        d.box(x - 0.07, x + 0.07, y - D / 2 - 0.022, y - D / 2 - 0.012, hz - 0.006, hz + 0.006, M("M_DeskWhite"), R)
        for hx in (-0.07, 0.07): d.box(x + hx - 0.006, x + hx + 0.006, y - D / 2 - 0.022, y - D / 2, hz - 0.006, hz + 0.006, M("M_DeskWhite"), R)
        if k == 0: d.cyl((x + 0.15, 0, hz + 0.02), "Y", y - D / 2 - 0.006, y - D / 2, 0.008, M("M_SteelHandle"), 10)   # lock
        o = d.build(C, a)
        ax = "-Y" if face == "-Y" else "+X"
        moving(o, "slide", ax, [0, 0.40 if k == 2 else 0.30], tip="pedestal_drawer")
        z += hgt
    return a
for i, x in enumerate((-3.35, -1.35, 0.35)): pedestal(f"pedestal_{i + 1}", x, Y1 - 0.40, "-Y")
for i, y in enumerate((0.25, 2.05)): pedestal(f"pedestal_{i + 4}", X0 + 0.40, y, "+X")

# ---------- centre table: 2.0 x 1.0 top at 1.00, A-frame legs ----------
TX, TY, TW, TD, TH = -0.40, 0.55, 2.00, 1.00, 1.00
t = Part("table", (TX, TY, 0))
t.box(TX - TW / 2, TX + TW / 2, TY - TD / 2, TY + TD / 2, TH - 0.03, TH, WH)
q = 0.02
for ex in (TX - TW / 2 + 0.18, TX + TW / 2 - 0.18):
    for s in (-1, 1):                                                  # A legs: narrow at the top, splayed at the floor
        top = Vector((ex, TY + s * 0.06, TH - 0.03)); bot = Vector((ex, TY + s * 0.42, 0.0)); mid = (top + bot) / 2
        L = (top - bot).length; ang = math.atan2(bot.y - top.y, top.z - bot.z)
        mtx = Matrix.Translation(mid) @ Matrix.Rotation(ang, 4, "X") @ Matrix.Translation(-mid)
        t.box(ex - q, ex + q, mid.y - q, mid.y + q, mid.z - L / 2, mid.z + L / 2, WH, mtx)
    t.box(ex - q, ex + q, TY - 0.42, TY + 0.42, 0, 0.04, WH)            # floor foot
    t.box(ex - q, ex + q, TY - 0.31, TY + 0.31, 0.33, 0.37, WH)         # crossbar
t.box(TX - TW / 2 + 0.18, TX + TW / 2 - 0.18, TY - q, TY + q, 0.33, 0.37, WH)   # stretcher
t.build(C, root)
lnode("slot_table_server", (TX + 0.25, TY, TH), C, root, role="slot", accepts="server", note="server rests here, front towards -Y")
lnode("slot_table_screwdriver", (TX - 0.75, TY - 0.30, TH + 0.0175), C, root, role="slot", accepts="screwdriver")
lnode("slot_table_partsmat", (TX - 0.55, TY + 0.15, TH), C, root, role="area", size=[0.6, 0.45], note="parts mat area")

# ---------- wall TVs on the -X wall ----------
tv = Part("tvs")
for (y, w_, h_, z) in ((0.35, 1.45, 0.83, 1.85), (2.05, 1.23, 0.71, 1.80)):
    x = X0 + 0.005
    tv.box(x + 0.03, x + 0.09, y - w_ / 2, y + w_ / 2, z - h_ / 2, z + h_ / 2, M("M_TVBlack"))
    tv.box(x, x + 0.03, y - 0.2, y + 0.2, z - 0.2, z + 0.2, M("M_Galv"))       # wall bracket
tv.build(C, root)

# ---------- blue tool cabinet (E wall, north half, facing -X): 1.00 W x 0.65 D x 1.95 H ----------
# Built in a local frame (back at y=0, front at y=+0.65, centred on x=0), then mapped by RC onto the wall.
CW, CDp, CH = 1.00, 0.65, 1.95; BL, GR = M("M_BottBlue"), M("M_BottGrey")
CAB_Y = 1.20
RC = Matrix.Translation((X1, CAB_Y, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z")
def W_(p): return tuple(RC @ Vector(p))
cab = lnode("fixed_tool_cabinet", W_((0, CDp, 0)), C, root, role="fixed", tip="tool_cabinet")
def cpart(name, org): return Part(name, W_(org))
k = cpart("cabinet_body", (0, CDp, 0))
k.box(-CW / 2, CW / 2, 0, CDp - 0.02, 0.0, CH, GR, RC)
k.box(-CW / 2 + 0.02, CW / 2 - 0.02, CDp - 0.021, CDp - 0.02, 0.06, CH - 0.06, M("M_SocketDark"), RC)
k.box(-0.45, 0.15, 0.05, 0.45, CH, CH + 0.30, M("M_Card"), RC)                    # box on top
k.build(C, cab)
for i, sz in enumerate((1.20, 1.52)):
    sp = cpart(f"cabinet_shelf_{i + 1}", (0, CDp, sz)); sp.box(-CW / 2 + 0.03, CW / 2 - 0.03, 0.05, CDp - 0.03, sz, sz + 0.02, M("M_Galv"), RC); sp.build(C, cab)
for i in range(7):
    z = 0.08 + i * 0.13
    d = cpart(f"cabinet_drawer_{i + 1}", (0, CDp, z))
    d.box(-CW / 2 + 0.05, CW / 2 - 0.05, CDp - 0.05, CDp - 0.03, z, z + 0.122, BL, RC)
    d.box(-0.25, 0.25, CDp - 0.03, CDp - 0.02, z + 0.09, z + 0.11, BL, RC)
    moving(d.build(C, cab), "slide", "-X", [0, 0.45], tip="cabinet_drawer")
for side, hx in (("L", -CW / 2), ("R", CW / 2)):
    dw = CW / 2 - 0.004
    x0_, x1_ = (hx, hx + dw) if side == "L" else (hx - dw, hx)
    d = cpart(f"cabinet_door_{side}", (hx, CDp, 0))
    d.box(x0_, x1_, CDp - 0.02, CDp + 0.005, 0.02, CH - 0.02, BL, RC)
    d.box(x0_ + 0.01, x1_ - 0.01, CDp + 0.005, CDp + 0.008, 0.04, CH - 0.04, BL, RC)
    if side == "R": d.box(x0_ + 0.03, x0_ + 0.06, CDp + 0.008, CDp + 0.03, 0.95, 1.10, M("M_SteelHandle"), RC)
    moving(d.build(C, cab), "hinge", "Z", [-110, 0] if side == "L" else [0, 110], tip="cabinet_door")

# ---------- blue tool trolley with pegboard (near the racks) ----------
TRX, TRY = 1.25, -2.10
tr = lnode("asset_trolley", (TRX, TRY, 0), C, root, role="asset", tip="trolley", pull=[[0, 0, 0]], note="rolls on castors")
p = Part("trolley_frame", (TRX, TRY, 0)); W2, D2 = 0.38, 0.24
for sx in (-1, 1):
    for sy in (-1, 1): p.box(TRX + sx * W2 - 0.015, TRX + sx * W2 + 0.015, TRY + sy * D2 - 0.015, TRY + sy * D2 + 0.015, 0.10, 1.05, BL)
for z in (0.18, 0.62): p.box(TRX - W2, TRX + W2, TRY - D2, TRY + D2, z, z + 0.025, BL)
for sx in (-1, 1):
    for sy in (-1, 1):
        p.cyl((TRX + sx * (W2 - 0.03), TRY + sy * (D2 - 0.03), 0), "Z", 0.05, 0.10, 0.012, M("M_Galv"), 8)
        p.cyl((TRX + sx * (W2 - 0.03), 0, 0.05), "Y", TRY + sy * (D2 - 0.03) - 0.015, TRY + sy * (D2 - 0.03) + 0.015, 0.05, M("M_Rubber"), 12)
p.build(C, tr)
# pegboard: alpha-clipped hole pattern (10 mm holes at 25 mm pitch)
n = 128; yy, xx = np.mgrid[0:n, 0:n] / n * 4; peg = np.ones((n, n, 4)); peg[:, :, :3] = [0.12, 0.28, 0.72]
hole = ((xx % 1 - 0.5) ** 2 + (yy % 1 - 0.5) ** 2) < 0.04; peg[hole, 3] = 0.0
tex_material("M_Pegboard", save_png("lab_pegboard", peg), rough=0.45, metal=0.3, alpha_clip=True)
pg = Part("trolley_pegboard", (TRX, TRY, 0))
pg.box(TRX - W2, TRX + W2, TRY + D2 - 0.002, TRY + D2 + 0.002, 0.65, 1.05, M("M_Pegboard"))
pg.box(TRX + W2 - 0.002, TRX + W2 + 0.002, TRY - D2, TRY + D2, 0.65, 1.05, M("M_Pegboard"))
po = pg.build(C, tr); uv_box(po, 1 / 0.1)

# ---------- cardboard boxes ----------
bx = Part("boxes")
bx.box(X1 - 0.10, X1 - 0.02, -0.30, 0.45, 0.0, 0.90, M("M_Card"))            # flat TV box against the east wall
bx.box(X1 - 0.60, X1 - 0.10, 2.20, 2.50, 0.0, 0.12, M("M_Card")); bx.box(X1 - 0.55, X1 - 0.15, 2.23, 2.47, 0.12, 0.22, M("M_Card"))
bx.build(C, root)
print("FURN_REPORT", {"tris": tris(C)})
lab_save()
