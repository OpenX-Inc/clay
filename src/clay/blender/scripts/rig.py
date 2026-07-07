"""Headless Blender: heuristic per-profile auto-rig → skinned/parented FBX.

Profiles: humanoid (biped), quadruped, vehicle (split body + wheels, per-wheel
bones/sockets), generic (bone chain along the longest axis). Skeletons are
positioned from mesh bounds and bound with automatic weights (deforming
profiles) or rigid bone-parenting (vehicle). Best-effort, not production-perfect.

in.json: {"input", "output", "rig_type", "options"}
out.json: {"ok", "output", "rig_type", "bones", "wheels"?}
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402
import mathutils  # noqa: E402
from _common import export_mesh, import_mesh, join_meshes, payload, reset, run  # noqa: E402


def _bounds(objs):
    cs = []
    for obj in objs:
        cs += [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
    mn = mathutils.Vector((min(c.x for c in cs), min(c.y for c in cs), min(c.z for c in cs)))
    mx = mathutils.Vector((max(c.x for c in cs), max(c.y for c in cs), max(c.z for c in cs)))
    return mn, mx


def _armature():
    data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", data)
    bpy.context.scene.collection.objects.link(arm)
    return arm


def _bind_auto(mesh_obj, arm):
    for o in bpy.data.objects:
        o.select_set(False)
    mesh_obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    for mode in ("ARMATURE_AUTO", "ARMATURE_ENVELOPE", "ARMATURE_NAME"):
        try:
            bpy.ops.object.parent_set(type=mode)
            return
        except Exception:
            continue


def _deforming_rig(mesh_obj, bone_fn):
    """Create an armature, let bone_fn place bones, bind mesh with auto weights."""
    arm = _armature()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    mn, mx = _bounds([mesh_obj])
    bone_fn(arm.data.edit_bones, mn, mx)
    n = len(arm.data.edit_bones)
    bpy.ops.object.mode_set(mode="OBJECT")
    _bind_auto(mesh_obj, arm)
    return n


def _chain(eb, mn, mx, segments, name="Bone"):
    axis = max(range(3), key=lambda i: (mx - mn)[i])  # longest axis
    lo, hi = mn[axis], mx[axis]
    center = [(mn[i] + mx[i]) / 2 for i in range(3)]
    prev = None
    for s in range(segments):
        b = eb.new(f"{name}_{s}")
        h = [*center]
        t = [*center]
        h[axis] = lo + (hi - lo) * s / segments
        t[axis] = lo + (hi - lo) * (s + 1) / segments
        b.head, b.tail = h, t
        if prev:
            b.parent = prev
            b.use_connect = True
        prev = b


def _biped(eb, mn, mx):
    h = mx.z - mn.z
    cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
    w = mx.x - mn.x

    def add(name, z0, z1, parent=None, x=0.0):
        b = eb.new(name)
        b.head = (cx + x, cy, mn.z + z0 * h)
        b.tail = (cx + x, cy, mn.z + z1 * h)
        if parent:
            b.parent = parent
        return b

    hips = add("Hips", 0.50, 0.58)
    spine = add("Spine", 0.58, 0.70, hips)
    chest = add("Chest", 0.70, 0.82, spine)
    neck = add("Neck", 0.82, 0.88, chest)
    add("Head", 0.88, 1.0, neck)
    for side, sx in (("L", -1), ("R", 1)):
        thigh = eb.new(f"UpperLeg_{side}")
        thigh.head = (cx + sx * 0.12 * w, cy, mn.z + 0.50 * h)
        thigh.tail = (cx + sx * 0.12 * w, cy, mn.z + 0.28 * h)
        thigh.parent = hips
        shin = eb.new(f"LowerLeg_{side}")
        shin.head = thigh.tail
        shin.tail = (cx + sx * 0.12 * w, cy, mn.z + 0.04 * h)
        shin.parent = thigh
        foot = eb.new(f"Foot_{side}")
        foot.head = shin.tail
        foot.tail = (cx + sx * 0.12 * w, cy - 0.10 * (mx.y - mn.y), mn.z)
        foot.parent = shin
        up = eb.new(f"UpperArm_{side}")
        up.head = (cx + sx * 0.14 * w, cy, mn.z + 0.80 * h)
        up.tail = (cx + sx * 0.30 * w, cy, mn.z + 0.78 * h)
        up.parent = chest
        fore = eb.new(f"LowerArm_{side}")
        fore.head = up.tail
        fore.tail = (cx + sx * 0.44 * w, cy, mn.z + 0.76 * h)
        fore.parent = up
        hand = eb.new(f"Hand_{side}")
        hand.head = fore.tail
        hand.tail = (cx + sx * 0.52 * w, cy, mn.z + 0.75 * h)
        hand.parent = fore


def _quadruped(eb, mn, mx):
    # spine along the longest horizontal axis + 4 legs down to the floor
    ax = 0 if (mx.x - mn.x) >= (mx.y - mn.y) else 1
    other = 1 - ax
    zmid = mn.z + 0.6 * (mx.z - mn.z)
    a0, a1 = mn[ax], mx[ax]
    oc = (mn[other] + mx[other]) / 2

    def pt(a, o, z):
        v = [0, 0, 0]
        v[ax], v[other], v[2] = a, o, z
        return tuple(v)

    spine = eb.new("Spine")
    spine.head = pt(a0 + 0.15 * (a1 - a0), oc, zmid)
    spine.tail = pt(a1 - 0.15 * (a1 - a0), oc, zmid)
    ow = mx[other] - mn[other]
    for i, af in enumerate((0.2, 0.8)):
        for side, sf in (("L", -0.3), ("R", 0.3)):
            leg = eb.new(f"Leg_{i}_{side}")
            leg.head = pt(a0 + af * (a1 - a0), oc + sf * ow, zmid)
            leg.tail = pt(a0 + af * (a1 - a0), oc + sf * ow, mn.z)
            leg.parent = spine


def _vehicle(mesh_obj, options):
    """Split loose parts, detect wheels, rig body + per-wheel bones (rigid parenting)."""
    bpy.context.view_layer.objects.active = mesh_obj
    for o in bpy.data.objects:
        o.select_set(False)
    mesh_obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

    parts = [o for o in bpy.data.objects if o.type == "MESH"]
    mn, mx = _bounds(parts)
    height = max(mx.z - mn.z, 1e-6)
    body_w = mx.x - mn.x

    wheels, body = [], []
    for p in parts:
        pmn, pmx = _bounds([p])
        pw, pd, ph = pmx.x - pmn.x, pmx.y - pmn.y, pmx.z - pmn.z
        low = pmx.z < mn.z + 0.45 * height
        roundish = abs(pw - pd) < 0.4 * max(pw, pd, 1e-6)
        smallish = max(pw, pd) < 0.5 * max(body_w, 1e-6)
        if low and roundish and smallish and ph < 0.5 * height:
            wheels.append(p)
        else:
            body.append(p)

    arm = _armature()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.data.edit_bones
    root = eb.new("Root")
    root.head = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)
    root.tail = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.15 * height)
    body_bone = eb.new("Body")
    body_bone.head = root.tail
    body_bone.tail = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + 0.6 * height)
    body_bone.parent = root
    wheel_names = []
    for i, wobj in enumerate(wheels):
        wmn, wmx = _bounds([wobj])
        c = ((wmn.x + wmx.x) / 2, (wmn.y + wmx.y) / 2, (wmn.z + wmx.z) / 2)
        wb = eb.new(f"Wheel_{i}")
        wb.head = c
        wb.tail = (c[0], c[1] + 0.1 * max(wmx.y - wmn.y, 1e-3), c[2])
        wb.parent = root
        wheel_names.append(f"Wheel_{i}")
    bone_count = len(eb)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Rigid parent each part to its bone (object → bone).
    def parent_to_bone(obj, bone_name):
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = bone_name
        obj.matrix_parent_inverse = arm.matrix_world.inverted()

    for wobj, bname in zip(wheels, wheel_names):
        parent_to_bone(wobj, bname)
    for bobj in body:
        parent_to_bone(bobj, "Body")

    return bone_count, len(wheels)


def main():
    p = payload()
    rig_type = p.get("rig_type", "generic")
    options = p.get("options") or {}
    reset()
    import_mesh(p["input"])
    mesh_obj = join_meshes()

    wheels = None
    if rig_type == "humanoid":
        bones = _deforming_rig(mesh_obj, _biped)
    elif rig_type == "quadruped":
        bones = _deforming_rig(mesh_obj, _quadruped)
    elif rig_type == "vehicle":
        bones, wheels = _vehicle(mesh_obj, options)
    else:  # generic
        bones = _deforming_rig(mesh_obj, lambda eb, mn, mx: _chain(eb, mn, mx, 4))

    export_mesh(p["output"])
    result = {"ok": True, "output": p["output"], "rig_type": rig_type, "bones": bones}
    if wheels is not None:
        result["wheels"] = wheels
    return result


run(main)
