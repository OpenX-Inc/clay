"""Tests for material generation (R2) + provider categories. GPU-gated → tested to boundary."""

from __future__ import annotations

import json
from pathlib import Path

import clay.tools.all  # noqa: F401 — register tools
from clay.config import Config
from clay.material import MaterialGenerator
from clay.providers import available_providers, get_provider, provider_categories
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY


def test_provider_categories():
    cats = provider_categories()
    assert "shape" in cats and "material" in cats
    assert "trellis2" in available_providers("shape")
    assert "stablematerials" in available_providers("material")
    # category-scoped lookup; shape default keeps back-compat
    assert get_provider("trellis2").category == "shape"
    assert get_provider("stablematerials", "material").category == "material"


def test_registry_has_generate_material():
    assert "generate_material" in REGISTRY


def test_generate_material_requires_prompt_or_image(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)
    res = dispatch(ctx, "generate_material", {"kind": "facade"})
    assert res["ok"] is False and res["error"]["code"] == "invalid"


def test_generate_material_no_backend(tmp_path):
    ctx = ToolContext(config=Config(), output_dir=tmp_path)  # no gpu_backend.url
    res = dispatch(ctx, "generate_material", {"prompt": "glass facade", "kind": "facade"})
    assert res["ok"] is False and res["error"]["code"] == "no_backend"


def test_material_writes_maps_and_manifest(tmp_path, monkeypatch):
    """With a (stubbed) backend, the client writes PNG maps + a material.json manifest."""
    import base64

    cfg = Config()
    cfg.gpu_backend.url = "http://backend"
    px = base64.b64encode(b"\x89PNG\r\n\x1a\n").decode()
    monkeypatch.setattr(
        MaterialGenerator, "_post",
        lambda self, endpoint, payload: {
            "base_color_b64": px, "normal_b64": px, "roughness_b64": px,
        },
    )
    res = MaterialGenerator(cfg).generate(kind="facade", prompt="glass facade", out_dir=tmp_path)
    assert Path(res["manifest"]).exists()
    manifest = json.loads(Path(res["manifest"]).read_text())
    assert manifest["kind"] == "facade" and manifest["tiling"] is True
    assert "base_color" in manifest["maps"] and Path(manifest["maps"]["base_color"]).exists()
