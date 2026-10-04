"""PDC breaker panel (owner, 2026-10-04; research/reference/pdc_05_breaker_strip.png). Shared by 74_hall_pdc.py (in the
cabinet) and 76_pdc_panel.py (on its own). Load after _hall.py:  exec(open(os.path.join(HERE, "_pdc_panel.py")).read())
3 strips of 10 identical single breakers touching edge to edge (numbered 1-10, 11-20, 21-30 on black tabs to the right),
a blank white write-on strip to the left of every breaker (for the rack location, e.g. 20304 = hall 2, row 03, rack 04),
space between the strips, 3 master breakers (the same breaker) on their own above the strips with a 200 mm gap.
Breakers stand 12 mm proud of the plate. Every handle is a moving part (switch). Faces -Y."""
_MAT_DEFS.update({"M_BrkBlack": ("#1B1B1C", 0.55, 0), "M_BrkPrint": ("#8C8C8C", 0.6, 0), "M_PanelGrey": ("#8E9398", 0.45, 0.5),
                  "M_TabBlack": ("#121212", 0.5, 0), "M_HandleBlack": ("#0C0C0C", 0.4, 0), "M_WriteWhite": ("#F1F1EC", 0.7, 0)})
BRK = dict(W=0.105, H=0.030, D=0.012, TAB=0.026, WRITE=0.050, GAP=0.004, SPACE=0.035, MGAP=0.200)
BRK["STRIP"] = BRK["WRITE"] + BRK["GAP"] + BRK["W"] + BRK["GAP"] + BRK["TAB"]                     # one strip, write-on to tab
PANEL_W = 3 * BRK["STRIP"] + 2 * BRK["SPACE"]
PANEL_H = 10 * BRK["H"] + BRK["MGAP"] + BRK["H"]

def _handle_mesh():
    me = bpy.data.meshes.get("pdc_breaker_handle_v2")
    if me: return me
    h = Part("pdc_breaker_handle_v2"); h.box(-0.006, 0.006, -0.010, 0, -0.008, 0.008, M("M_HandleBlack")); return h.mesh()

def breaker_panel(p, cx, yface, zbot, C, parent, prefix, row=None):
    """Add the panel into Part p (world coords): centred on cx, plate face at y = yface (faces -Y), bottom of the
    strips at z = zbot. Handles and number texts become objects named <prefix>_... under `parent`."""
    W, H, D = BRK["W"], BRK["H"], BRK["D"]; yf = yface - D; HANDLE = _handle_mesh()
    def breaker(bx, zb, name, **props):
        zc = zb + H / 2
        p.box(bx - W / 2, bx + W / 2, yf, yface, zb + 0.0004, zb + H - 0.0004, M("M_BrkBlack"))                       # body
        p.box(bx - W / 2 + 0.003, bx - W / 2 + 0.009, yf - 0.0006, yf, zc - 0.009, zc + 0.009, M("M_LabelWhite"))    # white end tab
        for k in range(4):
            z = zb + 0.006 + k * 0.005; p.box(bx - W / 2 + 0.013, bx - W / 2 + 0.030, yf - 0.0004, yf, z, z + 0.0018, M("M_BrkPrint"))
        hx = bx - 0.008
        p.box(hx - 0.016, hx + 0.016, yf - 0.0005, yf, zb + 0.005, zb + H - 0.005, M("M_TVBlack"))                  # handle window
        p.box(bx + 0.020, bx + 0.036, yf - 0.0006, yf, zc - 0.007, zc + 0.007, M("M_LabelWhite"))                   # rating box
        p.box(bx + 0.0215, bx + 0.0345, yf - 0.0008, yf - 0.0006, zc - 0.0055, zc + 0.0055, M("M_BrkBlack"))
        for k in range(3):
            z = zb + 0.008 + k * 0.006; p.box(bx + 0.040, bx + 0.049, yf - 0.0004, yf, z, z + 0.0018, M("M_BrkPrint"))
        p.box(bx + W / 2 - 0.003, bx + W / 2, yf - 0.002, yf, zb + 0.002, zb + H - 0.002, M("M_BrkBlack"))        # end rib
        o = bpy.data.objects.new(name, HANDLE); C.objects.link(o); place(o, (hx, yf, zc), parent)
        moving(o, "hinge", "Z", [-25, 25], state="on", **props)
    x_left = cx - PANEL_W / 2; z_top = zbot + 10 * H
    for s in range(3):
        sx = x_left + s * (BRK["STRIP"] + BRK["SPACE"])
        wx = sx + BRK["WRITE"] / 2; bx = sx + BRK["WRITE"] + BRK["GAP"] + W / 2; tx = bx + W / 2 + BRK["GAP"] + BRK["TAB"] / 2
        ph = f"L{s + 1}"
        breaker(bx, z_top + BRK["MGAP"], f"{prefix}_master_{ph}", tip="pdc_master_breaker", phase=ph, note=f"turns off strip {ph}")
        for n in range(10):
            num = s * 10 + n + 1; zb = z_top - (n + 1) * H                                                     # 1 at the top
            extra = {"feeds": f"rack_{row}{n + 1:02d}", "whip": s + 1} if row else {}
            breaker(bx, zb, f"{prefix}_brk_{num:02d}", tip="pdc_breaker", phase=ph, circuit=num, **extra)
            p.box(wx - BRK["WRITE"] / 2, wx + BRK["WRITE"] / 2, yface - 0.002, yface, zb + 0.0015, zb + H - 0.0015, M("M_WriteWhite"))   # write-on strip
            p.box(tx - BRK["TAB"] / 2, tx + BRK["TAB"] / 2, yface - 0.006, yface, zb + 0.0015, zb + H - 0.0015, M("M_TabBlack"))       # number tab
            text_obj(f"{prefix}_num_{num:02d}", str(num), 0.014, M("M_LabelWhite"), (tx, yface - 0.0065, zb + H / 2), C, parent,
                     rot=(math.pi / 2, 0, 0))
