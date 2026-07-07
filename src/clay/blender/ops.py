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
