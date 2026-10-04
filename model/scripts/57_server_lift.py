"""Lab 57 (v3) — server lift (DataLift F Pro type). Reference: assets/reference/parts/server-lift (user's photos 01, 02,
03-06 + maker's brochure; the IXOLIFT-branded photo was wrong and is not used). Brochure specs: platform 0.42 x 0.61,
platform height 0.135 -> 2.40, brake bar 0.36 wide, reaches 300 mm into a rack.
Shape: one tall black column with solid sides (deep rear housing, rear face tilting in above the control panel),
slatted window in the rear face, yellow/black safety top; base block with corner feet over the rear castors, long low
flat front legs with hazard tape, sloped side plates; red U brake bar at the rear; rear control shelf with key, e-stop,
wheel-lock lever and buttons; curved push handle; grey table on a black arm with striped front and tube noses;
remote in a holster with a coiled cable. Local frame: origin = floor under the mast front centre; platform -Y, handle +Y.
Parked in the lab north-west, side to the west wall, platform towards the racks; charging from a west-wall socket."""
import bpy, bmesh, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("server_lift"); wipe(C)
for m_ in [m for m in bpy.data.meshes if m.users == 0]: bpy.data.meshes.remove(m_)
R = load_layout()["lab_room"]; W, L = R["W"], R["L"]; OX, OY = -W / 2, -L / 2
_MAT_DEFS.update({"M_LiftBlack": ("#151617", 0.55, 0.25), "M_LiftYellow": ("#F2B705", 0.5, 0), "M_BrakeRed": ("#C8201E", 0.4, 0.1),
                  "M_PUOrange": ("#A9572A", 0.65, 0), "M_EStopYellow": ("#F5C400", 0.5, 0), "M_EStopRed": ("#D41A1A", 0.35, 0),
                  "M_RemoteGrey": ("#C9CBCC", 0.5, 0), "M_TableSteel": ("#8E9396", 0.4, 0.8), "M_LiftBlue": ("#2A55C8", 0.5, 0)})
K, YL, RD, GV = M("M_LiftBlack"), M("M_LiftYellow"), M("M_BrakeRed"), M("M_Galv")

# ---------- textures ----------
n = 128; yy, xx = np.mgrid[0:n, 0:n] / n
hz = np.ones((n, n, 4)); stripe = ((xx + yy) % 1.0) < 0.5
hz[stripe, :3] = [0.95, 0.72, 0.02]; hz[~stripe, :3] = [0.04, 0.04, 0.04]
tex_material("M_Hazard", save_png("lift_hazard", hz), rough=0.5)          # one stripe pair per UV unit
cg = np.ones((64, 16, 4)); cg[:, :, :3] = 0.07
for k in range(4): cg[k * 16 + 5:k * 16 + 16, :, 3] = 0                  # 4 slats per tile (5 px bar, 11 px gap)
tex_material("M_LiftCage", save_png("lift_cage", cg), rough=0.5, metal=0.3, alpha_clip=True)
STRIPE = 0.06                                                            # hazard stripe pitch (m per UV unit)

POS = Vector((OX + 0.55, OY + 5.30, 0.0))                                # parked: north of the rack row, side to the west wall
root = lnode("asset_server_lift", tuple(POS), C, None, role="asset", tip="server_lift", pull=[[0, 0, 0]],
             note="IXOLIFT DataLift F Pro: push on castors; platform 0.135-2.40 m; front-loading 300 mm into a rack",
             capacity_kg=200, platform=[0.42, 0.61])
def V(x, y, z=0.0): return POS + Vector((x, y, z))

# ---------- helpers (local coordinates) ----------
def lbox(p, x0, x1, y0, y1, z0, z1, m): p.box(POS.x + x0, POS.x + x1, POS.y + y0, POS.y + y1, z0, z1, m)
def lcyl(p, x, y, z, axis, a0, a1, r, m, segs=12):
    c = V(x, y, z); off = {"X": POS.x, "Y": POS.y, "Z": 0.0}[axis]
    p.cyl(tuple(c), axis, off + a0, off + a1, r, m, segs)
def prism(p, prof, x0, x1, m):
    """Side-profile polygon [(y, z), ...] extruded across x0..x1."""
    bm = p.bm; mi = p._mi(m)
    A = [bm.verts.new(V(x0, y, z) - p.o) for y, z in prof]; B = [bm.verts.new(V(x1, y, z) - p.o) for y, z in prof]
    fs = [bm.faces.new(A[::-1]), bm.faces.new(B)]
    for i in range(len(prof)):
        j = (i + 1) % len(prof); fs.append(bm.faces.new((A[i], A[j], B[j], B[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def plan_prism(p, poly, z0, z1, m):
    """Plan polygon [(x, y), ...] extruded z0..z1."""
    bm = p.bm; mi = p._mi(m)
    A = [bm.verts.new(V(x, y, z0) - p.o) for x, y in poly]; B = [bm.verts.new(V(x, y, z1) - p.o) for x, y in poly]
    fs = [bm.faces.new(A[::-1]), bm.faces.new(B)]
    for i in range(len(poly)):
        j = (i + 1) % len(poly); fs.append(bm.faces.new((A[i], A[j], B[j], B[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def hazard_quad(p, a, b, c, d, length):
    """Striped quad a-b-c-d (world points); stripes repeat along a->b over `length` metres."""
    u = length / STRIPE; h = (Vector(d) - Vector(a)).length / STRIPE
    tquad(p, [a, b, c, d], [(0, 0), (u, 0), (u, h), (0, h)], M("M_Hazard"))
def bevel(o, w=0.004, segs=2, ang=40):
    md = o.modifiers.new("bevel", "BEVEL"); md.width = w; md.segments = segs; md.limit_method = "ANGLE"
    md.angle_limit = math.radians(ang)
    for f in o.data.polygons: f.use_smooth = True
    try: o.data.set_sharp_from_angle(angle=math.radians(35))
    except Exception: pass
    return o
def fillet(pts, r, k=4):
    """Polyline with rounded corners (radius r, k segments per corner)."""
    P = [Vector(q) for q in pts]; out = [P[0]]
    if r <= 0: return P
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]; u = (a - b).normalized(); v = (c - b).normalized()
        ang = u.angle(v)
        if ang > math.radians(175): out.append(b); continue
        t = min(r / math.tan(ang / 2), (a - b).length * 0.45, (c - b).length * 0.45)
        p0, p1 = b + u * t, b + v * t
        for s in range(k + 1):
            f = s / k; out.append((1 - f) ** 2 * p0 + 2 * (1 - f) * f * b + f * f * p1)
    out.append(P[-1]); return out
def pipe(name, pts_local, r, m, parent, segs=10, rr=0.05):
    """Smooth tube along a local polyline (rounded corners) -> mesh object, origin at the first point."""
    pts = fillet([V(*q) for q in pts_local], rr)
    cu = bpy.data.curves.new(name + "_cu", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r
    cu.bevel_resolution = max(0, segs // 4 - 1); cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, q in enumerate(pts): sp.points[i].co = (*(q - pts[0]), 1)
    tmp = bpy.data.objects.new(name + "_tmp", cu); bpy.context.scene.collection.objects.link(tmp)
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    old = bpy.data.meshes.get(name)
    if old: bpy.data.meshes.remove(old)
    me.name = name; me.materials.clear(); me.materials.append(m)
    for f in me.polygons: f.use_smooth = True
    o = bpy.data.objects.new(name, me); C.objects.link(o); place(o, tuple(pts[0]), parent); return o
def castor(p, x, y, swivel=True):
    r, w = 0.05, 0.032; c = V(x, y, r)
    p.cyl(tuple(c), "X", c.x - w / 2, c.x + w / 2, r, M("M_PUOrange"), 14)                                    # PU tyre
    p.cyl(tuple(c), "X", c.x - w / 2 - 0.003, c.x + w / 2 + 0.003, r * 0.62, M("M_RackBlack"), 10)          # black centre
    p.cyl(tuple(c), "X", c.x - w / 2 - 0.012, c.x + w / 2 + 0.012, 0.007, GV, 8)                             # axle
    for s in (-1, 1):                                                                                         # fork legs
        p.box(c.x + s * (w / 2 + 0.004) - 0.003, c.x + s * (w / 2 + 0.004) + 0.003, c.y - 0.006, c.y + 0.03,
              r - 0.008, 2 * r + 0.018, GV)
    p.box(c.x - w / 2 - 0.008, c.x + w / 2 + 0.008, c.y - 0.03, c.y + 0.04, 2 * r + 0.018, 2 * r + 0.026, GV)    # top plate
    if swivel: p.cyl((c.x, c.y + 0.012, 0), "Z", 2 * r + 0.026, 2 * r + 0.04, 0.02, GV, 12)                    # swivel bearing

# ---------- base frame (refs 03-base-closeup, 05-side, 06-rear) ----------
# Rear: wide base block under the body with blocky corner feet over the rear castors, red brake bar between them.
# Front: two long low flat legs (hazard tape on top near the tips), joined to the base by a sloped side plate, castors
# under the leg tips. Legs sit outside the platform (inner gap 0.50 > 0.42 table).
b = Part("lift_base", tuple(POS))
plan_prism(b, [(-0.24, -0.06), (0.24, -0.06), (0.24, 0.44), (-0.24, 0.44)], 0.11, 0.21, K)            # base block under the body
for s in (-1, 1):
    x0, x1 = sorted((s * 0.25, s * 0.33))
    prism(b, [(0.24, 0.11), (0.50, 0.11), (0.50, 0.215), (0.24, 0.215)], x0, x1, K)                     # rear corner foot
    prism(b, [(-0.74, 0.115), (0.24, 0.115), (0.24, 0.215), (0.02, 0.215), (-0.20, 0.165), (-0.74, 0.165)], x0, x1, K)   # sloped side plate -> flat leg
    hazard_quad(b, V(x0, -0.70, 0.1655), V(x0, -0.24, 0.1655), V(x1, -0.24, 0.1655), V(x1, -0.70, 0.1655), 0.46)
    castor(b, s * 0.29, -0.70); castor(b, s * 0.29, 0.44)
lbox(b, -0.25, 0.25, 0.44, 0.50, 0.11, 0.215, K)                                                         # rear cross member
b.build(C, root)
br = pipe("lift_brake_bar", [(-0.18, 0.50, 0.075), (-0.18, 0.60, 0.075), (0.18, 0.60, 0.075), (0.18, 0.50, 0.075)], 0.011, RD, root, 10, 0.04)
moving(br, "hinge", "X", [0, -12], tip="lift_brake", note="press with the foot to brake the rear wheels; 0.36 m wide")

# ---------- body: one tall black column with solid sides (ref 05-side) ----------
# Side profile: vertical front (mast) face; rear housing deep at the bottom, rear face tilts in above the control panel.
hs = Part("lift_body", tuple(POS))
prism(hs, [(0.00, 0.21), (0.42, 0.21), (0.42, 0.84), (0.40, 0.86), (0.36, 0.86), (0.352, 0.94), (0.00, 0.94)], -0.21, 0.21, K)   # lower housing
for sx in (-1, 1):                                                                                      # upper mast: two solid side posts (see-through between)
    a0, a1 = sorted((sx * 0.21, sx * 0.165))
    prism(hs, [(0.00, 0.94), (0.352, 0.94), (0.26, 1.86), (0.00, 1.86)], a0, a1, K)
prism(hs, [(0.00, 1.78), (0.268, 1.78), (0.26, 1.86), (0.00, 1.86)], -0.165, 0.165, K)                   # top beam
for gx in (-0.09, 0.0, 0.09):                                                                           # 3 recessed grip slots (rear)
    lbox(hs, gx - 0.035, gx + 0.035, 0.4205, 0.425, 0.50, 0.58, M("M_RackBlack"))
lbox(hs, -0.08, 0.08, 0.4205, 0.4225, 0.26, 0.32, M("M_LabelWhite"))                                    # rating label (rear, low)
lbox(hs, -0.075, 0.075, 0.4225, 0.4235, 0.27, 0.285, M("M_EStopRed"))
lcyl(hs, 0.0, 0.0, 0.66, "Y", 0.4205, 0.423, 0.032, M("M_LiftBlue"), 16)                                 # blue round sticker (rear)
lcyl(hs, 0.0, 0.30, 0.66, "X", 0.2105, 0.212, 0.03, M("M_LiftBlue"), 16)                                 # blue sticker (side)
for s in (-1, 1):                                                                                       # side pegs
    a0, a1 = sorted((s * 0.21, s * 0.30)); lcyl(hs, 0.0, 0.36, 0.47, "X", a0, a1, 0.012, K, 10)
for k in range(4):                                                                                      # side label strips (lower side)
    lbox(hs, 0.2105, 0.212, 0.06, 0.10, 0.30 + k * 0.03, 0.315 + k * 0.03, M("M_LabelWhite"))
bevel(hs.build(C, root), 0.008, 2)
def rear_y(z): return 0.36 + (z - 0.86) * (0.26 - 0.36) / (1.86 - 0.86)
cg_ = Part("lift_cage", tuple(POS))                                                                     # slatted window in the sloped rear face
z0, z1 = 0.96, 1.78
tquad(cg_, [V(0.165, rear_y(z0) + 0.002, z0), V(-0.165, rear_y(z0) + 0.002, z0),
            V(-0.165, rear_y(z1) + 0.002, z1), V(0.165, rear_y(z1) + 0.002, z1)], [(0, 0), (1, 0), (1, 20), (0, 20)], M("M_LiftCage"))
cg_.build(C, root)
inn = Part("lift_mast_inner", tuple(POS))                                                               # behind the slats

lbox(inn, -0.008, 0.008, 0.10, 0.13, 0.94, 1.70, GV)                                                    # lift belt
lbox(inn, -0.08, 0.08, 0.06, 0.18, 1.62, 1.76, YL)                                                      # yellow winch block
lcyl(inn, 0.0, 0.115, 1.60, "X", -0.05, 0.05, 0.035, GV, 14)                                           # pulley
inn.build(C, root)
fr = Part("lift_mast_front", tuple(POS))                                                                # front face: carriage slot + yellow guide
lbox(fr, -0.03, 0.03, -0.004, 0.0, 0.24, 0.94, M("M_RackBlack"))
for gx in (-0.11, 0.11): lbox(fr, gx - 0.02, gx + 0.02, -0.014, 0.0, 0.215, 1.80, YL)                   # yellow guide rails (carriage runs on these)

lbox(fr, -0.12, 0.02, -0.002, 0.0, 0.70, 0.76, M("M_LabelWhite")); lbox(fr, -0.11, 0.01, -0.003, -0.002, 0.715, 0.735, M("M_EStopRed"))
fr.build(C, root)

# ---------- insulated safety top ----------
tp = Part("lift_safety_top", tuple(POS))
z0, z1 = 1.86, 1.90; x0, x1, y0, y1 = -0.215, 0.215, -0.005, 0.265
hazard_quad(tp, V(x0, y0, z0), V(x1, y0, z0), V(x1, y0, z1), V(x0, y0, z1), 0.43)
hazard_quad(tp, V(x1, y1, z0), V(x0, y1, z0), V(x0, y1, z1), V(x1, y1, z1), 0.43)
hazard_quad(tp, V(x1, y0, z0), V(x1, y1, z0), V(x1, y1, z1), V(x1, y0, z1), 0.27)
hazard_quad(tp, V(x0, y1, z0), V(x0, y0, z0), V(x0, y0, z1), V(x0, y1, z1), 0.27)
lbox(tp, x0, x1, y0, y1, z1, z1 + 0.005, K)
lbox(tp, -0.06, 0.06, 0.02, 0.12, 1.905, 1.95, M("M_TableSteel"))                                        # pulley housing
tp.build(C, root)

# ---------- rear control panel (ref 04-panel-closeup): shelf with key, e-stop, lever, buttons ----------
PZc = 0.86
pn = Part("lift_panel", tuple(POS))
lbox(pn, -0.205, 0.205, 0.30, 0.42, PZc - 0.004, PZc, M("M_RackBlack"))                                  # panel plate
lbox(pn, -0.205, -0.12, 0.34, 0.41, PZc, PZc + 0.002, M("M_LabelWhite"))                                 # labels
lbox(pn, -0.195, -0.13, 0.345, 0.37, PZc + 0.002, PZc + 0.003, M("M_EStopRed"))
lbox(pn, 0.10, 0.17, 0.365, 0.41, PZc, PZc + 0.002, M("M_LiftBlue"))                                     # blue info label
pn.build(C, root)
ky = Part("lift_key", tuple(V(-0.165, 0.39, PZc)))
lcyl(ky, -0.165, 0.39, 0, "Z", PZc, PZc + 0.012, 0.014, GV, 12)
lbox(ky, -0.172, -0.158, 0.386, 0.394, PZc + 0.012, PZc + 0.04, M("M_EStopYellow"))                       # yellow key head
moving(ky.build(C, root), "hinge", "Z", [0, 90], tip="lift_key", note="power key switch")
es = Part("lift_estop", tuple(V(-0.05, 0.39, PZc)))
lcyl(es, -0.05, 0.39, 0, "Z", PZc, PZc + 0.012, 0.032, M("M_EStopYellow"), 16)                           # yellow collar
lcyl(es, -0.05, 0.39, 0, "Z", PZc + 0.012, PZc + 0.025, 0.013, M("M_RackBlack"), 10)
lcyl(es, -0.05, 0.39, 0, "Z", PZc + 0.025, PZc + 0.045, 0.026, M("M_EStopRed"), 18)                       # red mushroom
moving(es.build(C, root), "press", "-Z", [0, 0.008], tip="lift_estop", note="emergency stop: push to stop, twist to reset")
lv = Part("lift_wheel_lock", tuple(V(0.05, 0.39, PZc)))
lcyl(lv, 0.05, 0.39, 0, "Z", PZc, PZc + 0.015, 0.018, M("M_RackBlack"), 12)
lbox(lv, 0.044, 0.056, 0.34, 0.39, PZc + 0.015, PZc + 0.03, M("M_EStopRed"))                              # red rotary wheel-lock lever (turns flat on the panel)
lbox(lv, 0.040, 0.060, 0.338, 0.352, PZc + 0.03, PZc + 0.07, M("M_EStopRed"))                              # grip
moving(lv.build(C, root), "hinge", "Z", [0, 90], tip="lift_wheel_lock", note="locks / releases the front wheels")
for i, col in enumerate(("M_EStopYellow", "M_LEDGreen")):                                                  # small buttons
    by = 0.36 + i * 0.035
    bt = Part(f"lift_button_{i + 1}", tuple(V(0.19, by, PZc)))
    lcyl(bt, 0.19, by, 0, "Z", PZc, PZc + 0.012, 0.011, M(col), 12)
    moving(bt.build(C, root), "press", "-Z", [0, 0.004], tip="lift_button")

# ---------- push handle (curved tube up the rear, ref 05-side) ----------
for sx in (-1, 1):
    x = sx * 0.15
    pipe(f"lift_handle_{'L' if sx < 0 else 'R'}", [(x, 0.40, 0.90), (x, 0.52, 1.02), (x, 0.52, 1.50), (x, 0.36, 1.74), (x, 0.27, 1.78)],
         0.0135, K, root, 12, 0.10)
pipe("lift_handle_grip", [(-0.15, 0.52, 1.25), (0.15, 0.52, 1.25)], 0.0145, M("M_RackBlack"), root, 12, 0.01)

# ---------- shelf + carriage: one moving unit on the central pulley carriage (refs 02-in-use, 07-shelf) ----------
# Flat steel top (nothing raised, so a server slides on); the brace is UNDER the shelf: a black striped arm from the
# carriage. Lowered: shelf top level with the striped leg tops (0.1655) so a server never drops below the legs; brace clear of the floor.
PZ = 0.1655; ST = 0.020                                                                                  # lowest shelf top = level with the leg tape (U1 floor)
pl = lnode("lift_platform", tuple(V(0, 0, PZ)), C, root, role="moving", motion="slide", axis="Z", limits=[0.0, 2.40 - PZ],
           tip="lift_platform", note="shelf + central carriage; top 0.1655 (lowered, level with the legs) to 2.40 m; remote raises/lowers")
pt = Part("lift_platform_mesh", tuple(V(0, 0, PZ)))
lbox(pt, -0.07, 0.07, -0.040, -0.004, PZ - 0.10, PZ + 0.34, K)                                            # central carriage (pulley system)
for zz in (PZ + 0.12, PZ + 0.26):                                                                         # label plates on the carriage
    lbox(pt, -0.05, 0.05, -0.042, -0.040, zz, zz + 0.05, M("M_LabelWhite")); lbox(pt, -0.045, 0.045, -0.043, -0.042, zz + 0.01, zz + 0.025, M("M_EStopRed"))
lcyl(pt, 0.0, -0.03, PZ + 0.30, "X", -0.075, 0.075, 0.012, GV, 10)                                        # pulley axle
Y0_, Y1_ = -0.04, -0.65
lbox(pt, -0.21, 0.21, Y1_, Y0_, PZ - ST, PZ - 0.003, K)                                                   # shelf plate (black edges)
lbox(pt, -0.207, 0.207, Y1_ + 0.003, Y0_, PZ - 0.003, PZ, M("M_TableSteel"))                             # flat steel top
BZ0, BZ1, BY = PZ - ST - 0.06, PZ - ST, -0.40                                                             # brace arm under the shelf (clear of the floor)
lbox(pt, -0.17, 0.17, BY, Y0_, BZ0, BZ1, K)
hazard_quad(pt, V(-0.1705, BY - 0.0005, BZ0), V(0.1705, BY - 0.0005, BZ0), V(0.1705, BY - 0.0005, BZ1), V(-0.1705, BY - 0.0005, BZ1), 0.34)
for sx in (-1, 1):
    x = sx * 0.1705
    a_, b_ = (V(x, BY, BZ0), V(x, Y0_, BZ0)) if sx > 0 else (V(x, Y0_, BZ0), V(x, BY, BZ0))
    hazard_quad(pt, a_, b_, b_ + Vector((0, 0, BZ1 - BZ0)), a_ + Vector((0, 0, BZ1 - BZ0)), 0.36)
    a0, a1 = sorted((sx * 0.17, sx * 0.20)); lcyl(pt, 0, BY + 0.03, (BZ0 + BZ1) / 2, "X", a0, a1, 0.025, K, 14)   # tube noses
bevel(pt.build(C, pl), 0.003, 2)
lnode("slot_lift_server", tuple(V(0, -0.35, PZ)), C, pl, role="slot", accepts="server",
      note="server sits here (front towards -Y, out over the table end); slides 300 mm into a rack")

# ---------- remote in a holster on the sloped rear face, coiled cable ----------
RY = rear_y(1.30)
hl = Part("lift_remote_holster", tuple(POS))
lbox(hl, 0.095, 0.165, RY, RY + 0.014, 1.22, 1.36, K)
hl.build(C, root)
rm = lnode("asset_lift_remote", tuple(V(0.13, RY + 0.03, 1.30)), C, root, role="asset", tip="lift_remote", pull=[[0, 0.06, 0.05]],
           note="up/down remote; hangs in a holster on the rear; works from either side")
r = Part("lift_remote_mesh", tuple(V(0.13, RY + 0.03, 1.30)))
lbox(r, 0.103, 0.157, RY + 0.014, RY + 0.044, 1.20, 1.37, M("M_RemoteGrey"))
for zz in (1.33, 1.29): lcyl(r, 0.13, 0, zz, "Y", RY + 0.044, RY + 0.049, 0.011, M("M_RackBlack"), 12)     # up / down buttons
bevel(r.build(C, rm), 0.006, 2, 60)
coil = [(0.13 + 0.013 * math.cos(k * 1.3), RY + 0.03 + 0.013 * math.sin(k * 1.3), 1.20 - k * 0.017) for k in range(18)]
coil += [(0.13, 0.40, 0.92), (0.12, 0.40, 0.865)]
pipe("lift_remote_cable", coil, 0.0035, M("M_CableBlack"), root, 4, 0.0)

# ---------- charge inlet + wall socket + lead ----------
inl = Part("lift_charge_inlet", tuple(POS))
lcyl(inl, -0.21, 0.20, 0.40, "X", -0.222, -0.21, 0.02, M("M_SocketDark"), 14)
inl.build(C, root)
FX = OX; sy, sz = POS.y + 0.35, 0.45
lfw = lnode("fixed_lift_charging", (FX, sy, sz), C, None, role="fixed", tip="lift_charging")
ws = Part("lift_charge_socket")
ws.box(FX, FX + 0.042, sy - 0.073, sy + 0.073, sz - 0.043, sz + 0.043, M("M_SocketGrey"))
for dy in (-0.036, 0.036):
    ws.box(FX + 0.041, FX + 0.043, sy + dy - 0.020, sy + dy + 0.020, sz - 0.025, sz + 0.010, M("M_SocketDark"))
ws.cyl((FX + 0.03, sy, 0), "Z", sz + 0.045, 3.00, 0.010, GV, 8)                                          # conduit drop from the top run
ws.box(FX + 0.043, FX + 0.078, sy - 0.055, sy - 0.015, sz - 0.03, sz + 0.02, M("M_TVBlack"))            # charger plug
ws.build(C, lfw)
lead = [(FX + 0.078 - POS.x, sy - 0.035 - POS.y, sz), (FX + 0.10 - POS.x, sy - 0.04 - POS.y, 0.25),
        (FX + 0.13 - POS.x, sy - 0.08 - POS.y, 0.012), (-0.40, 0.20, 0.012), (-0.40, 0.20, 0.34), (-0.222, 0.20, 0.40)]
ld = pipe("lift_charge_lead", lead, 0.005, M("M_CableBlack"), lfw, 6, 0.05)
setp(ld, role="connector", tip="lift_charge_lead", note="unplug before moving the lift")
print("LIFT_REPORT", {"tris": tris(C)})
lab_save()
