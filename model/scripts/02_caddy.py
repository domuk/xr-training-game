"""Asset 2 (polish v2) — drive caddy x24: frame, release button (press), handle (hinge), activity/fault LEDs,
4 M3 drive screws, drive as a sub-asset. Shared meshes. MODEL-SPEC §8.2, §12.3b."""
import bpy
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
from mathutils import Vector
lay = load_layout()

S = server_coll(); P = coll("parts", S); CAD = coll("caddies", P); wipe(CAD)

HW = 0.0155 / 2
Z0, Z1 = 0.006 - 0.044, 0.082 - 0.044          # caddy bottom/top relative to the slot (front-face centre)
DEPTH, TAB_Z1 = 0.115, Z0 + 0.010
O = Vector((0, 0, 0))

def mesh_of(name, boxes, origin=(0, 0, 0)):
    p = Part(name, origin)
    for b in boxes: p.box(*b[:6], M(b[6]))
    return p.mesh()

frame_me = mesh_of("caddy_frame", [
    (-HW, HW, 0.004, DEPTH, Z0, Z0 + 0.003, "M_CaddyBlack"), (-HW, HW, 0.004, DEPTH, Z1 - 0.003, Z1, "M_CaddyBlack"),
    (-HW, -HW + 0.001, 0.004, DEPTH - 0.005, Z0, Z1, "M_CaddyBlack"), (-HW, HW, 0.004, 0.012, Z0, Z1, "M_CaddyBlack")])

# handle = black face above the button; hinge at the top front edge (local origin = hinge)
HZ0, HZ1, HINGE = TAB_Z1 + 0.001, Z1, (0.0, -0.002, Z1)
hb = [(-HW, HW, 0.0005, 0.004, HZ0, HZ1), (-HW, HW, -0.002, 0.0005, HZ0, HZ0 + 0.003), (-HW, HW, -0.002, 0.0005, HZ1 - 0.003, HZ1),
      (-HW, -HW + 0.0025, -0.002, 0.0005, HZ0, HZ1), (HW - 0.0025, HW, -0.002, 0.0005, HZ0, HZ1), (-0.001, 0.001, -0.002, 0.0005, HZ0, HZ1)]
span = (HZ1 - 0.003) - (HZ0 + 0.003)
hb += [(-HW, HW, -0.002, 0.0005, HZ0 + 0.003 + span * r / 4 - 0.0015, HZ0 + 0.003 + span * r / 4 + 0.0015) for r in (1, 2, 3)]
handle_me = mesh_of("caddy_handle", [(*b, "M_CaddyBlack") for b in hb], HINGE)
tz = (Z0 + TAB_Z1) / 2
button_me = mesh_of("caddy_button", [(-HW + 0.0005, HW - 0.0005, -0.0015, 0.0015, Z0, TAB_Z1, "M_CaddyRed")], (0, 0, tz))
led_g_me = mesh_of("caddy_led_act", [(-0.0045, -0.0025, -0.0026, -0.0020, HZ1 - 0.0025, HZ1 - 0.0010, "M_LEDGreen")], HINGE)
led_r_me = mesh_of("caddy_led_fault", [(0.0025, 0.0045, -0.0026, -0.0020, HZ1 - 0.0025, HZ1 - 0.0010, "M_LEDRed")], HINGE)

DW, DD, DH = 0.007, 0.100, 0.0699
DC = Vector((0.0005, 0.013 + DD / 2, (Z0 + 0.003 + Z1 - 0.003) / 2))
drive_me = mesh_of("drive_25", [(-DW / 2, DW / 2, -DD / 2, DD / 2, -DH / 2, DH / 2, "M_DriveGrey"),
                                (-DW / 2 + 0.001, DW / 2 - 0.001, DD / 2, DD / 2 + 0.002, -DH / 2 + 0.003, -DH / 2 + 0.030, "M_SlotBlack")])
screw_me = screw_mesh("caddy_screw", 0.0018, 0.0008, "phillips", shaft=(0.0008, 0.0047), segs=10)   # head outside, shaft into the drive
SCREWS = [(DC.y - 0.035, DC.z - 0.020), (DC.y - 0.035, DC.z + 0.020), (DC.y + 0.035, DC.z - 0.020), (DC.y + 0.035, DC.z + 0.020)]

for n in range(1, 25):
    s = Vector(lay["slots"][f"slot_caddy_{n:02d}"]); nn = f"{n:02d}"
    a = asset(f"caddy_{nn}", s, CAD, pull=[[0, -0.13, 0]], requires=f"caddy_{nn}_button,caddy_{nn}_handle",
              tip="drive_caddy", bay=n - 1)
    inst(f"caddy_{nn}_frame", frame_me, s, CAD, a)
    h = inst(f"caddy_{nn}_handle", handle_me, s + Vector(HINGE), CAD, a)
    moving(h, "hinge", "X", [0.0, -60.0], tip="caddy_handle")
    inst(f"caddy_{nn}_led_act", led_g_me, s + Vector(HINGE), CAD, h); inst(f"caddy_{nn}_led_fault", led_r_me, s + Vector(HINGE), CAD, h)
    b = inst(f"caddy_{nn}_button", button_me, s + Vector((0, -0.0005, tz)), CAD, a)
    moving(b, "press", "Y", [0.0, 0.0015], tip="caddy_button")
    d = asset(f"drive_{nn}", s + DC, CAD, parent=a, pull=[[0.015, 0, 0]],
              requires=",".join(f"caddy_{nn}_screw_{k}" for k in range(1, 5)), tip="drive_in_caddy")
    inst(f"drive_{nn}_body", drive_me, s + DC, CAD, d)
    for k, (y, z) in enumerate(SCREWS, 1):
        sc = screw(f"caddy_{nn}_screw_{k}", screw_me, s + Vector((-HW, y, z)), CAD, a, axis="-X")
        fastener(sc, "phillips_1", axis="X", turns=4, rise=0.004)

print("CADDY_REPORT", {"objects": len(CAD.all_objects), "tris": tris(CAD), "per_caddy": tris(CAD) // 24})
save()
