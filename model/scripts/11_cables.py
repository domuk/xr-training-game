"""Asset 11 (polish v2) — cable assets with plug bodies at every connector end:
SATA bundle (16 plugs, through the fan-bracket notch), 4 backplane power bundles, ATX 24-pin + 8-pin; zip ties.
MODEL-SPEC §8.10, §12."""
import bpy
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
lay = load_layout()
S = server_coll(); CB = coll("cables", S); wipe(CB)
for cu in [c for c in bpy.data.curves if c.name.startswith(("sata_", "pwr_", "atx_"))]: bpy.data.curves.remove(cu)

def cable(name, routes, radius, parent):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    cu.bevel_depth = radius; cu.bevel_resolution = 0; cu.use_fill_caps = True; mats = []
    for pts, m in routes:
        if m not in mats: mats.append(m)
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for q, v in zip(sp.points, pts): q.co = (*v, 1)
        sp.material_index = mats.index(m)
    for m in mats: cu.materials.append(m)
    o = bpy.data.objects.new(name, cu); CB.objects.link(o); place(o, (0, 0, 0), parent); return o

bp = lay["backplane"]; BY1 = bp["y"][1]
# ---------- SATA x8 ----------
a = asset("cable_sata", (-0.150, 0.170, 0.045), CB, pull=[[0, 0, 0.12]], tip="sata_cable",
          note="unplug both ends: press the latch, pull straight out")
p = Part("sata_plugs"); routes = []
for k in range(8):
    xs = bp["sata_x0"] + k * bp["sata_pitch"] + 0.004; xr = -0.205 + k * 0.006; xp = -0.190 + k * 0.0135 + 0.004
    p.box(xs - 0.0042, xs + 0.0042, BY1 + 0.0062, BY1 + 0.0112, 0.0410, 0.0490, M("M_SATARed"))        # backplane end
    p.box(xp - 0.0042, xp + 0.0042, 0.2185, 0.2315, 0.0138, 0.0198, M("M_SATARed"))                    # board end
    routes.append(([(xs, BY1 + 0.0112, 0.045), (xs, 0.1320, 0.025), (xr, 0.1500, 0.025), (xr, 0.1600, 0.060),
                    (xr, 0.1950, 0.0835), (xr, 0.2070, 0.0835), (xp, 0.2140, 0.035), (xp, 0.2250, 0.0198)], M("M_SATARed")))
p.build(CB, a); cable("sata_bundle", routes, 0.0006, a)

# ---------- backplane power: hardwired to the PSU cage (fixed); white plug at the backplane end unplugs ----------
fxc = fixed("cables", CB)
COLS = ["M_Wire_Black", "M_Wire_Red", "M_Wire_Yellow", "M_Wire_Blue"]
for i, px in enumerate(sorted(bp["power_x"], reverse=True)):
    yb = 0.138 + i * 0.006; sx = 0.135 + i * 0.008
    p = Part(f"pwr_{i+1}_plug", (px, BY1 + 0.0112, 0.015)); p.box(px - 0.0105, px + 0.0105, BY1 + 0.0082, BY1 + 0.0142, 0.0105, 0.0195, M("M_PlugWhite"))
    p.box(px - 0.003, px + 0.003, BY1 + 0.0082, BY1 + 0.0142, 0.0195, 0.0210, M("M_PlugWhite"))
    moving(p.build(CB, fxc), "slide", "Y", [0.0, 0.008], tip="power_plug", note="press the latch, pull straight out")
    routes = []
    for w, col in enumerate(COLS):
        o = (w - 1.5) * 0.0011
        routes.append(([(sx + o, 0.1690, 0.020), (sx + o, 0.1600, 0.0016), (sx + o, yb + o, 0.0016),
                        (px + o, yb + o, 0.0016), (px + o, 0.1330, 0.0150), (px + o, BY1 + 0.0142, 0.0150)], M(col)))
    cable(f"pwr_bundle_{i+1}", routes, 0.0005, fxc)

# ---------- ATX 24-pin + 8-pin ----------
ATXP = {}
for nm, (y0, y1) in (("atx_plug_24", (0.3268, 0.3552)), ("atx_plug_8", (0.2998, 0.3182))):
    p = Part(nm, (0.108, (y0 + y1) / 2, 0.0236)); p.box(0.1040, 0.1120, y0, y1, 0.0206, 0.0266, M("M_PlugWhite"))
    ATXP[nm] = moving(p.build(CB, fxc), "slide", "Z", [0.0, 0.015], tip="atx_plug", note="squeeze the latch, pull straight up")
r24 = [([(0.1142, 0.2560 + w * 0.0040, 0.046), (0.1125, 0.2900, 0.044), (0.1105, y, 0.038), (0.1080, y, 0.0266)],
        M(("M_Wire_Yellow", "M_Wire_Red", "M_Wire_Black")[w % 3])) for w, y in enumerate(0.330 + k * 0.0045 for k in range(6))]
r8 = [([(0.1142, 0.2620 + w * 0.0040, 0.036), (0.1125, 0.2850, 0.036), (0.1105, y, 0.034), (0.1080, y, 0.0266)],
       M(("M_Wire_Yellow", "M_Wire_Black", "M_Wire_Yellow")[w])) for w, y in enumerate(0.303 + k * 0.005 for k in range(3))]
cable("atx_wires_24", r24, 0.0005, ATXP["atx_plug_24"]); cable("atx_wires_8", r8, 0.0005, ATXP["atx_plug_8"])   # wires follow their plug

# ---------- zip ties (fixed) ----------
fx = fxc; z = Part("zip_ties")
for (x, y) in ((0.090, 0.147), (-0.010, 0.144), (-0.100, 0.141)):
    z.box(x - 0.00125, x + 0.00125, y - 0.011, y + 0.011, 0.0002, 0.0038, M("M_ZipTie"))
z.build(CB, fx)
print("CABLE_REPORT", {"tris": tris(CB)})
save()
