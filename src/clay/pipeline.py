"""Pipeline — the end-to-end loop: request → generate → post-process → asset."""

from __future__ import annotations

from clay.config import Config, PostprocessConfig
from clay.generator import Generator
from clay.postprocess import PostProcessor
from clay.schemas import Generated3DAsset, GenerationRequest


class Pipeline:
    """image/text → 3D generation → game-ready post-processing → asset."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.generator = Generator(config)

    def run(self, request: GenerationRequest, out_path: str | None = None) -> Generated3DAsset:
        # 1) Generate the raw mesh on the GPU backend.
        raw = self.generator.generate(request)
        # 2) Make it game-ready — request params override config defaults.
        pp = PostProcessor(PostprocessConfig(
            target_tris=request.target_tris,
            unwrap_uvs=request.unwrap_uvs,
            format=request.format,
            pbr=request.pbr,
        ))
        return pp.process(raw, out_path=out_path)
