"""Blue 32 A IEC 60309 'commando' connectors, 2P+E (owner, 2026-10-04; research/reference/commando_01..04).
Shared by the lab rack, the hall whips and 77_commando.py. Load after _lib.py / _lab.py / _hall.py.
commando_meshes() -> {"male", "female", "flap"} meshes (built once, then shared/instanced):
  - male (plug, on the rack PDU lead): blue shroud round 3 brass pins (earth pin larger, at 6 o'clock), key tab on top,
    grey ribbed grip, cable nut at the back.
  - female (connector, on the PDC whip): blue body, dark face insert with 3 holes, hinge lugs, ribbed rear, grey nut.
  - flap: the female's spring flap, pivot on its hinge (axis X), opens upwards (moving part).
Axis: mating face at y = 0 facing +Y, body towards -Y, origin = face centre. Real size: about 190 mm long, 70 mm across."""
_MAT_DEFS.update({"M_CommandoBlue": ("#1F5FD6", 0.5, 0), "M_CommGrey": ("#B4B8BB", 0.55, 0), "M_CommInsert": ("#1A1C22", 0.6, 0),
                  "M_CommHole": ("#050506", 0.9, 0), "M_Brass": ("#C9A14A", 0.3, 1.0)})

def _tube(p, r_out, r_in, y0, y1, m, segs=32):
    """Open tube along Y (outer + inner wall + both end rings), centred on x = z = 0."""
    bm = p.bm; mi = p._mi(m); rings = []
    for (r, y) in ((r_out, y0), (r_out, y1), (r_in, y1), (r_in, y0)):
        rings.append([bm.verts.new(Vector((r * math.cos(2 * math.pi * k / segs), y, r * math.sin(2 * math.pi * k / segs))) - p.o)
                      for k in range(segs)])
    for a in range(4):
        A, B = rings[a], rings[(a + 1) % 4]
        for k in range(segs):
            f = bm.faces.new((A[k], A[(k + 1) % segs], B[(k + 1) % segs], B[k])); f.material_index = mi

def _ribs(p, y0, y1, r, n, m, depth=0.0015):
    for k in range(n):
        y = y0 + (y1 - y0) * (k + 0.5) / n
        p.cyl((0, 0, 0), "Y", y - 0.002, y + 0.002, r + depth, m, 24)

PIN_R = 0.016                                   # pin circle radius
PINS = [(-90, 0.0040, 0.024), (30, 0.0030, 0.022), (150, 0.0030, 0.022)]   # angle (deg, 0 = +X), radius, length; earth at 6 o'clock

def commando_meshes():
    if all(bpy.data.meshes.get(n) for n in ("commando_male", "commando_female", "commando_flap")):
        return {k: bpy.data.meshes[f"commando_{k}"] for k in ("male", "female", "flap")}
    B, G, IN, H, BR = M("M_CommandoBlue"), M("M_CommGrey"), M("M_CommInsert"), M("M_CommHole"), M("M_Brass")
    # ---- male plug ----
    m = Part("commando_male")
    _tube(m, 0.032, 0.027, -0.004, 0.026, B)                                    # shroud round the pins
    m.cyl((0, 0, 0), "Y", -0.006, -0.002, 0.0275, IN, 32)                      # pin carrier (dark)
    m.box(-0.006, 0.006, -0.004, 0.020, 0.031, 0.037, B)                        # key tab on top
    m.cyl((0, 0, 0), "Y", -0.020, -0.004, 0.036, B, 32)                         # face collar
    for (a, r, L) in PINS:
        x, z = PIN_R * math.cos(math.radians(a)), PIN_R * math.sin(math.radians(a))
        m.cyl((x, 0, z), "Y", -0.002, L - 0.002 - r, r, BR, 12)
        m.cyl((x, 0, z), "Y", L - 0.002 - r, L - 0.002, r * 0.75, BR, 12)       # rounded tip
    res = bmesh.ops.create_cone(m.bm, cap_ends=True, segments=32, radius1=0.024, radius2=0.032, depth=0.11,
                                matrix=Matrix.Translation(Vector((0, -0.075, 0)) - m.o) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    m._tag(res["verts"], G)                                                     # grey grip, tapering to the back
    _ribs(m, -0.12, -0.06, 0.027, 3, G)
    m.cyl((0, 0, 0), "Y", -0.165, -0.130, 0.022, G, 24)                         # cable nut
    m.cyl((0, 0, 0), "Y", -0.1655, -0.164, 0.009, H, 16)                        # cable entry
    male = m.mesh()
    # ---- female connector ----
    f = Part("commando_female")
    f.cyl((0, 0, 0), "Y", -0.060, 0.0, 0.035, B, 32)                            # front body
    f.cyl((0, 0, 0), "Y", 0.0, 0.0012, 0.029, IN, 32)                           # face insert
    for (a, r, L) in PINS:
        x, z = PIN_R * math.cos(math.radians(a)), PIN_R * math.sin(math.radians(a))
        f.cyl((x, 0, z), "Y", 0.0005, 0.0018, r + 0.0012, H, 12)                # contact holes
    _tube(f, 0.035, 0.030, 0.0, 0.004, B)                                       # rim round the insert
    for sx in (-0.022, 0.016):
        f.box(sx, sx + 0.006, -0.010, 0.004, 0.033, 0.042, B)                   # hinge lugs on top
    f.box(-0.008, 0.008, -0.008, 0.002, -0.040, -0.034, B)                      # latch catch at the bottom
    res = bmesh.ops.create_cone(f.bm, cap_ends=True, segments=32, radius1=0.026, radius2=0.033, depth=0.08,
                                matrix=Matrix.Translation(Vector((0, -0.100, 0)) - f.o) @ Matrix.Rotation(math.radians(-90), 4, "X"))
    f._tag(res["verts"], B)                                                     # rear body
    _ribs(f, -0.135, -0.075, 0.028, 2, B)
    f.cyl((0, 0, 0), "Y", -0.175, -0.140, 0.024, G, 24)                         # grey cable nut
    _ribs(f, -0.172, -0.143, 0.024, 4, G, 0.001)
    f.cyl((0, 0, 0), "Y", -0.1755, -0.174, 0.009, H, 16)
    female = f.mesh()
    # ---- flap (pivot on the hinge: origin = hinge axis, flap hangs down over the face when closed) ----
    fl = Part("commando_flap")
    fl.cyl((0, 0.0075, -0.037), "Y", 0.0, 0.006, 0.037, B, 32)                  # lid disc (centre 37 mm below the hinge)
    fl.box(-0.014, 0.014, 0.0, 0.010, -0.006, 0.004, B)                          # hinge knuckle
    fl.box(-0.010, 0.010, 0.006, 0.013, -0.078, -0.070, B)                       # thumb lip at the bottom
    flap = fl.mesh()
    return {"male": male, "female": female, "flap": flap}

def place_female(name, loc, rot_z, C, parent, flap_deg=0.0, face_down=False):
    """Female connector + its flap (moving part). rot_z turns the +Y face direction about Z; face_down hangs it face down."""
    me = commando_meshes()
    body = bpy.data.objects.new(name, me["female"]); C.objects.link(body); place(body, loc, parent)
    body.rotation_euler = (-math.pi / 2, 0, 0) if face_down else (0, 0, rot_z)
    fl = bpy.data.objects.new(f"{name}_flap", me["flap"]); C.objects.link(fl)
    fl.parent = body; fl.matrix_parent_inverse = Matrix.Identity(4); fl.location = (0, 0.0045, 0.037)
    fl.rotation_euler = (math.radians(flap_deg), 0, 0)
    moving(fl, "hinge", "X", [0, 100], tip="commando_flap", note="spring flap over the socket face")
    return body, fl

MATE_Z = 2.385                                                        # mating faces of a rack's pairs (mid-air, rack top -> basket)

def mated_pair_lod(p, x, y, z_top, cable_top, segs=10):
    """Simplified mated pair (for 60+ racks), hanging in mid-air above the rack (owner, 2026-10-04):
    rack PDU lead out of the rack top (z_top) up to the rack's MALE plug (grey grip, blue collar + shroud, facing up),
    plugged into the whip's FEMALE connector (blue, flap open, grey nut) facing down, whip cable up to cable_top.
    Mating faces at MATE_Z. Built into Part p (world coords)."""
    B, G, K, D = M("M_CommandoBlue"), M("M_CommGrey"), M("M_CableBlack"), M("M_CommInsert")
    zf = MATE_Z; zm = zf - 0.165                                       # male cable nut bottom
    p.cyl((x, y, 0), "Z", z_top, zm, 0.010, K, 6)                      # rack PDU lead out of the rack top
    p.cyl((x, y, 0), "Z", zm, zm + 0.035, 0.022, G, segs)              # male: cable nut
    p.cyl((x, y, 0), "Z", zm + 0.035, zm + 0.130, 0.027, G, segs)      # male: grey grip
    for zr in (zm + 0.060, zm + 0.085, zm + 0.110):
        p.cyl((x, y, 0), "Z", zr - 0.002, zr + 0.002, 0.0285, G, segs)  # grip ribs
    p.cyl((x, y, 0), "Z", zm + 0.130, zm + 0.150, 0.036, B, segs)      # male: blue face collar
    p.cyl((x, y, 0), "Z", zm + 0.150, zf, 0.032, B, segs)              # male: blue shroud
    p.cyl((x, y, 0), "Z", zf - 0.002, zf + 0.002, 0.0345, D, segs)     # dark seam where the two meet
    p.cyl((x, y, 0), "Z", zf + 0.002, zf + 0.060, 0.035, B, segs)      # female: front body
    p.cyl((x, y, 0), "Z", zf + 0.060, zf + 0.140, 0.030, B, segs)      # female: rear body
    p.cyl((x, y, 0), "Z", zf + 0.140, zf + 0.175, 0.024, G, segs)      # female: grey cable nut
    p.box(x - 0.028, x + 0.028, y + 0.036, y + 0.042, zf - 0.020, zf + 0.050, B)   # female: flap, open, lying back
    p.cyl((x, y, 0), "Z", zf + 0.175, cable_top, 0.010, K, 6)          # whip cable up to the tray / basket
