"""Lab 52 — rack row (reference: assets/reference/lab/02-door-racks), 42U, fronts facing +Y (towards the table).
Row runs along the door wall (-Y) with a 1.0 m rear aisle; rack 1 touches the east wall (as in the lab).
  rack_1  big black cabinet 800 W, perforated front door + split rear doors, solid sides, yellow label, red lamp
  rack_2  black cabinet 600 W, doors removed (as in the photo)
  rack_3, rack_4  open-frame 4-post racks 600 W, grey
All 1200 D x 2000 H, U1 bottom at z 0.10, 19" rails (holes 465 mm apart) with front rail 0.10 behind the front.
Rear: 2 vertical 0U PDUs. Top: 3 mated blue 32 A commando pairs (rack male plug + whip female), whips up to the tray at 2.75 m.
Contents (servers, switches, blanking) are added by 53_rack_fill.py using the RACKS table saved to layout."""
import bpy, math, json, numpy as np
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
exec(open(os.path.join(HERE, "_commando.py")).read())
C = lab_coll("racks"); wipe(C); root = lfixed("racks", C)
# Built in a local ROW frame (root at the origin, unrotated): local X runs along the row from the north end (0) to the
# south end (3.2, 0.15 off the south wall); local Y = 0 is the rear plane, +Y the fronts. At the end the root is moved and
# turned -90 deg about Z onto the west wall, so local +Y (fronts) faces world +X (east, towards the table).
R_ = load_layout()["lab_room"]; RW_, RL_ = R_["W"], R_["L"]
REAR_AISLE, ROW_LEN = 1.00, 3.20
SOUTH_GAP = 0.60                              # gap to the south wall (one tile)
ROW_ORIGIN = (-RW_ / 2 + REAR_AISLE, -RL_ / 2 + SOUTH_GAP + ROW_LEN, 0.0)       # world point of local (0, 0): north end, rear plane
RDp, RHt, U, UZ0 = 1.20, 2.00, 0.04445, 0.10
YR = 0.0; YF = YR + RDp                       # rear / front plane (local)
FRAIL = YF - 0.10; RRAIL = FRAIL - 0.75       # rail planes
X1 = ROW_LEN
RACKS = [("rack_1", 0.00, 0.80, "cabinet_doors"),                                            # big door cabinet (empty)
         ("rack_2", 1.40, 2.00, "open_frame"), ("rack_3", 2.00, 2.60, "open_frame"),          # 0.80-1.40 = one-rack gap;
         ("rack_4", 2.60, 3.20, "open_frame")]                                                # 3 identical silver open frames
# Kept for later: "cabinet_open" (black cabinet, doors off) from the photo.
_MAT_DEFS.update({"M_RackGrey": ("#9DA1A4", 0.45, 0.8), "M_RackPanel": ("#B7BABC", 0.4, 0.7), "M_LabelYellow": ("#F2C200", 0.6, 0)})

# ---------- textures: perforated door (hex holes), rail square holes ----------
n = 64; yy, xx = np.mgrid[0:n, 0:n] / n
img = np.ones((n, n, 4)); img[:, :, :3] = 0.06
for (cx, cy) in ((0.25, 0.25), (0.75, 0.25), (0.0, 0.75), (0.5, 0.75), (1.0, 0.75), (0.25, 1.25), (0.75, 1.25), (0.25, -0.25), (0.75, -0.25)):
    img[((xx - cx) ** 2 + (yy - cy) ** 2) < 0.028, 3] = 0
tex_material("M_RackPerf", save_png("lab_rack_perf", img), rough=0.5, metal=0.3, alpha_clip=True)
h = 48; w = 16; r = np.ones((h, w, 4)); r[:, :, :3] = 0.10
for k in range(3):
    c = int((k + 0.5) * h / 3); r[c - 4:c + 4, 4:12, 3] = 0
r[-2:, :, :3] = 0.85                                                             # printed U-boundary line (1 tile = 1U)
tex_material("M_RailBlack", save_png("lab_rail_black", r), rough=0.5, metal=0.5, alpha_clip=True)
rg = r.copy(); rg[:-2, :, :3] = 0.55; rg[-2:, :, :3] = 0.15
tex_material("M_RailGrey", save_png("lab_rail_grey", rg), rough=0.45, metal=0.8, alpha_clip=True)
PERF_TILE = 0.025

def perf_panel(p, x0, x1, y, z0, z1, m=None):
    """Two-sided perforated panel in the XZ plane at y."""
    m = m or M("M_RackPerf"); u1, v1 = (x1 - x0) / PERF_TILE, (z1 - z0) / PERF_TILE
    tquad(p, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(0, 0), (u1, 0), (u1, v1), (0, v1)], m)
    tquad(p, [(x1, y - 0.0005, z0), (x0, y - 0.0005, z0), (x0, y - 0.0005, z1), (x1, y - 0.0005, z1)], [(u1, 0), (0, 0), (0, v1), (u1, v1)], m)

def rail(p, x, y, m, face=+1):
    """Vertical 19-inch rail: textured 16 mm flange in the XZ plane (holes per U) + solid return to the side."""
    z0, z1 = UZ0, UZ0 + 42 * U; w2 = 0.008
    for s in (0, -0.0006 * face):
        pts = [(x - w2, y + s, z0), (x + w2, y + s, z0), (x + w2, y + s, z1), (x - w2, y + s, z1)]
        if s: pts = [pts[1], pts[0], pts[3], pts[2]]
        tquad(p, pts, [(0, 0), (1, 0), (1, 42), (0, 42)] if not s else [(1, 0), (0, 0), (0, 42), (1, 42)], m)
    side = 1 if x > 0 else -1
    return side

layout = {}
for name, xa, xb, kind in RACKS:
    cx = (xa + xb) / 2; W = xb - xa
    grp = lnode(f"fixed_{name}", (cx, YR, 0), C, root, role="fixed", tip="rack", kind=kind, units=42)
    dark = kind != "open_frame"; FM = M("M_RackBlack") if dark else M("M_RackGrey")
    f = Part(f"{name}_frame", (cx, YR, 0)); t = 0.045
    for (px, py) in ((xa, YR), (xb - t, YR), (xa, YF - t), (xb - t, YF - t)):                       # corner posts
        f.box(px, px + t, py, py + t, 0.03, RHt, FM)
    for (za, zb) in ((0.03, 0.10), (RHt - 0.04, RHt)):                                                # bottom + top frames
        f.box(xa, xb, YR, YR + t, za, zb, FM); f.box(xa, xb, YF - t, YF, za, zb, FM)
        f.box(xa, xa + t, YR, YF, za, zb, FM); f.box(xb - t, xb, YR, YF, za, zb, FM)
    for (px, py) in ((xa + 0.05, YR + 0.05), (xb - 0.05, YR + 0.05), (xa + 0.05, YF - 0.05), (xb - 0.05, YF - 0.05)):
        f.cyl((px, py, 0), "Z", 0.0, 0.03, 0.02, M("M_Rubber"), 8)                                       # levelling feet
    for yy_ in (FRAIL, RRAIL):                                                                         # rail mounting bars
        f.box(xa + t, xb - t, yy_ - 0.01, yy_ + 0.01, 0.06, 0.10, FM); f.box(xa + t, xb - t, yy_ - 0.01, yy_ + 0.01, RHt - 0.08, RHt - 0.04, FM)
    if dark:
        f.box(xa + t, xb - t, YR + t, YF - t, RHt - 0.012, RHt, FM)                                     # roof
        f.box(cx - 0.12, cx + 0.12, YR + 0.25, YR + 0.45, RHt, RHt + 0.004, M("M_Rubber"))             # brush cable entry
        f.box(xa - 0.002, xa, YR + 0.02, YF - 0.02, 0.10, RHt - 0.04, FM)                                # side panels
        f.box(xb, xb + 0.002, YR + 0.02, YF - 0.02, 0.10, RHt - 0.04, FM)
    else:
        for side_x in (xa, xb - t):                                                                    # open frame side rails
            for zz in (0.55, 1.05, 1.55): f.box(side_x, side_x + t, YR, YF, zz, zz + 0.03, FM)
        SP = M("M_RackPanel")                                                                          # silver side panels
        f.box(xa - 0.002, xa, YR + 0.02, YF - 0.02, 0.10, RHt - 0.04, SP); f.box(xb, xb + 0.002, YR + 0.02, YF - 0.02, 0.10, RHt - 0.04, SP)
    rm = M("M_RailBlack") if dark else M("M_RailGrey")
    for ry in (FRAIL, RRAIL):                                                                          # 4 rails + depth brackets
        for sx in (-1, 1):
            rx = cx + sx * 0.2325; rail(f, rx, ry, rm, +1 if ry == FRAIL else -1)
            f.box(rx + sx * 0.008, rx + sx * 0.030, ry - 0.015, ry + 0.015, UZ0, UZ0 + 42 * U, FM)
    for sx in (-1, 1):                                                                                 # side cross members to rails
        x_in = cx + sx * 0.2625; x_out = xa + t if sx < 0 else xb - t
        for zz in (0.12, RHt - 0.10):
            f.box(min(x_in, x_out), max(x_in, x_out), FRAIL - 0.01, FRAIL + 0.01, zz, zz + 0.02, FM)
            f.box(min(x_in, x_out), max(x_in, x_out), RRAIL - 0.01, RRAIL + 0.01, zz, zz + 0.02, FM)
    # rear 0U PDUs (black body, outlets)
    for sx in (-1, 1):
        px = cx + sx * (0.2625 + 0.035) if W < 0.7 else cx + sx * 0.32
        py = YR + 0.10
        f.box(px - 0.028, px + 0.028, py - 0.025, py + 0.025, 0.25, 1.85, M("M_CableBlack"))
        for k in range(20):
            z = 0.32 + k * 0.075
            f.box(px - 0.012, px + 0.012, py - 0.027, py - 0.025, z, z + 0.016, M("M_SocketGrey"))
        f.box(px - 0.02, px + 0.02, py - 0.027, py - 0.025, 1.78, 1.82, M("M_TVBlack"))                 # PDU display
    # top: 3 whips per rack (owner, 2026-10-04): the rack PDU's male 32 A commando plug standing on the rack top, the
    # whip's female connector plugged onto it, the whip cable up to the tray at 2.75 (_commando.py, simplified model)
    for k in (-1, 0, 1):
        mated_pair_lod(f, cx + k * W * 0.25, YR + 0.38, RHt, 2.75)
    if kind == "cabinet_doors":                                                                     # label + lamp on every door cabinet
        f.box(cx - 0.12, cx - 0.02, YF + 0.003, YF + 0.004, RHt - 0.09, RHt - 0.06, M("M_LabelYellow"))
        f.cyl((cx - 0.18, 0, RHt - 0.075), "Y", YF, YF + 0.01, 0.009, M("M_LEDRed"), 12)
    f.build(C, grp)
    # doors on rack_1: perforated front (hinge left), split rear (hinges at both sides)
    if kind == "cabinet_doors":
        def door(nm, x0, x1, y, hinge_x, out):
            d = Part(nm, (hinge_x, y, 0)); bw = 0.035
            d.box(x0, x1, y, y + 0.02 * out, 0.10, 0.10 + bw, FM); d.box(x0, x1, y, y + 0.02 * out, RHt - 0.04 - bw, RHt - 0.04, FM)
            d.box(x0, x0 + bw, y, y + 0.02 * out, 0.10, RHt - 0.04, FM); d.box(x1 - bw, x1, y, y + 0.02 * out, 0.10, RHt - 0.04, FM)
            perf_panel(d, x0 + bw, x1 - bw, y + 0.01 * out, 0.10 + bw, RHt - 0.04 - bw)
            hx = x1 - 0.06 if hinge_x < (x0 + x1) / 2 else x0 + 0.06
            d.box(hx - 0.012, hx + 0.012, y + 0.02 * out, y + 0.045 * out if out > 0 else y + 0.02 * out, 0.95, 1.20, M("M_TVBlack")) if out > 0 else \
                d.box(hx - 0.012, hx + 0.012, y + 0.02 * out - 0.025, y + 0.02 * out, 0.95, 1.20, M("M_TVBlack"))
            o = d.build(C, grp)
            lim = [0, 110] if (hinge_x < (x0 + x1) / 2) == (out > 0) else [-110, 0]
            moving(o, "hinge", "Z", lim, tip="rack_door")
        door(f"{name}_door_front", xa + 0.005, xb - 0.005, YF, xa + 0.005, +1)
        door(f"{name}_door_rear_L", xa + 0.005, cx - 0.002, YR, xa + 0.005, -1)
        door(f"{name}_door_rear_R", cx + 0.002, xb - 0.005, YR, xb - 0.005, -1)
    layout[name] = {"x": [xa, xb], "cx": cx, "kind": kind, "front_rail_y": FRAIL, "rear_rail_y": RRAIL,
                    "rear_y": YR, "front_y": YF, "u1_z": UZ0, "u": U}

# ---------- cable tray over the row ----------
tr = Part("rack_tray"); G = M("M_Galv"); ty = YR + 0.38; tz = 2.75
tr.box(0.05, X1 - 0.05, ty - 0.15, ty + 0.15, tz, tz + 0.004, G)
for s in (-1, 1): tr.box(0.05, X1 - 0.05, ty + s * 0.15 - 0.002, ty + s * 0.15 + 0.002, tz, tz + 0.06, G)
for x in (0.3, 1.6, 2.9):
    for s in (-1, 1): tr.cyl((x, ty + s * 0.17, 0), "Z", tz - 0.04, STRUT_Z, 0.005, G, 6)
    tr.box(x - 0.02, x + 0.02, ty - 0.19, ty + 0.19, tz - 0.041, tz, G)
tr.build(C, root)

root.location = ROW_ORIGIN; root.rotation_euler = (0, 0, -math.pi / 2)     # onto the west wall, fronts east
layout["_row"] = {"origin": list(ROW_ORIGIN), "rot_z_deg": -90, "note": "rack coords are in the row frame (fixed_racks)"}
lay = load_layout(); lay["lab_racks"] = layout; save_layout(lay)
print("RACK_REPORT", {"tris": tris(C)})
lab_save()
