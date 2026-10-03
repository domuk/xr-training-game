"""Rear I/O v2 — modern server panel (no audio/serial/parallel), with contact-level detail.
Seen from the REAR, PSU side (+X) first:
  PS/2 combo · USB 2.0 x2 · VGA (DE-15) · IPMI RJ45 over USB 3.0 x2 · USB-C · LAN1 · LAN2 · UID button
Connector geometry from the standards: USB-A opening 12.0 x 4.5, tongue 11 x 1.8, 4 (USB2) / 9 (USB3) contacts;
RJ45 8 contacts @ 1.02 mm; DE-15 3 rows of 5 @ 2.29 mm; USB-C opening 8.34 x 2.56, 12 contacts/side @ 0.5 mm.
Ports are children of the board asset; the shield is fixed chassis. MODEL-SPEC §12.5."""
import bpy, bmesh, math
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
from mathutils import Vector
S = server_coll(); IO = coll("rear_io", S); wipe(IO)

BT = 0.0076
YB, YF = 0.607, 0.6392          # port body back / front face (front sits inside the shield cut-out)
SY0, SY1 = 0.6385, 0.6395       # shield
board = bpy.data.objects["asset_board"]; fxc = bpy.data.objects["fixed_chassis"]
MET, DARK, GOLD = M("M_EarAlu"), M("M_ChipBlack"), M("M_Gold")
mm = 0.001
cutters = []

exec(open(bpy.path.abspath("//scripts/_ports.py")).read())   # hull, jack, rj45, usb_a

def cut_box(x0, x1, z0, z1, c=0.0005):
    k = Part("cut"); k.box(x0 - c, x1 + c, 0.62, 0.66, z0 - c, z1 + c, DARK); cutters.append(k)


# ---------- 1. PS/2 combo (purple/green split face, 6 pins + key) ----------
x0, x1, z0, z1 = 0.0880, 0.1020, BT, BT + 0.0130
xc, zc = (x0 + x1) / 2, BT + 0.0065
p = Part("io_ps2", (xc, YF, BT))
p.box(x0, x1, YB, YF - 0.0004, z0, z1, MET)
semi = lambda zs: [(xc + 5.8 * mm * math.cos(a), y, zc + zs * 5.8 * mm * abs(math.sin(a)))
                   for a in [math.pi * k / 10 for k in range(11)] for y in (YF - 0.0004, YF)]
hull(p, semi(1), M("M_IO_Purple")); hull(p, semi(-1), M("M_IO_Green"))
for (dx, dz) in ((-3.3, 0.6), (3.3, 0.6), (-3.4, -1.8), (3.4, -1.8), (-1.3, -3.4), (1.3, -3.4)):
    p.cyl((xc + dx * mm, 0, zc + dz * mm), "Y", YF, YF + 0.0001, 0.5 * mm, DARK, 6)
p.box(xc - 1.0 * mm, xc + 1.0 * mm, YF, YF + 0.0001, zc + 2.5 * mm, zc + 3.9 * mm, DARK)     # key
cut_box(x0, x1, z0, z1)
p.build(IO, board)

# ---------- 2. USB 2.0 x2 (black tongues, 4 contacts) ----------
x0, x1, z0, z1 = 0.0700, 0.0845, BT, BT + 0.0160
xc = (x0 + x1) / 2
p = Part("io_usb2", (xc, YF, BT))
zcs = [BT + 0.0040, BT + 0.0118]
yd = YF - 0.009
p.box(x0, x1, YB, yd, z0, z1, MET)
for zc in zcs:
    p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd - 0.0003, yd, zc - 2.25 * mm, zc + 2.25 * mm, DARK)
    usb_a(p, xc, zc, M("M_SlotBlack"), 4)
# shell frame around both openings
p.box(x0, xc - 6.0 * mm, yd, YF, z0, z1, MET); p.box(xc + 6.0 * mm, x1, yd, YF, z0, z1, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, z0, zcs[0] - 2.25 * mm, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, zcs[0] + 2.25 * mm, zcs[1] - 2.25 * mm, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, zcs[1] + 2.25 * mm, z1, MET)
cut_box(x0, x1, z0, z1)
p.build(IO, board)

# ---------- 3. VGA DE-15 (blue insert, 15 holes in 3 rows, metal shell + jack screws) ----------
xc, zc = 0.0490, BT + 0.0065
p = Part("io_vga", (xc, YF, BT))
p.box(xc - 0.0120, xc + 0.0120, YB, 0.6360, BT, BT + 0.0110, M("M_VGABlue"))                 # body
p.box(xc - 0.0154, xc + 0.0154, 0.6360, 0.6375, BT, BT + 0.0140, MET)                       # flange plate
D = lambda y0, y1, wt, wb, h: [(xc + sx * w / 2, y, zc + sz * h / 2) for y in (y0, y1)
                               for (w, sz) in ((wt, 1), (wb, -1)) for sx in (-1, 1)]
hull(p, D(0.6375, 0.6400, 16.9 * mm, 14.6 * mm, 8.4 * mm), MET)                             # D shell
hull(p, D(0.6400, 0.64008, 15.0 * mm, 12.8 * mm, 6.6 * mm), M("M_VGABlue"))                 # insert face
for row, (xs0, n, dz) in enumerate(((-4.57, 5, 1.98), (-5.72, 5, 0.0), (-4.57, 5, -1.98))):
    for k in range(n):
        p.cyl((xc + (xs0 + 2.29 * k) * mm, 0, zc + dz * mm), "Y", 0.64008, 0.6402, 0.45 * mm, DARK, 6)
for s in (-1, 1):
    p.cyl((xc + s * 12.5 * mm, 0, zc), "Y", 0.6375, 0.6400, 2.4 * mm, MET, 6)               # hex jack screws
    p.cyl((xc + s * 12.5 * mm, 0, zc), "Y", 0.6400, 0.64005, 1.1 * mm, DARK, 8)
    k = Part("cut"); k.cyl((xc + s * 12.5 * mm, 0, zc), "Y", 0.62, 0.66, 3.0 * mm, DARK, 12); cutters.append(k)
k = Part("cut"); hull(k, D(0.62, 0.66, 17.9 * mm, 15.6 * mm, 9.4 * mm), DARK); cutters.append(k)
p.build(IO, board)

# ---------- 4. IPMI management RJ45 over USB 3.0 x2 (blue tongues, 9 contacts) ----------
x0, x1 = 0.0160, 0.0320; xc = (x0 + x1) / 2
p = Part("io_ipmi_usb3", (xc, YF, BT))
zcs = [BT + 0.0040, BT + 0.0118]; yd = YF - 0.009; z1u = BT + 0.0160
p.box(x0, x1, YB, yd, BT, z1u, MET)
for zc in zcs:
    p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd - 0.0003, yd, zc - 2.25 * mm, zc + 2.25 * mm, DARK)
    usb_a(p, xc, zc, M("M_USB3Blue"), 9)
p.box(x0, xc - 6.0 * mm, yd, YF, BT, z1u, MET); p.box(xc + 6.0 * mm, x1, yd, YF, BT, z1u, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, BT, zcs[0] - 2.25 * mm, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, zcs[0] + 2.25 * mm, zcs[1] - 2.25 * mm, MET)
p.box(xc - 6.0 * mm, xc + 6.0 * mm, yd, YF, zcs[1] + 2.25 * mm, z1u, MET)
rj45(p, x0, x1, z1u + 0.0005, 0.0135)
cut_box(x0, x1, BT, z1u + 0.0140)
p.build(IO, board)

# ---------- 5. USB-C (capsule shell, tongue with 12 contacts per side) ----------
xc, zc = 0.0085, BT + 0.0045
p = Part("io_usbc", (xc, YF, BT))
def capsule(w, h, y0, y1, n=8):
    r = h / 2; pts = []
    for s in (-1, 1):
        for k in range(n + 1):
            a = -math.pi / 2 + math.pi * k / n
            pts += [(xc + s * (w / 2 - r + r * math.cos(a)), y, zc + r * math.sin(a)) for y in (y0, y1)]
    return pts
p.box(xc - 4.47 * mm, xc + 4.47 * mm, YB + 0.022, YF - 0.0065, zc - 1.58 * mm, zc + 1.58 * mm, MET)
hull(p, capsule(8.94 * mm, 3.16 * mm, YF - 0.0065, YF), MET)                                # shell
hull(p, capsule(8.34 * mm, 2.56 * mm, YF, YF + 0.00005), DARK)                              # opening face
p.box(xc - 3.3 * mm, xc + 3.3 * mm, YF - 0.0060, YF + 0.00007, zc - 0.35 * mm, zc + 0.35 * mm, M("M_SlotBlack"))   # tongue
for k in range(12):
    x = xc + (k - 5.5) * 0.5 * mm
    for z in (zc + 0.35 * mm, zc - 0.36 * mm):
        p.box(x - 0.12 * mm, x + 0.12 * mm, YF - 0.0040, YF + 0.00008, z, z + 0.01 * mm, GOLD)
k = Part("cut"); hull(k, [(q[0], 0.62 if q[1] < YF - 0.003 else 0.66, q[2]) for q in capsule(9.94 * mm, 4.16 * mm, 0.62, 0.66)], DARK); cutters.append(k)
p.build(IO, board)

# ---------- 6. LAN1 + LAN2 (single RJ45 each) ----------
for nm, (x0, x1) in (("io_lan1", (-0.0230, -0.0070)), ("io_lan2", (-0.0420, -0.0260))):
    p = Part(nm, ((x0 + x1) / 2, YF, BT)); rj45(p, x0, x1, BT, 0.0135); cut_box(x0, x1, BT, BT + 0.0135); p.build(IO, board)

# ---------- 7. UID button (blue LED button, press) ----------
xc, zc = -0.0520, BT + 0.0060
p = Part("io_uid_bezel", (xc, YF, zc)); p.cyl((xc, 0, zc), "Y", YB + 0.020, YF, 3.4 * mm, MET, 16); p.build(IO, board)
u = Part("io_uid_button", (xc, YF, zc)); u.cyl((xc, 0, zc), "Y", YF - 0.002, YF + 0.0003, 2.5 * mm, M("M_UIDBlue"), 16)
moving(u.build(IO, board), "press", "Y", [0.0, -0.0012], tip="uid_button", note="lights the blue UID LED front and rear")
k = Part("cut"); k.cyl((xc, 0, zc), "Y", 0.62, 0.66, 4.0 * mm, DARK, 16); cutters.append(k)

# ---------- I/O shield: plain zinc, port cut-outs, printed labels ----------
old = bpy.data.objects.get("io_shield")
if old: bpy.data.objects.remove(old, do_unlink=True)
sh = Part("io_shield"); sh.box(-0.069, 0.105, SY0, SY1, 0.006, 0.054, M("M_IOShield")); shield = sh.build(IO, fxc)
for c in cutters:
    co = c.build(IO)
    md = shield.modifiers.new("c", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = co; md.solver = "EXACT"
    bpy.context.view_layer.objects.active = shield; bpy.ops.object.modifier_apply(modifier=md.name)
    bpy.data.objects.remove(co, do_unlink=True)
REAR = (math.radians(90), 0, math.radians(180))                 # text reads correctly from behind the server
for txt, x, z in (("IPMI", 0.0240, BT + 0.0330), ("VGA", 0.0490, BT + 0.0185), ("USB", 0.0772, BT + 0.0190),
                  ("LAN1", -0.0150, BT + 0.0165), ("LAN2", -0.0340, BT + 0.0165), ("UID", -0.0520, BT + 0.0120)):
    text_obj(f"io_label_{txt.lower()}", txt, 0.0022, M("M_LabelBlack"), (x, SY1 + 0.00005, z), IO, fxc, rot=REAR)

print("REAR_IO_REPORT", {"objects": len(IO.all_objects), "tris": tris(IO), "cutters": len(cutters)})
save()
