"""Shared connector builders (exec after _lib.py). The caller defines: YB, YF (port back / front face Y),
MET, DARK, GOLD materials and mm = 0.001."""
import bmesh, math
from mathutils import Vector

def hull(p, pts, m):
    vs = [p.bm.verts.new(Vector(q) - p.o) for q in pts]
    r = bmesh.ops.convex_hull(p.bm, input=vs); i = p._mi(m)
    for f in [g for g in r["geom"] if isinstance(g, bmesh.types.BMFace)]: f.material_index = i

def jack(p, x0, x1, z0, z1, ox0, ox1, oz0, oz1, depth, shell=None, yb=None):
    """Metal shell with a real rectangular opening `depth` deep and a dark back wall."""
    shell = shell or MET; yb = YB if yb is None else yb; yd = YF - depth
    p.box(x0, x1, yb, yd, z0, z1, shell)
    p.box(x0, ox0, yd, YF, z0, z1, shell); p.box(ox1, x1, yd, YF, z0, z1, shell)
    p.box(ox0, ox1, yd, YF, z0, oz0, shell); p.box(ox0, ox1, yd, YF, oz1, z1, shell)
    p.box(ox0, ox1, yd - 0.0003, yd, oz0, oz1, DARK)

def rj45(p, x0, x1, z0, h, leds=True, yb=None):
    """RJ45 jack: cavity, latch notch at the bottom, 8 contacts @ 1.02 mm, link (green) + activity (amber) LEDs.
    Returns (opening z0, opening height) for cut-outs."""
    xc = (x0 + x1) / 2; ow, oh = 11.7 * mm, 8.2 * mm
    oz0 = z0 + (h - oh) / 2 - 1.0 * mm
    jack(p, x0, x1, z0, z0 + h, xc - ow / 2, xc + ow / 2, oz0, oz0 + oh, 0.012, yb=yb)
    p.box(xc - 3.0 * mm, xc + 3.0 * mm, YF - 0.012, YF, oz0 - 2.2 * mm, oz0 + 0.0001, DARK)
    for k in range(8):
        x = xc + (k - 3.5) * 1.02 * mm
        p.box(x - 0.2 * mm, x + 0.2 * mm, YF - 0.0095, YF - 0.0055, oz0 + oh - 2.2 * mm, oz0 + oh - 0.4 * mm, GOLD)
    if leds:
        p.box(x0 + 0.6 * mm, x0 + 2.6 * mm, YF, YF + 0.0002, z0 + h - 1.6 * mm, z0 + h - 0.4 * mm, M("M_LEDGreen"))
        p.box(x1 - 2.6 * mm, x1 - 0.6 * mm, YF, YF + 0.0002, z0 + h - 1.6 * mm, z0 + h - 0.4 * mm, M("M_LEDAmber"))
    return oz0, oh

def usb_a(p, xc, zc, tongue_mat, n_contacts):
    ty0, ty1 = YF - 0.0080, YF - 0.0008
    p.box(xc - 5.5 * mm, xc + 5.5 * mm, ty0, ty1, zc + 0.2 * mm, zc + 2.0 * mm, tongue_mat)
    xs = [(-3.75 + 2.5 * k) * mm for k in range(4)]; ws = [1.0 * mm] * 4
    if n_contacts == 9:
        xs += [(-4.0 + 2.0 * k) * mm for k in range(5)]; ws += [0.6 * mm] * 5
    for i, (x, w) in enumerate(zip(xs, ws)):
        y0 = ty1 - (0.0035 if i < 4 else 0.0065)
        p.box(xc + x - w / 2, xc + x + w / 2, y0, y0 + 0.0025, zc + 0.15 * mm, zc + 0.2 * mm, GOLD)

def boolean_cut(obj, cutter_parts, coll_):
    """Apply each cutter Part (built at its own coordinates) as an exact boolean difference."""
    import bpy
    for c in cutter_parts:
        co = c.build(coll_)
        md = obj.modifiers.new("c", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = co; md.solver = "EXACT"
        bpy.context.view_layer.objects.active = obj; bpy.ops.object.modifier_apply(modifier=md.name)
        bpy.data.objects.remove(co, do_unlink=True)
