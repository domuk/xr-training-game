"""Hall 71 — 6 rows x 10 empty racks (the lab's 600 x 1200 rack_2, shared mesh), rows running south-north.
Hot aisle containment layout (LOG.md sections 2, 12, 13): 3 pods; in each pod the two rows stand back to back
with a 1.2 m hot aisle between them, fronts facing out into the cold aisles / walkways.
Rows A-F from west to east; racks 01-10 from south to north. Rack origin = rear-centre at floor (as in the lab).
The rack mesh (with its 3 mated commando pairs and whips) is re-copied from lab.blend on every run.
Empty positions (owner: random blank spaces): no rack; the position's 3 whips hang with their female connectors
(face down, flap closed) at the middle of the position, waiting for a rack."""
import bpy, math, random
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
exec(open(os.path.join(HERE, "_commando.py")).read())
hall_open()
C = hall_coll("racks"); wipe(C); root = hfixed("racks", C)
if bpy.data.meshes.get("rack_2_frame"): bpy.data.meshes.remove(bpy.data.meshes["rack_2_frame"])   # take the current lab rack
RACK_ME = from_lab(meshes=("rack_2_frame",))["rack_2_frame"]
N_EMPTY = 8
EMPTY = set(random.Random(2026).sample([(l, k) for l in "ABCDEF" for k in range(N_RACKS)], N_EMPTY))
LEAD, RACK_TOP, WHIP_TOP = 0.38, RACK_H, 2.75          # lab rack: whips 0.38 in front of the back, up to 2.75
_MAT_DEFS.update({"M_ContainAlu": ("#C7CBCE", 0.35, 1.0)})
def frosted(name="M_FrostedPerspex", hexcol="#E8ECEE", alpha=0.65):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); lin = _lin(hexcol)
    b.inputs["Base Color"].default_value = (*lin, 1); b.inputs["Roughness"].default_value = 0.55; b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*lin, alpha)
    try: m.surface_render_method = "BLENDED"
    except Exception: m.blend_method = "BLEND"
    return m

def gap_panel(name, x, y, C, parent):
    """Frosted blanking panel closing an empty position in the hot aisle wall (owner, 2026-10-04): containment-style
    aluminium frame (40 mm), mid rail, frosted perspex; 600 wide, floor to rack top, in the plane of the rack backs."""
    A, FR = M("M_ContainAlu"), 0.04; y0, y1 = y - RACK_W / 2 + 0.002, y + RACK_W / 2 - 0.002
    g = Part(name, (x, y, 0))
    for (ya, yb) in ((y0, y0 + FR), (y1 - FR, y1)): g.box(x - FR / 2, x + FR / 2, ya, yb, 0, RACK_TOP, A)          # posts
    for z in (0, RACK_TOP / 2 - FR / 2, RACK_TOP - FR): g.box(x - FR / 2, x + FR / 2, y0, y1, z, z + FR, A)        # rails
    g.box(x - 0.004, x + 0.004, y0 + FR, y1 - FR, FR, RACK_TOP - FR, frosted())                                       # perspex
    o = g.build(C, parent); setp(o, role="asset", tip="containment_blank", note="remove before a rack goes in")
    return o
rows = {}
for i in range(3):
    x0 = pod_x0(i)
    for side, letter in ((0, "ABCDEF"[2 * i]), (1, "ABCDEF"[2 * i + 1])):
        rear_x = x0 + RACK_D if side == 0 else x0 + RACK_D + HOT       # rear plane on the hot aisle
        rot = math.pi / 2 if side == 0 else -math.pi / 2                 # lab rack fronts face local +Y -> west / east
        grp = hnode(f"fixed_row_{letter}", (*P(rear_x, ROW_Y0), 0), C, root, role="fixed", tip="rack_row", row=letter,
                    faces="west" if side == 0 else "east")
        for k in range(N_RACKS):
            y = ROW_Y0 + RACK_W / 2 + k * RACK_W
            if (letter, k) in EMPTY:                                         # empty: 3 whips hang waiting for a rack
                wx = P(rear_x + (-LEAD if side == 0 else LEAD), 0)[0]; wy = P(0, y)[1]
                e = hnode(f"empty_pos_{letter}{k + 1:02d}", (wx, wy, 0), C, grp, role="slot", tip="empty_rack_position",
                          row=letter, number=k + 1)
                cab = Part(f"empty_pos_{letter}{k + 1:02d}_whips", (wx, wy, 0)); zf = MATE_Z
                for j in (-1, 0, 1):
                    place_female(f"whip_{letter}{k + 1:02d}_{j + 2}", (wx, wy + j * RACK_W * 0.25, zf), 0, C, e, face_down=True)
                    cab.cyl((wx, wy + j * RACK_W * 0.25, 0), "Z", zf + 0.175, WHIP_TOP, 0.010, M("M_CableBlack"), 6)
                cab.build(C, e)
                gap_panel(f"asset_blank_{letter}{k + 1:02d}", P(rear_x, 0)[0], wy, C, e)
                continue
            o = inst(f"rack_{letter}{k + 1:02d}", RACK_ME, (*P(rear_x, y), 0), C, grp)
            o.rotation_euler = (0, 0, rot); setp(o, role="fixed", tip="rack", row=letter, number=k + 1, units=42)
        rows[letter] = {"rear_x": P(rear_x, 0)[0], "front_x": P(rear_x - RACK_D if side == 0 else rear_x + RACK_D, 0)[0],
                        "y": [P(0, ROW_Y0)[1], P(0, ROW_Y0 + ROW_LEN)[1]], "faces": "west" if side == 0 else "east"}
hall_layout("rows", rows)
hall_layout("empty_positions", sorted(f"{l}{k + 1:02d}" for l, k in EMPTY))
print("HALL_RACKS_REPORT", {"racks": N_ROWS * N_RACKS - N_EMPTY, "empty": N_EMPTY, "tris": tris(C)})
hall_save()
