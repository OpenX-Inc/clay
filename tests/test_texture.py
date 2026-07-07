"""Tests for texture_asset (R4). GPU-gated → tested to boundary."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay.config import Config
from clay.providers import available_providers
from clay.texture import TextureAssetGenerator
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _sphere(tmp_path):
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=2)
    p = tmp_path / "m.glb"
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    p.write_bytes(buf.getvalue())
    return p


def test_texture_providers_registered():
    assert "paint3d" in available_providers("texture")


def test_registry_has_texture_asset():
    assert "texture_asset" in REGISTRY


def test_texture_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "texture_asset", {"input_path": str(tmp_path / "no.glb"), "prompt": "x"})
    assert res["ok"] is False and res["error"]["code"] == "not_found"


def test_texture_requires_prompt_or_image(tmp_path):
    src = _sphere(tmp_path)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "texture_asset", {"input_path": str(src)})
    assert res["ok"] is False and res["error"]["code"] == "invalid"


def test_texture_no_backend(tmp_path):
    src = _sphere(tmp_path)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)  # no gpu_backend.url
    res = dispatch(ctx, "texture_asset", {"input_path": str(src), "prompt": "graffiti livery"})
    assert res["ok"] is False and res["error"]["code"] == "no_backend"


def test_texture_writes_maps_mesh_manifest(tmp_path, monkeypatch):
    src = _sphere(tmp_path)
    cfg = Config()
    cfg.gpu_backend.url = "http://backend"
    px = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
    mesh_b64 = base64.b64encode(src.read_bytes()).decode()
    monkeypatch.setattr(
        TextureAssetGenerator, "_post",
        lambda self, endpoint, payload: {"base_color_b64": px, "mesh_b64": mesh_b64},
    )
    res = TextureAssetGenerator(cfg).texture(src, prompt="nganya livery", out_dir=tmp_path)
    assert Path(res["manifest"]).exists()
    manifest = json.loads(Path(res["manifest"]).read_text())
    assert "base_color" in manifest["maps"]
    assert manifest["mesh"] and Path(manifest["mesh"]).exists()
