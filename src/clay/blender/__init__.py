"""Headless Blender engine — Clay's mesh-processing backend (FBX/rig/retopo/bake)."""

from __future__ import annotations

from clay.blender.engine import (
    BlenderError,
    available,
    require_blender,
    resolve_blender,
    run_script,
)
from clay.blender.ops import bake_normals, export_fbx, retopo

__all__ = [
    "BlenderError",
    "available",
    "resolve_blender",
    "require_blender",
    "run_script",
    "export_fbx",
    "retopo",
    "bake_normals",
]
