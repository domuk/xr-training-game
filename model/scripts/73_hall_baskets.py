"""Hall 73 — 3-tier wire cable baskets over every row (LOG.md section 4; research/reference/basket_01/02).
Tiers, bottom up: power (whips from the PDC at the south end of the row to each rack's commando plug; the run stops
just north of the PDC so the incoming feeders can drop past it),
fibre (to the network racks), Ethernet (to the network racks). Each run covers the row, centred where the lab rack's power lead rises (0.38 m in front of the rack back), so the leads meet
the power tier. Hung on threaded rods from the roof with strut cross-bars under each tier (as basket_01).
Wire mesh = alpha-clipped texture on the basket faces (cheap for the headset)."""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
hall_open()
C = hall_coll("baskets"); wipe(C); root = hfixed("baskets", C)
_MAT_DEFS.update({"M_WhipBlack": ("#1A1A1A", 0.6, 0), "M_FibreYellow": ("#E8C21E", 0.5, 0), "M_EthBlue": ("#2F6FC9", 0.5, 0)})
G = M("M_Galv")
TIERS = [("power", 2.75, "M_WhipBlack"), ("fibre", 3.05, "M_FibreYellow"), ("ethernet", 3.35, "M_EthBlue")]
BW, BH, CELL = 0.30, 0.06, 0.05                    # basket width, side height, mesh cell (50 mm)
LEAD = 0.38                                         # lab rack lead: 0.38 m in front of the rack back (52_racks.py)

# ---------- wire mesh texture: one 50 x 50 mm cell per tile, 2 wires ----------
n = 32; img = np.zeros((n, n, 4)); img[:, :, :3] = 0.66
img[:3, :, 3] = 1; img[:, :3, 3] = 1
tex_material("M_BasketWire", save_png("hall_basket_wire", img), rough=0.4, metal=1.0, alpha_clip=True)
WM = M("M_BasketWire")

def mesh_quad(p, pts, du, dv):
    """Two-sided wire-mesh quad; du, dv = its size (m) along the first and last edge."""
    u, v = du / CELL, dv / CELL
    tquad(p, pts, [(0, 0), (u, 0), (u, v), (0, v)], WM)
    tquad(p, [pts[1], pts[0], pts[3], pts[2]], [(u, 0), (0, 0), (0, v), (u, v)], WM)

rows = hall_layout()["rows"]
for letter, r in rows.items():
    sgn = -1 if r["faces"] == "west" else 1
    cx = r["rear_x"] + sgn * LEAD; y0, y1 = r["y"][0] - 0.25, r["y"][1]   # stops just north of the PDC (its whips come in at this end)
    grp = hnode(f"fixed_baskets_{letter}", (cx, (y0 + y1) / 2, 0), C, root, role="fixed", tip="cable_basket", row=letter)
    rods = Part(f"baskets_{letter}_hangers")
    for name, z, cm in TIERS:
        b = Part(f"basket_{letter}_{name}"); xa, xb = cx - BW / 2, cx + BW / 2; L_ = y1 - y0
        mesh_quad(b, [(xa, y0, z), (xb, y0, z), (xb, y1, z), (xa, y1, z)], BW, L_)                 # floor
        for x in (xa, xb):
            mesh_quad(b, [(x, y0, z), (x, y1, z), (x, y1, z + BH), (x, y0, z + BH)], L_, BH)        # sides
            b.cyl((x, 0, z + BH), "Y", y0, y1, 0.0025, G, 4)                                           # top edge wire
        b.box(cx - 0.11, cx + 0.11, y0 + 0.05, y1 - 0.05, z + 0.003, z + 0.035, M(cm))                 # the cables it carries
        setp(b.build(C, grp), role="fixed", tip=f"basket_{name}", carries=name)
        for y in np.arange(y0 + 0.3, y1, 1.5):                                                       # strut bar under the tier
            rods.box(cx - 0.24, cx + 0.24, y - 0.02, y + 0.02, z - 0.041, z, G)
    for y in np.arange(y0 + 0.3, y1, 1.5):                                                           # threaded rods to the roof
        for s in (-0.21, 0.21): rods.cyl((cx + s, y, 0), "Z", TIERS[0][1] - 0.06, roof_under(cx + s, y) - 0.002, 0.005, G, 6)
    rods.build(C, grp)
print("HALL_BASKETS_REPORT", {"tris": tris(C)})
hall_save()
