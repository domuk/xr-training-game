"""Hall 74 — PDC (power distribution cabinet) at the south end of every row, outside the containment (LOG.md section 14;
research/reference/pdc_01_placement_pod.png, pdc_02_cabinet.png). Generic, no branding.
  - black cabinet 1200 W x 600 D x 2000 H facing south (owner: about 1.2 m wide), on 4 feet.
    Left door (60 %): glass, hinged, opens (moving part). Right door: solid, fixed, nothing behind it,
  - behind the glass: meter (LED kVA screen) above the breaker panel (_pdc_panel.py): 3 strips of 10 breakers,
    breaker n of strip k feeds rack n of the row (whip k), 3 masters on top; all handles are moving parts,
  - top: incoming box with 3 large glands left/centre, output glands right (same on every PDC, as the photo),
  - power whips rise from the outputs into the row's power basket (bottom tier),
  - incoming: 2 thick baskets enter through the south wall above each door and run along the PDC line; diverse feed:
    each PDC gets L1 from the left entry, L2 from the right, L3 alternating (A, C, E left; B, D, F right)."""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
exec(open(os.path.join(HERE, "_pdc_panel.py")).read())
hall_open()
C = hall_coll("pdc"); wipe(C); root = hfixed("pdc", C)
_MAT_DEFS.update({"M_PDCBlack": ("#151617", 0.5, 0.3), "M_PDCInner": ("#3A3D40", 0.6, 0.2), "M_DINGrey": ("#9A9DA0", 0.4, 0.8),
                  "M_MCBWhite": ("#E8E8E4", 0.5, 0), "M_MeterGreen": ("#7FC24A", 0.3, 0), "M_GlandBlack": ("#0E0E0E", 0.7, 0),
                  "M_WhipBlack": ("#1A1A1A", 0.6, 0), "M_PowerCable": ("#222222", 0.6, 0)})
def tinted(name="M_PDCGlass", hexcol="#2A3236", alpha=0.35):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); lin = _lin(hexcol)
    b.inputs["Base Color"].default_value = (*lin, 1); b.inputs["Roughness"].default_value = 0.05; b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*lin, alpha)
    try: m.surface_render_method = "BLENDED"
    except Exception: m.blend_method = "BLEND"
    return m
K, IN, GLS = M("M_PDCBlack"), M("M_PDCInner"), tinted()
PW, PD, PH = 1.20, 0.60, 2.00
GAP = 0.15                                   # clear of the containment door track at the row end
LEAD, POWER_Z, IN_Z = 0.38, 2.75, 3.70       # power basket position (73_hall_baskets.py); incoming basket height

rows = hall_layout()["rows"]
pdcs = {}
for letter, r in rows.items():
    west = r["faces"] == "west"
    xa, xb = sorted((r["front_x"], r["rear_x"]))
    # sit the cabinet on the front (cold) side of the row, its outputs on the side of the power basket
    x0, x1 = (xa, xa + PW) if west else (xb - PW, xb)
    y1 = r["y"][0] - GAP; y0 = y1 - PD; cx = (x0 + x1) / 2
    basket_x = r["rear_x"] + (-LEAD if west else LEAD); out_dir = 1 if basket_x > cx else -1
    grp = hnode(f"fixed_pdc_{letter}", (cx, (y0 + y1) / 2, 0), C, root, role="fixed", tip="pdc", row=letter)
    # body: open-fronted steel shell on 4 feet; mounting plate inside; front face at y0 + 0.025 (doors in front of it)
    b = Part(f"pdc_{letter}_body", (cx, (y0 + y1) / 2, 0)); FT, ZB = 0.02, 0.10; yf = y0 + 0.025; yp = yf + 0.26
    for (fx, fy_) in ((x0 + 0.03, yf + 0.03), (x1 - 0.07, yf + 0.03), (x0 + 0.03, y1 - 0.07), (x1 - 0.07, y1 - 0.07)):
        b.box(fx, fx + 0.04, fy_, fy_ + 0.04, 0, ZB, K)                                            # feet
    b.box(x0, x1, yf, y1, ZB, ZB + FT, K); b.box(x0, x1, yf, y1, PH - FT, PH, K)                 # bottom, top
    b.box(x0, x0 + FT, yf, y1, ZB, PH, K); b.box(x1 - FT, x1, yf, y1, ZB, PH, K)                 # sides
    b.box(x0, x1, y1 - FT, y1, ZB, PH, K)                                                        # back
    b.box(x0, x1, yf, yf + FT, ZB + FT, ZB + 0.08, K); b.box(x0, x1, yf, yf + FT, PH - 0.08, PH - FT, K)   # front frame rails
    LW = round(PW * 0.60, 3); xm = x0 + LW                                                       # left (glass) door width / split
    b.box(xm - 0.01, xm + 0.01, yf, yp, ZB, PH, K)                                               # partition behind the split
    b.box(x0 + FT, xm - 0.01, yp, yp + 0.01, ZB + FT, PH - FT, IN)                               # mounting plate (left bay)
    # behind the glass door (outgoing side, LOG.md section 15): a cover plate; at the top a meter with an LED kVA screen;
    # then the breakers (below).
    cxl = (x0 + FT + xm - 0.01) / 2; yc = yp - 0.03                                              # bay centre x, cover plate face
    b.box(x0 + FT, xm - 0.01, yc, yp, ZB + FT, PH - FT, M("M_PanelGrey"))                        # cover plate
    for (sx, sz) in ((x0 + 0.05, 0.26), (xm - 0.04, 0.26), (x0 + 0.05, 1.84), (xm - 0.04, 1.84)):
        b.cyl((sx, 0, sz), "Y", yc - 0.004, yc, 0.007, M("M_Screw"), 8)                           # corner screws
    b.box(cxl - 0.09, cxl + 0.09, yc - 0.05, yc, 1.66, 1.80, M("M_SlotBlack"))                    # meter
    b.box(cxl - 0.075, cxl + 0.075, yc - 0.051, yc - 0.05, 1.70, 1.77, M("M_TVBlack"))           # LED screen
    kva = text_obj(f"pdc_{letter}_meter_text", "48.6 kVA", 0.026, M("M_LEDGreen"), (cxl, yc - 0.052, 1.735), C, grp,
                   rot=(math.pi / 2, 0, 0))
    breaker_panel(b, cxl, yc, 0.80, C, grp, f"pdc_{letter}", row=letter)                          # strips 0.80-1.10, masters 1.30
    ix = x0 + 0.40                                                                               # incoming box: top left/centre (as the photo)
    b.box(ix - 0.20, ix + 0.20, y0 + 0.12, y1 - 0.10, PH, PH + 0.14, K)
    for k in range(3): b.cyl((ix - 0.11 + k * 0.11, y0 + 0.20, 0), "Z", PH + 0.14, PH + 0.20, 0.035, M("M_GlandBlack"), 10)   # gland line 100 mm south of centre
    ox = x1 - 0.16                                                                               # output glands: top right
    b.box(ox - 0.13, ox + 0.13, y0 + 0.10, y1 - 0.06, PH, PH + 0.04, K)
    glands = [(ox - 0.1125 + i * 0.045, y0 + 0.16 + j * 0.075) for i in range(6) for j in range(5)]   # 30 outputs (1 per breaker)
    for (gx, gy) in glands: b.cyl((gx, gy, 0), "Z", PH + 0.04, PH + 0.09, 0.016, M("M_GlandBlack"), 8)
    b.build(C, grp)
    # right door: solid, no window, does not open (nothing behind it)
    rd = Part(f"pdc_{letter}_door_R"); rd.box(xm + 0.003, x1 - 0.003, y0, yf, ZB + 0.01, PH - 0.01, K)
    rd.build(C, grp)
    # left door: glass window, hinged on the left (outer) edge, opens outwards; handle near the split
    d = Part(f"pdc_{letter}_door_L", (x0 + 0.003, (y0 + yf) / 2, 0)); dx0, dx1, bw = x0 + 0.003, xm - 0.003, 0.04
    d.box(dx0, dx1, y0, yf, ZB + 0.01, ZB + 0.01 + bw * 2, K); d.box(dx0, dx1, y0, yf, PH - 0.01 - bw * 2, PH - 0.01, K)
    d.box(dx0, dx0 + bw, y0, yf, ZB + 0.01, PH - 0.01, K); d.box(dx1 - bw, dx1, y0, yf, ZB + 0.01, PH - 0.01, K)
    d.box(dx0 + bw, dx1 - bw, (y0 + yf) / 2 - 0.003, (y0 + yf) / 2 + 0.003, ZB + 0.01 + bw * 2, PH - 0.01 - bw * 2, GLS)
    d.box(dx1 - 0.045, dx1 - 0.025, y0 - 0.03, y0, 0.98, 1.16, M("M_SteelHandle"))               # lever handle
    o = d.build(C, grp)
    moving(o, "hinge", "Z", [-110, 0], tip="pdc_door", note="glass door: rack breakers behind it")
    cab = Part(f"pdc_{letter}_cables")
    # whips leave the output glands into a short whip basket (z 2.75) that runs north from above the glands to the
    # south end of the row's power basket, then along it to the basket line, so they are carried all the way
    yb = r["y"][0] - 0.20; zb = POWER_Z; WB = 0.20                                               # power basket end / whip basket
    gy0, gy1 = min(g[1] for g in glands), max(g[1] for g in glands)
    wb = Part(f"pdc_{letter}_whip_basket")
    def wq(pts, du, dv):
        u, v = du / 0.05, dv / 0.05
        tquad(wb, pts, [(0, 0), (u, 0), (u, v), (0, v)], M("M_BasketWire")); tquad(wb, [pts[1], pts[0], pts[3], pts[2]], [(u, 0), (0, 0), (0, v), (u, v)], M("M_BasketWire"))
    ya, yz = gy0 - 0.03, yb + WB / 2                                              # along Y over the glands to the basket end
    wq([(ox - WB / 2, ya, zb), (ox + WB / 2, ya, zb), (ox + WB / 2, yz, zb), (ox - WB / 2, yz, zb)], WB, yz - ya)
    for sx in (-1, 1): wq([(ox + sx * WB / 2, ya, zb), (ox + sx * WB / 2, yz, zb), (ox + sx * WB / 2, yz, zb + 0.06), (ox + sx * WB / 2, ya, zb + 0.06)], yz - ya, 0.06)
    xa_, xz_ = sorted((ox, basket_x))                                              # along X to the power basket line
    wq([(xa_, yb - WB / 2, zb), (xz_, yb - WB / 2, zb), (xz_, yb + WB / 2, zb), (xa_, yb + WB / 2, zb)], xz_ - xa_, WB)
    for sy in (-1, 1): wq([(xa_, yb + sy * WB / 2, zb), (xz_, yb + sy * WB / 2, zb), (xz_, yb + sy * WB / 2, zb + 0.06), (xa_, yb + sy * WB / 2, zb + 0.06)], xz_ - xa_, 0.06)
    for py in (ya + 0.04, min(yz - 0.05, y1 - 0.04)):                             # stands on 2 posts on the PDC top
        wb.box(ox - WB / 2 - 0.01, ox + WB / 2 + 0.01, py - 0.02, py + 0.02, zb - 0.041, zb, M("M_Galv"))
        for sx in (-1, 1): wb.box(ox + sx * (WB / 2 + 0.005) - 0.02, ox + sx * (WB / 2 + 0.005) + 0.02, py - 0.02, py + 0.02, PH, zb - 0.041, M("M_Galv"))
    setp(wb.build(C, grp), role="fixed", tip="whip_basket", note="carries the whips from the output glands to the power basket")
    for k, (gx, gy) in enumerate(glands):                                                        # 30 whips: up into the whip basket, along it
        zw = zb + 0.012 + 0.008 * (k % 3); lx = ox - WB / 2 + 0.02 + (k % 8) * 0.02
        cab.cyl((gx, gy, 0), "Z", PH + 0.09, zw, 0.008, M("M_WhipBlack"), 6)
        cab.cyl((gx, 0, zw), "X", min(gx, lx), max(gx, lx), 0.008, M("M_WhipBlack"), 6) if abs(gx - lx) > 0.001 else None
        cab.cyl((lx, 0, zw), "Y", min(gy, yb), max(gy, yb), 0.008, M("M_WhipBlack"), 6)
        cab.cyl((0, yb - WB / 2 + 0.02 + (k % 8) * 0.02, zw), "X", min(lx, basket_x), max(lx, basket_x), 0.008, M("M_WhipBlack"), 6)
    cab.build(C, grp)
    pdcs[letter] = {"x": [x0, x1], "y": [y0, y1], "incoming_x": ix}

# ---------- incoming power (owner, 2026-10-04): ONE incoming basket over the top of the PDCs, fed from both ends: the
# left entry comes through the south wall above the west door and joins its west end, the right entry above the east
# door joins its east end. Incoming only (whips never share it). Diverse feed: every PDC takes L1 from the left entry,
# L2 from the right, L3 alternately (A, C, E left; B, D, F right).
# Cable layout (no cable passes through another): 4 layers; left-fed cables in the 2 lower layers, right-fed in the 2
# upper. Within a layer, the cable that drops first runs nearest the south edge, so it leaves over the edge (drop-out)
# without crossing anything, then falls straight into its gland (gland line just south of the basket).
WM = M("M_BasketWire"); CELL = 0.05
IW, IH, IZ = 0.40, 0.26, 3.47                                                  # basket width, depth, floor height
R_, PITCH, LP = 0.03, 0.065, 0.062                                             # cable radius, lane pitch, layer pitch
ygl = pdcs["A"]["y"][0] + 0.20                                                 # incoming gland line (all PDCs)
ys0 = ygl + 0.02; ys1 = ys0 + IW; yrun = (ys0 + ys1) / 2                       # basket over the PDC tops, clear of the containment
XL, XR = P(SIDE / 2, 0)[0], P(W - SIDE / 2, 0)[0]                             # entry legs (above the doors)
FEED = {l: ("L", "R", "L" if i % 2 == 0 else "R") for i, l in enumerate(sorted(pdcs))}
def mesh_quad(p, pts, du, dv):
    u, v = du / CELL, dv / CELL
    tquad(p, pts, [(0, 0), (u, 0), (u, v), (0, v)], WM); tquad(p, [pts[1], pts[0], pts[3], pts[2]], [(u, 0), (0, 0), (0, v), (u, v)], WM)
def tray(p, x0, x1, y0_, y1_):
    """Open-topped wire basket over the box x0..x1, y0_..y1_, floor at IZ, sides IH high, all 4 sides except where open."""
    mesh_quad(p, [(x0, y0_, IZ), (x1, y0_, IZ), (x1, y1_, IZ), (x0, y1_, IZ)], x1 - x0, y1_ - y0_)
    return p
bk = Part("basket_incoming")
# run along the PDC line, from the west leg to the east leg
tray(bk, XL - IW / 2, XR + IW / 2, ys0, ys1)
drops = [pdcs[l]["incoming_x"] for l in pdcs]
mesh_quad(bk, [(XL - IW / 2, ys1, IZ), (XR + IW / 2, ys1, IZ), (XR + IW / 2, ys1, IZ + IH), (XL - IW / 2, ys1, IZ + IH)], XR - XL + IW, IH)   # north side
gaps = sorted([(XL - IW / 2, XL + IW / 2), (XR - IW / 2, XR + IW / 2)] + [(d - 0.20, d + 0.20) for d in drops])  # open: legs + drop-outs
xa_ = XL - IW / 2
for (g0, g1) in gaps + [(XR + IW / 2, XR + IW / 2)]:                            # south side, open where the legs join / cables drop out
    if g0 > xa_ + 0.001: mesh_quad(bk, [(xa_, ys0, IZ), (g0, ys0, IZ), (g0, ys0, IZ + IH), (xa_, ys0, IZ + IH)], g0 - xa_, IH)
    xa_ = max(xa_, g1)
for x in (XL - IW / 2, XR + IW / 2): mesh_quad(bk, [(x, ys0, IZ), (x, ys1, IZ), (x, ys1, IZ + IH), (x, ys0, IZ + IH)], IW, IH)
# 2 legs: from the wall sleeve north to the run
for x in (XL, XR):
    tray(bk, x - IW / 2, x + IW / 2, OY, ys0)
    for sx in (-1, 1): mesh_quad(bk, [(x + sx * IW / 2, OY, IZ), (x + sx * IW / 2, ys0, IZ), (x + sx * IW / 2, ys0, IZ + IH), (x + sx * IW / 2, OY, IZ + IH)], ys0 - OY, IH)
    bk.box(x - IW / 2 - 0.05, x + IW / 2 + 0.05, OY - 0.02, OY + 0.03, IZ - 0.05, IZ + IH + 0.05, M("M_GlandBlack"))      # wall sleeve
    for y in np.arange(OY + 0.6, ys0 - 0.2, 1.2):                              # leg hangers
        bk.box(x - IW / 2 - 0.05, x + IW / 2 + 0.05, y - 0.02, y + 0.02, IZ - 0.041, IZ, M("M_Galv"))
        for sx in (-1, 1): bk.cyl((x + sx * (IW / 2 + 0.03), y, 0), "Z", IZ - 0.06, roof_under(x + sx * (IW / 2 + 0.03), y) - 0.002, 0.005, M("M_Galv"), 6)
# trapeze struts under the run (clear of every drop-out)
for x in np.arange(XL + 0.6, XR - 0.3, 1.2):
    while any(abs(x - d) < 0.35 for d in drops): x += 0.15
    bk.box(x - 0.02, x + 0.02, ys0 - 0.06, ys1 + 0.06, IZ - 0.041, IZ, M("M_Galv"))
    for y in (ys0 - 0.04, ys1 + 0.04): bk.cyl((x, y, 0), "Z", IZ - 0.06, roof_under(x, y) - 0.002, 0.005, M("M_Galv"), 6)
for d in drops: bk.box(d - 0.20, d + 0.20, ys0 - 0.010, ys0 + 0.002, IZ - 0.02, IZ + 0.02, M("M_Galv"))   # drop-out lip on the south edge
setp(bk.build(C, root), role="fixed", tip="basket_incoming", note="one incoming basket over the PDCs, fed from the left and right entries")

# ---------- the 18 incoming cables
cab = Part("incoming_cables"); PC = M("M_PowerCable")
for side, layers, xe in (("L", (0, 1), XL), ("R", (2, 3), XR)):
    mine = [(pdcs[l]["incoming_x"] - 0.11 + k * 0.11, l, k) for l, f in FEED.items() for k, s_ in enumerate(f) if s_ == side]
    mine.sort(key=lambda t: abs(t[0] - xe))                                    # nearest drop first
    for j, (gx, letter, k) in enumerate(mine):
        layer = layers[j % 2]; lane = j // 2                                    # alternate the 2 layers, then next lane
        zc = IZ + R_ + 0.004 + layer * LP
        ly = ys0 + 0.045 + lane * PITCH                                         # nearest drop = nearest the south edge
        # leg: lanes across the leg map to the run's lanes without crossing (south lane in the run = outside of the bend)
        lx = xe + (IW / 2 - 0.045 - lane * PITCH) * (1 if side == "L" else -1)
        cab.cyl((lx, 0, zc), "Y", OY - 0.05, ly, R_, PC, 10)                    # leg from the wall
        cab.cyl((0, ly, zc), "X", min(lx, gx), max(lx, gx), R_, PC, 10)        # along the run to its PDC
        cab.cyl((gx, 0, zc), "Y", ygl, ly, R_, PC, 10)                          # over the south edge (drop-out)
        cab.cyl((gx, ygl, 0), "Z", PH + 0.20, zc, R_, PC, 10)                   # down into its gland
setp(cab.build(C, root), role="fixed", tip="incoming_feeders", note="diverse: L1 left entry, L2 right, L3 alternating")
hall_layout("pdc", pdcs); hall_layout("incoming_feed", {l: list(f) for l, f in FEED.items()})
print("HALL_PDC_REPORT", {"tris": tris(C)})
hall_save()
