"""Headless Blender: bake high-poly detail into a tangent-space normal map (+ optional AO)
on a low-poly mesh (selected-to-active, Cycles).

in.json: {"high", "low"?, "resolution", "ao", "output", "normal_map", "ao_map"?}
If "low" is omitted, the high mesh is decimated to make the low-poly target.
out.json: {"ok", "output", "normal_map", "ao_map"?, "resolution", "low_faces"}
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402
from _common import export_mesh, import_mesh, payload, reset, run  # noqa: E402


def _join_selected(objs, name):
    for o in bpy.data.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    return obj


def _ensure_uv(obj):
    if not obj.data.uv_layers:
        for o in bpy.data.objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.151917)
        bpy.ops.object.mode_set(mode="OBJECT")


def _bake_target_material(obj, res):
    mat = bpy.data.materials.new("clay_baked")
    mat.use_nodes = True
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    nt = mat.node_tree
    img = bpy.data.images.new("clay_normal", res, res, alpha=False)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.nodes.active = tex
    return mat, nt, tex, img


def main():
    p = payload()
    res = int(p.get("resolution", 1024))
    want_ao = bool(p.get("ao", False))
    reset()

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8

    # High-poly source.
    import_mesh(p["high"])
    high = _join_selected([o for o in bpy.data.objects if o.type == "MESH"], "HIGH")

    # Low-poly target: provided, or decimate the high.
    if p.get("low"):
        before = {o.name for o in bpy.data.objects}
        import_mesh(p["low"])
        low = _join_selected(
            [o for o in bpy.data.objects if o.type == "MESH" and o.name not in before], "LOW"
        )
    else:
        low = high.copy()
        low.data = high.data.copy()
        low.name = "LOW"
        scene.collection.objects.link(low)
        dec = low.modifiers.new("dec", "DECIMATE")
        dec.ratio = 0.1
        bpy.context.view_layer.objects.active = low
        bpy.ops.object.modifier_apply(modifier="dec")

    _ensure_uv(low)
    mat, nt, tex, img = _bake_target_material(low, res)

    bake = scene.render.bake
    bake.use_selected_to_active = True
    bake.cage_extrusion = 0.08

    # Normal bake (tangent space).
    for o in bpy.data.objects:
        o.select_set(False)
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    img.filepath_raw = p["normal_map"]
    img.file_format = "PNG"
    os.makedirs(os.path.dirname(os.path.abspath(p["normal_map"])), exist_ok=True)
    img.save()
    tex.image.colorspace_settings.name = "Non-Color"

    # Wire the normal map into the material for the exported low mesh.
    nm = nt.nodes.new("ShaderNodeNormalMap")
    bsdf = nt.nodes.get("Principled BSDF")
    nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
    if bsdf:
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    result = {
        "ok": True,
        "output": p["output"],
        "normal_map": p["normal_map"],
        "resolution": res,
        "low_faces": len(low.data.polygons),
    }

    if want_ao and p.get("ao_map"):
        ao_img = bpy.data.images.new("clay_ao", res, res, alpha=False)
        ao_tex = nt.nodes.new("ShaderNodeTexImage")
        ao_tex.image = ao_img
        nt.nodes.active = ao_tex
        scene.cycles.samples = 64
        bpy.ops.object.bake(type="AO")
        ao_img.filepath_raw = p["ao_map"]
        ao_img.file_format = "PNG"
        ao_img.save()
        result["ao_map"] = p["ao_map"]

    export_mesh(p["output"])
    return result


run(main)
