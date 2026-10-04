"""Asset 9 (polish v2) — PSU cage (fixed) + 2 PSU module assets (release tab, handle, LED, inlet, grille)
+ 2 power cord assets. MODEL-SPEC §8.8, §12.3b (SC216 §5-10)."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
from mathutils import Matrix, Vector
S = server_coll(); PW = coll("power", S); wipe(PW)
for cu in [c for c in bpy.data.curves if c.name.startswith("cord_")]: bpy.data.curves.remove(cu)

X0, X1, Y0, Y1, Z0, Z1 = 0.115, 0.213, 0.170, 0.6375, 0.001, 0.082
fx = fixed("power", PW)
c = Part("psu_cage")
for b in ((X0, X0 + 0.001, Y0, Y1, Z0, Z1), (X1 - 0.001, X1, Y0, Y1, Z0, Z1), (X0, X1, Y0, Y1, Z1 - 0.001, Z1), (X0, X1, Y0, Y0 + 0.001, Z0, Z1)):
    c.box(*b, M("M_Zinc"))
c.box(X0 + 0.010, X1 - 0.010, 0.315, 0.600, Z1, Z1 + 0.0006, M("M_Zinc"))       # embossed panel (module bay)
c.box(X0, X1, 0.2905, 0.2915, Z1, Z1 + 0.0003, M("M_ChipBlack"))                         # seam: distributor section | module bay
c.box(X0 + 0.015, X0 + 0.050, Y0 - 0.0004, Y0, 0.008, 0.030, M("M_ChipBlack"))
for k in range(5):
    z = 0.040 + k * 0.007; c.box(X0 + 0.055, X1 - 0.012, Y0 - 0.0004, Y0, z, z + 0.004, M("M_ChipBlack"))
c.box(X0 - 0.0004, X0, 0.250, 0.285, 0.030, 0.055, M("M_ChipBlack"))          # ATX/8-pin exit (distributor section)
c.box(X0 + 0.003, X1 - 0.003, 0.176, 0.284, Z0 + 0.002, Z0 + 0.0036, M("M_PCBGreen"))       # PDB board (front section floor)
for (x, y) in ((0.130, 0.200), (0.142, 0.200), (0.154, 0.200), (0.130, 0.215), (0.142, 0.215)):
    c.cyl((x, y, 0), "Z", Z0 + 0.0036, Z0 + 0.0206, 0.0045, M("M_CapBody"), 12)           # bulk caps (seen through the vents)
c.box(0.168, 0.200, 0.190, 0.220, Z0 + 0.0036, Z0 + 0.0156, M("M_Choke"))                  # output inductor
c.box(0.175, 0.205, 0.240, 0.270, Z0 + 0.0036, Z0 + 0.0236, M("M_PlugWhite"))              # output connector block
c.build(PW, fx)

# ---------- power distributor board: card-edge socket per module (ref parts/psu-module) ----------
MODS = ((0.002, 0.040), (0.042, 0.080))
TX0, TX1, NX0, NX1 = 0.1500, 0.2050, 0.1750, 0.1770      # PSU tongue X span + polarising notch
TZ = 0.0040                                               # tongue bottom above module bottom (1.6 mm PCB)
dist = Part("psu_distributor")
dist.box(0.1170, 0.2110, 0.2880, 0.2896, 0.002, 0.080, M("M_PCBGreen"))                 # board across the cage
for (x, z) in ((0.125, 0.062), (0.135, 0.062), (0.125, 0.020), (0.135, 0.020)):           # bulk capacitors
    dist.cyl((x, 0, z), "Y", 0.2790, 0.2880, 0.0040, M("M_CapBody"), 12)
    dist.cyl((x, 0, z), "Y", 0.2785, 0.2790, 0.0036, M("M_EarAlu"), 12)
for (z0, z1) in MODS:                                                                    # 2 card-edge sockets
    sz0, sz1 = z0 + TZ - 0.0007, z0 + TZ + 0.0016 + 0.0007        # slot (tongue + 0.7 mm)
    hz0, hz1 = sz0 - 0.0025, sz1 + 0.0025
    sx0, sx1 = TX0 - 0.0005, TX1 + 0.0005
    hx0, hx1 = sx0 - 0.0020, sx1 + 0.0015
    yb, yf = 0.2896, 0.3020
    dist.box(hx0, hx1, yb, yf - 0.0080, hz0, hz1, M("M_SlotBlack"))                     # body behind the slot
    dist.box(hx0, hx1, yf - 0.0080, yf, hz0, sz0, M("M_SlotBlack"))                     # lower lip
    dist.box(hx0, hx1, yf - 0.0080, yf, sz1, hz1, M("M_SlotBlack"))                     # upper lip
    dist.box(hx0, sx0, yf - 0.0080, yf, sz0, sz1, M("M_SlotBlack"))                     # ends
    dist.box(sx1, hx1, yf - 0.0080, yf, sz0, sz1, M("M_SlotBlack"))
    dist.box(NX0 + 0.0002, NX1 - 0.0002, yf - 0.0080, yf, sz0, sz1, M("M_SlotBlack"))   # polarising key
    for k in range(19):                                                                  # contact springs, top + bottom
        x = TX0 + 0.0015 + k * 0.0028
        if NX0 - 0.0005 < x < NX1 + 0.0005: continue
        dist.box(x - 0.0006, x + 0.0006, yf - 0.0075, yf - 0.0005, sz0, sz0 + 0.00015, M("M_Gold"))
        dist.box(x - 0.0006, x + 0.0006, yf - 0.0075, yf - 0.0005, sz1 - 0.00015, sz1, M("M_Gold"))
setp(dist.build(PW, fx), role="fixed", tip="power_distributor")

RY = 0.640
mm = 0.001; MET, DARK, GOLD = M("M_EarAlu"), M("M_ChipBlack"), M("M_Gold")
YF, YB = RY + 0.0010, RY - 0.004                 # inlet housing stands 1 mm proud of the rear face
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_ports.py")).read())
# ---------- module outer face, matched to assets/reference/parts/psu-module/04 (Supermicro) ----------
# From the outer edge (+X) inward: release paddle | LED | portrait C14 inlet | 40 mm fan + wire guard + fold-out handle
IX, FXC = 0.1810, 0.1420                         # inlet centre, fan centre
TABX = 0.2085                                    # release paddle plane (outer edge)

def c14_pts(zc, dx_in=0.0, y0=YF - 0.009, y1=YF + 0.002):
    """IEC 60320 C14 recess, rotated portrait: chamfered side + earth toward the fan (-X)."""
    w, h, cx, cz, r = 0.01225 - dx_in, 0.00815 - dx_in, 0.0046, 0.0044, 0.0012
    o = [(-w, h - cz), (-w + cx, h), (w - cx, h), (w, h - cz), (w, -h + r), (w - r, -h), (-w + r, -h), (-w, -h + r)]
    return [(IX - z, y, zc + x) for (x, z) in o for y in (y0, y1)]          # (x, z) -> (-z, x): "up" points to -X

for n, (z0, z1) in enumerate(((0.002, 0.040), (0.042, 0.080)), 1):
    zc = (z0 + z1) / 2
    a = asset(f"psu_{n}", (0.164, RY, zc), PW, pull=[[0, 0.35, 0]], requires=f"asset_cord_{n},psu_{n}_tab",
              tip="psu", note="hot-swap; unplug the cord, squeeze the release paddle, pull by the handle")
    shp = Part(f"psu_{n}_shell"); shp.box(0.1165, 0.2115, 0.304, RY, z0, z1, M("M_Zinc"))     # 336 mm long case
    shell = shp.build(PW, a)
    p = Part(f"psu_{n}_body")                                                                  # details on the case
    # --- inner end (ref 01): louvered vent grille above, gold-finger PCB tongue below + guard flange ---
    p.box(0.1185, 0.2095, 0.3035, 0.3040, z0 + 0.0090, z1 - 0.0020, DARK)
    for k in range(23):
        x = 0.1200 + k * 0.0039
        p.box(x, x + 0.0012, 0.3010, 0.3040, z0 + 0.0090, z1 - 0.0020, M("M_Zinc"))
    for (xa, xb) in ((TX0, NX0), (NX1, TX1)):
        p.box(xa, xb, 0.2960, 0.3040, z0 + TZ, z0 + TZ + 0.0016, M("M_PCBGreen"))
    for k in range(19):
        x = TX0 + 0.0015 + k * 0.0028
        if NX0 - 0.0005 < x < NX1 + 0.0005: continue
        for (za, zb) in ((z0 + TZ - 0.00005, z0 + TZ), (z0 + TZ + 0.0016, z0 + TZ + 0.00165)):
            p.box(x - 0.0009, x + 0.0009, 0.2965, 0.3025, za, zb, GOLD)
    p.box(0.2085, 0.2095, 0.2940, 0.3040, z0 + 0.0010, z0 + 0.0120, M("M_Zinc"))
    # --- top: hot-surface label near the outer end ---
    p.tri(((0.193, 0.626, z1 + 0.00005), (0.205, 0.626, z1 + 0.00005), (0.199, 0.636, z1 + 0.00005)), M("M_IO_Yellow"))
    # --- 40 mm fan: square flange, 4 screws, dark well, 7 pitched blades, hub sticker, wire guard ---
    p.box(FXC - 0.0200, FXC + 0.0200, RY, RY + 0.0010, zc - 0.0185, zc + 0.0185, M("M_FanBlack"))      # flange
    p.cyl((FXC, 0, zc), "Y", RY + 0.0010, RY + 0.0011, 0.0175, DARK, 24)                              # well
    for k in range(7):
        ang = 2 * math.pi * k / 7
        p.box(0.0050, 0.0165, -0.0001, 0.0001, -0.0024, 0.0024, M("M_FanBlack"),
              Matrix.Translation((FXC, RY + 0.0013, zc)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Rotation(math.radians(22), 4, "X"))
    p.cyl((FXC, 0, zc), "Y", RY + 0.0011, RY + 0.0016, 0.0055, M("M_FanBlack"), 16)
    p.cyl((FXC, 0, zc), "Y", RY + 0.0016, RY + 0.0017, 0.0042, M("M_Gold"), 16)                      # hub sticker
    G0, G1, gm = RY + 0.0020, RY + 0.0028, M("M_EarAlu")
    for r_ in (0.0172, 0.0095):                                                                      # 2 wire rings
        for k in range(24):
            ang = 2 * math.pi * (k + 0.5) / 24; L = 2 * r_ * math.sin(math.pi / 24) + 0.0003
            p.box(-L / 2, L / 2, G0, G1, -0.0004, 0.0004, gm,
                  Matrix.Translation((FXC + r_ * math.cos(ang), 0, zc + r_ * math.sin(ang))) @ Matrix.Rotation(-ang + math.pi / 2, 4, "Y"))
    for k in range(3):                                                                               # 3 spokes (slightly swept)
        ang = math.radians(90 + k * 120)
        p.box(0.0095, 0.0172, G0, G1, -0.0004, 0.0004, gm,
              Matrix.Translation((FXC, 0, zc)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Rotation(math.radians(12), 4, "Y"))
    for (dx, dz) in ((-0.0165, -0.0150), (0.0165, -0.0150), (-0.0165, 0.0150), (0.0165, 0.0150)):  # wire-guard clips
        p.box(FXC + dx - 0.0012, FXC + dx + 0.0012, RY + 0.0010, G1, zc + dz - 0.0012, zc + dz + 0.0012, gm)
    p.build(PW, a)
    SCR = screw_mesh("screw_psu_case", 0.0011, 0.0005, "phillips", segs=10)
    for i_, (dx, dz) in enumerate(((-0.0165, -0.0150), (0.0165, -0.0150), (-0.0165, 0.0150), (0.0165, 0.0150)), 1):
        screw(f"psu_{n}_fan_screw_{i_}", SCR, (FXC + dx, G1, zc + dz), PW, a, axis="+Y")
    screw(f"psu_{n}_case_screw_1", SCR, (0.1985, RY, zc - 0.0140), PW, a, axis="+Y")
    # --- fold-out handle: chrome U in front of the fan, hinged at the top, swings out to pull ---
    hg = Part(f"psu_{n}_handle", (FXC, RY + 0.0040, zc + 0.0150))
    for s in (-1, 1):
        hg.box(FXC + s * 0.0195 - 0.0012, FXC + s * 0.0195 + 0.0012, RY + 0.0032, RY + 0.0048, zc - 0.0160, zc + 0.0150, M("M_EarAlu"))
        hg.cyl((FXC + s * 0.0195, 0, zc + 0.0150), "Y", RY, RY + 0.0050, 0.0018, M("M_EarAlu"), 10)   # pivot boss
    hg.box(FXC - 0.0207, FXC + 0.0207, RY + 0.0032, RY + 0.0048, zc - 0.0172, zc - 0.0148, M("M_EarAlu"))  # grip bar
    moving(hg.build(PW, a), "hinge", "X", [0.0, 90.0], tip="psu_handle", note="swing out, then pull")
    # --- portrait IEC C14 inlet: black housing, recess cut into housing + case, 3 blades ---
    inl = Part(f"psu_{n}_inlet", (IX, YF, zc))
    inl.box(IX - 0.0110, IX + 0.0110, RY - 0.004, YF, zc - 0.0155, zc + 0.0155, DARK)
    io = inl.build(PW, a)
    k = Part("cut"); hull(k, c14_pts(zc), DARK); boolean_cut(io, [k], PW)
    k = Part("cut"); hull(k, c14_pts(zc), DARK); boolean_cut(shell, [k], PW)
    ip = Part(f"psu_{n}_inlet_pins", (IX, YF, zc))
    hull(ip, c14_pts(zc, 0.0, YF - 0.0091, YF - 0.0089), M("M_CordBlack"))                         # recess floor
    for (x_, z_) in ((-0.0071, -0.0022), (0.0071, -0.0022), (0.0, 0.0020)):                        # L, N, earth
        px, pz = IX - z_, zc + x_                                                                   # rotated with the recess
        ip.box(px - 0.0022, px + 0.0022, YF - 0.0090, YF - 0.0030, pz - 0.0012, pz + 0.0012, M("M_Screw"))
    ip.build(PW, a)
    # --- LED + release paddle (outer edge) ---
    led = Part(f"psu_{n}_led", (0.1985, RY, zc + 0.0130)); led.cyl((0.1985, 0, zc + 0.0130), "Y", RY, RY + 0.0010, 0.0014, M("M_LEDGreen"), 10)
    setp(led.build(PW, a), role="indicator", tip="psu_led", states="green=on,amber=off")
    t = Part(f"psu_{n}_tab", (TABX, RY + 0.008, zc))
    t.box(TABX - 0.0010, TABX + 0.0010, RY, RY + 0.0160, zc - 0.0110, zc + 0.0110, M("M_TabMaroon"))  # paddle
    t.box(TABX + 0.0010, TABX + 0.0016, RY + 0.0100, RY + 0.0140, zc - 0.0040, zc + 0.0040, M("M_ChipBlack"))  # finger hole
    t.box(TABX - 0.0016, TABX - 0.0010, RY + 0.0100, RY + 0.0140, zc - 0.0040, zc + 0.0040, M("M_ChipBlack"))
    t.box(TABX - 0.0010, TABX + 0.0010, RY + 0.0160, RY + 0.0175, zc - 0.0110, zc + 0.0110, M("M_TabMaroon"))  # rolled end
    moving(t.build(PW, a), "press", "X", [0.0, -0.0020], tip="psu_release_tab", note="squeeze toward the inlet")
    # --- power cord (asset): portrait C13 plug seated in the inlet + cord on the table ---
    ca = asset(f"cord_{n}", (IX, RY + 0.001, zc), PW, pull=[[0, 0.03, 0]], tip="power_cord")
    pl = Part(f"cord_{n}_plug")
    hull(pl, c14_pts(zc, 0.0005, YF - 0.0026, YF + 0.0005), M("M_CordBlack"))                        # C13 nose
    pl.box(IX - 0.0105, IX + 0.0105, YF + 0.0005, YF + 0.0090, zc - 0.0145, zc + 0.0145, M("M_CordBlack"))   # body
    pl.box(IX - 0.0080, IX + 0.0080, YF + 0.0090, YF + 0.0230, zc - 0.0105, zc + 0.0105, M("M_CordBlack"))   # grip
    for k2 in range(4):
        y = YF + 0.0105 + k2 * 0.0032
        pl.box(IX - 0.0085, IX + 0.0085, y, y + 0.0012, zc - 0.0110, zc + 0.0110, M("M_CordBlack"))
    pl.build(PW, ca)
    cu = bpy.data.curves.new(f"cord_{n}_cable", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.0035; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); y0 = YF + 0.023
    pts = ([(IX, y0, zc), (IX, y0 + 0.020, zc), (IX, y0 + 0.045, 0.0035), (IX, y0 + 0.125, 0.0035)] if n == 1 else
           [(IX, y0, zc), (IX, y0 + 0.020, zc), (0.235, y0 + 0.035, zc), (0.235, y0 + 0.065, 0.0035), (0.235, y0 + 0.125, 0.0035)])
    sp.points.add(len(pts) - 1)
    for q, v in zip(sp.points, pts): q.co = (*v, 1)
    cu.materials.append(M("M_CordBlack"))
    co = bpy.data.objects.new(f"cord_{n}_cable", cu); PW.objects.link(co); place(co, (0, 0, 0), ca)
print("PSU_REPORT", {"tris": tris(PW)})
save()
