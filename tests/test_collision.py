"""Tests for physics colliders (R7) — real trimesh geometry, CPU-only."""

from __future__ import annotations

from pathlib import Path

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay.collision import make_collision
from clay.config import Config
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def _sphere(tmp_path, subdiv=3):
    trimesh = pytest.importorskip("trimesh")
    mesh = trimesh.creation.icosphere(subdivisions=subdiv)
    p = tmp_path / "m.glb"
    mesh.export(str(p))
    return p, len(mesh.faces)


def test_registry_has_make_collision():
    assert "make_collision" in REGISTRY


def test_convex_hull(tmp_path):
    src, n = _sphere(tmp_path)
    res = make_collision(src, kind="convex", out_dir=tmp_path)
    assert Path(res["path"]).exists()
    assert res["kind"] == "convex" and res["hulls"] == 1
    assert res["faces"] <= n  # a hull is no denser than the source sphere


def test_box_collider(tmp_path):
    src, _ = _sphere(tmp_path)
    res = make_collision(src, kind="box", out_dir=tmp_path)
    assert Path(res["path"]).exists()
    assert res["faces"] == 12  # a box is 12 triangles


def test_compound_collider(tmp_path):
    """Compound falls back to per-component hulls when coacd is absent — still valid."""
    src, _ = _sphere(tmp_path)
    res = make_collision(src, kind="compound", max_hulls=8, out_dir=tmp_path)
    assert Path(res["path"]).exists()
    assert res["hulls"] >= 1


def test_unknown_kind_raises(tmp_path):
    src, _ = _sphere(tmp_path)
    with pytest.raises(ValueError):
        make_collision(src, kind="banana", out_dir=tmp_path)


def test_make_collision_tool(tmp_path):
    src, _ = _sphere(tmp_path)
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "make_collision", {"input_path": str(src), "kind": "box"})
    assert res["ok"] is True and Path(res["path"]).exists()


def test_make_collision_tool_missing_input(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "make_collision", {"input_path": str(tmp_path / "no.glb")})
    assert res["ok"] is False and res["error"]["code"] == "not_found"
