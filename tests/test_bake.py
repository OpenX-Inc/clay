"""Tests for normal baking (R9) — real Blender bake when available, else honest gating."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay import blender
from clay.config import Config
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _icosphere_glb(path: Path, subdivisions: int = 4) -> Path:
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    path.write_bytes(buf.getvalue())
    return path


def test_registry_has_bake_normals():
    assert "bake_normals" in REGISTRY


def test_bake_missing_blender_fails_visibly(monkeypatch, tmp_path):
    high = _icosphere_glb(tmp_path / "h.glb")
    monkeypatch.setattr("clay.blender.engine.resolve_blender", lambda explicit=None: None)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "bake_normals", {"high_path": str(high), "resolution": 128})
    assert res["ok"] is False and res["error"]["code"] == "blender_unavailable"


def test_bake_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "bake_normals", {"high_path": str(tmp_path / "no.glb")})
    assert res["ok"] is False and res["error"]["code"] == "not_found"


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_real_bake_normals(tmp_path):
    high = _icosphere_glb(tmp_path / "h.glb", subdivisions=4)
    out = tmp_path / "h_baked.glb"
    normal = tmp_path / "h_normal.png"
    res = blender.bake_normals(high, out, normal, resolution=256)
    assert res["ok"] is True
    assert normal.exists() and normal.stat().st_size > 0
    assert out.exists()
    assert res["resolution"] == 256 and res["low_faces"] > 0
