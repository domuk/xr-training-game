"""Commando connectors on their own (models in _commando.py). Saved to assets/blender/commando.blend:
male plug at x = -0.12, female connector (flap open) at x = +0.12, both facing -Y (towards the viewer)."""
import bpy, math
import os
HERE = bpy.path.abspath("//scripts")
exec(open(os.path.join(HERE, "_hall.py")).read())
exec(open(os.path.join(HERE, "_commando.py")).read())
BLEND = os.path.join(ROOT, "assets", "blender", "commando.blend")
bpy.ops.wm.read_factory_settings(use_empty=True)
C = coll("commando"); root = bpy.data.objects.new("commando_root", None); C.objects.link(root)
me = commando_meshes()
male = bpy.data.objects.new("commando_male", me["male"]); C.objects.link(male); place(male, (-0.12, 0, 0.05), root)
male.rotation_euler = (0, 0, math.pi)
place_female("commando_female", (0.12, 0, 0.05), math.pi, C, root, flap_deg=95)
print("COMMANDO_REPORT", {"tris": tris(C)})
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
