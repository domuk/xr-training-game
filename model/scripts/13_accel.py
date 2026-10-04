"""Asset 13 — Annapurna Labs K2T-QB accelerator / network card in PCIe slot 2 (replaces blank bracket 2).
Ref: assets/reference/parts/accel-k2t-qb. Real card is full height; built at low-profile height for this 2U
(same length, parts and layout). Component side faces -X (away from the CPU), ATX orientation as the NIC.
  - perforated bracket (square vent grid) with RJ45 (top, near the tab) + QSFP cage (lower), peg + tab + screw
  - 2 finned aluminium heatsinks (fins along the card) with black push-pins
  - chokes, SATA connector, JTAG FPC, white UART connectors, 2x5 header
  - back side: 10 DRAM chips + labels
  - x16 fingers in the slot + second finger segment (as the real card)"""
import bpy
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
from mathutils import Vector
lay = load_layout()
S = server_coll(); P = coll("parts", S); A = coll("accel", P); wipe(A)
mm = 0.001; YF, YB = 0.6392, 0.6215
MET, DARK, GOLD = M("M_EarAlu"), M("M_ChipBlack"), M("M_Gold")
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_ports.py")).read())

xc = lay["pcie_x"][1]; t = 0.0008               # slot 2
PX, BK = xc - t, xc + t                          # component face (-X), back face (+X)
SZ = lay["board"]["pcie_groove_floor"]           # groove floor
x1o = -0.073 - 0.0203; x0o = x1o - 0.0203        # rear opening 2 (full pitch)
BX0, BX1 = x0o + 0.00025, x1o - 0.00025          # 19.8 mm bracket, 0.5 mm gaps
slot = Vector((xc, 0.5845, SZ)); lay["slots"]["slot_accel"] = [round(v, 5) for v in slot]

a = asset("accel", slot, A, pull=[[0, 0, 0.10]], requires="accel_screw", tip="accel_card",
          note="K2T-QB: RJ45 + QSFP; remove bracket screw, lift straight up")

# ---------- PCB + fingers ----------
c = Part("accel_card")
c.box(xc - t, xc + t, 0.4700, 0.6375, 0.0186, 0.0770, M("M_PCBGreen"))                   # ~168 mm long
for (y0, y1) in ((0.6174, 0.6290), (0.5400, 0.6158)):                                    # x16: power + data (in the slot)
    c.box(xc - t, xc + t, y0, y1, SZ, 0.0186, M("M_PCBGreen"))
    c.box(xc - t - 0.00005, xc + t + 0.00005, y0 + 0.0005, y1 - 0.0005, SZ + 0.0002, 0.0170, GOLD)
for (y0, y1) in ((0.5200, 0.5300), (0.4760, 0.5160)):                                    # second finger segment (no slot)
    c.box(xc - t, xc + t, y0, y1, SZ, 0.0186, M("M_PCBGreen"))
    c.box(xc - t - 0.00005, xc + t + 0.00005, y0 + 0.0005, y1 - 0.0005, SZ + 0.0002, 0.0170, GOLD)
# component side (-X)
for (y0, y1, z0, z1) in ((0.6000, 0.6080, 0.0430, 0.0510), (0.5880, 0.5960, 0.0430, 0.0510),
                         (0.5160, 0.5240, 0.0300, 0.0380), (0.4880, 0.4960, 0.0620, 0.0700)):
    c.box(PX - 0.0040, PX, y0, y1, z0, z1, M("M_Choke"))                                 # "MAGIC" chokes
c.box(PX - 0.0060, PX, 0.4900, 0.4960, 0.0420, 0.0560, M("M_SlotBlack"))                # SATA connector
c.box(PX - 0.0020, PX, 0.4760, 0.4790, 0.0560, 0.0720, M("M_ChipBlack"))                # JTAG FPC
c.box(PX - 0.0020, PX, 0.4720, 0.4760, 0.0570, 0.0715, M("M_PlugWhite"))
for z in (0.0300, 0.0360):                                                               # white UART connectors
    c.box(PX - 0.0035, PX, 0.4740, 0.4790, z, z + 0.0040, M("M_PlugWhite"))
c.box(PX - 0.0025, PX, 0.6230, 0.6290, 0.0700, 0.0760, M("M_SlotBlack"))                # 2x5 header base
for i in range(5):
    for j in range(2):
        y = 0.6242 + j * 0.0025; z = 0.07035 + i * 0.00125
        c.box(PX - 0.0085, PX - 0.0025, y - 0.0003, y + 0.0003, z - 0.0003, z + 0.0003, GOLD)
for (y, z) in ((0.5300, 0.0480), (0.5480, 0.0300), (0.4950, 0.0300)):                    # small ICs
    c.box(PX - 0.0010, PX, y - 0.004, y + 0.004, z - 0.004, z + 0.004, DARK)
# back side (+X): 10 DRAM + labels
for i in range(5):
    y = 0.6150 - i * 0.0120; c.box(BK, BK + 0.0012, y - 0.0050, y + 0.0050, 0.0640, 0.0740, DARK)
for i in range(5):
    z = 0.0270 + i * 0.0080; c.box(BK, BK + 0.0012, 0.4800, 0.4950, z, z + 0.0065, DARK)
c.box(BK, BK + 0.0002, 0.5580, 0.5900, 0.0570, 0.0610, M("M_LabelWhite"))                # PN:K2T-QB
c.box(BK, BK + 0.0002, 0.5200, 0.5540, 0.0570, 0.0610, M("M_LabelWhite"))                # K2T-QB 1E R0B V3A
c.box(BK, BK + 0.0002, 0.5100, 0.5600, 0.0200, 0.0250, M("M_LabelWhite"))                # serial label
c.build(A, a)

# ---------- heatsinks (fins along the card, push-pins) ----------
def heatsink(name, y0, y1, z0, z1, h):
    hs = Part(name)
    hs.box(PX - 0.0020, PX, y0, y1, z0, z1, MET)                                         # base
    z = z0 + 0.0004
    while z + 0.0008 <= z1:
        hs.box(PX - h, PX - 0.0020, y0, y1, z, z + 0.0008, MET); z += 0.0026             # fins
    return hs
hsA = heatsink("accel_heatsink_a", 0.5580, 0.6120, 0.0450, 0.0760, 0.0110)
hsB = heatsink("accel_heatsink_b", 0.4980, 0.5560, 0.0240, 0.0720, 0.0120)
for (hs, pins, h) in ((hsA, ((0.5700, 0.0560), (0.6000, 0.0660)), 0.0110), (hsB, ((0.5100, 0.0600), (0.5420, 0.0340)), 0.0120)):
    for (y, z) in pins:
        hs.cyl((0, y, z), "X", PX - h - 0.0012, PX - 0.0020, 0.0016, M("M_CordBlack"), 10)   # push-pin heads
    hs.build(A, a)

# ---------- RJ45 (top of bracket, rotated: notch toward the PCB) + QSFP cage (lower) ----------
hx0, hx1, hz0, hz1 = BX0 + 0.0008, PX - 0.0002, 0.0560, 0.0705
ox0, ox1 = hx0 + 0.0012, hx0 + 0.0012 + 0.0082
oz0, oz1 = hz0 + 0.0014, hz0 + 0.0014 + 0.0117
nz0, nz1 = (oz0 + oz1) / 2 - 0.0030, (oz0 + oz1) / 2 + 0.0030; nx1 = ox1 + 0.0015; yd = YF - 0.012
j = Part("accel_rj45", ((hx0 + hx1) / 2, YF, hz0)); H = M("M_EarAlu")
j.box(hx0, hx1, YB, yd, hz0, hz1, H); j.box(hx0, ox0, yd, YF, hz0, hz1, H)
j.box(ox0, nx1, yd, YF, hz0, oz0, H); j.box(ox0, nx1, yd, YF, oz1, hz1, H)
j.box(ox1, nx1, yd, YF, oz0, nz0, H); j.box(ox1, nx1, yd, YF, nz1, oz1, H); j.box(nx1, hx1, yd, YF, hz0, hz1, H)
j.box(ox0, ox1, yd - 0.0003, yd, oz0, oz1, DARK); j.box(ox1, nx1, yd - 0.0003, yd, nz0, nz1, DARK)
for k in range(8):
    z = (oz0 + oz1) / 2 + (k - 3.5) * 1.02 * mm
    j.box(ox0, ox0 + 0.0018, YF - 0.0095, YF - 0.0055, z - 0.0002, z + 0.0002, GOLD)
for (zz, mat) in ((hz1 - 0.0016, "M_LEDGreen"), (hz0 + 0.0004, "M_LEDAmber")):          # link / activity LEDs
    j.box(hx1 - 0.0024, hx1 - 0.0008, YF, YF + 0.0002, zz, zz + 0.0012, M(mat))
j.build(A, a)
qx0, qx1, qz0, qz1 = PX - 0.0100, PX - 0.0002, 0.0220, 0.0408                          # QSFP cage 9.8 x 18.8
q = Part("accel_qsfp", ((qx0 + qx1) / 2, YF, qz0))
q.box(qx0, qx1, 0.5850, YF - 0.0060, qz0, qz1, MET)                                     # cage body
q.box(qx0, qx1, YF - 0.0060, YF, qz0, qz0 + 0.0008, MET); q.box(qx0, qx1, YF - 0.0060, YF, qz1 - 0.0008, qz1, MET)
q.box(qx0, qx0 + 0.0008, YF - 0.0060, YF, qz0, qz1, MET); q.box(qx1 - 0.0008, qx1, YF - 0.0060, YF, qz0, qz1, MET)
q.box(qx0 + 0.0008, qx1 - 0.0008, YF - 0.0063, YF - 0.0060, qz0 + 0.0008, qz1 - 0.0008, DARK)   # port cavity
q.box(qx0 + 0.0035, qx1 - 0.0035, YF - 0.0062, YF - 0.0058, qz0 + 0.0030, qz1 - 0.0030, GOLD)   # host connector edge
for k in range(4):                                                                       # EMI spring fingers
    z = qz0 + 0.0030 + k * 0.0042
    q.box(qx0 - 0.0003, qx0, YF - 0.0040, YF, z, z + 0.0020, MET)
q.build(A, a)

# ---------- perforated bracket: windows for RJ45 + QSFP, square vent grid, peg, tab ----------
b = Part("accel_bracket")
b.box(BX0, BX1, 0.6385, 0.6395, 0.0100, 0.0847, M("M_Zinc"))
b.box(BX0, BX1, 0.6385, 0.6450, 0.0847, 0.0855, M("M_Zinc"))
bc = (BX0 + BX1) / 2
b.box(bc - 0.0065, bc + 0.0065, 0.6385, 0.6395, 0.0070, 0.0100, M("M_Zinc"))
b.box(bc - 0.0050, bc + 0.0050, 0.6385, 0.6395, 0.0055, 0.0070, M("M_Zinc"))
br = b.build(A, a)
cuts = []
k = Part("cut"); k.box(hx0 - 0.0003, hx1 + 0.0003, 0.630, 0.650, hz0 - 0.0003, hz1 + 0.0003, DARK); cuts.append(k)
k = Part("cut"); k.box(qx0 - 0.0004, qx1 + 0.0004, 0.630, 0.650, qz0 - 0.0004, qz1 + 0.0004, DARK); cuts.append(k)
g = Part("cut")                                                                          # square vent grid (one cutter)
for zr in [0.0120 + r * 0.0032 for r in range(3)] + [0.0440 + r * 0.0032 for r in range(3)] + [0.0745 + r * 0.0032 for r in range(3)]:
    for ci in range(4):
        x = BX0 + 0.0022 + ci * 0.0038
        g.box(x, x + 0.0022, 0.630, 0.650, zr, zr + 0.0022, DARK)
cuts.append(g)
boolean_cut(br, cuts, A)
fastener(screw("accel_screw", screw_mesh("screw_bracket", 0.0022, 0.0018, "phillips"), ((BX0 + BX1) / 2, 0.6425, 0.0855), A, a),
         "phillips_2", turns=3, rise=0.003)

save_layout(lay)
print("ACCEL_REPORT", {"tris": tris(A), "objects": len(A.all_objects)})
save()
