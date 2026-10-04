"""Hall 72 — hot aisle containment (LOG.md section 2; research/reference/hac_03_containment_doors.webp).
Per pod: the hot aisle between the rack backs is closed 'top to bottom':
  - sliding glass double doors at the south and north ends (aluminium frame, header at rack-top height),
  - glazed aluminium panels from the rack tops up to the roof along both rack rows and above the doors,
  - extract vents in the roof over the aisle (hot air out through the ceiling).
Door leaves are moving parts: slide along X (west leaf west, east leaf east) over the end racks."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
hall_open()
C = hall_coll("containment"); wipe(C); root = hfixed("containment", C)
_MAT_DEFS.update({"M_ContainAlu": ("#C7CBCE", 0.35, 1.0), "M_VentGrey": ("#5A5E62", 0.5, 0.5), "M_VentDark": ("#1C1D1E", 0.7, 0),
                  "M_DoorRubber": ("#202020", 0.8, 0)})

def glass(name="M_ContainGlass", hexcol="#D6E2E6", alpha=0.18):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); lin = _lin(hexcol)
    b.inputs["Base Color"].default_value = (*lin, 1); b.inputs["Roughness"].default_value = 0.05
    b.inputs["Alpha"].default_value = alpha; m.diffuse_color = (*lin, alpha)
    try: m.surface_render_method = "BLENDED"
    except Exception: m.blend_method = "BLEND"
    return m
A, GL = M("M_ContainAlu"), glass()
FR = 0.04                                   # aluminium section
TOP = RACK_H                                # rack tops (door header / panels start here)
DOOR_H = TOP - 0.062                        # leaf height (floor gap + header)

def panel_wall(p, x0, x1, y0, y1, z0, z1, posts=1.2):
    """Glazed wall in a vertical plane from (x0,y0) to (x1,y1): frame, posts every `posts` m, mid rail, glass."""
    along_x = abs(x1 - x0) > abs(y1 - y0); n = max(1, round((abs(x1 - x0) if along_x else abs(y1 - y0)) / posts))
    zm = (z0 + z1) / 2
    def bar(a0, a1, za, zb):                 # bar along the wall between fractions a0..a1
        if along_x: p.box(x0 + (x1 - x0) * a0, x0 + (x1 - x0) * a1, y0 - FR / 2, y0 + FR / 2, za, zb, A)
        else:       p.box(x0 - FR / 2, x0 + FR / 2, y0 + (y1 - y0) * a0, y0 + (y1 - y0) * a1, za, zb, A)
    for z in (z0, zm - FR / 2, z1 - FR): bar(0, 1, z, z + FR)
    for k in range(n + 1):
        a = k / n; d = FR / (abs(x1 - x0) if along_x else abs(y1 - y0))
        bar(max(0, a - d / 2), min(1, a + d / 2), z0, z1)
    if along_x: p.box(min(x0, x1), max(x0, x1), y0 - 0.003, y0 + 0.003, z0 + FR, z1 - FR, GL)
    else:       p.box(x0 - 0.003, x0 + 0.003, min(y0, y1), max(y0, y1), z0 + FR, z1 - FR, GL)

pods = {}
for i in range(3):
    xa, xb = (P(pod_x0(i) + RACK_D, 0)[0], P(pod_x0(i) + RACK_D + HOT, 0)[0])        # hot aisle, world x
    ys, yn = P(0, ROW_Y0)[1], P(0, ROW_Y0 + ROW_LEN)[1]
    grp = hnode(f"fixed_hot_aisle_{i + 1}", ((xa + xb) / 2, (ys + yn) / 2, 0), C, root, role="fixed", tip="hot_aisle")
    w = Part(f"hot_aisle_{i + 1}_walls")
    for x in (xa, xb): panel_wall(w, x, x, ys, yn, TOP, CEIL)                       # above both rack rows
    for y in (ys, yn):
        panel_wall(w, xa, xb, y, y, TOP, CEIL, posts=HOT)                             # above the doors
        w.box(xa, xb, y - 0.06, y + 0.06, TOP - 0.06, TOP + 0.04, A)                  # door header + track
        for x in (xa, xb): w.box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0, TOP, A)  # door posts (on the rack corners)
    w.build(C, grp)
    for end, y, out in (("S", ys, -1), ("N", yn, 1)):                                 # sliding double doors, outside face
        yl = y + out * 0.078; half = (xb - xa) / 2
        for side, x0, x1, sgn in (("W", xa + 0.03, xa + half, -1), ("E", xa + half, xb - 0.03, 1)):
            hinge = (x0 if sgn < 0 else x1, yl, 0)
            d = Part(f"hot_aisle_{i + 1}_door_{end}_{side}", hinge)
            d.box(x0, x1, yl - 0.015, yl + 0.015, 0.02, 0.02 + FR, A); d.box(x0, x1, yl - 0.015, yl + 0.015, DOOR_H - FR, DOOR_H, A)
            d.box(x0, x0 + FR, yl - 0.015, yl + 0.015, 0.02, DOOR_H, A); d.box(x1 - FR, x1, yl - 0.015, yl + 0.015, 0.02, DOOR_H, A)
            d.box(x0 + FR, x1 - FR, yl - 0.004, yl + 0.004, 0.02 + FR, DOOR_H - FR, GL)
            hx = x1 - 0.07 if sgn < 0 else x0 + 0.07                                  # pull handle near the meeting edge
            d.box(hx - 0.012, hx + 0.012, yl + out * 0.015, yl + out * 0.045, 0.85, 1.25, M("M_DoorRubber"))
            d.box(hx - 0.012, hx + 0.012, yl - out * 0.045, yl - out * 0.015, 0.85, 1.25, M("M_DoorRubber"))
            o = d.build(C, grp)
            moving(o, "slide", "X", [0, -0.55] if sgn < 0 else [0, 0.55], tip="containment_door")
    v = Part(f"hot_aisle_{i + 1}_vents")                                              # roof extract vents over the aisle
    for k in range(5):
        cy = ys + ROW_LEN * (k + 0.5) / 5; cx = (xa + xb) / 2; hw, hl = 0.30, 0.45
        v.box(cx - hw - 0.03, cx + hw + 0.03, cy - hl - 0.03, cy + hl + 0.03, CEIL - 0.012, CEIL, M("M_VentGrey"))
        v.box(cx - hw, cx + hw, cy - hl, cy + hl, CEIL - 0.004, CEIL - 0.001, M("M_VentDark"))
        for s in range(-5, 6):
            v.box(cx - hw, cx + hw, cy + s * 0.08 - 0.008, cy + s * 0.08 + 0.008, CEIL - 0.06, CEIL - 0.012, M("M_VentGrey"))
    setp(v.build(C, grp), role="fixed", note="hot air extract vents")
    pods[f"hot_aisle_{i + 1}"] = {"x": [xa, xb], "y": [ys, yn], "rows": "ABCDEF"[2 * i:2 * i + 2]}
hall_layout("hot_aisles", pods)
print("HALL_CONTAINMENT_REPORT", {"tris": tris(C)})
hall_save()
