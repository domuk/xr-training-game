"""Lab 50 — room shell + power outlets, from the user's plan sketch and photos (assets/reference/lab).
Plan (north = +Y): room 8.4 W x 8.4 D (14 x 14 floor tiles of 600). South-east corner cut out: the east wall steps in
1.0 (0.25 past the east bench front) for the southern 3.2 m; the east bench runs up to the step wall, level with the front of the east desks (inset wall faces west: the blue cabinet's spare wall).
Rack row (later) runs N-S along the west wall; door on the south wall just east of it; L desks along the north wall
(TVs above, later) and down the east wall to the step; island table in the middle (51_tables).
Scale from the racks: 3 x 600 + one-rack gap + 800 cabinet = 3.2 m. Walls 3.6 m, open roof to 4.2 m.
Coordinates: metres, Z up, origin = centre of the room's bounding box (x -4.2..4.2, y -4.2..4.2)."""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("room"); wipe(C); root = lfixed("room", C)
W, L = 8.4, 8.4                    # bounding box (widened 1.2 to the west for the rack end)
XI, YS = 8.4 - 1.00, 3.20          # inset east wall 1.0 in (0.25 past the east bench front) / step at the end of the east bench
RH, CEIL, STRUT = 3.6, 4.2, 3.40
OX, OY = -W / 2, -L / 2
def P(x, y): return (OX + x, OY + y)             # plan coords (from the SW inside corner) -> world
G = M("M_Galv")

# ---------- floor (L-shape), tile texture per 600 mm ----------
rng = np.random.default_rng(3); n = 256
img = np.ones((n, n, 4)); img[:, :, :3] = [0.89, 0.885, 0.87]
spk = rng.random((n, n)); img[spk > 0.985, :3] = [0.70, 0.70, 0.70]; img[(spk > 0.97) & (spk <= 0.985), :3] = [0.80, 0.80, 0.79]
img[:, :, :3] *= (0.985 + 0.015 * rng.random((n, n, 1)))
img[:2, :, :3] = img[-2:, :, :3] = img[:, :2, :3] = img[:, -2:, :3] = [0.74, 0.74, 0.73]
tex_material("M_FloorTile", save_png("lab_floor_tile", img), rough=0.55)
f = Part("room_floor")
for (xa, xb, ya, yb) in ((0, XI, 0, L), (XI, W, YS, L)):
    (x0, y0), (x1, y1) = P(xa, ya), P(xb, yb); f.box(x0, x1, y0, y1, -0.02, 0.0, M("M_FloorTile"))
fo = f.build(C, root); uv_box(fo, 1 / TILE)
for l in fo.data.uv_layers[0].data: l.uv = (l.uv[0] - OX / TILE, l.uv[1] - OY / TILE)   # joints start at the SW corner

# ---------- walls: one object per wall, inner face on the room outline; seams every 1.2 m ----------
T = 0.10
WALLS = {   # name: (plan start, plan end, inward normal)
    "W":  ((0, 0), (0, L), (1, 0)),     "N": ((0, L), (W, L), (0, -1)),
    "E":  ((W, L), (W, YS), (-1, 0)),   "ES": ((W, YS), (XI, YS), (0, 1)),
    "EI": ((XI, YS), (XI, 0), (-1, 0)), "S": ((XI, 0), (0, 0), (0, 1)),
}
for k, (a, b, nrm) in WALLS.items():
    (ax, ay), (bx, by) = P(*a), P(*b); nx, ny = nrm
    xa, xb = sorted((ax, bx)); ya, yb = sorted((ay, by))
    if nx: xa, xb = (xa - T, xa) if nx > 0 else (xa, xa + T); ya, yb = ya - T, yb + T
    else:  ya, yb = (ya - T, ya) if ny > 0 else (ya, ya + T); xa, xb = xa - T, xb + T
    w = Part(f"room_wall_{k}")
    holes = [(OX + 4.0, OX + 5.8)] if k == "S" else []                    # door-sized hole behind the door (owner, 2026-10-04)
    cuts = [xa] + [v for h in holes for v in h] + [xb]
    for i in range(0, len(cuts), 2): w.box(cuts[i], cuts[i + 1], ya, yb, 0, RH, M("M_LabWall"))
    for (h0, h1) in holes: w.box(h0, h1, ya, yb, 2.40, RH, M("M_LabWall"))   # wall above the door (opening 2.40 high)
    w.box(xa, xb, ya, yb, RH, CEIL, M("M_LabCeil"))
    length = math.hypot(bx - ax, by - ay); d = Vector((bx - ax, by - ay, 0)).normalized()
    for s in np.arange(1.2, length - 0.1, 1.2):
        px, py = ax + d.x * s, ay + d.y * s
        if any(h0 < px < h1 for (h0, h1) in holes): continue                 # no seam across the door hole
        if nx: w.box(px + (0 if nx > 0 else -0.003), px + (0.003 if nx > 0 else 0), py - 0.003, py + 0.003, 0, RH, M("M_LabSeam"))
        else:  w.box(px - 0.003, px + 0.003, py + (0 if ny > 0 else -0.003), py + (0.003 if ny > 0 else 0), 0, RH, M("M_LabSeam"))
    w.build(C, root)
cl = Part("room_ceiling")
for (xa, xb, ya, yb) in ((0, XI, 0, L), (XI, W, YS, L)):
    (x0, y0), (x1, y1) = P(xa - 0.1, ya - 0.1), P(xb + 0.1, yb + 0.1); cl.box(x0, x1, y0, y1, CEIL, CEIL + 0.05, M("M_LabCeil"))
cl.build(C, root)

# ---------- white steel: column in the NE corner (+ knee brace, rafter along the north wall); the step is a plain wall corner ----------
st = Part("room_steel"); CW_ = M("M_ColumnWhite")
cx, cy = P(W, L); st.box(cx - 0.30, cx, cy - 0.30, cy, 0, CEIL, CW_)
x0, _ = P(0, L); st.box(x0, cx, cy - 0.25, cy, CEIL - 0.45, CEIL, CW_)                       # rafter along the north wall
for k in range(8):                                                                            # knee brace (stepped)
    t = k / 8; zb = RH - 0.25 + 0.5 * t
    st.box(cx - 0.42 - 0.9 * t, cx - 0.30 - 0.9 * t, cy - 0.22, cy - 0.03, zb, zb + 0.12, CW_)
st.build(C, root)

# ---------- ceiling: unistrut grid on rods, LED battens, strut channel along the wall tops ----------
s = Part("room_strut"); h = 0.0205
for yy in (1.4, 4.2, 7.0):
    (xa, y), (xb, _) = P(0.3, yy), P((W if yy > YS else XI) - 0.3, yy); s.box(xa, xb, y - h, y + h, STRUT - 0.041, STRUT, G)
for xx in (1.5, 4.3, 7.0):
    (x, ya), (_, yb) = P(xx, 0.3 if xx < XI else YS + 0.3), P(xx, L - 0.3); s.box(x - h, x + h, ya, yb, STRUT, STRUT + 0.041, G)
    for yy in (1.4, 4.2, 7.0):
        if xx > XI and yy < YS: continue
        rx, ry = P(xx, yy); s.cyl((rx, ry, 0), "Z", STRUT + 0.041, CEIL, 0.005, G, 6)
        s.box(rx - 0.03, rx + 0.03, ry - 0.03, ry + 0.03, STRUT - 0.05, STRUT + 0.05, G)
WT = 3.25
for k, (a, b, nrm) in WALLS.items():
    (ax, ay), (bx, by) = P(*a), P(*b); nx, ny = nrm
    if nx: s.box(ax + (0 if nx > 0 else -0.041), ax + (0.041 if nx > 0 else 0), min(ay, by), max(ay, by), WT, WT + 0.041, G)
    else:  s.box(min(ax, bx), max(ax, bx), ay + (0 if ny > 0 else -0.041), ay + (0.041 if ny > 0 else 0), WT, WT + 0.041, G)
s.build(C, root)
Lg = Part("room_lights")
for (xx, yy) in ((5.1, 4.2), (5.1, 7.0), (2.0, 2.6), (7.9, 6.2)):
    x, y = P(xx, yy)
    Lg.box(x - 0.04, x + 0.04, y - 0.75, y + 0.75, STRUT - 0.10, STRUT - 0.045, G)
    Lg.box(x - 0.035, x + 0.035, y - 0.74, y + 0.74, STRUT - 0.115, STRUT - 0.10, M("M_LEDDiffuser"))
setp(Lg.build(C, root), role="light", note="LED battens; diffuser faces down")

# ---------- conduit + sockets (as in the photos) ----------
cd = Part("room_conduit"); R, OFF = 0.010, 0.030; SZ = 1.15
sk = Part("room_sockets"); SG, SD = M("M_SocketGrey"), M("M_SocketDark")
def conduit(a, b):
    a, b = Vector(a), Vector(b); d = b - a; ax = max(range(3), key=lambda i: abs(d[i]))
    cd.cyl(tuple((a + b) / 2), "XYZ"[ax], min(a[ax], b[ax]), max(a[ax], b[ax]), R, G, 8)
def socket(x, y, z, nrm):
    """Grey metal-clad twin switched socket on a wall face at (x, y); nrm points into the room."""
    nx, ny = nrm
    if ny:
        y0, y1 = (y, y + 0.042) if ny > 0 else (y - 0.042, y); yf = y1 if ny > 0 else y0
        sk.box(x - 0.073, x + 0.073, y0, y1, z - 0.043, z + 0.043, SG)
        for dx in (-0.036, 0.036):
            sk.box(x + dx - 0.020, x + dx + 0.020, yf - 0.001, yf + 0.001, z - 0.025, z + 0.010, SD)
            sk.box(x + dx + 0.008, x + dx + 0.020, min(yf, yf + 0.004 * ny), max(yf, yf + 0.004 * ny), z + 0.018, z + 0.032, SD)
    else:
        x0, x1 = (x, x + 0.042) if nx > 0 else (x - 0.042, x); xf = x1 if nx > 0 else x0
        sk.box(x0, x1, y - 0.073, y + 0.073, z - 0.043, z + 0.043, SG)
        for dy in (-0.036, 0.036):
            sk.box(xf - 0.001, xf + 0.001, y + dy - 0.020, y + dy + 0.020, z - 0.025, z + 0.010, SD)
            sk.box(min(xf, xf + 0.004 * nx), max(xf, xf + 0.004 * nx), y + dy - 0.020, y + dy - 0.008, z + 0.018, z + 0.032, SD)
TOP = 3.00
yN = OY + L - OFF                                         # north wall: top run + 2 sockets, each on its own drop
conduit((OX + 0.3, yN, TOP), (OX + W - 0.35, yN, TOP))
for xx in (4.4, 6.2):
    x = OX + xx; conduit((x, yN, SZ + 0.04), (x, yN, TOP)); socket(x, OY + L, SZ, (0, -1))
xE = OX + W - OFF                                         # east wall: 3 near the corner (fed mid), 2 further south (fed at south end)
conduit((xE, OY + YS + 0.35, TOP), (xE, OY + L - 0.35, TOP))
g1 = [6.95, 6.45, 5.95]; conduit((xE, OY + g1[2], SZ), (xE, OY + g1[0], SZ)); conduit((xE, OY + g1[1], SZ + 0.04), (xE, OY + g1[1], TOP))
for yy in g1: socket(OX + W, OY + yy, SZ, (-1, 0))
g2 = [4.60, 4.00]; conduit((xE, OY + 3.60, SZ), (xE, OY + g2[0], SZ)); conduit((xE, OY + 3.60, SZ), (xE, OY + 3.60, TOP))
for yy in g2: socket(OX + W, OY + yy, SZ, (-1, 0))
yS = OY + OFF                                             # door wall: run above the door, drop to the card reader / release
conduit((OX + 0.3, yS, 2.65), (OX + XI - 0.35, yS, 2.65)); conduit((OX + 3.65, yS, 1.47), (OX + 3.65, yS, 2.65))   # drop to the card reader (door x0 - 0.35)
xW = OX + OFF; conduit((xW, OY + 0.35, TOP), (xW, OY + L - 0.35, TOP))   # west wall: top run
cd.build(C, root); sk.build(C, root)

# ---------- door: grey steel double door, two equal 0.9 leaves, 1.8 x 2.4, south wall x 4.0-5.8 (clear of the rack area), opens inwards ----------
DX0, DX1, DH = OX + 4.0, OX + 5.8, 2.40; DM = (DX0 + DX1) / 2; yf = OY; DT = 0.05; DF = M("M_DoorFrame")
fr = Part("door_frame")
fr.box(DX0 - 0.06, DX0, yf, yf + 0.03, 0, DH + 0.06, DF); fr.box(DX1, DX1 + 0.06, yf, yf + 0.03, 0, DH + 0.06, DF)
fr.box(DX0 - 0.06, DX1 + 0.06, yf, yf + 0.03, DH, DH + 0.06, DF)
# door closer (owner, 2026-10-04): body on the west leaf (moves with it), spindle on top, 2 level arms in a V to a shoe on
# the frame head (photos: assets/reference door closer). Set for the door shut.
CL_SP, CL_EL, CL_SHOE = (0.16, 0.028), (0.31, 0.20), (0.46, 0.035)           # spindle / elbow / shoe pin: x from the hinge, y from the leaf face / frame
fr.box(DX0 + CL_SHOE[0] - 0.045, DX0 + CL_SHOE[0] + 0.045, yf + 0.03, yf + 0.09, DH, DH + 0.04, M("M_SocketGrey"))   # shoe on the frame head
fr.cyl((DX0 + CL_SHOE[0], yf + 0.03 + CL_SHOE[1], 0), "Z", DH - 0.03, DH, 0.009, M("M_SocketGrey"), 12)
fr.build(C, root)
def closer_arm(p, a, b, z0, z1, w):
    """Level arm from plan point a to b (closer)."""
    d = Vector(b) - Vector(a); mtx = Matrix.Translation((a[0], a[1], 0)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
    p.box(-w / 2, d.length + w / 2, -w / 2, w / 2, z0, z1, M("M_SocketGrey"), mtx)
def leaf(name, x0, x1, hinge_x, kind):
    p = Part(name, (hinge_x, yf + 0.03, 0)); y0, y1 = yf + 0.03, yf + 0.03 + DT
    p.box(x0, x1, y0, y1, 0.005, DH - 0.005, M("M_DoorGrey"))
    p.box(x0 + 0.01, x1 - 0.01, y1, y1 + 0.002, 0.01, 0.30, DF)                                   # kick plate
    west = hinge_x <= x0 + 0.01; near = x1 if west else x0; sgn = -1 if west else 1               # meeting edge
    # positions from the meeting edge, as in the photo: pull bars at the same height either side of the gap,
    # blue fire-door signs just above them near the gap, lever (narrow leaf) below its bar pointing to the hinge
    hx = near + sgn * (0.18 if kind == "vision" else 0.10)
    p.cyl((hx, y1 + 0.055, 0), "Z", 1.00, 1.45, 0.013, M("M_SteelHandle"), 10)                     # pull bar
    for zz in (1.01, 1.44): p.box(hx - 0.01, hx + 0.01, y1, y1 + 0.055, zz - 0.01, zz + 0.01, M("M_SteelHandle"))
    sx_ = near + sgn * (0.12 if kind == "vision" else 0.10)                                       # blue fire-door sign
    for (r, y_, m_) in ((0.04, 0.002, "M_UIDBlue"), (0.03, 0.0025, "M_LabelWhite"), (0.026, 0.003, "M_UIDBlue")):
        p.cyl((sx_, 0, 1.60), "Y", y1, y1 + y_, r, M(m_), 16)
    if kind == "vision":                                                                          # upper vision panel + lower frosted panel
        vx0, vx1 = sorted((near + sgn * 0.25, near + sgn * 0.47))
        p.box(vx0 - 0.02, vx1 + 0.02, y1, y1 + 0.004, 1.08, 1.92, DF)                              # steel bead frame
        p.box(vx0, vx1, y1 + 0.004, y1 + 0.005, 1.36, 1.90, M("M_Glass"))                            # clear glass (upper)
        p.box(vx0, vx1, y1 + 0.004, y1 + 0.006, 1.10, 1.34, M("M_Chequer"))                          # chequer plate below it
        vx0, vx1 = sorted((near + sgn * 0.27, near + sgn * 0.47))
        p.box(vx0 - 0.02, vx1 + 0.02, y1, y1 + 0.004, 0.30, 0.78, DF)
        p.box(vx0, vx1, y1 + 0.004, y1 + 0.006, 0.62, 0.76, M("M_Chequer"))                          # chequer on top
        p.box(vx0, vx1, y1 + 0.004, y1 + 0.005, 0.32, 0.60, M("M_FrostGlass"))                       # frosted glass below
    else:                                                                                         # lever handle (latch ~50 mm from the edge)
        rx = near + sgn * 0.05; LZ = 0.90
        p.box(rx - 0.022, rx + 0.022, y1, y1 + 0.008, LZ - 0.04, LZ + 0.04, M("M_SteelHandle"))      # rose plate
        p.cyl((rx, 0, LZ), "Y", y1 + 0.008, y1 + 0.05, 0.009, M("M_SteelHandle"), 10)
        lx0, lx1 = sorted((rx, near + sgn * 0.18))                                                # lever points away from the gap (to the hinge)
        p.box(lx0, lx1, y1 + 0.04, y1 + 0.056, LZ - 0.01, LZ + 0.01, M("M_SteelHandle"))
    if west:                                                                                      # door closer on this leaf
        SG = M("M_SocketGrey"); sp = (hinge_x + CL_SP[0], y1 + CL_SP[1]); el = (hinge_x + CL_EL[0], y1 + CL_EL[1])
        shoe = (hinge_x + CL_SHOE[0], yf + 0.03 + CL_SHOE[1])
        p.box(hinge_x + 0.12, hinge_x + 0.52, y1, y1 + 0.055, DH - 0.16, DH - 0.09, SG)             # closer body
        p.cyl((sp[0], sp[1], 0), "Z", DH - 0.09, DH - 0.025, 0.009, SG, 12)                          # spindle on top
        closer_arm(p, sp, el, DH - 0.045, DH - 0.025, 0.030)                                        # main arm, out into the room
        p.cyl((el[0], el[1], 0), "Z", DH - 0.05, DH - 0.015, 0.011, SG, 12)                          # elbow
        closer_arm(p, el, shoe, DH - 0.025, DH - 0.010, 0.022)                                      # forearm back to the shoe
    o = p.build(C, root)
    moving(o, "hinge", "Z", [0, 90] if west else [-90, 0], tip="lab_door")                       # opens inwards (into the room)
    return o
leaf("door_leaf_W", DX0 + 0.003, DM - 0.002, DX0, "vision")
leaf("door_leaf_E", DM + 0.002, DX1 - 0.003, DX1, "signs")
eg = Part("door_release"); ex = DX0 - 0.35                                                         # card reader above, green release below
eg.box(ex - 0.045, ex + 0.045, yf, yf + 0.03, 1.32, 1.47, M("M_TVBlack"))
eg.box(ex - 0.025, ex + 0.025, yf + 0.03, yf + 0.032, 1.38, 1.44, M("M_SocketDark"))
eg.box(ex - 0.045, ex + 0.045, yf, yf + 0.03, 1.12, 1.21, M("M_CallGreen"))
eg.box(ex - 0.035, ex + 0.035, yf + 0.03, yf + 0.032, 1.13, 1.20, M("M_LabWall"))
eg.box(ex - 0.05, ex + 0.05, yf, yf + 0.002, 0.95, 1.05, M("M_CallGreen"))                         # sign below
eg.build(C, root)

# ---------- dome cameras: north wall near the column, ceiling strut over the rack area ----------
cam = Part("room_cctv")
for (x, y, z) in ((OX + W - 1.10, OY + L - 0.07, 3.05), (OX + 2.0, OY + 2.8, STRUT - 0.04)):
    cam.cyl((x, y, 0), "Z", z, z + 0.03, 0.06, M("M_LabWall"), 16); cam.cyl((x, y, 0), "Z", z - 0.05, z, 0.045, M("M_TVBlack"), 16)
cam.build(C, root)

lay = load_layout(); lay["lab_room"] = {"W": W, "L": L, "inset_x": XI, "step_y": YS, "origin": "bbox centre", "wall_h": RH}; save_layout(lay)
print("ROOM_REPORT", {"tris": tris(C)})
lab_save()
