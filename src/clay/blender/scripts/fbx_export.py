"""Headless Blender script: import a mesh and export it as FBX.

Invoked by ``clay.blender.engine.run_script`` as::

    blender -b --factory-startup --python fbx_export.py -- <in.json> <out.json>

in.json: {"input": "<mesh path>", "output": "<fbx path>"}
out.json: {"ok": true, "output": ..., "mesh_count": n, "faces": n}
"""

import json
import os
import sys

import bpy


def _io_paths():
    argv = sys.argv
    idx = argv.index("--")
    return argv[idx + 1], argv[idx + 2]


def _reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _import(path):
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


def main():
    in_path, out_path = _io_paths()
    payload = json.load(open(in_path))
    src, dst = payload["input"], payload["output"]
    _reset()
    _import(src)
    out_dir = os.path.dirname(os.path.abspath(dst))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=dst,
        use_selection=False,
        apply_unit_scale=True,
        path_mode="COPY",
        embed_textures=True,
        mesh_smooth_type="FACE",
    )
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    faces = sum(len(o.data.polygons) for o in meshes)
    return {"ok": True, "output": dst, "mesh_count": len(meshes), "faces": faces}


try:
    _result = main()
except Exception as err:  # noqa: BLE001
    import traceback

    _result = {
        "ok": False,
        "error": f"{type(err).__name__}: {err}",
        "trace": traceback.format_exc()[-800:],
    }

json.dump(_result, open(sys.argv[sys.argv.index("--") + 2], "w"))
