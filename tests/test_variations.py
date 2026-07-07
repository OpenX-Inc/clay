"""Tests for generate_variations (R6) — shape reuse; generation mocked (GPU-gated)."""

from __future__ import annotations

from pathlib import Path

import clay.tools.all  # noqa: F401 — register tools
from clay import variations as V
from clay.config import Config
from clay.schemas import Generated3DAsset
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def test_registry_has_generate_variations():
    assert "generate_variations" in REGISTRY


def test_variations_loop_uses_incrementing_seeds(monkeypatch, tmp_path):
    seeds = []

    def fake_run(self, req, out_path=None):
        seeds.append(req.seed)
        Path(out_path).write_bytes(b"glb")
        return Generated3DAsset(path=out_path, format="glb", triangles=123)

    monkeypatch.setattr("clay.variations.Pipeline.run", fake_run)
    res = V.generate_variations(
        Config(), mode="text", prompt="a chair", count=3, seed=10, out_dir=tmp_path
    )
    assert res["count"] == 3
    assert seeds == [10, 11, 12]
    assert all(Path(v["path"]).exists() for v in res["variations"])


def test_variations_validates_mode(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "generate_variations", {"mode": "image", "count": 2})
    assert res["ok"] is False and res["error"]["code"] == "invalid"


def test_variations_no_backend(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)  # no gpu_backend.url
    res = dispatch(ctx, "generate_variations", {"mode": "text", "prompt": "x", "count": 2})
    assert res["ok"] is False and res["error"]["code"] == "no_backend"
