"""Lab 55 — blue tool cabinet, two wall TVs, bench chairs (reference: assets/reference/lab photos; no centre stools).
- Tool cabinet (Bott-style): 1.00 W x 0.65 D x 1.95 H, light-grey body, blue doors (hinged), 2 shelves, 7-drawer stack
  (sliding), on the stepped-in east wall facing west (the user's plan, blue box).
- TVs: two identical 65" (1.45 x 0.83) on the north wall above the long bench, bottoms ~0.55 above the bench.
- Chairs: draughtsman office chairs (5-star base on castors, gas lift, chrome foot ring, black seat + back) at the
  benches: 3 on the north run, 3 on the east run, small random turns. One shared mesh, instanced."""
import bpy, math, random
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("furnishings"); wipe(C); root = lfixed("furnishings", C)
R = load_layout()["lab_room"]; W, L, XI, YS = R["W"], R["L"], R["inset_x"], R["step_y"]; OX, OY = -W / 2, -L / 2
_MAT_DEFS.update({"M_ChairFabric": ("#1C1C1D", 0.85, 0), "M_ChairPlastic": ("#161616", 0.5, 0), "M_Chrome": ("#D5D7D9", 0.15, 1.0),
                  "M_TVScreen": ("#050607", 0.08, 0.2)})

# ---------- blue tool cabinet on the inset east wall (faces west) ----------
CW, CDp, CH = 1.00, 0.65, 1.95; BL, GR = M("M_BottBlue"), M("M_BottGrey")
CAB_Y = OY + 2.20                                         # opposite the middle of the rack row (wall runs y OY..OY+YS)
RC = Matrix.Translation((OX + XI, CAB_Y, 0)) @ Matrix.Rotation(math.radians(90), 4, "Z")   # local +Y (front) -> world -X
def W_(p): return tuple(RC @ Vector(p))
cab = lnode("fixed_tool_cabinet", W_((0, CDp, 0)), C, root, role="fixed", tip="tool_cabinet")
def cpart(name, org): return Part(name, W_(org))
k = cpart("lab_cabinet_body", (0, CDp, 0)); t = 0.015; FY = CDp - 0.02          # hollow carcass, open front at FY
k.box(-CW / 2, CW / 2, 0, t, 0.0, CH, GR, RC)                                          # back
k.box(-CW / 2, -CW / 2 + t, 0, FY, 0.0, CH, GR, RC); k.box(CW / 2 - t, CW / 2, 0, FY, 0.0, CH, GR, RC)   # sides
k.box(-CW / 2, CW / 2, 0, CDp, CH - 0.03, CH, GR, RC)                                  # top (lip over the doors)
k.box(-CW / 2, CW / 2, 0, FY, 0.0, 0.06, GR, RC)                                       # plinth
k.box(-CW / 2 + t, CW / 2 - t, t, t + 0.001, 0.06, CH - 0.03, M("M_LabWall"), RC)        # light interior back
for sx in (-1, 1):                                                                     # shelf-pin strips (slotted uprights)
    k.box(sx * (CW / 2 - t) - 0.01 * (sx > 0), sx * (CW / 2 - t) + 0.01 * (sx < 0), FY - 0.05, FY - 0.03, 1.05, CH - 0.05, M("M_Galv"), RC)
k.build(C, cab)
for i, sz in enumerate((1.03, 1.36, 1.68)):                                              # 3 galvanised shelves (first = drawer-unit top)
    sp = cpart(f"lab_cabinet_shelf_{i + 1}", (0, CDp, sz))
    sp.box(-CW / 2 + t, CW / 2 - t, t, FY - 0.01, sz, sz + 0.02, M("M_Galv"), RC)
    sp.box(-CW / 2 + t, CW / 2 - t, FY - 0.03, FY - 0.01, sz - 0.03, sz + 0.02, M("M_Galv"), RC)   # folded front lip
    sp.build(C, cab)
DD = 0.50                                                                               # drawer depth
for i in range(7):                                                                      # 7 drawers: blue front + tray
    z = 0.065 + i * 0.137; hgt = 0.13
    d = cpart(f"lab_cabinet_drawer_{i + 1}", (0, CDp, z))
    d.box(-CW / 2 + t + 0.003, CW / 2 - t - 0.003, FY - 0.035, FY - 0.015, z, z + hgt, BL, RC)                 # front
    d.box(-CW / 2 + t + 0.003, CW / 2 - t - 0.003, FY - 0.015, FY + 0.005, z + hgt - 0.03, z + hgt - 0.02, BL, RC)  # handle lip
    d.box(-CW / 2 + t + 0.02, CW / 2 - t - 0.02, FY - 0.035 - DD, FY - 0.035, z + 0.005, z + 0.012, M("M_BottGrey"), RC)  # tray floor
    for sx in (-1, 1):
        x_ = sx * (CW / 2 - t - 0.02)
        d.box(min(x_, x_ - sx * 0.008), max(x_, x_ - sx * 0.008), FY - 0.035 - DD, FY - 0.035, z + 0.005, z + hgt - 0.03, M("M_BottGrey"), RC)
    d.box(-CW / 2 + t + 0.02, CW / 2 - t - 0.02, FY - 0.043 - DD, FY - 0.035 - DD, z + 0.005, z + hgt - 0.03, M("M_BottGrey"), RC)  # tray back
    moving(d.build(C, cab), "slide", "-X", [0, 0.45], tip="cabinet_drawer", holds="parts",
           note="pull-out drawer for spare parts; contents travel with the drawer")
for side, hx in (("L", -CW / 2), ("R", CW / 2)):
    dw = CW / 2 - 0.004
    x0_, x1_ = (hx, hx + dw) if side == "L" else (hx - dw, hx)
    d = cpart(f"lab_cabinet_door_{side}", (hx, CDp, 0))
    d.box(x0_, x1_, CDp - 0.02, CDp + 0.005, 0.02, CH - 0.03, BL, RC)
    d.box(x0_ + 0.01, x1_ - 0.01, CDp + 0.005, CDp + 0.008, 0.04, CH - 0.05, BL, RC)
    if side == "R": d.box(x0_ + 0.03, x0_ + 0.06, CDp + 0.008, CDp + 0.03, 0.95, 1.10, M("M_SteelHandle"), RC)
    moving(d.build(C, cab), "hinge", "Z", [0, 90] if side == "L" else [-90, 0], tip="cabinet_door")     # 90 deg max (can't fold back)

# ---------- two identical 65" TVs on the north wall ----------
tv = Part("lab_tvs"); yw = OY + L; TVW, TVH, TVD, TZ = 1.45, 0.83, 0.06, 1.865
for cx in (OX + 4.60, OX + 6.40):
    tv.box(cx - 0.20, cx + 0.20, yw - 0.03, yw, TZ - 0.20, TZ + 0.20, M("M_Galv"))                                   # bracket
    tv.box(cx - TVW / 2, cx + TVW / 2, yw - 0.03 - TVD, yw - 0.03, TZ - TVH / 2, TZ + TVH / 2, M("M_TVBlack"))      # body
    tv.box(cx - TVW / 2 + 0.012, cx + TVW / 2 - 0.012, yw - 0.031 - TVD, yw - 0.03 - TVD, TZ - TVH / 2 + 0.012, TZ + TVH / 2 - 0.012, M("M_TVScreen"))
setp(tv.build(C, root), role="fixed", tip="tv")

# ---------- draughtsman chair (one mesh, instanced) ----------
ch = Part("lab_chair_mesh"); FAB, PL, CR = M("M_ChairFabric"), M("M_ChairPlastic"), M("M_Chrome")
for k5 in range(5):                                                                   # 5-star base + castors
    a = 2 * math.pi * k5 / 5; Rz = Matrix.Rotation(a, 4, "Z")
    ch.box(0.0, 0.31, -0.02, 0.02, 0.07, 0.10, PL, Rz)
    c = Rz @ Vector((0.30, 0, 0)); ch.cyl((c.x, c.y, 0), "Z", 0.0, 0.07, 0.025, PL, 8)
ch.cyl((0, 0, 0), "Z", 0.07, 0.14, 0.035, PL, 12)                                     # hub
ch.cyl((0, 0, 0), "Z", 0.14, 0.62, 0.022, M("M_RackBlack"), 12)                         # gas lift
for k16 in range(16):                                                                 # chrome foot ring at 0.42
    a = 2 * math.pi * k16 / 16; Rz = Matrix.Rotation(a, 4, "Z"); seg = 2 * 0.22 * math.sin(math.pi / 16) + 0.004
    ch.box(0.215, 0.235, -seg / 2, seg / 2, 0.415, 0.432, CR, Rz)
for a in (0, 2.0944, 4.1888):
    ch.box(0.02, 0.22, -0.007, 0.007, 0.415, 0.43, CR, Matrix.Rotation(a, 4, "Z"))     # ring spokes
ch.box(-0.12, 0.12, -0.10, 0.12, 0.60, 0.64, PL)                                      # seat mechanism
ch.box(0.12, 0.20, 0.0, 0.015, 0.60, 0.615, PL)                                       # height lever
ch.box(-0.235, 0.235, -0.22, 0.24, 0.64, 0.71, FAB)                                   # seat cushion (front = -Y)
ch.box(-0.03, 0.03, 0.20, 0.27, 0.58, 0.95, PL)                                       # back bar
ch.box(-0.20, 0.20, 0.27, 0.33, 0.90, 1.24, FAB)                                      # backrest
CHAIR = ch.mesh()
random.seed(7)
spots = [((OX + x, OY + L - 0.75 - 0.42), math.pi) for x in (4.3, 5.7, 7.1)] + \
        [((OX + W - 0.75 - 0.42, OY + y), math.pi / 2) for y in (3.9, 5.3, 6.7)]       # N run faces +Y, E run faces +X
for i, ((x, y), yaw) in enumerate(spots, 1):
    o = bpy.data.objects.new(f"asset_chair_{i}", CHAIR); C.objects.link(o); place(o, (x, y, 0), root)
    o.rotation_euler = (0, 0, yaw + random.uniform(-0.35, 0.35))           # seat front faces the bench
    setp(o, role="asset", tip="chair", pull=[[0, 0, 0]], note="office chair; moves on castors")
print("FURNISH_REPORT", {"tris": tris(C)})
lab_save()
