"""Asset 3 (polish v2) — backplane (asset): PCB, 8 SATA + 4 power + 3 fan headers, 4 mounting screws.
MODEL-SPEC §8.3, §12."""
import bpy
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
from mathutils import Vector
lay = load_layout()

S = server_coll(); B = coll("backplane", S); wipe(B)
Y0, Y1 = 0.116, 0.1176
SCREW_POS = [(-0.205, 0.070), (-0.072, 0.070), (0.072, 0.070), (0.205, 0.070)]
bp = asset("backplane", (0, Y1, 0.040), B, pull=[[0, 0, 0.10]],
           requires=",".join([f"backplane_screw_{i}" for i in range(1, 5)] + ["asset_cable_sata", "pwr_1_plug",
                     "pwr_2_plug", "pwr_3_plug", "pwr_4_plug", "fan_01_plug", "fan_02_plug", "fan_03_plug"]),
           tip="backplane", note="all drives pulled out ~2 cm first")
p = Part("backplane_pcb")
p.box(-0.213, 0.213, Y0, Y1, 0.005, 0.075, M("M_PCBGreen"))
for i in range(8):
    x = -0.205 + i * 0.0105; p.box(x, x + 0.008, Y1, Y1 + 0.006, 0.042, 0.048, M("M_SlotBlack"))
for x in (-0.160, -0.053, 0.053, 0.160):
    p.box(x - 0.011, x + 0.011, Y1, Y1 + 0.008, 0.010, 0.020, M("M_PlugWhite"))
p.build(B, bp)
for i, fx in enumerate(lay["fan_x"]):              # fan headers, low, in line with each holder socket
    x = fx + 0.027
    h = Part(f"fan_header_{i+1:02d}", (x, Y1 + 0.003, 0.030)); h.box(x - 0.005, x + 0.005, Y1, Y1 + 0.006, 0.027, 0.033, M("M_PlugWhite"))
    setp(h.build(B, bp), role="connector", tip="fan_header")
    lay["slots"][f"slot_fanplug_{i+1:02d}"] = [round(x, 5), round(Y1 + 0.009, 5), 0.030]
fl = Part("backplane_flange"); fl.box(-0.213, 0.213, Y0, Y1 + 0.0060, 0.075, 0.076, M("M_Zinc")); fl.build(B, bp)  # top flange
for i, (x, _) in enumerate(SCREW_POS, 1):          # screws go down through the flange (reachable from above)
    s = screw(f"backplane_screw_{i}", screw_mesh("screw_backplane", 0.0026, 0.0018, "phillips"), (x, Y1 + 0.0032, 0.076), B, bp)
    fastener(s, "phillips_2", turns=4, rise=0.004)

lay["backplane"] = {"y": [Y0, Y1], "sata_x0": -0.205, "sata_pitch": 0.0105, "sata_z": 0.045,
                    "power_x": [-0.160, -0.053, 0.053, 0.160], "power_z": 0.015}
save_layout(lay)
print("BACKPLANE_REPORT", {"objects": len(B.all_objects), "tris": tris(B)})
save()
