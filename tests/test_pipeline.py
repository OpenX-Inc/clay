"""Pipeline end-to-end test (generate mocked, real post-processing)."""

from pathlib import Path

import trimesh

from clay.config import Config
from clay.generator import Generator
from clay.pipeline import Pipeline
from clay.schemas import Generated3DAsset, GenerationRequest, GenMode


def test_pipeline_generates_then_postprocesses(tmp_path, monkeypatch):
    # Raw mesh the "backend" would return: a dense sphere.
    raw_mesh = trimesh.creation.icosphere(subdivisions=4)
    raw = tmp_path / "raw.glb"
    raw_mesh.export(str(raw))

    def fake_generate(self, request):
        return Generated3DAsset(path=str(raw), format="glb",
                                triangles=len(raw_mesh.faces), provider="trellis2")

    monkeypatch.setattr(Generator, "generate", fake_generate)

    cfg = Config()
    cfg.gpu_backend.url = "https://backend.example"
    out = tmp_path / "out.glb"
    asset = Pipeline(cfg).run(
        GenerationRequest(mode=GenMode.image, image_path="x.png", target_tris=800, format="glb"),
        out_path=str(out),
    )
    assert Path(asset.path).exists()
    assert asset.triangles < len(raw_mesh.faces)  # post-processed down
    assert asset.triangles <= 1000
