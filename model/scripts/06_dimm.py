"""Asset 6 (polish v2) — DIMM asset x8: PCB with off-centre notch + end cut-outs for the ejectors,
gold contacts, chips. Shared mesh. MODEL-SPEC §8.6, §12.3b."""
import bpy
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
lay = load_layout()
S = server_coll(); P = coll("parts", S); D = coll("dimms", P); wipe(D)

NOTCH = lay["board"]["dimm_notch_y"]
L, H, T = 0.1333, 0.031, 0.0012
nw, nd = 0.0020, 0.0030
CZ0, CZ1, CD = 0.012, 0.016, 0.0015          # ejector cut-outs at both ends (local Z band, depth)
p = Part("dimm")
pcb = M("M_PCBGreen")
p.box(-T / 2, T / 2, -L / 2, NOTCH - nw / 2, 0, nd, pcb); p.box(-T / 2, T / 2, NOTCH + nw / 2, L / 2, 0, nd, pcb)
p.box(-T / 2, T / 2, -L / 2, L / 2, nd, CZ0, pcb)
p.box(-T / 2, T / 2, -L / 2 + CD, L / 2 - CD, CZ0, CZ1, pcb)
p.box(-T / 2, T / 2, -L / 2, L / 2, CZ1, H, pcb)
for s in (-1, 1):
    x0, x1 = sorted((s * T / 2, s * (T / 2 + 0.00005)))
    p.box(x0, x1, -L / 2 + 0.002, NOTCH - nw / 2, 0.0005, 0.0030, M("M_Gold"))
    p.box(x0, x1, NOTCH + nw / 2, L / 2 - 0.002, 0.0005, 0.0030, M("M_Gold"))
    x0, x1 = sorted((s * T / 2, s * (T / 2 + 0.0012)))
    for k in range(8):
        yc = -L / 2 + 0.010 + k * 0.0161 + (0.003 if k >= 4 else 0)
        p.box(x0, x1, yc - 0.0055, yc + 0.0055, 0.017, 0.028, M("M_ChipBlack"))
me = p.mesh()
for n in range(1, 9):
    nn = f"{n:02d}"; loc = lay["slots"][f"slot_dimm_{nn}"]
    a = asset(f"dimm_{nn}", loc, D, pull=[[0, 0, 0.06]], requires=f"dimm_slot_{nn}_clipF,dimm_slot_{nn}_clipR",
              tip="dimm", check="notch lines up with the slot key; press both corners until the ejectors click")
    inst(f"dimm_{nn}_pcb", me, loc, D, a)
print("DIMM_REPORT", {"tris": tris(D)})
save()
