"""Hall 70 — room shell: floor, walls, roof, steel columns + beams, LED battens, 2 lab double doors on the south wall.
References: research/reference/room_01_empty_hall.webp (columns, exposed steel roof, LED battens), LOG.md sections 1, 12, 13.
Heights from the lab: walls 3.6 m, roof 4.2 m. Door + card reader + floor tile copied from lab.blend.
The south wall has a door-sized hole (1.8 x 2.4 m) behind each door, so the doors open onto empty space (owner, 2026-10-04).
Run headless:  python -c "import runpy; runpy.run_path('assets/blender/scripts/70_hall_room.py')"  (bpy module)"""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
hall_open()
LAB = from_lab(objects=("door_frame", "door_leaf_W", "door_leaf_E", "door_release"),
               materials=("M_FloorTile", "M_LabWall", "M_LabSeam", "M_LabCeil", "M_Galv", "M_ColumnWhite", "M_LEDDiffuser"))
C = hall_coll("room"); wipe(C); root = hfixed("room", C)
G, CW_ = M("M_Galv"), M("M_ColumnWhite")

# ---------- floor: lab tile, joints from the SW corner ----------
f = Part("hall_floor"); f.box(OX, OX + W, OY, OY + L, -0.02, 0.0, M("M_FloorTile"))
uv_world(f.build(C, root), 1 / TILE, OX, OY)

# ---------- walls (inner face on the outline), seams every 1.2 m, lab colours ----------
T = 0.10
DOOR_W, DOOR_H = 1.80, 2.40                  # lab door opening (50_room.py): hole in the south wall behind each door
WALLS = {"W": ((0, 0), (0, L), (1, 0)), "N": ((0, L), (W, L), (0, -1)), "E": ((W, L), (W, 0), (-1, 0)), "S": ((W, 0), (0, 0), (0, 1))}
for k, (a, b, nrm) in WALLS.items():
    (ax, ay), (bx, by) = P(*a), P(*b); nx, ny = nrm
    xa, xb = sorted((ax, bx)); ya, yb = sorted((ay, by))
    if nx: xa, xb = (xa - T, xa) if nx > 0 else (xa, xa + T); ya, yb = ya - T, yb + T
    else:  ya, yb = (ya - T, ya) if ny > 0 else (ya, ya + T); xa, xb = xa - T, xb + T
    w = Part(f"hall_wall_{k}")
    holes = [(P(dx, 0)[0] - DOOR_W / 2, P(dx, 0)[0] + DOOR_W / 2) for dx in (SIDE / 2, W - SIDE / 2)] if k == "S" else []
    cuts = [xa] + [v for h in holes for v in h] + [xb]
    for i in range(0, len(cuts), 2):                                          # wall pieces either side of the door holes
        w.box(cuts[i], cuts[i + 1], ya, yb, 0, RH, M("M_LabWall"))
    for (h0, h1) in holes: w.box(h0, h1, ya, yb, DOOR_H, RH, M("M_LabWall"))   # wall above each door hole
    w.box(xa, xb, ya, yb, RH, CEIL, M("M_LabCeil"))
    length = math.hypot(bx - ax, by - ay); d = Vector((bx - ax, by - ay, 0)).normalized()
    for s in np.arange(1.2, length - 0.1, 1.2):
        px, py = ax + d.x * s, ay + d.y * s
        if any(h0 < px < h1 for (h0, h1) in holes): continue                 # no seam across a door hole
        if nx: w.box(px + (0 if nx > 0 else -0.003), px + (0.003 if nx > 0 else 0), py - 0.003, py + 0.003, 0, RH, M("M_LabSeam"))
        else:  w.box(px - 0.003, px + 0.003, py + (0 if ny > 0 else -0.003), py + (0.003 if ny > 0 else 0), 0, RH, M("M_LabSeam"))
    w.build(C, root)
rf = Part("hall_roof"); rf.box(OX - T, OX + W + T, OY - T, OY + L + T, CEIL, CEIL + 0.05, M("M_LabCeil")); rf.build(C, root)

# ---------- steel: free columns in the cold aisles, wall columns on the same grid, main beams + joists ----------
st = Part("hall_steel"); CS, BD, BW = 0.30, 0.45, 0.25          # column size, beam depth / width
for x in COL_X:
    for y in COL_Y:
        cx, cy = P(x, y); st.box(cx - CS / 2, cx + CS / 2, cy - CS / 2, cy + CS / 2, 0, CEIL, CW_)
for x in COL_X:                                                                       # wall columns, north + south
    cx, _ = P(x, 0); st.box(cx - CS / 2, cx + CS / 2, OY, OY + 0.15, 0, CEIL, CW_); st.box(cx - CS / 2, cx + CS / 2, OY + L - 0.15, OY + L, 0, CEIL, CW_)
for y in COL_Y:                                                                       # wall columns, west + east
    _, cy = P(0, y); st.box(OX, OX + 0.15, cy - CS / 2, cy + CS / 2, 0, CEIL, CW_); st.box(OX + W - 0.15, OX + W, cy - CS / 2, cy + CS / 2, 0, CEIL, CW_)
for y in COL_Y:                                                                       # main beams west-east
    _, cy = P(0, y); st.box(OX, OX + W, cy - BW / 2, cy + BW / 2, CEIL - BD, CEIL, CW_)
for x in COL_X:                                                                       # main beams south-north
    cx, _ = P(x, 0); st.box(cx - BW / 2, cx + BW / 2, OY, OY + L, CEIL - BD, CEIL, CW_)
for x in np.arange(1.5, W, 1.5):                                                       # joists south-north (as the photo's roof joists)
    if min(abs(x - c) for c in COL_X) < 0.4: continue
    jx, _ = P(x, 0); st.box(jx - 0.04, jx + 0.04, OY, OY + L, CEIL - 0.25, CEIL, CW_)
st.build(C, root)

# ---------- LED battens (lab style), south-north lines over the walkways and cold aisles, hung on rods ----------
LZ = 3.40; LINES_X = [SIDE / 2 + 0.7] + COL_X + [W - SIDE / 2 - 0.7]   # walkway lines clear of the door / basket lines
Lg = Part("hall_lights")
for x in LINES_X:
    for y in np.arange(1.2, L - 0.6, 2.4):
        if abs(y - (ROW_Y0 - 0.45)) < 0.9: y = ROW_Y0 - 1.95                     # not over the PDC line (incoming baskets)
        lx, ly = P(x, y)
        if any(abs(x - c) < 0.5 and abs(y - r) < 1.0 for c in COL_X for r in COL_Y): lx += 0.45   # step past a column
        Lg.box(lx - 0.04, lx + 0.04, ly - 0.75, ly + 0.75, LZ, LZ + 0.055, G)
        Lg.box(lx - 0.035, lx + 0.035, ly - 0.74, ly + 0.74, LZ - 0.015, LZ, M("M_LEDDiffuser"))
        for s in (-0.6, 0.6): Lg.cyl((lx, ly + s, 0), "Z", LZ + 0.055, roof_under(lx, ly + s), 0.004, G, 6)
setp(Lg.build(C, root), role="light", note="LED battens; diffuser faces down")

# ---------- doors: the lab double door + card reader, one at the west end and one at the east end of the south wall ----------
LAB_DOOR_MID, LAB_WALL_Y = 0.70, -4.20                     # lab door centre x and its wall face (50_room.py)
DOOR_X = {"W": SIDE / 2, "E": W - SIDE / 2}
for side, x in DOOR_X.items():
    dx = P(x, 0)[0] - LAB_DOOR_MID; dy = OY - LAB_WALL_Y
    for n in ("door_frame", "door_leaf_W", "door_leaf_E", "door_release"):
        src = LAB[n]; o = src.copy(); o.name = f"door_{side}_{n.replace('door_', '')}"
        for k in list(o.keys()):
            if k.startswith("_"): del o[k]
        C.objects.link(o); w_loc = src.location.copy()                # lab parents sit at the origin, so location = world
        o.parent = None; o.matrix_parent_inverse = Matrix.Identity(4)
        place(o, (w_loc.x + dx, w_loc.y + dy, w_loc.z), root)
        if "tip" in o: o["tip"] = "hall_door"
for n in ("door_frame", "door_leaf_W", "door_leaf_E", "door_release"):    # the appended originals are not used
    bpy.data.objects.remove(LAB[n], do_unlink=True)

hall_layout("room", {"W": W, "L": L, "wall_h": RH, "roof": CEIL, "origin": "room centre",
                                         "col_x": [P(x, 0)[0] for x in COL_X], "col_y": [P(0, y)[1] for y in COL_Y]})
print("HALL_ROOM_REPORT", {"size": [W, L], "tris": tris(C)})
hall_save()
