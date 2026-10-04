"""Viewport helper for live checks (not part of the build): look(eye, target, lens)."""
import bpy, mathutils
def look(eye, target, lens=24):
    for a in bpy.context.screen.areas:
        if a.type == "VIEW_3D":
            sp = a.spaces[0]; sp.lens = lens; r3 = sp.region_3d
            e, t = mathutils.Vector(eye), mathutils.Vector(target)
            r3.view_perspective = "PERSP"; r3.view_location = t; r3.view_distance = (e - t).length
            r3.view_rotation = (e - t).to_track_quat("Z", "Y")
