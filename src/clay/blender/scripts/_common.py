"""Shared helpers for Clay's headless Blender scripts (import / export / io).

Imported *inside* Blender only (each script adds its own dir to sys.path). Never
imported by the clay package in normal use.
"""

import json
import os
import sys

import bpy


def io_paths():
    idx = sys.argv.index("--")
    return sys.argv[idx + 1], sys.argv[idx + 2]


def payload():
    return json.load(open(io_paths()[0]))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_mesh(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".stl":
        try:
            bpy.ops.wm.stl_import(filepath=path)
        except Exception:
            bpy.ops.import_mesh.stl(filepath=path)
    elif ext == ".ply":
        try:
            bpy.ops.wm.ply_import(filepath=path)
        except Exception:
            bpy.ops.import_mesh.ply(filepath=path)
    else:
        raise ValueError(f"unsupported input format: {ext}")


def export_mesh(path):
    ext = os.path.splitext(path)[1].lower()
    out_dir = os.path.dirname(os.path.abspath(path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    if ext in (".glb", ".gltf"):
        bpy.ops.export_scene.gltf(
            filepath=path, export_format="GLB" if ext == ".glb" else "GLTF_SEPARATE"
        )
    elif ext == ".obj":
        bpy.ops.wm.obj_export(filepath=path)
    elif ext == ".fbx":
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=False, path_mode="COPY", embed_textures=True
        )
    elif ext == ".ply":
        try:
            bpy.ops.wm.ply_export(filepath=path)
        except Exception:
            bpy.ops.export_mesh.ply(filepath=path)
    elif ext == ".stl":
        try:
            bpy.ops.wm.stl_export(filepath=path)
        except Exception:
            bpy.ops.export_mesh.stl(filepath=path)
    else:
        raise ValueError(f"unsupported output format: {ext}")


def join_meshes():
    """Select every mesh, join into one active object, return it."""
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise ValueError("no mesh found in input")
    for o in bpy.data.objects:
        o.select_set(o.type == "MESH")
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def run(main):
    """Run ``main`` and write its result dict (or an error) to the out.json path."""
    out = sys.argv[sys.argv.index("--") + 2]
    try:
        result = main()
    except Exception as err:  # noqa: BLE001
        import traceback

        result = {
            "ok": False,
            "error": f"{type(err).__name__}: {err}",
            "trace": traceback.format_exc()[-800:],
        }
    json.dump(result, open(out, "w"))
