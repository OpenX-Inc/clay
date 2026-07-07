"""Tests for the headless Blender engine + FBX export (R1)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay import blender
from clay.config import Config
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _icosphere_glb(path: Path) -> Path:
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=2)
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    path.write_bytes(buf.getvalue())
    return path


def test_registry_has_export_fbx():
    assert "export_fbx" in REGISTRY


def test_resolve_blender_env(monkeypatch, tmp_path):
    fake = tmp_path / "blender"
    fake.write_text("#!/bin/sh\n")
    monkeypatch.setenv("CLAY_BLENDER", str(fake))
    assert blender.resolve_blender() == str(fake)
    assert blender.available() is True


def test_missing_blender_fails_visibly(monkeypatch, tmp_path):
    """No Blender ⇒ the tool returns a clear error, never fakes an FBX."""
    src = _icosphere_glb(tmp_path / "s.glb")
    monkeypatch.setattr("clay.blender.engine.resolve_blender", lambda explicit=None: None)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "export_fbx", {"input_path": str(src)})
    assert res["ok"] is False
    assert res["error"]["code"] == "blender_unavailable"


def test_export_fbx_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "export_fbx", {"input_path": str(tmp_path / "nope.glb")})
    assert res["ok"] is False
    assert res["error"]["code"] == "not_found"


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_real_fbx_export(tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb")
    out = tmp_path / "s.fbx"
    res = blender.export_fbx(src, out)
    assert res["ok"] is True
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_postprocess_export_fbx(tmp_path):
    from clay.config import PostprocessConfig
    from clay.postprocess import PostProcessor
    from clay.schemas import Generated3DAsset

    src = _icosphere_glb(tmp_path / "raw.glb")
    pp = PostProcessor(PostprocessConfig(format="fbx", unwrap_uvs=False))
    out = tmp_path / "final.fbx"
    asset = pp.process(Generated3DAsset(path=str(src), format="glb"), out_path=str(out))
    assert Path(asset.path).exists() and Path(asset.path).suffix == ".fbx"
