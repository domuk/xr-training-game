"""Asset 10 (detail v4) — low-profile PCIe x1 gigabit NIC, matched to assets/reference/parts/nic-lp.
- Owns bracket slot 1: solid bracket, bottom peg, top tab + screw on the rail.
- RJ45 jack ROTATED as on real cards: latch notch toward the PCB, window low on the bracket (slot end),
  close to the PCB edge with a margin on the far side. 8 contacts on the far side, real cavity.
- 2 round green LED light pipes ON THE CARD shining through holes beside (above) the jack.
- x1 edge: power section + key + data section at the bracket end of the slot; rest of the card edge clear.
- Card parts: magnetics block, QFN controller, crystal, 3 blue jumpers.
ATX orientation: PCB at the bracket edge nearest the CPU/I-O, components facing away (-X). MODEL-SPEC §12.6."""
import bpy
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
from mathutils import Vector
lay = load_layout()
S = server_coll(); P = coll("parts", S); N = coll("nic", P); wipe(N)
mm = 0.001; YF, YB = 0.6392, 0.6215
MET, DARK, GOLD = M("M_EarAlu"), M("M_ChipBlack"), M("M_Gold")
exec(open(os.path.join(HERE, "_ports.py")).read())     # boolean_cut

sl = Vector(lay["slots"]["slot_nic"]); x = sl.x; t = 0.0008
PX = x - t                                       # component-side face of the PCB
BX0, BX1 = -0.09305, -0.07325                    # bracket = rear opening 1 (19.8 mm, 0.5 mm gaps)
a = asset("nic", sl, N, pull=[[0, 0, 0.10]], requires="nic_screw", tip="nic",
          check="slide the bracket into opening 1 (peg in the slit) while pressing the card into the slot; refit the screw")

# ---------- card: x1 edge at the bracket end of the slot ----------
c = Part("nic_card")
PW0, PW1 = 0.6174, 0.6290                        # power section (11.6 mm, next to the bracket)
DA0, DA1 = 0.6081, 0.6158                        # data section (x1), after the key gap
for (y0, y1) in ((PW0, PW1), (DA0, DA1)):
    c.box(x - t, x + t, y0, y1, sl.z, 0.0186, M("M_PCBGreen"))
    c.box(x - t - 0.00005, x + t + 0.00005, y0 + 0.0005, y1 - 0.0005, sl.z + 0.0002, 0.0170, GOLD)
c.box(x - t, x + t, 0.5480, 0.6375, 0.0186, 0.0650, M("M_PCBGreen"))                     # card body (~90 x 46 mm)
c.box(PX - 0.0035, PX, 0.6000, 0.6160, 0.0220, 0.0400, DARK)                             # magnetics (transformer)
c.box(PX - 0.0010, PX, 0.5650, 0.5750, 0.0350, 0.0450, DARK)                             # QFN controller
c.cyl((PX - 0.0018, 0.5505, 0.0570), "X", PX - 0.0036, PX, 0.0018, MET, 10)               # crystal (rounded can)
c.box(PX - 0.0036, PX, 0.5470, 0.5540, 0.0552, 0.0588, MET)
for (yj, zj) in ((0.6300, 0.0560), (0.6300, 0.0610), (0.6240, 0.0610)):                    # blue jumpers
    c.box(PX - 0.0060, PX, yj - 0.0012, yj + 0.0012, zj - 0.0018, zj + 0.0018, M("M_USB3Blue"))
c.build(N, a)

# ---------- RJ45, rotated: opening 11.7 along Z, 8.2 along X, latch notch toward the PCB (+X) ----------
hx0, hx1, hz0, hz1 = -0.0900, PX - 0.0002, 0.0200, 0.0345     # housing on the PCB, low on the bracket
ox0, ox1 = hx0 + 0.0012, hx0 + 0.0012 + 0.0082                # opening across the bracket width
oz0, oz1 = hz0 + 0.0014, hz0 + 0.0014 + 0.0117                # opening along the bracket length
nz0, nz1 = (oz0 + oz1) / 2 - 0.0030, (oz0 + oz1) / 2 + 0.0030 # latch notch
nx1 = ox1 + 0.0015
yd = YF - 0.012
j = Part("nic_rj45", ((hx0 + hx1) / 2, YF, hz0))
H = M("M_CordBlack")
j.box(hx0, hx1, YB, yd, hz0, hz1, H)                                         # body behind the cavity
j.box(hx0, ox0, yd, YF, hz0, hz1, H)                                         # far-side wall
j.box(ox0, nx1, yd, YF, hz0, oz0, H); j.box(ox0, nx1, yd, YF, oz1, hz1, H)   # ends
j.box(ox1, nx1, yd, YF, oz0, nz0, H); j.box(ox1, nx1, yd, YF, nz1, oz1, H)   # either side of the notch
j.box(nx1, hx1, yd, YF, hz0, hz1, H)                                         # PCB-side wall
j.box(ox0, ox1, yd - 0.0003, yd, oz0, oz1, DARK); j.box(ox1, nx1, yd - 0.0003, yd, nz0, nz1, DARK)
for k in range(8):                                                           # contacts on the far side
    z = (oz0 + oz1) / 2 + (k - 3.5) * 1.02 * mm
    j.box(ox0, ox0 + 0.0018, YF - 0.0095, YF - 0.0055, z - 0.0002, z + 0.0002, GOLD)
j.build(N, a)

# ---------- LED light pipes on the card, through the bracket (above the jack) ----------
LEDS = [(-0.0858, 0.0390), (-0.0826, 0.0390)]
for i, (lx, lz) in enumerate(LEDS, 1):
    l = Part(f"nic_led_{i}", (lx, YF, lz))
    l.cyl((lx, 0, lz), "Y", 0.6330, YF + 0.0004, 0.0012, M("M_LEDGreen"), 12)
    setp(l.build(N, a), role="indicator", tip="nic_led", states="link/activity")

# ---------- solid bracket: plate + tab over the rail + bottom peg; jack window + LED holes ----------
b = Part("nic_bracket")
b.box(BX0, BX1, 0.6385, 0.6395, 0.0100, 0.0847, M("M_Zinc"))
b.box(BX0, BX1, 0.6385, 0.6450, 0.0847, 0.0855, M("M_Zinc"))                # tab folded over the top band
bc = (BX0 + BX1) / 2
b.box(bc - 0.0065, bc + 0.0065, 0.6385, 0.6395, 0.0070, 0.0100, M("M_Zinc")) # wide bottom tongue ...
b.box(bc - 0.0050, bc + 0.0050, 0.6385, 0.6395, 0.0055, 0.0070, M("M_Zinc")) # ... chamfered end in the lip slot
br = b.build(N, a)
cuts = []
k = Part("cut"); k.box(hx0 - 0.0003, hx1 + 0.0003, 0.630, 0.650, hz0 - 0.0003, hz1 + 0.0003, DARK); cuts.append(k)
for (lx, lz) in LEDS:
    k = Part("cut"); k.cyl((lx, 0, lz), "Y", 0.630, 0.650, 0.00135, DARK, 12); cuts.append(k)
boolean_cut(br, cuts, N)

fastener(screw("nic_screw", screw_mesh("screw_bracket", 0.0022, 0.0018, "phillips"), ((BX0 + BX1) / 2, 0.6425, 0.0855), N, a),
         "phillips_2", turns=3, rise=0.003)
print("NIC_REPORT", {"tris": tris(N)})
save()
