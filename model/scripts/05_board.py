"""Asset 5 (polish v2) — motherboard asset: PCB, 10 screws on the chassis standoffs, sockets (lever + hook,
load plate, keys, triangle), DIMM slots (U, key, 2 ejector clips with nubs), PCIe slots (offset §12.3a),
chipset, battery holder + clip + battery asset, power headers, SATA ports, rear I/O through the shield,
labels. MODEL-SPEC §8.5, §12."""
import bpy, math
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
from mathutils import Vector
lay = load_layout()

S = server_coll(); BRD = coll("board", S); wipe(BRD)
BT = 0.0076; NOTCH_Y = 0.0040
SOCK = [tuple(s) for s in lay["sockets"]]; PCIE_X = lay["pcie_x"]

board = asset("board", (-0.044, 0.4225, BT), BRD, pull=[[0, 0, 0.0003], [0, -0.010, 0], [0, 0, 0.10]],
              requires=",".join([f"board_screw_{i}" for i in range(1, 11)] +
                                ["asset_shroud", "asset_nic", "asset_accel", "asset_cable_sata", "atx_plug_24", "atx_plug_8"]),
              carries="asset_dimm_*,asset_cpu_*,asset_hs_*,asset_battery", tip="motherboard")

# ---------- PCB + fixed components ----------
p = Part("board_pcb")
p.box(-0.200, 0.112, 0.215, 0.630, 0.006, BT, M("M_PCBGreen"))
cx, cy = -0.035, 0.420                                                        # chipset heatsink
p.box(cx - 0.020, cx + 0.020, cy - 0.020, cy + 0.020, BT, BT + 0.004, M("M_Zinc"))
for k in range(6):
    fx = cx - 0.0175 + k * 0.007; p.box(fx, fx + 0.002, cy - 0.020, cy + 0.020, BT + 0.004, 0.030, M("M_Zinc"))
p.box(0.1045, 0.1115, 0.327, 0.355, BT, BT + 0.013, M("M_PlugWhite"))           # 24-pin header
p.box(0.1045, 0.1115, 0.300, 0.318, BT, BT + 0.013, M("M_PlugWhite"))           # 8-pin header
for k in range(8):                                                           # SATA ports
    x = -0.190 + k * 0.0135; p.box(x, x + 0.008, 0.218, 0.232, BT, BT + 0.006, M("M_SATARed"))
for x in PCIE_X:                                                             # PCIe x16, U-section
    p.box(x - 0.00375, x + 0.00375, 0.540, 0.629, BT, BT + 0.003, M("M_SlotBlack"))
    p.box(x - 0.00375, x - 0.00095, 0.540, 0.629, BT + 0.003, BT + 0.011, M("M_SlotBlack"))
    p.box(x + 0.00095, x + 0.00375, 0.540, 0.629, BT + 0.003, BT + 0.011, M("M_SlotBlack"))
# rear I/O ports: built by 12_rear_io.py (children of this board asset)
bx, by = -0.010, 0.370                                                       # battery holder
p.cyl((bx, by, 0), "Z", BT, BT + 0.0010, 0.0115, M("M_SlotBlack"), 16)
p.build(BRD, board)

# labels
lab = M("M_LabelWhite"); flat = (0, 0, 0)
for i, (sx, sy) in enumerate(SOCK, 1):
    text_obj(f"label_cpu{i}", f"CPU{i}", 0.004, lab, (sx, sy - 0.046, BT + 0.0001), BRD, board)
for i in range(8):
    text_obj(f"label_dimm{i+1}", str(i + 1), 0.003, lab, (0.020 + 0.00325 + i * 0.0105, 0.3505, BT + 0.0001), BRD, board)
for i, x in enumerate(PCIE_X, 1):
    text_obj(f"label_pcie{i}", f"S{i}", 0.003, lab, (x, 0.5355, BT + 0.0001), BRD, board)

# ---------- board screws (rounded Phillips, on plated mounting holes; standoffs are in the chassis) ----------
SCR = screw_mesh("screw_board", 0.0030, 0.0020, "phillips")
for i, (x, y) in enumerate(lay["board_screws"], 1):
    fastener(screw(f"board_screw_{i}", SCR, (x, y, BT + 0.00005), BRD, board), "phillips_2", turns=5, rise=0.006)

# ---------- small details (ref 3dmi 02/06/08 + components img 8/9) ----------
d = Part("board_details")
for (x, y) in lay["board_screws"]:                                   # plated (gold) ring round each mounting hole
    d.cyl((x, y, 0), "Z", BT, BT + 0.00005, 0.0045, M("M_Gold"), 16)
# VRM: chokes + MOSFETs in front of each socket (between the fan wall and the heatsinks)
VRM_X = [x for x in [-0.052 + k * 0.0092 for k in range(17)] if abs(x - 0.100) > 0.008 and abs(x + 0.060) > 0.008 and x < 0.106]
for x in VRM_X:
    d.box(x - 0.0035, x + 0.0035, 0.2205, 0.2275, BT, BT + 0.0050, M("M_Choke"))          # choke
    d.box(x - 0.0025, x + 0.0025, 0.2155, 0.2195, BT, BT + 0.0010, M("M_ChipBlack"))      # MOSFET
# solid capacitors between the sockets and the DIMMs, and beside the rear I/O
CAPS = [(x, 0.340) for x in (-0.055, -0.045, -0.035, -0.025, -0.015, 0.032, 0.042, 0.052, 0.062, 0.072, 0.082, 0.092)]
CAPS += [(x, 0.592) for x in (-0.060, -0.050, 0.036, 0.046)]
for (x, y) in CAPS:
    d.cyl((x, y, 0), "Z", BT, BT + 0.0065, 0.0040, M("M_CapBody"), 12)
    d.cyl((x, y, 0), "Z", BT + 0.0065, BT + 0.0070, 0.0036, M("M_EarAlu"), 12)          # silver top
# BMC (management controller) + small ICs
d.box(0.0750, 0.0890, 0.5450, 0.5590, BT, BT + 0.0012, M("M_ChipBlack"))
for (x, y, w) in ((-0.150, 0.300, 0.007), (-0.130, 0.330, 0.005), (-0.160, 0.470, 0.008), (0.030, 0.575, 0.006),
                  (-0.040, 0.470, 0.006), (0.010, 0.470, 0.005)):
    d.box(x - w / 2, x + w / 2, y - w / 2, y + w / 2, BT, BT + 0.0010, M("M_ChipBlack"))
# front-panel header (2 x 10 pins) + white 4-pin fan/power header + clear-CMOS jumper
d.box(-0.152, -0.128, 0.2400, 0.2450, BT, BT + 0.0025, M("M_SlotBlack"))
for i in range(10):
    for j in range(2):
        x = -0.1508 + i * 0.00254; y = 0.2412 + j * 0.00254
        d.box(x - 0.00032, x + 0.00032, y - 0.00032, y + 0.00032, BT + 0.0025, BT + 0.0085, M("M_Gold"))
d.box(-0.120, -0.1105, 0.2400, 0.2450, BT, BT + 0.0060, M("M_PlugWhite"))
d.box(0.0050, 0.0100, 0.3720, 0.3760, BT, BT + 0.0025, M("M_SlotBlack"))
d.box(0.0055, 0.0095, 0.3725, 0.3755, BT + 0.0025, BT + 0.0050, M("M_SATARed"))
# scattered SMD parts (seeded) in the clear left area
import random
rnd = random.Random(7)
for _ in range(60):
    x = rnd.uniform(-0.185, -0.095); y = rnd.uniform(0.255, 0.525)
    if any(abs(x - sx) < 0.006 and abs(y - sy) < 0.006 for (sx, sy) in lay["board_screws"]): continue
    w, l = rnd.choice(((0.0020, 0.0012), (0.0016, 0.0008), (0.0032, 0.0016)))
    if rnd.random() < 0.5: w, l = l, w
    d.box(x - w / 2, x + w / 2, y - l / 2, y + l / 2, BT, BT + 0.0006, M(rnd.choice(("M_ChipBlack", "M_ClipGrey", "M_FanTan"))))
d.build(BRD, board)

# ---------- CPU sockets ----------
for n, (sx, sy) in enumerate(SOCK, 1):
    s = Part(f"socket_{n}", (sx, sy, BT))
    s.box(sx - 0.0225, sx + 0.0225, sy - 0.0225, sy + 0.0225, BT, 0.0094, M("M_SlotBlack"))
    s.box(sx - 0.026, sx + 0.026, sy - 0.039, sy + 0.039, 0.0040, 0.0058, M("M_ChipBlack"))           # backplate
    s.tri(((sx - 0.021, sy - 0.021, 0.00942), (sx - 0.015, sy - 0.021, 0.00942), (sx - 0.021, sy - 0.015, 0.00942)), M("M_PlugWhite"))
    for kx in (-1, 1):                                                                              # orientation keys
        s.box(*sorted((kx * 0.0179 + sx, kx * 0.0187 + sx)), sy + 0.005, sy + 0.007, 0.0094, 0.0104, M("M_SlotBlack"))
    lx = sx + 0.0275
    s.box(lx + 0.0009, lx + 0.0025, sy - 0.028, sy - 0.024, BT, 0.0118, M("M_SocketSilver"))       # lever hook post
    s.box(lx - 0.0010, lx + 0.0025, sy - 0.028, sy - 0.024, 0.0110, 0.0118, M("M_SocketSilver"))   # hook lip over lever
    so = s.build(BRD, board); setp(so, role="fixed", tip="cpu_socket")
    hy = sy + 0.026
    pl = Part(f"socket_{n}_plate", (sx, hy, 0.0106)); z0, z1 = 0.0106, 0.0116
    for b in ((sx - 0.024, sx + 0.024, sy - 0.026, sy - 0.016), (sx - 0.024, sx + 0.024, sy + 0.016, sy + 0.026),
              (sx - 0.024, sx - 0.016, sy - 0.016, sy + 0.016), (sx + 0.016, sx + 0.024, sy - 0.016, sy + 0.016)):
        pl.box(*b, z0, z1, M("M_SocketSilver"))
    pl.box(sx - 0.004, sx + 0.004, sy - 0.032, sy - 0.026, BT, z1, M("M_SocketSilver"))               # front tongue
    pl.cyl((sx, sy - 0.029, 0), "Z", z1, z1 + 0.002, 0.0025, M("M_SocketSilver"))                     # retention screw
    moving(pl.build(BRD, so), "hinge", "X", [0.0, -110.0], requires=f"socket_{n}_lever", tip="load_plate")
    lv = Part(f"socket_{n}_lever", (lx, sy + 0.030, 0.0100))
    lv.box(lx - 0.0008, lx + 0.0008, sy - 0.034, sy + 0.030, 0.0092, 0.0108, M("M_SocketSilver"))
    lv.box(lx - 0.0040, lx + 0.0008, sy - 0.036, sy - 0.034, 0.0092, 0.0108, M("M_SocketSilver"))     # finger tab
    moving(lv.build(BRD, so), "hinge", "X", [0.0, -100.0], requires=f"asset_hs_{n}", tip="socket_lever",
           note="push down and out from the hook, then lift")

# ---------- DIMM slots + ejector clips ----------
for n in range(8):
    x0 = 0.020 + n * 0.0105; xc = x0 + 0.00325
    d = Part(f"dimm_slot_{n+1:02d}", (xc, 0.431, BT))
    d.box(x0, x0 + 0.0065, 0.360, 0.502, BT, 0.0096, M("M_SlotBlack"))
    d.box(x0, x0 + 0.0022, 0.360, 0.502, 0.0096, BT + 0.008, M("M_SlotBlack"))
    d.box(x0 + 0.0043, x0 + 0.0065, 0.360, 0.502, 0.0096, BT + 0.008, M("M_SlotBlack"))
    d.box(x0 + 0.0022, x0 + 0.0043, 0.431 + NOTCH_Y - 0.0008, 0.431 + NOTCH_Y + 0.0008, 0.0096, 0.0124, M("M_SlotBlack"))
    do = d.build(BRD, board)
    for tag, (y0, y1, hy, ny0, ny1, sign) in (("F", (0.356, 0.360, 0.358, 0.3600, 0.3655, 1)),
                                              ("R", (0.502, 0.506, 0.504, 0.4965, 0.5020, -1))):
        c = Part(f"dimm_slot_{n+1:02d}_clip{tag}", (xc, hy, BT))
        c.box(x0, x0 + 0.0065, y0, y1, BT, 0.0260, M("M_ClipGrey"))
        c.box(x0 + 0.0022, x0 + 0.0043, ny0, ny1, 0.0218, 0.0254, M("M_ClipGrey"))                 # nub into the DIMM cut-out
        moving(c.build(BRD, do), "hinge", "X", [0.0, 40.0 * sign], tip="dimm_ejector")

# ---------- battery (asset) + clip ----------
cl = Part("battery_clip", (bx + 0.0105, by, BT + 0.004)); cl.box(bx + 0.0095, bx + 0.0120, by - 0.003, by + 0.003, BT, BT + 0.0048, M("M_Screw"))
moving(cl.build(BRD, board), "press", "X", [0.0, 0.0015], tip="battery_clip")
ba = asset("battery", (bx, by, BT + 0.001), BRD, parent=board, pull=[[0, 0, 0.02]], requires="battery_clip", tip="cmos_battery")
bt = Part("battery_cell"); bt.cyl((bx, by, 0), "Z", BT + 0.0010, BT + 0.0042, 0.0100, M("M_EarAlu"), 20); bt.build(BRD, ba)

lay["board"] = {"x": [-0.200, 0.112], "y": [0.215, 0.630], "top": BT, "dimm_notch_y": NOTCH_Y, "pcie_groove_floor": BT + 0.003}
save_layout(lay)
print("BOARD_REPORT", {"objects": len(BRD.all_objects), "tris": tris(BRD)})
save()
