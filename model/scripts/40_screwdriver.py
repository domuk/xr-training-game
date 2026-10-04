"""Tool 40 — ratcheting 12-bit screwdriver (black/orange), matched to assets/reference/parts/screwdriver.
Real size from the maker's listing: 213 mm long (storage closed), 260 mm open, shaft 82.2 mm, 35 mm wide, 12 bits.
Profile traced from 01-front.png (0.1641 mm/px, fits all three listed sizes).
Own file: assets/blender/tools.blend -> assets/glb/screwdriver.glb + screwdriver_manifest.json.
Frame: tool axis = Z, origin = tip of the fitted bit, handle towards +Z (glTF: handle towards +Y).
Grabbable: the tool, the fitted bit (pulls out of the magnetic holder), the bit store (end cap + carousel slides
out 47 mm) and the 11 stored bits (clip out sideways once the store is out). Ratchet ring turns: < | >.
Run headless:  blender --background --factory-startup --python 40_screwdriver.py"""
import bpy, bmesh, math, os, json
import os
HERE = bpy.path.abspath("//scripts")                   # this script's folder (assets/blender/scripts)
LIB = os.path.join(HERE, "_lib.py")
exec(open(LIB).read())
from mathutils import Matrix, Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
BLEND = os.path.join(ROOT, "model", "tools.blend")
TEX = os.path.join(ROOT, "model", "tex"); os.makedirs(TEX, exist_ok=True)
mm = 0.001; PX = 0.1641
def zpx(y): return 12.0 + (y - 90) * PX        # photo row -> mm along the axis (fitted bit sticks out 12 mm)

_MAT_DEFS.update({
    "M_SD_Rubber": ("#2B2B2D", 0.8, 0), "M_SD_Collar": ("#1F1F21", 0.55, 0), "M_SD_Orange": ("#EE5A24", 0.6, 0),
    "M_SD_Chrome": ("#D8D9DB", 0.18, 1.0), "M_SD_Bore": ("#3A3B3D", 0.5, 1.0), "M_SD_Bit": ("#262729", 0.45, 0.8),
    "M_SD_Mark": ("#6A6A6C", 0.6, 0), "M_SD_Knurl": ("#C9CACC", 0.35, 1.0),
})

# ---------- knurl normal map (diamond knurl, 8 x 8 diamonds per tile) ----------
def knurl_material():
    import numpy as np
    n = 256; u = (np.arange(n) + 0.5) / n * 8; U, V = np.meshgrid(u, u)
    tri = lambda t: 1 - 2 * np.abs(t - np.floor(t) - 0.5)
    h = np.minimum(tri(U + V), tri(U - V))
    gy, gx = np.gradient(h); k = 6.0
    N = np.dstack([-gx * k, -gy * k, np.ones_like(h)]); N /= np.linalg.norm(N, axis=2, keepdims=True)
    img = bpy.data.images.new("sd_knurl_n", n, n); px = np.dstack([(N + 1) / 2, np.ones((n, n, 1))])
    img.pixels = px.ravel().tolist(); img.filepath_raw = os.path.join(TEX, "sd_knurl_n.png"); img.file_format = "PNG"
    img.save(); img.colorspace_settings.name = "Non-Color"
    m = M("M_SD_Knurl"); nt = m.node_tree; bsdf = next(x for x in nt.nodes if x.type == "BSDF_PRINCIPLED")
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
    nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
knurl_material()

# ---------- lathe: profile [(z_mm, r_mm, material, tag)] revolved about Z into a Part ----------
def lathe(p, prof, segs, shape=None, urep=1.0, vlen=10.0):
    bm = p.bm; uvl = bm.loops.layers.uv.verify(); rings = []
    for (z, r, _m, tag) in prof:
        if r <= 1e-6:
            rings.append([bm.verts.new(Vector((0, 0, z * mm)) - p.o)])
        else:
            ring = []
            for i in range(segs):
                th = 2 * math.pi * i / segs; f = shape(i, th, z, tag) if shape else 1.0
                ring.append(bm.verts.new(Vector((r * f * math.cos(th) * mm, r * f * math.sin(th) * mm, z * mm)) - p.o))
            rings.append(ring)
    made = []
    for k in range(len(rings) - 1):
        a, b, mi = rings[k], rings[k + 1], p._mi(M(prof[k][2]))
        if len(a) == 1 and len(b) == 1: continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1: vs, ids = (a[0], b[j], b[i]), (None, j, i)
            elif len(b) == 1: vs, ids = (a[i], a[j], b[0]), (i, j, None)
            else: vs, ids = (a[i], a[j], b[j], b[i]), (i, j, j, i)
            try: f = bm.faces.new(vs)
            except ValueError: continue
            f.material_index = mi; f.smooth = True; made.append((f, i))
    bmesh.ops.recalc_face_normals(bm, faces=[f for f, _ in made])
    for f, i in made:                                    # cylindrical UVs, seam-safe
        for l in f.loops:
            co = l.vert.co + p.o; ang = math.atan2(co.y, co.x) % (2 * math.pi)
            u = ang / (2 * math.pi)
            if i == segs - 1 and u < 0.25: u += 1.0
            l[uvl].uv = (u * urep, co.z / mm / vlen)

def smooth_by_angle(o, deg=35):
    try: o.data.set_sharp_from_angle(angle=math.radians(deg))
    except Exception: pass

def node(name, loc, parent, c, **props):
    e = bpy.data.objects.new(name, None); e.empty_display_size = 0.01; c.objects.link(e)
    place(e, loc, parent); setp(e, **props); return e

C = coll("tools"); wipe(C)
root = node("asset_screwdriver", (0, 0, 0), None, C, role="asset", tool="screwdriver", tip="screwdriver",
            note="ratcheting 12-bit screwdriver; tool axis Z, origin = bit tip", fitted_bit="asset_sd_bit")
node("sd_tip", (0, 0, 0), root, C, role="anchor", note="bit tip; touch to the screw head")
node("sd_grip", (0, 0, 0.168 + 0.0), root, C, role="anchor", note="palm centre on the handle")

# ---------- shaft: hex bore + chrome tube + knurl + neck into the ratchet ring ----------
sh = Part("sd_shaft")
lathe(sh, [(20, 0, "M_SD_Bore", 0), (20, 3.7, "M_SD_Bore", 0), (12, 3.7, "M_SD_Chrome", 0), (12, 4.15, "M_SD_Chrome", 0),
           (12.4, 4.5, "M_SD_Chrome", 0), (zpx(315), 4.5, "M_SD_Chrome", 0), (zpx(330), 3.85, "M_SD_Knurl", 0),
           (zpx(525), 3.85, "M_SD_Chrome", 0), (zpx(535), 3.3, "M_SD_Chrome", 0), (100, 3.3, "M_SD_Chrome", 0),
           (100, 0, "M_SD_Chrome", 0)], 24, urep=3, vlen=7.2)
smooth_by_angle(sh.build(C, root))

# ---------- ratchet ring (collar): rounded nose, 24 ribs, < | > marking ----------
cz0, cz1 = zpx(590), zpx(745)
COL = [(590, 116), (600, 131), (610, 144), (620, 155), (630, 158), (650, 161), (680, 163), (700, 165), (745, 165)]
RIB0, RIB1 = zpx(652), zpx(712)
rc = lambda y: dict(COL).get(y, 165) * PX / 2
prof = [(cz0, 0, "M_SD_Collar", 0)] + [(zpx(y), d * PX / 2, "M_SD_Collar", 0) for y, d in COL if y <= 650] + \
       [(RIB0 - 0.15, rc(650), "M_SD_Collar", 0), (RIB0, rc(650), "M_SD_Collar", 1), (zpx(680), rc(680), "M_SD_Collar", 1), (zpx(700), rc(700), "M_SD_Collar", 1),
        (RIB1, rc(745), "M_SD_Collar", 1), (RIB1 + 0.15, rc(745), "M_SD_Collar", 0), (cz1, rc(745), "M_SD_Collar", 0),
        (cz1, 0, "M_SD_Collar", 0)]
rg = Part("sd_ratchet_ring", (0, 0, cz0 * mm))
lathe(rg, prof, 96, shape=lambda i, th, z, tag: (0.955 if (tag and i % 4 in (2, 3)) else 1.0))
RC = 165 * PX / 2; zm = (RIB1 + cz1) / 2
def stroke(x0, z0, x1, z1, w=0.45):
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; L = math.hypot(x1 - x0, z1 - z0); a = math.atan2(z1 - z0, x1 - x0)
    y = -math.sqrt(RC ** 2 - cx ** 2)
    mtx = Matrix.Translation((cx * mm, 0, cz * mm)) @ Matrix.Rotation(-a, 4, "Y") @ Matrix.Translation((-cx * mm, 0, -cz * mm))
    rg.box((cx - L / 2) * mm, (cx + L / 2) * mm, (y - 0.25) * mm, (y + 0.3) * mm, (cz - w / 2) * mm, (cz + w / 2) * mm,
           M("M_SD_Mark"), mtx)
stroke(-0.25, zm - 1.4, -0.25, zm + 1.4, 0.5)                      # |  (centre = locked)
for s in (-1, 1):                                                  # <  and  >
    stroke(s * 1.3, zm + 1.1, s * 2.6, zm, 0.4); stroke(s * 1.3, zm - 1.1, s * 2.6, zm, 0.4)
stroke(0, RIB0 + 0.2, 0, RIB1 - 0.2, 0.35)                         # pointer line down the ribs
ring = rg.build(C, root); smooth_by_angle(ring, 30)
moving(ring, "hinge", "Z", [-20, 20], states="anticlockwise (undo),locked,clockwise (tighten)",
       tip="sd_ratchet", note="turn to < to undo, > to tighten, | for a fixed driver")

# ---------- handle: orange ring + rubber body, bore for the bit store ----------
HND = [(757, 164), (770, 160), (780, 154), (790, 149), (800, 145), (810, 141), (825, 138), (840, 140), (850, 143),
       (860, 149), (870, 156), (880, 165), (890, 175), (900, 185), (910, 195), (920, 203), (930, 210), (945, 213),
       (960, 215), (1000, 213), (1050, 210), (1100, 208), (1150, 206), (1200, 203), (1250, 202), (1290, 197),
       (1306, 191), (1312, 189)]
HZ0, HZ1 = zpx(757), zpx(1312); BORE_R, BORE_Z = 12.8, 164.0
def nexp(z):
    y = (z - 12) / PX + 90
    if y < 860: return 2.0
    if y < 960: return 2.0 + 0.7 * (y - 860) / 100
    if y < 1200: return 2.7
    return 2.7 - 0.4 * min(1, (y - 1200) / 100)
# Cross-section from the public-domain STL clone (reference/parts/screwdriver/stl, sections.json): corners at
# 0/90/180/270 deg (front, sides), flats on the diagonals; round at the waist. The photo silhouette gives the corner
# radius, the STL gives r(angle)/r(corner). Clone body z 2 -> 88 maps onto handle HZ0 -> HZ1.
SEC = json.load(open(os.path.join(ROOT, "assets", "reference", "parts", "screwdriver", "stl", "sections.json")))["Main Body v2.stl"]
SEC = sorted((float(z), v) for z, v in SEC.items() if 2.0 <= float(z) <= 88.0)
def stl_factor(th, z):
    zc = 2.0 + (z - HZ0) / (HZ1 - HZ0) * 86.0
    zc = min(max(zc, SEC[0][0]), SEC[-1][0])
    k = max(i for i, (zz, _) in enumerate(SEC) if zz <= zc); k1 = min(k + 1, len(SEC) - 1)
    t = 0 if k1 == k else (zc - SEC[k][0]) / (SEC[k1][0] - SEC[k][0])
    a = (math.degrees(th) % 360) / 15.0; j = int(a) % 24; u = a - int(a)
    def f(v): return ((1 - u) * v[j] + u * v[(j + 1) % 24]) / max(v[0], v[6], v[12], v[18])
    return (1 - t) * f(SEC[k][1]) + t * f(SEC[k1][1])
def superell(i, th, z, tag):
    return stl_factor(th, z) if tag else 1.0
hd = Part("sd_handle", (0, 0, HZ0 * mm))
lathe(hd, [(zpx(744), 0, "M_SD_Orange", 0), (zpx(744), 12.9, "M_SD_Orange", 0), (HZ0, 12.9, "M_SD_Orange", 0),
           (HZ0, 0, "M_SD_Orange", 0)], 48)
prof = [(HZ0, 0, "M_SD_Rubber", 1)] + [(zpx(y), d * PX / 2, "M_SD_Rubber", 1) for y, d in HND] + \
       [(HZ1, BORE_R + 0.6, "M_SD_Bore", 1), (HZ1, BORE_R, "M_SD_Bore", 0), (BORE_Z, BORE_R, "M_SD_Bore", 0),
        (BORE_Z, 0, "M_SD_Bore", 0)]
lathe(hd, prof, 48, shape=superell)
smooth_by_angle(hd.build(C, root), 40)

# ---------- bits: 12-point lofted tips on a 1/4" hex shank (20 mm, tip 6 mm), origin at the tip, shank +Z ----------
HEXR = 6.35 / 2 / math.cos(math.radians(30))                       # corner radius 3.67
def poly_sort(pts): return sorted(pts, key=lambda p: math.atan2(p[1], p[0]) % (2 * math.pi))
def hexpts(R, n=12):
    out = []
    for k in range(6):
        a0, a1 = math.radians(60 * k), math.radians(60 * k + 60)
        p0 = (R * math.cos(a0), R * math.sin(a0)); p1 = (R * math.cos(a1), R * math.sin(a1))
        out += [p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)]
    return poly_sort(out)
def circ(r): return [(r * math.cos(math.radians(30 * k)), r * math.sin(math.radians(30 * k))) for k in range(12)]
def cross(L, w):
    a = w / 2
    return poly_sort([(a, L), (-a, L), (-a, a), (-L, a), (-L, -a), (-a, -a), (-a, -L), (a, -L), (a, -a), (L, -a), (L, a), (a, a)])
def rect(W, T):
    hw, ht = W / 2, T / 2
    return poly_sort([(hw, 0), (hw, ht), (hw / 2, ht), (0, ht), (-hw / 2, ht), (-hw, ht), (-hw, 0), (-hw, -ht),
                      (-hw / 2, -ht), (0, -ht), (hw / 2, -ht), (hw, -ht)])
def square(s): h = s / 2; return poly_sort([(h, h), (-h, h), (-h, -h), (h, -h), (h, 0), (0, h), (-h, 0), (0, -h),
                                            (h, h / 2), (-h / 2, h), (-h, -h / 2), (h / 2, -h)])
def hexk(d): return hexpts(d / 2 / math.cos(math.radians(30)))
def loft_mesh(name, rings):
    """rings: [(z_mm, pts12, material)], material = band from this ring to the next. Capped both ends."""
    p = Part(name); bm = p.bm; vr = []
    for z, pts, _m in rings: vr.append([bm.verts.new((x * mm, y * mm, z * mm)) for x, y in pts])
    for k in range(len(vr) - 1):
        mi = p._mi(M(rings[k][2]))
        for i in range(12):
            j = (i + 1) % 12; bm.faces.new((vr[k][i], vr[k][j], vr[k + 1][j], vr[k + 1][i])).material_index = mi
    bm.faces.new(vr[0][::-1]).material_index = p._mi(M(rings[0][2]))
    bm.faces.new(vr[-1]).material_index = p._mi(M(rings[-2][2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return p.mesh()
SHANK = [(6.0, hexpts(HEXR), "M_SD_Bit"), (13.5, hexpts(HEXR), "M_SD_Bit"), (13.8, circ(2.75), "M_SD_Bit"),
         (15.0, circ(2.75), "M_SD_Bit"), (15.3, hexpts(HEXR), "M_SD_Bit"), (19.6, hexpts(HEXR), "M_SD_Bit"),
         (20.0, hexpts(HEXR * 0.9), "M_SD_Bit")]
def bit_mesh(kind, size):
    nm = f"sd_bitmesh_{kind}_{size}"
    if kind == "phillips":
        Lb = {0: 1.5, 1: 2.2, 2: 3.0}[size]
        tip = [(0.0, cross(0.3, 0.25), "M_SD_Bit"), (1.8, cross(Lb * 0.55, 0.4 + 0.15 * size), "M_SD_Bit"),
               (4.0, cross(Lb, 0.5 + 0.25 * size), "M_SD_Bit"),
               (5.2, circ(Lb), "M_SD_Bit")]
    elif kind == "slot":
        W = float(size); tip = [(0.0, rect(W, 0.35 + 0.08 * W), "M_SD_Bit"), (3.5, rect(W, 1.5), "M_SD_Bit"),
                                (5.2, circ(max(W / 2, 1.6)), "M_SD_Bit")]
    elif kind == "hex":
        d = float(size); tip = [(0.0, hexk(d), "M_SD_Bit"), (4.5, hexk(d), "M_SD_Bit"), (5.2, circ(d * 0.6), "M_SD_Bit")]
    elif kind == "robertson":
        s = {1: 2.1, 2: 2.6}[size]; tip = [(0.0, square(s), "M_SD_Bit"), (3.5, square(s * 1.12), "M_SD_Bit"),
                                          (5.0, circ(s * 0.85), "M_SD_Bit")]
    else:                                                          # magnet bit: hex body, chrome magnet face
        tip = [(0.0, hexpts(HEXR * 0.92), "M_SD_Chrome"), (0.8, hexpts(HEXR * 0.92), "M_SD_Bit"), (5.2, hexpts(HEXR), "M_SD_Bit")]
    me = loft_mesh(nm, tip + SHANK)
    return me
BITS = {"phillips_0": ("phillips", 0), "phillips_1": ("phillips", 1), "phillips_2": ("phillips", 2),
        "hex_2": ("hex", 2), "hex_2.5": ("hex", 2.5), "hex_4": ("hex", 4), "slot_2": ("slot", 2), "slot_4": ("slot", 4),
        "slot_6": ("slot", 6), "robertson_1": ("robertson", 1), "robertson_2": ("robertson", 2), "magnet": ("magnet", 0)}
MESH = {k: bit_mesh(*v) for k, v in BITS.items()}
def bit_obj(name, tool, tip_loc, up, c, parent, **props):
    """Bit asset: grab empty at the bit centre, mesh child with its origin at the tip. up=+1 shank towards +Z."""
    ctr = Vector(tip_loc) + Vector((0, 0, 0.010 * up))
    a = node(f"asset_{name}", ctr, parent, c, role="asset", bit=tool, tip="sd_bit", **props)
    o = bpy.data.objects.new(name, MESH[tool]); c.objects.link(o); place(o, tip_loc, a)
    if up < 0: o.rotation_euler = (math.pi, 0, 0)
    for f in o.data.polygons: f.use_smooth = False
    return a

# fitted bit (PH2, as in the reference photo) + its slot in the holder
bit_obj("sd_bit", "phillips_2", (0, 0, 0), +1, C, root, pull=[[0, 0, -0.025]],
        check="push the hex end into the holder until the magnet takes it")
node("slot_sd_bit", (0, 0, 0.010), root, C, role="slot", accepts="bit")

# ---------- bit store: end cap + carousel (two tiers of 6), slides out 47 mm ----------
CZ = HZ1                                                         # cap underside = handle end
store = node("asset_sd_storage", (0, 0, CZ * mm), root, C, role="asset", tip="sd_storage", pull=[[0, 0, 0.047]],
             check="line the bits up with the bore and push the cap home")
CAP = [(1312, 188), (1320, 185), (1330, 180), (1340, 172), (1350, 165), (1360, 152), (1370, 130), (1380, 92), (1386, 52)]
cp = Part("sd_cap", (0, 0, CZ * mm))
lathe(cp, [(CZ, 0, "M_SD_Orange", 0)] + [(zpx(y), d * PX / 2, "M_SD_Orange", 0) for y, d in CAP] +
      [(zpx(1387.5), 0, "M_SD_Orange", 0)], 48)
for s in (-1, 1):                                                 # 3 pull ridges each side
    for k, y in enumerate((1322, 1334, 1346)):
        z = zpx(y); r = dict(CAP).get(y, None) or [d for yy, d in CAP if yy <= y][-1]; r = r * PX / 2
        L = 9.0 - 1.5 * k
        xa, xb = sorted((s * (r - 0.35) * mm, s * (r + 0.35) * mm))
        cp.box(xa, xb, -L / 2 * mm, L / 2 * mm,
               (z - 0.35) * mm, (z + 0.35) * mm, M("M_SD_Orange"))
smooth_by_angle(cp.build(C, store), 35)

ca = Part("sd_carousel", (0, 0, CZ * mm)); TOPB, LOWB = 166.0, CZ - 0.3
ca.cyl((0, 0, 0), "Z", TOPB * mm, 211.0 * mm, 4.5 * mm, M("M_SD_Orange"), 16)              # centre post
ca.cyl((0, 0, 0), "Z", 211.0 * mm, LOWB * mm, 12.4 * mm, M("M_SD_Collar"), 32)             # black washer under the cap
ca.cyl((0, 0, 0), "Z", TOPB * mm, 167.2 * mm, 5.5 * mm, M("M_SD_Orange"), 16)              # foot
ca.cyl((0, 0, 0), "Z", 187.6 * mm, 189.6 * mm, 6.0 * mm, M("M_SD_Collar"), 16)             # hub between tiers
RB = 8.6
for z0, z1 in ((193.0, 197.0), (179.5, 183.5)):                                             # two clip bands
    ca.cyl((0, 0, 0), "Z", z0 * mm, z1 * mm, 8.0 * mm, M("M_SD_Orange"), 24)
    for k in range(6):
        a = math.radians(30 + 60 * k); R = Matrix.Rotation(a, 4, "Z")
        ca.box(7.5 * mm, 12.2 * mm, -1.2 * mm, 1.2 * mm, z0 * mm, z1 * mm, M("M_SD_Orange"), R)
ca.build(C, store)
UPPER = ["slot_2", "slot_4", "slot_6", "robertson_1", "robertson_2", "magnet"]              # tips towards the cap
LOWER = ["phillips_0", "phillips_1", None, "hex_2", "hex_2.5", "hex_4"]                       # PH2 is in the holder
n = 0
for tier, names, tipz, up in (("u", UPPER, 210.0, -1), ("l", LOWER, 167.0, +1)):
    for k, tool in enumerate(names):
        n += 1; a = math.radians(60 * k); d = Vector((math.cos(a), math.sin(a), 0))
        tip = Vector((RB * d.x * mm, RB * d.y * mm, tipz * mm))
        node(f"slot_sd_store_{n:02d}", tip + Vector((0, 0, 0.010 * up)), store, C, role="slot", accepts="bit")
        if tool:
            bit_obj(f"sd_bit_{tool.replace('.', '_')}", tool, tip, up, C, store,
                    pull=[[round(d.x * 0.012, 5), round(d.y * 0.012, 5), 0.0]], requires="asset_sd_storage")

# ---------- report, save, export ----------
dg = bpy.context.evaluated_depsgraph_get(); T = 0
for o in C.all_objects:
    if o.type == "MESH": me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); T += len(me.loop_triangles); o.evaluated_get(dg).to_mesh_clear()
mats = {m.name for o in C.all_objects if o.type == "MESH" for m in o.data.materials}
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

OUT = os.path.join(ROOT, "app", "public", "gltf", "tools"); GLB = os.path.join(OUT, "screwdriver.glb")
objs = [root] + list(root.children_recursive)
bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=GLB, use_selection=True, export_extras=True, export_yup=True, export_apply=True,
                          export_cameras=False, export_lights=False, export_materials="EXPORT")
def conv(v):
    if hasattr(v, "to_dict"): return {k: conv(x) for k, x in v.to_dict().items()}
    if hasattr(v, "to_list"): return [conv(x) for x in v.to_list()]
    if isinstance(v, (list, tuple)): return [conv(x) for x in v]
    if isinstance(v, float): return round(v, 6)
    return v
man = {"file": "screwdriver.glb", "units": "metres", "up": "+Y (glTF); Blender source is Z-up",
       "note": "tool axis = Blender Z (glTF +Y), origin = fitted bit tip. Vectors in Blender axes: (x,y,z) -> (x,z,-y) glTF",
       "bits": {k: v[0] for k, v in BITS.items()}, "nodes": {}}
for o in objs:
    if o.get("role"):
        man["nodes"][o.name] = {"parent": o.parent.name if o.parent else None,
                                **{k: conv(v) for k, v in o.items() if not k.startswith(("_", "cycles"))},
                                "pos": [round(x, 5) for x in o.matrix_world.translation]}
json.dump(man, open(os.path.join(OUT, "screwdriver_manifest.json"), "w"), indent=1)
print("SD_REPORT", {"tris": T, "materials": len(mats), "objects": len(objs), "glb_kb": round(os.path.getsize(GLB) / 1024)})
