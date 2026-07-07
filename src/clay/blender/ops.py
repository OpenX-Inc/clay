"""High-level headless-Blender operations (thin wrappers over ``engine.run_script``)."""

from __future__ import annotations

from pathlib import Path

from clay.blender.engine import run_script


def export_fbx(
    input_path: str | Path, output_path: str | Path, *, blender: str | None = None
) -> dict:
    """Convert a mesh (glb/obj/fbx/stl/ply) to FBX via Blender. Returns the script result."""
    return run_script(
        "fbx_export.py",
        {"input": str(input_path), "output": str(output_path)},
        blender=blender,
    )


def retopo(
    input_path: str | Path,
    output_path: str | Path,
    *,
    target_faces: int = 5000,
    quads: bool = True,
    blender: str | None = None,
) -> dict:
    """Retopologize a mesh (Quadriflow) to clean quad topology + re-unwrap UVs."""
    return run_script(
        "retopo.py",
        {
            "input": str(input_path),
            "output": str(output_path),
            "target_faces": int(target_faces),
            "quads": bool(quads),
        },
        blender=blender,
        timeout=1800,
    )


def bake_normals(
    high_path: str | Path,
    output_path: str | Path,
    normal_map: str | Path,
    *,
    low_path: str | Path | None = None,
    resolution: int = 1024,
    ao: bool = False,
    ao_map: str | Path | None = None,
    blender: str | None = None,
) -> dict:
    """Bake high→low tangent-space normal map (+ optional AO). Returns script result."""
    data: dict = {
        "high": str(high_path),
        "output": str(output_path),
        "normal_map": str(normal_map),
        "resolution": int(resolution),
        "ao": bool(ao),
    }
    if low_path:
        data["low"] = str(low_path)
    if ao and ao_map:
        data["ao_map"] = str(ao_map)
    return run_script("bake_normals.py", data, blender=blender, timeout=1800)
