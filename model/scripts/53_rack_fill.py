"""Lab 53 — rack contents. Low-poly stand-in of our 2U server (16 triangles: body box + baked front/rear faces from
53a_bake_server_faces.py, alpha-clipped so the ears/handles read), 1U switches (port grid texture, one blue as in the
lab photo), 1U patch panels, black blanking panels, and a slot marker for every 2U server position.
Rack servers are shared-mesh copies (instance in the app). Fronts face +Y; the server's own front faces -Y, so each
copy is turned 180 deg about Z (in the row frame; the row root turns it onto the west wall). Rack servers are `asset_rack_N_srv_uNN` (pull out of the front on rails)."""
import bpy, math, numpy as np
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
exec(open(os.path.join(HERE, "_lab.py")).read())
C = lab_coll("rack_fill"); wipe(C)
lay = load_layout()["lab_racks"]; U = 0.04445
# Rack coords are in the row frame: place everything with the row root at the origin, then put it back on the wall.
ROW = bpy.data.objects["fixed_racks"]; _loc, _rot = tuple(ROW.location), tuple(ROW.rotation_euler)
ROW.location = (0, 0, 0); ROW.rotation_euler = (0, 0, 0); bpy.context.view_layer.update()

# ---------- low-poly server mesh (server frame: front at y=0 facing -Y, origin front-bottom-middle) ----------
mf = tex_material("M_RackSrvFront", os.path.join(TEX, "rack_server_front.png"), rough=0.5, alpha_clip=True)
mr = tex_material("M_RackSrvRear", os.path.join(TEX, "rack_server_rear.png"), rough=0.5, alpha_clip=True)
s = Part("rack_server_lp")
s.box(-0.219, 0.219, 0.0, 0.640, 0.0, 0.0892, M("M_ShellGrey"))
ZB, ZT = 0.0446 - 0.045, 0.0446 + 0.045
tquad(s, [(-0.24, -0.006, ZB), (0.24, -0.006, ZB), (0.24, -0.006, ZT), (-0.24, -0.006, ZT)], [(0, 0), (1, 0), (1, 1), (0, 1)], mf)
tquad(s, [(0.24, 0.6415, ZB), (-0.24, 0.6415, ZB), (-0.24, 0.6415, ZT), (0.24, 0.6415, ZT)], [(0, 0), (1, 0), (1, 1), (0, 1)], mr)
SRV = s.mesh()

# ---------- 1U textures: switch (black / blue), patch panel ----------
def ports_tex(name, bg, rows=2, cols=24, sfp=4, leds=True):
    w, h = 512, 48; img = np.ones((h, w, 4)); img[:, :, :3] = bg
    x0 = 40
    for c in range(cols):
        for r in range(rows):
            px = x0 + c * 16 + (c // 6) * 6; py = 6 + r * 20
            img[py:py + 14, px:px + 13, :3] = 0.05; img[py + 1:py + 3, px + 4:px + 9, :3] = 0.25
            if leds and (c * 7 + r * 3) % 5: img[py - 2 if r == 0 else py + 15:(py - 1 if r == 0 else py + 16), px + 1:px + 4, :3] = [0.2, 0.9, 0.3]
    for k in range(sfp):
        px = 455 + (k % 2) * 26; py = 8 + (k // 2) * 18; img[py:py + 12, px:px + 22, :3] = 0.12
    img[20:28, 12:20, :3] = [0.2, 0.9, 0.3]
    return save_png(name, img)
tex_material("M_SwitchBlack", ports_tex("lab_switch_black", [0.10, 0.10, 0.11]), rough=0.5)
tex_material("M_SwitchBlue", ports_tex("lab_switch_blue", [0.12, 0.32, 0.80]), rough=0.45)
tex_material("M_PatchPanel", ports_tex("lab_patch", [0.07, 0.07, 0.08], rows=1, cols=24, sfp=0, leds=False), rough=0.5)

_bl = Part("rack_blank_1u")                                                     # shared 1U blanking-panel mesh (origin: bottom centre, rail plane)
_bl.box(-0.2413, 0.2413, 0.0005, 0.0025, 0.0004, U - 0.0004, M("M_RackBlack"))
_bl.box(-0.20, 0.20, 0.0025, 0.0035, 0.018, 0.026, M("M_RackRail"))
BLANK = _bl.mesh()

def unit_box(name, m_front, depth, nU=1, ears=True):
    p = Part(name); hgt = nU * U - 0.0008
    p.box(-0.219, 0.219, 0.0, depth, 0.0004, hgt, M("M_RackBlack"))
    tquad(p, [(-0.2413 if ears else -0.219, -0.002, 0.0004), (0.2413 if ears else 0.219, -0.002, 0.0004),
              (0.2413 if ears else 0.219, -0.002, hgt), (-0.2413 if ears else -0.219, -0.002, hgt)], [(0, 0), (1, 0), (1, 1), (0, 1)], m_front)
    return p.mesh()
SW_K, SW_B = unit_box("rack_switch_black", M("M_SwitchBlack"), 0.40), unit_box("rack_switch_blue", M("M_SwitchBlue"), 0.40)
PATCH = unit_box("rack_patch_panel", M("M_PatchPanel"), 0.12)

FILL = {   # U numbers: servers (2U, bottom U), switches, patch panels, empty 2U slots (marked, no blank)
    "rack_1": {"srv": [], "sw": [], "patch": [], "empty": [], "bare": True},                  # door cabinet: left empty
    # 3 identical open frames: switch at U42, blanking everywhere else, every 2U position marked as a server slot
    **{rk: {"srv": [], "sw": [(42, "k")], "patch": [], "empty": [], "slots_all": True} for rk in ("rack_2", "rack_3", "rack_4")},
}
count = 0
for rk, spec in FILL.items():
    L = lay[rk]; cx, fy = L["cx"], L["front_rail_y"]; z0 = L["u1_z"]; grp = bpy.data.objects[f"fixed_{rk}"]
    used = set()
    def uz(u): return z0 + (u - 1) * U
    for u in spec["srv"]:
        o = bpy.data.objects.new(f"asset_{rk}_srv_u{u:02d}", SRV); C.objects.link(o)
        place(o, (cx, fy - 0.003, uz(u)), grp); o.rotation_euler = (0, 0, math.pi)
        req = f"{rk}_door_front" if L["kind"] == "cabinet_doors" else ""
        setp(o, role="asset", tip="rack_server", rack=rk, u=u, size_u=2, pull=[[0, 0.70, 0]], pull_frame="fixed_racks", requires=req,
             note="low-poly stand-in for server.glb; swap to the detailed model when pulled")
        used |= {u, u + 1}; count += 1
    for (u, col) in spec["sw"]:
        o = bpy.data.objects.new(f"{rk}_switch_u{u:02d}", SW_B if col == "b" else SW_K); C.objects.link(o)
        place(o, (cx, fy - 0.002, uz(u)), grp); o.rotation_euler = (0, 0, math.pi); setp(o, role="fixed", tip="switch", u=u)
        used.add(u)
    for u in spec["patch"]:
        o = bpy.data.objects.new(f"{rk}_patch_u{u:02d}", PATCH); C.objects.link(o)
        place(o, (cx, fy - 0.002, uz(u)), grp); o.rotation_euler = (0, 0, math.pi); setp(o, role="fixed", tip="patch_panel", u=u)
        used.add(u)
    # every U (1-42): a marker on the front rail plane (bottom of the U) so the app can address single units
    for u in range(1, 43):
        lnode(f"u_{rk}_{u:02d}", (cx, fy, uz(u)), C, grp, role="rack_unit", rack=rk, u=u, height=round(U, 5),
              note="bottom edge of this U on the front rails")
    if spec.get("slots_all"):                                                  # 2U server slots behind removable blanks
        for u in range(1, 41, 2):
            lnode(f"slot_{rk}_u{u:02d}", (cx, fy - 0.003, uz(u)), C, grp, role="slot", accepts="server", rack=rk, u=u, size_u=2,
                  filled=False, facing="+Y", requires=f"asset_{rk}_blank_u{u:02d},asset_{rk}_blank_u{u + 1:02d}",
                  note="remove both 1U blanks first; server slides in from the front (+Y in the row frame)")
    for u in spec["srv"] + spec["empty"]:
        lnode(f"slot_{rk}_u{u:02d}", (cx, fy - 0.003, uz(u)), C, grp, role="slot", accepts="server", rack=rk, u=u, size_u=2,
              filled=u in spec["srv"], facing="+Y")
    for u in spec["empty"]: used |= {u, u + 1}
    if spec.get("bare"): continue                                              # empty rack: rails only, no blanks
    for u in range(1, 43):                                                     # 1U tool-less blanking panels, each removable
        if u in used: continue
        o = bpy.data.objects.new(f"asset_{rk}_blank_u{u:02d}", BLANK); C.objects.link(o)
        place(o, (cx, fy, uz(u)), grp)
        setp(o, role="asset", tip="blanking_panel", rack=rk, u=u, size_u=1, pull=[[0, 0.04, 0]], pull_frame="fixed_racks",
             note="tool-less 1U blank: squeeze the clips, pull straight out")
ROW.location = _loc; ROW.rotation_euler = _rot
print("FILL_REPORT", {"servers": count, "tris": tris(C)})
lab_save()
