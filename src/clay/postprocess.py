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
        """Post-process a raw asset into a game-ready one.

        If the provider already produced a textured, budget-sized mesh (e.g.
        TRELLIS bakes a PBR texture onto its simplified mesh), preserve it and
        only enforce the export format — re-unwrapping/decimating would orphan
        the baked texture. Otherwise apply the full decimate → UV-unwrap path.
        """
        import trimesh

        mesh = trimesh.load(asset.path, force="mesh")

        if self._is_textured(mesh):
            final = mesh
        else:
            final = self.decimate(mesh, self.config.target_tris)
            if self.config.unwrap_uvs:
                final = self.unwrap(final)

        fmt = self.config.format
        out = Path(out_path) if out_path else Path(
            tempfile.mkdtemp(prefix="clay_post_")) / f"asset.{fmt}"
        self.export(final, out, fmt)

        return Generated3DAsset(
            path=str(out), format=fmt, triangles=int(len(final.faces)),
            provider=asset.provider, textures=asset.textures, raw_path=asset.path,
        )

    @staticmethod
    def _is_textured(mesh) -> bool:
        """True if the mesh already carries UVs + a real baked texture image.

        Guards against trivial placeholder textures (e.g. a 2×2 default) so we
        only skip our pipeline when there's a genuine texture to preserve.
        """
        visual = getattr(mesh, "visual", None)
        uv = getattr(visual, "uv", None)
        if uv is None or len(uv) == 0:
            return False
        material = getattr(visual, "material", None)
        image = getattr(material, "baseColorTexture", None) if material else None
        return image is not None and min(image.size) >= 16

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
