"""Asset 1 (polish v2) — chassis (fixed), lid (asset), air shroud (asset), blank brackets (assets),
I/O shield, standoffs, front control panel, bay numbers. Writes layout.json. MODEL-SPEC §8.1, §12."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())

if "Cube" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
sc = bpy.context.scene; sc.unit_settings.system = "METRIC"; sc.unit_settings.scale_length = 1.0

S = server_coll()
C = coll("chassis", S); L = coll("lid", S); SH = coll("shroud", S); BL = coll("blanks", S); SL = coll("slots", S)
for c in (C, L, SH, BL, SL): wipe(c)
root = server_root()

W, D, H = 0.438, 0.640, 0.0892
HW, T, IN, TOP = W / 2, 0.001, 0.213, 0.0882
BT = 0.0076
FAN_X = (-0.112, -0.022, 0.068)
PCIE_X = (-0.0765, -0.0968, -0.1171)            # ATX: card PCB at the bracket edge nearest the CPU/I-O, parts face away
HOOK_Y = (0.200, 0.400, 0.600)                  # lid studs (on the side walls) / J-slots (in the lid lips)
STUD_Z = 0.0800
BOARD_SCREWS = [(-0.192, 0.223), (-0.192, 0.420), (-0.192, 0.622), (-0.060, 0.223), (0.100, 0.223),
                (0.020, 0.335), (-0.060, 0.500), (0.060, 0.540), (0.100, 0.600), (-0.100, 0.420)]
IO_PORTS = [  # name, x0, x1, z0, z1, material  (board rear edge, read by 05_board.py)
    ("ps2_kb", -0.065, -0.050, BT, BT + 0.012, "M_IO_Purple"), ("ps2_ms", -0.065, -0.050, BT + 0.012, BT + 0.024, "M_IO_Green"),
    ("usb", -0.046, -0.032, BT, BT + 0.030, "M_EarAlu"), ("serial_1", -0.028, -0.006, BT, BT + 0.012, "M_IO_Blue"),
    ("serial_2", -0.002, 0.020, BT, BT + 0.012, "M_IO_Blue"), ("rj45", 0.026, 0.042, BT, BT + 0.028, "M_EarAlu"),
    ("audio", 0.046, 0.066, BT, BT + 0.040, "M_SlotBlack")]

def cut(target, x0, x1, y0, y1, z0, z1):
    import bmesh as _b
    p = Part("tmp_cut", (0, 0, 0)); p.box(x0, x1, y0, y1, z0, z1, M("M_Zinc")); cutter = p.build(C)
    mod = target.modifiers.new("cut", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = cutter; mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    for o in bpy.context.selected_objects: o.select_set(False)
    target.select_set(True); bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

def solo(name, boxes, mat, parent, origin=None):
    """One-material object from a list of boxes (world coords)."""
    p = Part(name, origin or (0, 0, 0))
    for b in boxes: p.box(*b, M(mat))
    return p.build(C if parent is None or parent.name.startswith("fixed") else parent.users_collection[0], parent)

FX = fixed("chassis", C)

# ---------- tray: bottom + side walls with L-shaped lid slots ----------
solo("tray_bottom", [(-HW, HW, 0, D, 0, T)], "M_ShellGrey", FX)
for s, side in ((-1, "L"), (1, "R")):
    xa, xb = sorted((s * HW, s * (HW - T)))
    wall = solo(f"tray_side_{side}", [(xa, xb, 0, D, T, TOP)], "M_ShellGrey", FX)
    st = Part(f"lid_studs_{side}")                     # riveted studs pressed out of the wall (nothing inside the chassis)
    for yh in HOOK_Y:
        st.cyl((0, yh, STUD_Z), "X", *sorted((s * HW, s * (HW + 0.0011))), 0.0015, M("M_Zinc"), 12)       # shank through the lip slot
        st.cyl((0, yh, STUD_Z), "X", *sorted((s * (HW + 0.0006), s * (HW + 0.0012))), 0.0026, M("M_Zinc"), 16)  # head outside the lip
    st.build(C, FX)

# ---------- drive cage + bay numbers 0-23 ----------
solo("cage", [(-IN, IN, 0, 0.115, 0.083, 0.084), (-0.0720, -0.0710, 0, 0.115, T, 0.083), (0.0710, 0.0720, 0, 0.115, T, 0.083),
              (-HW + T, -IN, 0, 0.115, T, TOP), (IN, HW - T, 0, 0.115, T, TOP),
              (-HW + T, HW - T, -0.002, 0, 0.083, TOP), (-HW + T, HW - T, -0.002, 0, T, 0.0055)], "M_CaddyBlack", FX)
BAYS = (-0.213, -0.071, 0.072)
slots = {}
n = 0
for bx in BAYS:
    for k in range(8):
        x = bx + 0.0175 * (k + 0.5)
        text_obj(f"bay_label_{n:02d}", str(n), 0.0028, M("M_LabelWhite"), (x, -0.00205, 0.0032), C, FX,
                 rot=(math.radians(90), 0, 0))
        slots[f"slot_caddy_{n+1:02d}"] = [round(x, 5), 0.0, 0.044]; n += 1

# ---------- rack ears + loop handles + front control panel (right ear) ----------
for s, side in ((-1, "L"), (1, "R")):
    xa, xb = sorted((s * HW, s * 0.237)); hx0, hx1 = sorted((s * 0.223, s * 0.233))
    solo(f"ear_{side}", [(xa, xb, -0.004, 0, 0, H), (hx0, hx1, -0.022, -0.004, 0.068, 0.074),
                         (hx0, hx1, -0.022, -0.004, 0.046, 0.052), (hx0, hx1, -0.022, -0.016, 0.046, 0.074)], "M_EarAlu", FX)
pb = Part("ctrl_power_button", (0.228, -0.0040, 0.034)); pb.cyl((0.228, 0, 0.034), "Y", -0.0058, -0.0040, 0.0030, M("M_ChipBlack"), 16)
moving(pb.build(C, FX), "press", "Y", [0.0, 0.0012], tip="ctrl_power")
rb = Part("ctrl_reset_button", (0.228, -0.0040, 0.026)); rb.cyl((0.228, 0, 0.026), "Y", -0.0043, -0.0040, 0.0012, M("M_ChipBlack"), 10)
moving(rb.build(C, FX), "press", "Y", [0.0, 0.0006], tool="pin", tip="ctrl_reset")
for i, (nm, mat) in enumerate((("power", "M_LEDGreen"), ("hdd", "M_LEDAmber"), ("nic1", "M_LEDGreen"),
                               ("nic2", "M_LEDGreen"), ("overheat", "M_LEDRed"), ("powerfail", "M_LEDRed"))):
    x = 0.2245 if i % 2 == 0 else 0.2315; z = 0.018 - (i // 2) * 0.0045
    led = Part(f"ctrl_led_{nm}", (x, -0.0042, z)); led.cyl((x, 0, z), "Y", -0.0044, -0.0040, 0.0011, M(mat), 8)
    setp(led.build(C, FX), role="indicator", tip=f"led_{nm}")

# ---------- fan bracket (3 holes, SATA cable notch, shroud groove) ----------
fb = solo("fan_bracket", [(-IN, 0.114, 0.200, 0.202, T, 0.086)], "M_Zinc", FX)
for x in FAN_X:
    p = Part("tmp_hole"); p.cyl((x, 0, 0.043), "Y", 0.195, 0.207, 0.037, M("M_Zinc"), 24); h = p.build(C)
    mod = fb.modifiers.new("h", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.object = h; mod.solver = "EXACT"
    bpy.context.view_layer.objects.active = fb; bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(h, do_unlink=True)
cut(fb, -0.209, -0.159, 0.195, 0.207, 0.080, 0.090)                       # SATA notch
solo("shroud_grooves", [(-0.0735, -0.0725, 0.202, 0.2045, 0.040, 0.086), (-0.0705, -0.0695, 0.202, 0.2045, 0.040, 0.086),
                        (-0.0735, -0.0725, 0.6355, 0.638, 0.040, 0.086), (-0.0705, -0.0695, 0.6355, 0.638, 0.040, 0.086)],
     "M_Zinc", FX)

# ---------- rear wall: open-top bracket openings, I/O opening, PSU bay; ledge; lid screw flange ----------
rw = solo("rear_wall", [(-HW + T, HW - T, 0.638, D, T, TOP)], "M_Zinc", FX)
cut(rw, -0.2155, -0.073, 0.630, 0.650, 0.010, TOP + 0.001)                # 7 bracket openings (20.3 mm pitch) above a 9 mm bottom lip
cut(rw, -0.069, 0.105, 0.630, 0.650, 0.006, 0.054)                         # I/O opening
cut(rw, 0.115, 0.213, 0.630, 0.650, T, 0.082)                              # PSU bay
solo("bracket_band", [(-0.2155, -0.073, 0.6397, 0.6450, 0.0810, 0.0847)], "M_Zinc", FX)  # smooth top band the tabs fold over
for k in range(1, 8):                                                      # tongue slot in the bottom lip for each bracket
    xc = -0.073 - (k - 1) * 0.0203 - 0.01015
    cut(rw, xc - 0.0068, xc + 0.0068, 0.630, 0.650, 0.0050, 0.0101)
solo("lid_screw_flange", [(-0.012, -0.002, 0.631, 0.638, 0.0872, TOP), (0.002, 0.012, 0.631, 0.638, 0.0872, TOP),
                          (-0.002, 0.002, 0.631, 0.6325, 0.0872, TOP), (-0.002, 0.002, 0.6365, 0.638, 0.0872, TOP)], "M_Zinc", FX)
# I/O shield + ports: built by 12_rear_io.py

# ---------- motherboard standoffs ----------
sp = Part("board_standoffs")
for (x, y) in BOARD_SCREWS:
    sp.cyl((x, y, 0), "Z", T, 0.006, 0.0028, M("M_Zinc"), 6)
sp.build(C, FX)

# ---------- blank brackets 2-7 (assets, 1 screw each) ----------
FILLED = {1: "nic", 2: "accel"}                              # openings owned by real cards (no blank)
for k in [k for k in range(1, 8) if k not in FILLED]:
    x1 = -0.073 - (k - 1) * 0.0203; x0 = x1 - 0.0203; xc = (x0 + x1) / 2      # full pitch, 0.25 mm inset each side
    a = asset(f"blank_{k}", (xc, 0.6390, 0.0450), BL, pull=[[0, 0, 0.10]], requires=f"blank_{k}_screw",
              tip="blank_bracket")
    p = Part(f"blank_{k}_plate"); p.box(x0 + 0.00025, x1 - 0.00025, 0.6385, 0.6395, 0.0100, 0.0847, M("M_Zinc"))
    p.box(x0 + 0.00025, x1 - 0.00025, 0.6385, 0.6450, 0.0847, 0.0855, M("M_Zinc"))                     # tab folded over the top band
    p.box(xc - 0.0065, xc + 0.0065, 0.6385, 0.6395, 0.0070, 0.0100, M("M_Zinc"))                     # bottom tongue (wide) ...
    p.box(xc - 0.0050, xc + 0.0050, 0.6385, 0.6395, 0.0055, 0.0070, M("M_Zinc"))                     # ... chamfered end, sits in the lip slot
    pl = p.build(BL, a)
    cut(pl, xc + 0.0020, xc + 0.0045, 0.630, 0.650, 0.018, 0.075)                                  # blank: long vent slot
    for (z0, z1) in ((0.012, 0.022), (0.027, 0.037), (0.042, 0.052), (0.057, 0.067), (0.072, 0.080)):
        cut(pl, xc - 0.0055, xc - 0.0030, 0.630, 0.650, z0, z1)                                    # blank: short vent slots
    sc_ = screw(f"blank_{k}_screw", screw_mesh("screw_bracket", 0.0022, 0.0018, "phillips"), (xc, 0.6425, 0.0855), BL, a)
    fastener(sc_, "phillips_2", turns=3, rise=0.003)
    slots[f"slot_blank_{k}"] = [round(xc, 5), 0.6390, 0.0450]

# ---------- lid (asset): panel, lips with hooks, 2 release tabs, rear lock screw ----------
LO = (0.0, 0.0, H)
lid = asset("lid", LO, L, pull=[[0, 0.015, 0], [0, 0, 0.06]], requires="lid_tab_L,lid_tab_R,lid_screw",
            tip="lid")
p = Part("lid_panel"); p.box(-0.2195, 0.2195, 0, D, TOP, H, M("M_ShellGrey")); p.build(L, lid)
for s, side in ((-1, "L"), (1, "R")):                  # lips with J-slots: closed = stud in the run; slide back 15 mm -> exit
    lp = Part(f"lid_lip_{side}"); lp.box(*sorted((s * 0.219, s * 0.2195)), 0, D, 0.074, TOP, M("M_ShellGrey"))
    lip = lp.build(L, lid)
    for yh in HOOK_Y:
        cut(lip, -0.25 if s < 0 else 0.21, -0.21 if s < 0 else 0.25, yh - 0.0168, yh + 0.0019, STUD_Z - 0.0018, STUD_Z + 0.0018)  # run
        cut(lip, -0.25 if s < 0 else 0.21, -0.21 if s < 0 else 0.25, yh - 0.0168, yh - 0.0132, 0.0730, STUD_Z + 0.0018)          # open exit
for s, side in ((-1, "L"), (1, "R")):
    x0, x1 = sorted((s * 0.150, s * 0.170))
    t = Part(f"lid_tab_{side}", ((x0 + x1) / 2, 0.0275, H)); t.box(x0, x1, 0.020, 0.035, H, H + 0.0010, M("M_Zinc"))
    moving(t.build(L, lid), "press", "Z", [0.0, -0.0008], tip="lid_tab")
ls_ = screw("lid_screw", screw_mesh("screw_lid", 0.0030, 0.0018, "phillips", shaft=(0.0015, H - 0.0872)), (0, 0.6345, H), L, lid)
fastener(ls_, "phillips_2", turns=4, rise=0.005, optional=True)

# ---------- air shroud (asset, the "divider" in the reference) ----------
sh = asset("shroud", (-0.0715, 0.420, 0.086), SH, pull=[[0, 0, 0.10]], tip="air_shroud")
p = Part("shroud_wall"); p.box(-0.0720, -0.0710, 0.2030, 0.6375, 0.012, 0.086, M("M_Zinc")); p.build(SH, sh)

# ---------- slot markers ----------
for i, x in enumerate(FAN_X):
    slots[f"slot_fan_{i+1:02d}"] = [x, 0.1825, 0.085]
SOCK = ((-0.024, 0.270), (0.064, 0.285))
for i, (x, y) in enumerate(SOCK):
    slots[f"slot_cpu_{i+1}"] = [x, y, 0.0094]; slots[f"slot_hs_{i+1}"] = [x, y, 0.0139]
for i in range(8):
    slots[f"slot_dimm_{i+1:02d}"] = [round(0.020 + 0.00325 + i * 0.0105, 5), 0.431, 0.0096]
for i, x in enumerate(PCIE_X):
    slots[f"slot_pcie_{i+1}"] = [x, 0.5845, BT]
slots["slot_nic"] = [PCIE_X[0], 0.5845, BT + 0.003]
slots["slot_lid"] = list(LO); slots["slot_shroud"] = [-0.0715, 0.420, 0.086]
for k, v in slots.items():
    e = bpy.data.objects.new(k, None); e.empty_display_type = "ARROWS"; e.empty_display_size = 0.008
    SL.objects.link(e); place(e, v, root)

_old = load_layout()                     # merge: keep keys/slots written by later scripts (board, backplane, ...)
_new = {
    "units": "metres", "axes": "Blender Z-up, front faces -Y, origin front-bottom-middle",
    "body": {"W": W, "D": D, "H": H, "W_incl_ears": 0.474},
    "inner": {"half_width": IN, "lid_underside": TOP, "board_top": BT},
    "fan_x": FAN_X, "pcie_x": PCIE_X, "shroud_x": [-0.072, -0.071], "psu_cage_x": [0.115, 0.213],
    "board_screws": BOARD_SCREWS, "io_ports": IO_PORTS, "sockets": SOCK,
}
_new["slots"] = {**_old.get("slots", {}), **slots}
save_layout({**_old, **_new})
# Working view: lid set down beside the server (its slot marker still holds the fitted position)
LID_ASIDE = True
if LID_ASIDE:
    lid.location = (0.50, 0.0, H - 0.074 + 0.0005)   # lips resting on the table, right of the server

print("CHASSIS_REPORT", {"chassis": tris(C), "lid": tris(L), "shroud": tris(SH), "blanks": tris(BL), "slots": len(slots)})
save()
