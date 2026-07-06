"""Tests for config loading + schemas."""

from clay.config import Config, load_config
from clay.schemas import GenerationRequest, GenMode


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path / "missing.toml")
    assert isinstance(cfg, Config)
    assert cfg.providers.model == "trellis2"
    assert cfg.postprocess.target_tris == 60000
    assert cfg.postprocess.format == "glb"


def test_loads_toml(tmp_path):
    p = tmp_path / "config.toml"
    p.write_text(
        "[providers]\nmodel = \"hunyuan3d\"\n\n[postprocess]\ntarget_tris = 30000\nformat = \"fbx\"\n"
    )
    cfg = load_config(p)
    assert cfg.providers.model == "hunyuan3d"
    assert cfg.postprocess.target_tris == 30000
    assert cfg.postprocess.format == "fbx"


def test_generation_request():
    req = GenerationRequest(mode=GenMode.image, image_path="nganya.png", target_tris=45000)
    assert req.mode == "image"
    assert req.target_tris == 45000
    assert req.format == "glb"
