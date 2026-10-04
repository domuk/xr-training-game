"""Hall 78 — carts and media destruction devices (research/reference/LOG.md sections 5-10; owner placement 2026-10-04:
along the south wall between the two doors). Generic, no branding. Real size. Each device is built in its own frame
(front faces -Y, origin = centre of its footprint on the floor) under one root, then the root is placed and turned
to face north into the room.
  - laptop crash cart (x1): star base on castors, column, height-adjustable lift (worksurface for a laptop, monitor on a
    VESA mount, keyboard tray sliding out, mouse tray sliding sideways), UPS in the holder on the column.
  - tool crash cart (x2): tool chest on castors with drawers (pull out) and an open bottom shelf, worksurface top that
    can hold a server (slot), pole at the back with a monitor.
  - red trolley (x1): 3-shelf red steel trolley on castors with a push handle; carries the degausser and the crusher.
  - degausser 248 x 629 x 430: drawer at the top front slides out; drop a drive in, close, it erases, take it out.
  - drive crusher 191 x 474 x 378: safety window over the chamber slides up into the unit; a V-shaped ram on a piston comes
    down onto a V anvil and bends the drive into a V; DESTROY button (press), POWER lamp, LCD.
Moving parts carry motion / axis / limits like the lab; drive positions are slot_* empties."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
hall_open()
C = hall_coll("devices"); wipe(C); root = hfixed("devices", C)
_MAT_DEFS.update({
    "M_CartGrey": ("#B4B8BC", 0.45, 0.4), "M_CartSilver": ("#C9CCCF", 0.3, 0.9), "M_CartBlack": ("#1C1D1F", 0.5, 0.2),
    "M_BumperOrange": ("#E8661C", 0.6, 0), "M_TrolleyRed": ("#B8141B", 0.35, 0.3), "M_MatBlack": ("#202020", 0.9, 0),
    "M_DegGrey": ("#44474A", 0.75, 0.3), "M_CrushBlack": ("#161718", 0.6, 0.2), "M_ScreenDark": ("#0B1220", 0.15, 0),
    "M_KeyBlack": ("#141414", 0.6, 0), "M_TyreBlack": ("#151515", 0.8, 0), "M_HubRed": ("#A0141A", 0.4, 0.2),
    "M_Steel": ("#B9BDC1", 0.3, 1.0), "M_LCDGreen": ("#8FCB3A", 0.4, 0), "M_SwitchRed": ("#C8202A", 0.4, 0), "M_CommHole": ("#050506", 0.9, 0),
})
def clear_glass(name="M_DeviceGlass", hexcol="#DCE6EA", alpha=0.25):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"); lin = _lin(hexcol)
    b.inputs["Base Color"].default_value = (*lin, 1); b.inputs["Roughness"].default_value = 0.05; b.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*lin, alpha)
    try: m.surface_render_method = "BLENDED"
    except Exception: m.blend_method = "BLEND"
    return m

def bar(p, a, b, z0, z1, w, m):
    """Level bar from plan point a to b, width w, z0..z1."""
    d = Vector(b) - Vector(a); mtx = Matrix.Translation((a[0], a[1], 0)) @ Matrix.Rotation(math.atan2(d.y, d.x), 4, "Z")
    p.box(0, d.length, -w / 2, w / 2, z0, z1, m, mtx)

def castor(p, x, y, r, hub="M_CartGrey", brake=False):
    """Swivel castor: top plate, fork, wheel (axle along X); wheel touches the floor."""
    p.box(x - 0.03, x + 0.03, y - 0.03, y + 0.03, 2 * r + 0.012, 2 * r + 0.018, M("M_Steel"))
    for s in (-1, 1): p.box(x + s * (0.012 + 0.003) - 0.003, x + s * (0.012 + 0.003) + 0.003, y - 0.012, y + 0.012, r, 2 * r + 0.012, M("M_Steel"))
    p.cyl((0, y, r), "X", x - 0.012, x + 0.012, r, M("M_TyreBlack"), 14)
    p.cyl((0, y, r), "X", x - 0.0125, x + 0.0125, r * 0.55, M(hub), 10)
    if brake: p.box(x - 0.02, x + 0.02, y - 0.045, y - 0.012, 2 * r - 0.01, 2 * r + 0.004, M(hub))

def node(name, loc, parent, **props):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.05; C.objects.link(e); place(e, loc, parent); setp(e, **props); return e

def finish(r, loc, rot_z=math.pi):
    r.location = loc; r.rotation_euler = (0, 0, rot_z)

# ======================= laptop crash cart =======================
def laptop_cart(name):
    r = node(f"asset_{name}", (0, 0, 0), root, role="asset", tip="crash_cart_laptop",
             note="laptop crash cart: laptop on the worksurface, monitor, keyboard + mouse trays, UPS; height adjusts")
    G, S, K = M("M_CartGrey"), M("M_CartSilver"), M("M_CartBlack")
    b = Part(f"{name}_base")
    for (cx_, cy_) in ((0.30, -0.26), (-0.30, -0.26), (0.30, 0.26), (-0.30, 0.26)):     # star base, castors at the leg ends
        bar(b, (0, 0.04), (cx_, cy_), 0.085, 0.115, 0.06, G); castor(b, cx_, cy_, 0.035)
    b.box(-0.13, 0.13, -0.14, 0.10, 0.115, 0.125, K)                                 # black foot plate
    b.box(-0.05, 0.05, 0.00, 0.08, 0.115, 0.78, G)                                    # lower column (outer sleeve)
    b.box(0.05, 0.16, -0.10, 0.17, 0.15, 0.47, K)                                     # UPS in the holder on the column side
    b.box(0.05, 0.16, -0.102, -0.10, 0.40, 0.44, M("M_TVBlack")); b.cyl((0.13, 0, 0.42), "Y", -0.104, -0.101, 0.006, M("M_LEDGreen"), 8)
    b.box(0.045, 0.165, -0.11, 0.18, 0.13, 0.15, S)                                   # holder strap
    b.build(C, r)
    lift = node(f"{name}_lift", (0, 0, 0), r)
    moving(lift, "slide", "Z", [-0.30, 0.33], tip="crash_cart_height", note="counterbalanced, tool-free: 63 cm of travel")
    L = Part(f"{name}_lift_parts")
    L.box(-0.035, 0.035, 0.015, 0.065, 0.70, 1.48, S)                                  # inner column
    L.box(-0.30, 0.30, -0.44, 0.03, 1.00, 1.02, G)                                     # worksurface (laptop goes here)
    L.box(-0.07, 0.07, -0.43, -0.39, 1.0195, 1.0205, K)                                # handle slot at the front
    L.box(-0.05, 0.05, -0.05, 0.015, 1.24, 1.34, K)                                    # VESA mount
    L.box(-0.28, 0.28, -0.08, -0.05, 1.18, 1.52, K)                                    # monitor
    L.box(-0.265, 0.265, -0.0805, -0.0795, 1.195, 1.505, M("M_ScreenDark"))            # screen (faces the front)
    L.box(-0.20, 0.20, -0.30, -0.04, 0.955, 0.97, G)                                   # keyboard tray runners under the top
    L.build(C, lift)
    kt = Part(f"{name}_keyboard_tray", (0, -0.30, 0.93))
    kt.box(-0.32, 0.10, -0.56, -0.30, 0.925, 0.94, G); kt.box(-0.30, 0.06, -0.54, -0.40, 0.94, 0.962, M("M_KeyBlack"))   # tray + keyboard
    o = kt.build(C, lift); moving(o, "slide", "-Y", [0, 0.12], tip="keyboard_tray")
    mt = Part(f"{name}_mouse_tray", (0.10, -0.43, 0.92))
    mt.box(0.10, 0.30, -0.55, -0.33, 0.912, 0.92, G); mt.box(0.18, 0.24, -0.47, -0.39, 0.92, 0.95, M("M_KeyBlack"))      # tray + mouse
    o = mt.build(C, lift); moving(o, "slide", "X", [0, 0.18], tip="mouse_tray")
    node(f"slot_{name}_laptop", (0, -0.20, 1.02), lift, role="slot", tip="laptop_place", note="put your work laptop here")
    return r

# ======================= tool crash cart =======================
def tool_cart(name):
    r = node(f"asset_{name}", (0, 0, 0), root, role="asset", tip="crash_cart_tools",
             note="tool crash cart: tools in the drawers, a server can sit on the top, monitor on the pole")
    K, S, O = M("M_CartBlack"), M("M_CartSilver"), M("M_BumperOrange")
    W2, D2, Z0, Z1 = 0.475, 0.30, 0.15, 0.98
    b = Part(f"{name}_body")
    b.box(-W2, W2, -D2, D2, Z0 - 0.03, Z0, K)                                           # base frame
    for (cx_, cy_, br) in ((W2 - 0.08, -D2 + 0.08, True), (-W2 + 0.08, -D2 + 0.08, True), (W2 - 0.08, D2 - 0.08, False), (-W2 + 0.08, D2 - 0.08, False)):
        castor(b, cx_, cy_, 0.055, "M_CartBlack", br)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):                               # orange corner bumpers
        b.box(sx * W2 - 0.04 if sx < 0 else W2 - 0.06, sx * W2 + 0.06 if sx < 0 else W2 + 0.04,
              sy * D2 - 0.04 if sy < 0 else D2 - 0.06, sy * D2 + 0.06 if sy < 0 else D2 + 0.04, Z0 - 0.05, Z0, O)
    b.box(-W2, -W2 + 0.02, -D2, D2, Z0, Z1, K); b.box(W2 - 0.02, W2, -D2, D2, Z0, Z1, K)  # sides
    b.box(-W2, W2, D2 - 0.02, D2, Z0, Z1, K)                                            # back
    b.box(-W2 - 0.005, W2 + 0.005, -D2 - 0.005, D2 + 0.005, Z1, Z1 + 0.02, K)           # worksurface top
    b.box(-W2 + 0.02, W2 - 0.02, -D2, D2 - 0.02, Z0, Z0 + 0.015, M("M_MatBlack"))      # open bottom shelf
    b.box(-W2 + 0.02, W2 - 0.02, -D2 + 0.02, D2 - 0.02, 0.37, 0.385, K)                 # shelf above the open bay
    for sx in (-1, 1):                                                                  # rubber side handles
        b.box(sx * (W2 + 0.035) - 0.015, sx * (W2 + 0.035) + 0.015, -0.12, 0.12, 0.80, 0.83, M("M_TyreBlack"))
        for yy in (-0.11, 0.11): b.box(min(sx * W2, sx * (W2 + 0.035)) - 0.01, max(sx * W2, sx * (W2 + 0.035)) + 0.01, yy - 0.01, yy + 0.01, 0.80, 0.83, M("M_TyreBlack"))
    b.box(W2 - 0.10, W2 - 0.05, D2 - 0.08, D2 - 0.03, Z1 + 0.02, 1.85, S)               # pole at the back right
    b.box(0.0, W2 - 0.10, D2 - 0.07, D2 - 0.04, 1.42, 1.46, S)                          # monitor arm
    b.box(-0.05, 0.05, D2 - 0.10, D2 - 0.07, 1.38, 1.50, K)                             # VESA plate
    b.box(-0.28, 0.28, D2 - 0.13, D2 - 0.10, 1.29, 1.62, K)                             # monitor
    b.box(-0.265, 0.265, D2 - 0.1305, D2 - 0.1295, 1.305, 1.605, M("M_ScreenDark"))
    b.build(C, r)
    DRAWERS = [(0.86, 0.96), (0.73, 0.85), (0.58, 0.72), (0.40, 0.57)]                  # top shallow ... bottom deep
    for i, (za, zb) in enumerate(DRAWERS):
        d = Part(f"{name}_drawer_{i + 1}", (0, -D2, za))
        d.box(-W2 + 0.025, W2 - 0.025, -D2 - 0.02, -D2, za + 0.004, zb - 0.004, K)       # front
        d.box(-0.20, 0.20, -D2 - 0.045, -D2 - 0.035, zb - 0.035, zb - 0.020, S)          # pull bar
        for x in (-0.20, 0.20): d.box(x - 0.006, x + 0.006, -D2 - 0.04, -D2 - 0.02, zb - 0.035, zb - 0.020, S)
        d.box(-W2 + 0.03, W2 - 0.03, -D2, D2 - 0.05, za + 0.006, za + 0.012, M("M_MatBlack"))      # drawer floor
        for x in (-W2 + 0.03, W2 - 0.04): d.box(x, x + 0.01, -D2, D2 - 0.05, za + 0.006, zb - 0.02, K)   # drawer sides
        d.box(-W2 + 0.03, W2 - 0.03, D2 - 0.06, D2 - 0.05, za + 0.006, zb - 0.02, K)    # drawer back
        o = d.build(C, r); moving(o, "slide", "-Y", [0, 0.40], tip="tool_drawer", holds="tools")
    node(f"slot_{name}_server", (0, 0, Z1 + 0.02), r, role="slot", tip="crash_cart_server", note="a 2U server can sit on the top")
    return r

# ======================= degausser =======================
def degausser(name, parent):
    r = node(f"asset_{name}", (0, 0, 0), parent, role="asset", tip="degausser",
             note="drawer out, drop a drive in, close, it erases the drive, drawer out, take the drive out")
    G, K = M("M_DegGrey"), M("M_CrushBlack"); w, d, h = 0.124, 0.3145, 0.430
    b = Part(f"{name}_body")
    for (fx, fy) in ((-0.09, -0.27), (0.09, -0.27), (-0.09, 0.27), (0.09, 0.27)): b.cyl((fx, fy, 0), "Z", 0.0, 0.012, 0.012, M("M_TyreBlack"), 10)
    b.box(-w, w, -d + 0.002, d, 0.012, h, G)                                            # cabinet
    b.box(-w + 0.002, w - 0.002, -d, -d + 0.002, 0.014, h - 0.002, G)                   # front panel
    b.box(-0.080, 0.080, -d - 0.004, -d, 0.295, 0.395, K)                              # drawer surround plate
    b.box(-0.068, 0.068, -d - 0.0045, -d - 0.004, 0.306, 0.384, M("M_CommHole"))        # drawer opening
    b.box(-0.095, -0.075, -d - 0.006, -d, 0.180, 0.205, M("M_SwitchRed"))                  # power switch
    b.box(-0.010, 0.080, -d - 0.004, -d, 0.170, 0.205, K)                               # LCD bezel
    b.box(-0.004, 0.074, -d - 0.0045, -d - 0.004, 0.176, 0.199, M("M_LCDGreen"))        # LCD
    for x in (-w + 0.008, w - 0.008):                                                   # screw heads round the front
        for z in (0.04, 0.22, 0.40): b.cyl((x, 0, z), "Y", -d - 0.002, -d, 0.003, M("M_Screw"), 6)
    b.build(C, r)
    dr = Part(f"{name}_drawer", (0, -d, 0.34))
    dr.box(-0.066, 0.066, -d - 0.008, -d - 0.004, 0.308, 0.382, K)                      # drawer front
    dr.box(-0.040, 0.040, -d - 0.022, -d - 0.008, 0.365, 0.375, K)                      # pull lip
    dr.box(-0.060, 0.060, -d - 0.004, -0.02, 0.312, 0.318, G)                           # tray (drive lies on it)
    for x in (-0.060, 0.054): dr.box(x, x + 0.006, -d - 0.004, -0.02, 0.312, 0.340, G)
    o = dr.build(C, r); moving(o, "slide", "-Y", [0, 0.20], tip="degausser_drawer")
    node(f"slot_{name}_drive", (0, -0.17, 0.318), o, role="slot", tip="degausser_drive", note="3.5 or 2.5 inch drive goes here")
    return r

# ======================= drive crusher =======================
def crusher(name, parent):
    r = node(f"asset_{name}", (0, 0, 0), parent, role="asset", tip="drive_crusher",
             note="open the window, put the drive in, close, press DESTROY: the V ram bends the drive into a V; take it out")
    K, G = M("M_CrushBlack"), M("M_DegGrey"); w, d, h = 0.0955, 0.237, 0.378
    CX0, CX1, CZ0, CZ1, CY1 = -0.072, 0.072, 0.050, 0.200, 0.060                       # chamber (open at the front)
    b = Part(f"{name}_body")
    for fx in (-0.06, 0.06): b.cyl((fx, -d + 0.03, 0), "Z", 0.0, 0.030, 0.022, K, 14)    # 2 round front feet
    for fx in (-0.07, 0.07): b.cyl((fx, d - 0.04, 0), "Z", 0.0, 0.030, 0.012, K, 10)
    b.box(-w, w, -d, d, 0.030, CZ0, G)                                                  # bottom
    SLOT = 0.016                                                                        # slot behind the front panel: the
    b.box(-w, w, -d + SLOT, d, CZ1, h, G)                                               # window slides up into it
    b.box(-w, CX0 - 0.008, -d, -d + SLOT, CZ1, h, G); b.box(CX1 + 0.008, w, -d, -d + SLOT, CZ1, h, G)
    b.box(-w, CX0, -d, d, CZ0, CZ1, G); b.box(CX1, w, -d, d, CZ0, CZ1, G)              # chamber side walls
    b.box(CX0, CX1, CY1, d, CZ0, CZ1, G)                                                # back of the chamber
    b.box(-w, w, -d - 0.004, -d, CZ1, h, K)                                             # black front panel (upper)
    b.box(-w, w, -d - 0.004, -d, 0.030, CZ0, K)
    for x in ((-w, CX0), (CX1, w)): b.box(x[0], x[1], -d - 0.004, -d, CZ0, CZ1, K)
    b.box(-0.075, 0.005, -d - 0.006, -d - 0.004, 0.318, 0.352, K)                      # LCD bezel
    b.box(-0.070, 0.000, -d - 0.0065, -d - 0.006, 0.323, 0.347, M("M_LCDGreen"))        # LCD
    b.box(0.030, 0.056, -d - 0.008, -d - 0.004, 0.335, 0.357, M("M_LEDAmber"))          # POWER lamp
    b.box(CX0 + 0.005, CX1 - 0.005, -d, CY1, CZ0, CZ0 + 0.012, K)                      # anvil base
    for s in (-1, 1):                                                                   # V anvil: two sloped faces
        b.box(-0.004, 0.004, -d + 0.01, CY1, CZ0 + 0.012, CZ0 + 0.035, M("M_Steel"), Matrix.Translation((s * 0.028, 0, CZ0 + 0.012)) @ Matrix.Rotation(s * 0.6, 4, "Y") @ Matrix.Translation((0, 0, -CZ0 - 0.012)))
    b.box(0.088, 0.0965, -0.06, 0.06, 0.20, 0.32, M("M_TyreBlack"))                    # fan grille on the side
    b.cyl((0.0966, 0, 0.26), "X", 0.0966, 0.0975, 0.045, K, 16)
    b.build(C, r)
    ram = Part(f"{name}_ram", (0, -0.09, CZ1))
    ram.box(-0.006, 0.006, -0.12, -0.06, CZ1 - 0.020, CZ1, M("M_Steel"))               # piston rod
    ram.box(CX0 + 0.008, CX1 - 0.008, -d + 0.012, CY1 - 0.005, CZ1 - 0.035, CZ1 - 0.020, M("M_Steel"))   # ram plate
    ram.box(-0.005, 0.005, -d + 0.012, CY1 - 0.005, CZ1 - 0.065, CZ1 - 0.035, M("M_Steel"))              # V blade
    o = ram.build(C, r); moving(o, "slide", "Z", [-0.075, 0], tip="crusher_ram", note="V ram comes down and bends the drive into a V")
    btn = Part(f"{name}_destroy_button", (0.043, -d - 0.004, 0.317))
    btn.box(0.030, 0.056, -d - 0.010, -d - 0.004, 0.306, 0.328, M("M_CartGrey"))
    o = btn.build(C, r); moving(o, "press", "Y", [0, 0.004], tip="crusher_destroy", note="only works with the window shut")
    dw = Part(f"{name}_window", (0, -d + 0.008, CZ0))                                  # safety window: just behind the front
    dw.box(CX0 - 0.006, CX1 + 0.006, -d + 0.004, -d + 0.012, CZ0 - 0.002, CZ1 + 0.004, M("M_Steel"))   # panel, slides up
    dw.box(CX0 + 0.004, CX1 - 0.004, -d + 0.0035, -d + 0.0125, CZ0 + 0.008, CZ1 - 0.006, clear_glass())   # into the unit
    dw.box(-0.015, 0.015, -d + 0.003, -d + 0.004, CZ0 + 0.002, CZ0 + 0.012, K)          # finger pull at the bottom edge
    o = dw.build(C, r); moving(o, "slide", "Z", [0, 0.155], tip="crusher_window", note="safety window lifts up into the unit to load the drive")
    node(f"slot_{name}_drive", (0, -0.09, CZ0 + 0.035), r, role="slot", tip="crusher_drive", note="drive lies on the V anvil")
    return r

# ======================= red trolley (carries the degausser + crusher) =======================
def red_trolley(name):
    r = node(f"asset_{name}", (0, 0, 0), root, role="asset", tip="media_trolley",
             note="red trolley for the degausser and the drive crusher")
    R_, MB = M("M_TrolleyRed"), M("M_MatBlack"); W2, D2 = 0.45, 0.33; TOP = 0.86
    b = Part(f"{name}_frame")
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x, y = sx * (W2 - 0.02), sy * (D2 - 0.02)
        b.box(x - 0.0175, x + 0.0175, y - 0.0175, y + 0.0175, 0.12, TOP, R_)             # legs
        castor(b, x, y, 0.05, "M_HubRed", brake=(sx < 0 and sy < 0))
    for (za, zb, mat) in ((TOP - 0.035, TOP, None), (0.47, 0.50, MB), (0.14, 0.17, MB)):   # 3 shelves with a lip
        b.box(-W2, W2, -D2, D2, za, zb - 0.01, R_)
        for s in (-1, 1): b.box(-W2, W2, s * D2 - 0.006, s * D2 + 0.006, za, zb + 0.012, R_); b.box(s * W2 - 0.006, s * W2 + 0.006, -D2, D2, za, zb + 0.012, R_)
        if mat: b.box(-W2 + 0.01, W2 - 0.01, -D2 + 0.01, D2 - 0.01, zb - 0.01, zb - 0.004, mat)
    for y in (-0.20, 0.20): b.box(-W2 - 0.07, -W2, y - 0.012, y + 0.012, 0.92, 0.95, R_)   # push handle brackets
    b.cyl((-W2 - 0.07, 0, 0.935), "Y", -0.22, 0.22, 0.014, M("M_TyreBlack"), 10)          # push handle grip
    b.build(C, r)
    deg = degausser(f"{name}_degausser", r); deg.location = (-0.19, 0.0, TOP)
    cru = crusher(f"{name}_crusher", r); cru.location = (0.21, 0.04, TOP)
    return r

# ======================= place: south wall, between the doors, facing north =======================
WALL = OY + 0.30                                                     # 300 mm off the wall
items = [(laptop_cart("laptop_cart"), -5.2, 0.30), (tool_cart("tool_cart_1"), -1.3, 0.30),
         (tool_cart("tool_cart_2"), 0.1, 0.30), (red_trolley("media_trolley"), 4.6, 0.33)]
plan = {}
for (r, x, half_d) in items:
    finish(r, (x, WALL + half_d, 0)); plan[r.name] = {"x": x, "y": round(WALL + half_d, 3), "faces": "north"}
hall_layout("devices", plan)
print("HALL_DEVICES_REPORT", {"tris": tris(C), "moving": sum(1 for o in C.all_objects if o.get("role") == "moving"),
                              "slots": sum(1 for o in C.all_objects if o.get("role") == "slot")})
hall_save()
