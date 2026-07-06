"""Data models for the Clay pipeline (requests + generated assets)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class GenMode(str, Enum):
    image = "image"  # image → 3D
    text = "text"    # text → 3D


class GenerationRequest(BaseModel):
    """One image/text → 3D request."""

    mode: GenMode
    prompt: str = ""
    image_path: str | None = None      # for image → 3D
    image_b64: str | None = None       # inline image (backend contract)
    target_tris: int = 60000
    format: str = "glb"                # glb | obj | fbx
    unwrap_uvs: bool = True
    pbr: bool = True


class Texture(BaseModel):
    """A PBR texture map."""

    kind: str          # base_color | normal | roughness | metallic | ...
    path: str | None = None
    url: str | None = None


class Generated3DAsset(BaseModel):
    """A generated (and optionally post-processed) 3D asset."""

    path: str                          # local mesh file
    format: str = "glb"
    triangles: int = 0
    provider: str = ""
    textures: list[Texture] = []
    raw_path: str | None = None        # pre-post-processing mesh, if kept
