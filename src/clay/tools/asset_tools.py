"""Clay's asset tools — the one registry the agent and MCP both drive.

- ``generate_asset``   image/text → game-ready 3D via the pipeline (needs a
                       deployed GPU backend).
- ``remesh_asset``     decimate an existing mesh to a triangle budget (CPU-only).
- ``list_assets``      list generated assets in the output directory.
- ``list_providers``   the available 3D model providers + their modes.
"""

from __future__ import annotations

import io
from pathlib import Path

from clay.tools.context import ToolContext
from clay.tools.registry import tool
from clay.tools.result import error, ok

_MESH_EXTS = {".glb", ".obj", ".ply", ".fbx", ".stl"}


@tool(
    "generate_asset",
    "Generate a game-ready 3D asset from an image or a text prompt. Requires a "
    "deployed GPU backend ([gpu_backend].url).",
    {
        "mode": {"type": "string", "enum": ["image", "text"], "description": "input kind"},
        "prompt": "string?",
        "image_path": "string?",
        "format": {"type": "string", "enum": ["glb", "obj"], "optional": True},
        "target_tris": {"type": "integer", "minimum": 100, "optional": True},
    },
    generates=True,
)
def generate_asset(ctx: ToolContext, args: dict) -> dict:
    from clay.pipeline import Pipeline
    from clay.providers import get_provider
    from clay.schemas import GenerationRequest, GenMode

    mode = GenMode(args.get("mode", "image"))
    if mode == GenMode.image and not args.get("image_path"):
        return error("invalid", "image mode needs image_path")
    if mode == GenMode.text and not args.get("prompt"):
        return error("invalid", "text mode needs prompt")

    try:
        provider = get_provider(ctx.config.providers.model)
    except ValueError as err:
        return error("unknown_provider", str(err))
    if not provider.supports(mode):
        return error("unsupported", f"{provider.name} does not support {mode} → 3D")

    pp = ctx.config.postprocess
    request = GenerationRequest(
        mode=mode,
        prompt=args.get("prompt", ""),
        image_path=args.get("image_path"),
        format=args.get("format", pp.format),
        target_tris=int(args.get("target_tris", pp.target_tris)),
        unwrap_uvs=pp.unwrap_uvs,
        pbr=pp.pbr,
    )
    asset = Pipeline(ctx.config).run(request, out_path=None)
    return ok(path=str(asset.path), triangles=asset.triangles,
              format=asset.format, provider=asset.provider)


@tool(
    "remesh_asset",
    "Decimate an existing mesh down to a triangle budget and re-export. CPU-only.",
    {
        "input_path": "string",
        "target_tris": {"type": "integer", "minimum": 100},
        "format": {"type": "string", "enum": ["glb", "obj", "ply"], "optional": True},
        "output_path": "string?",
    },
)
def remesh_asset(ctx: ToolContext, args: dict) -> dict:
    import trimesh

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    target = int(args["target_tris"])
    fmt = args.get("format") or src.suffix.lstrip(".") or "glb"

    mesh = trimesh.load(src, force="mesh")
    before = int(len(mesh.faces))
    if before > target:
        mesh = mesh.simplify_quadric_decimation(face_count=target)
    out = Path(args["output_path"]) if args.get("output_path") else (
        ctx.output_dir / f"{src.stem}_remesh.{fmt}"
    )
    buf = io.BytesIO()
    mesh.export(buf, file_type=fmt)
    out.write_bytes(buf.getvalue())
    return ok(path=str(out), triangles=int(len(mesh.faces)), triangles_before=before,
              format=fmt)


@tool("list_assets", "List generated 3D assets in the output directory.")
def list_assets(ctx: ToolContext, args: dict) -> dict:
    assets = [
        {"name": p.name, "path": str(p), "size": p.stat().st_size}
        for p in sorted(ctx.output_dir.glob("*"))
        if p.suffix.lower() in _MESH_EXTS
    ]
    return ok(assets=assets, count=len(assets))


@tool(
    "generate_variations",
    "Generate N seed-varied variations of a prop/livery via the shape model — "
    "for populating streets or building a catalogue. Needs a deployed GPU backend.",
    {
        "mode": {"type": "string", "enum": ["image", "text"], "optional": True},
        "prompt": "string?",
        "image_path": "string?",
        "count": {"type": "integer", "minimum": 1, "optional": True},
        "seed": {"type": "integer", "optional": True},
    },
    generates=True,
)
def generate_variations(ctx: ToolContext, args: dict) -> dict:
    from clay.variations import generate_variations as _gv

    mode = args.get("mode", "image")
    if mode == "image" and not args.get("image_path"):
        return error("invalid", "image mode needs image_path")
    if mode == "text" and not args.get("prompt"):
        return error("invalid", "text mode needs prompt")
    try:
        res = _gv(
            ctx.config, mode=mode,
            prompt=args.get("prompt"), image_path=args.get("image_path"),
            count=int(args.get("count", 4)), seed=int(args.get("seed", 0)),
            out_dir=ctx.output_dir,
        )
    except RuntimeError as err:
        return error("no_backend", str(err))
    return ok(**res)


@tool("list_providers", "List the available 3D model providers and their modes.")
def list_providers(ctx: ToolContext, args: dict) -> dict:
    from clay.providers import available_providers, get_provider

    provs = []
    for name in available_providers():
        p = get_provider(name)
        provs.append({"name": name, "modes": list(p.modes),
                      "license": p.license, "description": p.description})
    return ok(providers=provs, active=ctx.config.providers.model)
