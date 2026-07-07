"""Headless Blender: retopologize a mesh to clean quad-dominant topology (Quadriflow).

in.json: {"input", "output", "target_faces", "quads"}
out.json: {"ok", "output", "faces", "quads", "quad_ratio"}
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import bpy  # noqa: E402
from _common import export_mesh, import_mesh, join_meshes, payload, reset, run  # noqa: E402


def main():
    p = payload()
    target = int(p.get("target_faces", 5000))
    reset()
    import_mesh(p["input"])
    obj = join_meshes()

    bpy.ops.object.quadriflow_remesh(mode="FACES", target_faces=target)

    # Re-unwrap UVs on the fresh topology.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=1.151917)
    bpy.ops.object.mode_set(mode="OBJECT")

    export_mesh(p["output"])
    polys = obj.data.polygons
    faces = len(polys)
    quads = sum(1 for poly in polys if len(poly.vertices) == 4)
    return {
        "ok": True,
        "output": p["output"],
        "faces": faces,
        "quads": quads,
        "quad_ratio": round(quads / max(1, faces), 3),
    }


run(main)
