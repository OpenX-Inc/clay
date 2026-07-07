"""Tests for retopology (R8) — real Blender Quadriflow when available, else honest gating."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay import blender
from clay.config import Config
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _icosphere_glb(path: Path, subdivisions: int = 3) -> Path:
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    path.write_bytes(buf.getvalue())
    return path


def test_registry_has_retopo_asset():
    assert "retopo_asset" in REGISTRY


def test_retopo_missing_blender_fails_visibly(monkeypatch, tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb")
    monkeypatch.setattr("clay.blender.engine.resolve_blender", lambda explicit=None: None)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "retopo_asset", {"input_path": str(src), "target_faces": 500})
    assert res["ok"] is False and res["error"]["code"] == "blender_unavailable"


def test_retopo_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "retopo_asset", {"input_path": str(tmp_path / "no.glb")})
    assert res["ok"] is False and res["error"]["code"] == "not_found"


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_real_retopo(tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb", subdivisions=3)
    out = tmp_path / "s_retopo.glb"
    res = blender.retopo(src, out, target_faces=400)
    assert res["ok"] is True and out.exists()
    assert res["faces"] > 0
    assert res["quad_ratio"] >= 0.8  # quad-dominant topology
