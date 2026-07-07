"""Tests for LOD chains (R5) — real trimesh decimation, CPU-only."""

from __future__ import annotations

from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay.config import Config
from clay.lods import make_lods
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _sphere(tmp_path, subdiv=4):
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=subdiv)
    p = tmp_path / "m.glb"
    mesh.export(str(p))
    return p, len(mesh.faces)


def test_registry_has_make_lods():
    assert "make_lods" in REGISTRY


def test_lod_chain_descends(tmp_path):
    src, base = _sphere(tmp_path)
    res = make_lods(src, ratios=[1.0, 0.5, 0.25], out_dir=tmp_path)
    assert res["count"] == 3 and res["base_faces"] == base
    faces = [lod["faces"] for lod in res["lods"]]
    assert faces[0] == base          # LOD0 is the full mesh
    assert faces[0] > faces[1] > faces[2]  # each LOD is lighter
    for lod in res["lods"]:
        assert Path(lod["path"]).exists()


def test_empty_ratios_raises(tmp_path):
    src, _ = _sphere(tmp_path)
    with pytest.raises(ValueError):
        make_lods(src, ratios=[], out_dir=tmp_path)


def test_make_lods_tool(tmp_path):
    src, _ = _sphere(tmp_path)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "make_lods", {"input_path": str(src), "ratios": [1.0, 0.3]})
    assert res["ok"] is True and res["count"] == 2


def test_make_lods_tool_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "make_lods", {"input_path": str(tmp_path / "no.glb")})
    assert res["ok"] is False and res["error"]["code"] == "not_found"
