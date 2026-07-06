"""Game-ready post-processing — the point of Clay.

Raw AI meshes are unusable in games (500k-tri blobs, messy UVs). This turns them
into production-ready assets: decimate to a triangle budget, re-unwrap UVs, and
export in a real game format. Heavy geometry deps (trimesh/xatlas/…) are lazily
imported so the core stays light — install the ``postprocess`` extra to use it.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from clay.config import PostprocessConfig
from clay.schemas import Generated3DAsset


class PostProcessor:
    """Remesh/decimate → UV unwrap → export a game-ready asset."""

    def __init__(self, config: PostprocessConfig) -> None:
        self.config = config

    def process(self, asset: Generated3DAsset, out_path: str | None = None) -> Generated3DAsset:
        """Post-process a raw asset into a game-ready one."""
        import trimesh

        mesh = trimesh.load(asset.path, force="mesh")
        mesh = self.decimate(mesh, self.config.target_tris)
        if self.config.unwrap_uvs:
            mesh = self.unwrap(mesh)

        fmt = self.config.format
        out = Path(out_path) if out_path else Path(
            tempfile.mkdtemp(prefix="clay_post_")) / f"asset.{fmt}"
        self.export(mesh, out, fmt)

        return Generated3DAsset(
            path=str(out), format=fmt, triangles=int(len(mesh.faces)),
            provider=asset.provider, textures=asset.textures, raw_path=asset.path,
        )

    def decimate(self, mesh, target_tris: int):
        """Reduce triangle count to the budget (quadric decimation). No-op if under."""
        if len(mesh.faces) <= target_tris:
            return mesh
        return mesh.simplify_quadric_decimation(face_count=target_tris)

    def unwrap(self, mesh):
        """Re-unwrap UVs with xatlas for clean, non-overlapping texture space."""
        import trimesh
        import xatlas

        vmapping, indices, uvs = xatlas.parametrize(mesh.vertices, mesh.faces)
        return trimesh.Trimesh(
            vertices=mesh.vertices[vmapping], faces=indices,
            visual=trimesh.visual.TextureVisuals(uv=uvs), process=False,
        )

    def export(self, mesh, out: Path, fmt: str) -> None:
        """Export to a game format. GLB/OBJ are native; FBX needs a Blender path."""
        out.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "fbx":
            raise RuntimeError(
                "FBX export requires a Blender/assimp path (on the roadmap). "
                "Use format='glb' or 'obj' for now."
            )
        if fmt not in ("glb", "obj", "ply"):
            raise ValueError(f"unsupported format {fmt!r}; use glb | obj")
        mesh.export(str(out))
