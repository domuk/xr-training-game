"""Asset 4 (v3) — hot-swap fan rack.
FIXED (chassis): 3 tan holders, each with a release tab (press) and a quick-connect socket at the bottom front;
                 a permanent 4-wire cable from each socket to the backplane, with a plug that unplugs there.
ASSET:           the black fan only (frame, 7 blades, guard, airflow arrow) with a quick-connect plug on its
                 lower front edge that drops into the holder socket. Press tab -> lift fan; plug pulls free.
MODEL-SPEC §8.4, §12.8."""
import bpy, math
LIB = bpy.path.abspath("//scripts/_lib.py")
exec(open(LIB).read())
from mathutils import Matrix, Vector
lay = load_layout()

S = server_coll(); P = coll("parts", S); F = coll("fans", P); R = coll("fan_rack", S)
wipe(F); wipe(R)
for cu in [c for c in bpy.data.curves if c.name.startswith("fan_")]: bpy.data.curves.remove(cu)
FR = fixed("fan_rack", R)

FC, HY, SZ, B = -0.040, 0.0125, 0.040, 0.003     # local to fan origin (fan top-centre, Y 0.1825, Z 0.085)
FY, FZ = 0.1825, 0.085
PX0, PX1 = 0.022, 0.032                          # quick-connect plug X (local to fan centre)
PZ0, PZ1 = 0.008, 0.016                          # plug Z (world)

# ---------- fan body + quick-connect plug ----------
p = Part("fan_body")
for (x0, x1, z0, z1) in ((-SZ, SZ, SZ - B, SZ), (-SZ, SZ, -SZ, -SZ + B), (-SZ, -SZ + B, -SZ, SZ), (SZ - B, SZ, -SZ, SZ)):
    p.box(x0, x1, -HY, HY, FC + z0, FC + z1, M("M_FanBlack"))
for sx in (-1, 1):
    for sz in (-1, 1):
        p.box(*sorted((sx * SZ, sx * (SZ - 0.010))), -HY, HY, *sorted((FC + sz * SZ, FC + sz * (SZ - 0.010))), M("M_FanBlack"))
p.cyl((0, 0, FC), "Y", -HY + 0.002, HY - 0.001, 0.019, M("M_FanBlack"), 16)
for k in range(7):
    rot = Matrix.Translation((0, 0, FC)) @ Matrix.Rotation(math.radians(k * 360 / 7), 4, "Y") @ Matrix.Rotation(math.radians(30), 4, "X")
    p.box(0.017, 0.037, -0.001, 0.001, -0.009, 0.009, M("M_FanBlack"), rot)
for k in range(4):
    p.box(0.0, 0.037, -HY - 0.001, -HY, -0.0007, 0.0007, M("M_FanBlack"),
          Matrix.Translation((0, 0, FC)) @ Matrix.Rotation(math.radians(45 + k * 90), 4, "Y"))
for r in (0.036, 0.024):
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16; L = 2 * r * math.sin(math.pi / 16) + 0.0005
        p.box(-L / 2, L / 2, -HY - 0.001, -HY, -0.0006, 0.0006, M("M_FanBlack"),
              Matrix.Translation((r * math.cos(a), 0, FC + r * math.sin(a))) @ Matrix.Rotation(-a + math.pi / 2, 4, "Y"))
p.tri(((-0.004, -0.004, 0.0002), (0.004, -0.004, 0.0002), (0, 0.006, 0.0002)), M("M_PlugWhite"))   # airflow arrow -> rear
p.box(-0.0008, 0.0008, -0.010, -0.004, 0.0, 0.0002, M("M_PlugWhite"))
# quick-connect plug on the lower front edge (drops into the holder socket)
yq0, yq1 = 0.1665 - FY, 0.1700 - FY
p.box(PX0 + 0.0002, PX1 - 0.0002, yq0 + 0.0002, yq1, PZ0 - FZ + 0.0002, PZ1 - FZ, M("M_SlotBlack"))   # 0.2 mm fit in the socket
for i in range(4):                                                            # contact pads on the plug face
    x = PX0 + 0.0015 + i * 0.0023
    p.box(x, x + 0.0012, yq0 - 0.00005, yq0, PZ0 - FZ + 0.002, PZ1 - FZ - 0.002, M("M_Gold"))
fan_me = p.mesh()

# ---------- holder (fixed) ----------
HX, WT = 0.044, 0.003
Y0, Y1 = 0.164, 0.199
ZB, ZT = 0.002, 0.084
def holder_mesh():
    h = Part("fan_holder")
    h.box(-HX, -HX + WT, Y0, Y1, ZB, ZT, M("M_FanTan")); h.box(HX - WT, HX, Y0, Y1, ZB, ZT, M("M_FanTan"))
    h.box(-HX, HX, Y0, Y1, ZB, ZB + 0.003, M("M_FanTan"))
    for s in (-1, 1):
        h.box(*sorted((s * HX, s * (HX - 0.008))), Y0, Y0 + 0.002, ZB, ZT, M("M_FanTan"))
    h.box(-0.012, 0.012, Y1 - 0.002, Y1, ZB, ZB + 0.012, M("M_FanTan"))
    # quick-connect socket: U open at the top, at the bottom front (plug drops in from above)
    h.box(PX0 - 0.002, PX1 + 0.002, 0.1645, 0.1665, ZB + 0.003, PZ1 + 0.002, M("M_SlotBlack"))      # front wall
    h.box(PX0 - 0.002, PX0, 0.1665, 0.1700, ZB + 0.003, PZ1 + 0.002, M("M_SlotBlack"))             # side walls
    h.box(PX1, PX1 + 0.002, 0.1665, 0.1700, ZB + 0.003, PZ1 + 0.002, M("M_SlotBlack"))
    h.box(PX0, PX1, 0.1665, 0.1700, ZB + 0.003, PZ0, M("M_SlotBlack"))                              # floor
    for i in range(4):
        x = PX0 + 0.0015 + i * 0.0023
        h.box(x, x + 0.0012, 0.16650, 0.16660, PZ0 + 0.002, PZ1 - 0.002, M("M_Gold"))               # socket contacts
    return h.mesh()
holder_me = holder_mesh()
tab = Part("fan_release_tab", (HX - 0.0015, Y0 + 0.006, ZT))
tab.box(HX - WT, HX, Y0 + 0.001, Y0 + 0.011, ZT, ZT + 0.0008, M("M_FanTan"))
tab.box(HX - WT - 0.0005, HX - WT, Y0 + 0.001, Y0 + 0.011, ZT - 0.006, ZT + 0.0008, M("M_FanTan"))   # latch lip, just clear of the fan frame
tab_me = tab.mesh()
pl = Part("fan_plug"); pl.box(-0.005, 0.005, -0.003, 0.003, -0.003, 0.003, M("M_SlotBlack"))
pl.box(-0.002, 0.002, -0.003, 0.000, 0.003, 0.0038, M("M_SlotBlack")); plug_me = pl.mesh()
WIRES = [M("M_Wire_Black"), M("M_Wire_Red"), M("M_Wire_Yellow"), M("M_Wire_Blue")]

for i, fx in enumerate(lay["fan_x"]):
    n = f"{i+1:02d}"; org = Vector((fx, FY, FZ))
    lay["slots"][f"slot_fan_{n}"] = [round(v, 5) for v in org]
    # fixed rack parts
    inst(f"fan_{n}_holder", holder_me, (fx, 0, 0), R, FR)
    moving(inst(f"fan_{n}_release_tab", tab_me, (fx + HX - 0.0015, Y0 + 0.006, ZT), R, FR), "press", "X",
           [0.0, -0.0015], tip="fan_release_tab")
    plug_w = Vector(lay["slots"][f"slot_fanplug_{n}"])
    moving(inst(f"fan_{n}_plug", plug_me, plug_w, R, FR), "slide", "Y", [0.0, 0.008], tip="fan_cable_plug",
           note="only needed for backplane removal; press the latch, pull straight out")
    cu = bpy.data.curves.new(f"fan_{n}_cable", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0006; cu.bevel_resolution = 0
    sx = fx + (PX0 + PX1) / 2
    for w in range(4):
        sp = cu.splines.new("POLY"); off = (w - 1.5) * 0.0013
        pts = [(sx + off, 0.1645, 0.0110), (sx + off, 0.1500, 0.0110), (plug_w.x + off, 0.1340, plug_w.z),
               (plug_w.x + off, plug_w.y + 0.003, plug_w.z)]
        sp.points.add(len(pts) - 1)
        for q, v in zip(sp.points, pts): q.co = (*v, 1)
        sp.material_index = w
    for m in WIRES: cu.materials.append(m)
    co = bpy.data.objects.new(f"fan_{n}_cable", cu); R.objects.link(co); place(co, (0, 0, 0), FR)
    # the fan (asset)
    a = asset(f"fan_{n}", org, F, pull=[[0, 0, 0.10]], requires=f"fan_{n}_release_tab", tip="fan",
              check="airflow arrow points to the rear; plug drops into the holder socket")
    inst(f"fan_{n}_body", fan_me, org, F, a)

save_layout(lay)
print("FAN_REPORT", {"fans": tris(F), "rack": tris(R)})
save()
