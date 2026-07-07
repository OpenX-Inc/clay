"""Blender-backed tools (FBX export now; rig / retopo / bake later).

All fail *visibly* when Blender isn't available — Clay never fakes output.
"""

from __future__ import annotations

from pathlib import Path

from clay.blender import BlenderError
from clay.blender import export_fbx as _export_fbx
from clay.tools.context import ToolContext
from clay.tools.registry import tool
from clay.tools.result import error, ok


@tool(
    "export_fbx",
    "Convert an existing mesh (glb/obj/ply/stl/fbx) to FBX via headless Blender, "
    "preserving meshes + UVs (+ skeleton later).",
    {"input_path": "string", "output_path": "string?"},
)
def export_fbx(ctx: ToolContext, args: dict) -> dict:
    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    out = (
        Path(args["output_path"])
        if args.get("output_path")
        else ctx.output_dir / f"{src.stem}.fbx"
    )
    try:
        res = _export_fbx(src, out, blender=ctx.config.blender.path or None)
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(path=str(out), faces=res.get("faces"), mesh_count=res.get("mesh_count"))


@tool(
    "retopo_asset",
    "Retopologize a mesh to clean quad-dominant topology (Quadriflow) with UVs "
    "re-unwrapped — for anything animated/deformable. Blender-backed.",
    {
        "input_path": "string",
        "target_faces": {"type": "integer", "minimum": 20, "optional": True},
        "quads": "boolean?",
        "output_path": "string?",
    },
)
def retopo_asset(ctx: ToolContext, args: dict) -> dict:
    from clay.blender import retopo as _retopo

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    out = (
        Path(args["output_path"])
        if args.get("output_path")
        else ctx.output_dir / f"{src.stem}_retopo.glb"
    )
    try:
        res = _retopo(
            src, out,
            target_faces=int(args.get("target_faces", 5000)),
            quads=bool(args.get("quads", True)),
            blender=ctx.config.blender.path or None,
        )
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(path=str(out), faces=res.get("faces"), quads=res.get("quads"),
              quad_ratio=res.get("quad_ratio"))


@tool(
    "bake_normals",
    "Bake high-poly detail into a tangent-space normal map (+ optional AO) on a "
    "low-poly mesh. If low is omitted, the high mesh is decimated. Blender-backed.",
    {
        "high_path": "string",
        "low_path": "string?",
        "resolution": {"type": "integer", "minimum": 64, "optional": True},
        "ao": "boolean?",
    },
)
def bake_normals(ctx: ToolContext, args: dict) -> dict:
    from clay.blender import bake_normals as _bake

    high = Path(args["high_path"])
    if not high.exists():
        return error("not_found", f"no mesh at {high}")
    low_path = args.get("low_path")
    if low_path and not Path(low_path).exists():
        return error("not_found", f"no low mesh at {low_path}")
    ao = bool(args.get("ao", False))
    out_mesh = ctx.output_dir / f"{high.stem}_baked.glb"
    normal = ctx.output_dir / f"{high.stem}_normal.png"
    ao_map = ctx.output_dir / f"{high.stem}_ao.png" if ao else None
    try:
        res = _bake(
            high, out_mesh, normal,
            low_path=low_path,
            resolution=int(args.get("resolution", 1024)),
            ao=ao, ao_map=ao_map,
            blender=ctx.config.blender.path or None,
        )
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(
        path=str(out_mesh), normal_map=str(normal), ao_map=res.get("ao_map"),
        resolution=res.get("resolution"), low_faces=res.get("low_faces"),
    )


@tool(
    "rig_asset",
    "Auto-rig a mesh per profile → skinned/parented FBX. humanoid=biped, "
    "quadruped=4-leg, vehicle=split body+wheels with per-wheel bones/sockets, "
    "generic=bone chain. Heuristic/best-effort. Blender-backed.",
    {
        "input_path": "string",
        "rig_type": {
            "type": "string",
            "enum": ["humanoid", "quadruped", "vehicle", "generic"],
            "optional": True,
        },
        "options": "object?",
    },
)
def rig_asset(ctx: ToolContext, args: dict) -> dict:
    from clay.blender import rig_asset as _rig

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    rig_type = args.get("rig_type", "generic")
    out = ctx.output_dir / f"{src.stem}_rigged.fbx"
    try:
        res = _rig(
            src, out, rig_type=rig_type,
            options=args.get("options") or {},
            blender=ctx.config.blender.path or None,
        )
    except BlenderError as err:
        return error("blender_unavailable", str(err))
    return ok(
        path=str(out), rig_type=res.get("rig_type"), bones=res.get("bones"),
        wheels=res.get("wheels"),
    )
