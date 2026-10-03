"""Assets 7 + 8 (polish v2) — CPU asset x2 (edge notches, triangle), heatsink asset x2 (fins cut back at the
corners for tool access, 4 captive Torx screws numbered 1-4, sequence label). MODEL-SPEC §8.7, §12.3b."""
import bpy, math
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
lay = load_layout()
S = server_coll(); P = coll("parts", S); C = coll("cpus", P); H = coll("heatsinks", P)
wipe(C); wipe(H)

# ---------- CPU (local origin = centre of underside) ----------
E, NK = 0.01875, 0.001                    # half size, notch depth; notches at y +0.005..+0.007 on both sides
p = Part("cpu")
p.box(-E + NK, E - NK, -E, E, 0, 0.0012, M("M_PCBGreen"))
for s in (-1, 1):
    x0, x1 = sorted((s * (E - NK), s * E))
    p.box(x0, x1, -E, 0.005, 0, 0.0012, M("M_PCBGreen")); p.box(x0, x1, 0.007, E, 0, 0.0012, M("M_PCBGreen"))
p.box(-0.015, 0.015, -0.015, 0.015, 0.0012, 0.0045, M("M_SocketSilver"))
p.tri(((-0.013, -0.013, 0.00452), (-0.008, -0.013, 0.00452), (-0.013, -0.008, 0.00452)), M("M_Gold"))
cpu_me = p.mesh()

# ---------- heatsink (local origin = centre of base underside) ----------
TOPZ = 0.080 - 0.0139; CC = 0.025         # fin top; corner columns |x|,|y| > CC are clear for the screwdriver
p = Part("heatsink")
p.box(-0.040, 0.040, -0.040, 0.040, 0, 0.004, M("M_Copper"))
p.box(-CC, CC, -0.035, 0.035, 0.004, 0.007, M("M_HeatsinkFin")); p.box(-0.035, -CC, -CC, CC, 0.004, 0.007, M("M_HeatsinkFin"))
p.box(CC, 0.035, -CC, CC, 0.004, 0.007, M("M_HeatsinkFin"))
N, FT = 15, 0.0010; pitch = (0.070 - FT) / (N - 1)
for k in range(N):
    x = -0.035 + k * pitch
    yy = 0.035 if (x + FT > -CC and x < CC) else CC
    p.box(x, x + FT, -yy, yy, 0.007, TOPZ, M("M_HeatsinkFin"))
p.box(-0.016, 0.016, -0.007, 0.007, TOPZ, TOPZ + 0.0003, M("M_LabelWhite"))       # sequence label plate
hs_me = p.mesh()
label_me = text_mesh("hs_label_text", "OUT 4-3-2-1\nIN  1-2-3-4", 0.0026, M("M_LabelBlack"))
screw_me = screw_mesh("hs_screw", 0.0030, 0.0030, "torx", "M_Copper", shaft=(0.0015, 0.0179 - 0.0076 - 0.004))   # captive Torx
NUM = {d: text_mesh(f"hs_num_{d}", str(d), 0.0045, M("M_LabelWhite")) for d in (1, 2, 3, 4)}
ORDER = {1: (-1, -1), 2: (1, 1), 3: (1, -1), 4: (-1, 1)}         # diagonal: FL, RR, FR, RL

from mathutils import Vector
for n in (1, 2):
    cl = Vector(lay["slots"][f"slot_cpu_{n}"]); hl = Vector(lay["slots"][f"slot_hs_{n}"])
    ca = asset(f"cpu_{n}", cl, C, pull=[[0, 0, 0.05]], requires=f"asset_hs_{n},socket_{n}_lever,socket_{n}_plate",
               tip="cpu", check="triangle to the socket triangle; notches on the keys; hold by the edges")
    inst(f"cpu_{n}_body", cpu_me, cl, C, ca)
    ha = asset(f"hs_{n}", hl, H, pull=[[0, 0, 0.10]], requires=",".join(f"hs_{n}_screw_{k}" for k in (4, 3, 2, 1)),
               order_out="4,3,2,1", order_in="1,2,3,4", tip="heatsink", warn="may be hot")
    inst(f"hs_{n}_body", hs_me, hl, H, ha)
    lt = inst(f"hs_{n}_label", label_me, hl + Vector((0, 0, TOPZ + 0.00035)), H, ha)
    for k, (sx, sy) in ORDER.items():
        s = inst(f"hs_{n}_screw_{k}", screw_me, hl + Vector((sx * 0.034, sy * 0.034, 0.004)), H, ha)
        fastener(s, "torx_t20", turns=6, rise=0.006, captive=True, seq=k)
        inst(f"hs_{n}_num_{k}", NUM[k], hl + Vector((sx * 0.0295, sy * 0.0295, 0.00402)), H, ha)

print("CPU_HS_REPORT", {"cpus": tris(C), "heatsinks": tris(H)})
save()
