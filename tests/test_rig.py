"""Tests for auto-rigging (R3) — real Blender rig when available, else honest gating."""

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


def test_registry_has_rig_asset():
    assert "rig_asset" in REGISTRY


def test_rig_missing_blender_fails_visibly(monkeypatch, tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb")
    monkeypatch.setattr("clay.blender.engine.resolve_blender", lambda explicit=None: None)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "rig_asset", {"input_path": str(src), "rig_type": "humanoid"})
    assert res["ok"] is False and res["error"]["code"] == "blender_unavailable"


def test_rig_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "rig_asset", {"input_path": str(tmp_path / "no.glb")})
    assert res["ok"] is False and res["error"]["code"] == "not_found"


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_real_humanoid_rig(tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb")
    out = tmp_path / "s_rigged.fbx"
    res = blender.rig_asset(src, out, rig_type="humanoid")
    assert res["ok"] is True and out.exists()
    assert res["bones"] > 5  # a biped has a real skeleton


@pytest.mark.skipif(not blender.available(), reason="Blender not available")
def test_real_generic_rig(tmp_path):
    src = _icosphere_glb(tmp_path / "s.glb")
    out = tmp_path / "s_gen.fbx"
    res = blender.rig_asset(src, out, rig_type="generic")
    assert res["ok"] is True and out.exists() and res["bones"] >= 1
