"""PDC breaker panel on its own (the panel itself is in _pdc_panel.py, also used inside the PDC by 74_hall_pdc.py).
Grey plate with 4 corner screws. Saved to assets/blender/pdc_panel.blend (the hall is not touched)."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
exec(open(os.path.join(HERE, "_pdc_panel.py")).read())
BLEND = os.path.join(ROOT, "assets", "blender", "pdc_panel.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
C = coll("pdc_panel"); root = bpy.data.objects.new("pdc_panel_root", None); C.objects.link(root)
MARGIN = 0.05; pw, ph_ = PANEL_W + 2 * MARGIN, PANEL_H + 2 * MARGIN + 0.04
p = Part("pdc_panel_plate")
p.box(-pw / 2, pw / 2, 0, 0.012, 0, ph_, M("M_PanelGrey"))
for (sx, sz) in ((-pw / 2 + 0.025, 0.025), (pw / 2 - 0.025, 0.025), (-pw / 2 + 0.025, ph_ - 0.025), (pw / 2 - 0.025, ph_ - 0.025)):
    p.cyl((sx, 0, sz), "Y", -0.004, 0, 0.008, M("M_Screw"), 12)
breaker_panel(p, 0.0, 0.0, MARGIN, C, root, "panel")
p.build(C, root)
print("PDC_PANEL_REPORT", {"size_m": [round(pw, 3), round(ph_, 3)], "tris": tris(C)})
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
