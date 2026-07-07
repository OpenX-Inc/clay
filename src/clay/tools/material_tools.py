"""Material + texture generation tools (GPU-gated — fail visibly, never fake output)."""

from __future__ import annotations

from pathlib import Path

import httpx

from clay.tools.context import ToolContext
from clay.tools.registry import tool
from clay.tools.result import error, ok


@tool(
    "generate_material",
    "Generate a tiling PBR material set (base_color/normal/roughness/metallic/ao) "
    "+ a material.json manifest from a prompt/image. De-greys greybox surfaces. "
    "GPU-gated (needs a deployed material backend).",
    {
        "prompt": "string?",
        "image_path": "string?",
        "kind": {
            "type": "string",
            "enum": ["facade", "road", "ground", "concrete", "glass", "generic"],
            "optional": True,
        },
        "resolution": {"type": "integer", "minimum": 128, "optional": True},
        "tiling": "boolean?",
    },
)
def generate_material(ctx: ToolContext, args: dict) -> dict:
    from clay.material import MaterialGenerator

    if not args.get("prompt") and not args.get("image_path"):
        return error("invalid", "provide a prompt or an image_path")
    if args.get("image_path") and not Path(args["image_path"]).exists():
        return error("not_found", f"no image at {args['image_path']}")
    kind = args.get("kind", "generic")
    try:
        res = MaterialGenerator(ctx.config).generate(
            kind=kind,
            prompt=args.get("prompt"),
            image_path=args.get("image_path"),
            resolution=int(args.get("resolution", 1024)),
            tiling=args.get("tiling"),
            out_dir=ctx.output_dir,
            stem=f"{kind}_material",
        )
    except RuntimeError as err:
        return error("no_backend", str(err))
    except httpx.HTTPStatusError as err:
        return error("gpu_gated", f"backend {err.response.status_code}: {err.response.text[:200]}")
    return ok(**res)


@tool(
    "texture_asset",
    "Paint / re-skin an existing mesh from a prompt/image onto its own UVs "
    "(character skins, prop variants, vehicle liveries). Optional decal PNGs. "
    "GPU-gated (needs a deployed texture backend).",
    {
        "input_path": "string",
        "prompt": "string?",
        "image_path": "string?",
        "resolution": {"type": "integer", "minimum": 128, "optional": True},
        "keep_uvs": "boolean?",
        "emit_decals": "boolean?",
    },
)
def texture_asset(ctx: ToolContext, args: dict) -> dict:
    from clay.texture import TextureAssetGenerator

    src = Path(args["input_path"])
    if not src.exists():
        return error("not_found", f"no mesh at {src}")
    if not args.get("prompt") and not args.get("image_path"):
        return error("invalid", "provide a prompt or an image_path")
    try:
        res = TextureAssetGenerator(ctx.config).texture(
            src,
            prompt=args.get("prompt"),
            image_path=args.get("image_path"),
            resolution=int(args.get("resolution", 1024)),
            keep_uvs=bool(args.get("keep_uvs", True)),
            emit_decals=bool(args.get("emit_decals", False)),
            out_dir=ctx.output_dir,
        )
    except RuntimeError as err:
        return error("no_backend", str(err))
    except httpx.HTTPStatusError as err:
        return error("gpu_gated", f"backend {err.response.status_code}: {err.response.text[:200]}")
    return ok(**res)
