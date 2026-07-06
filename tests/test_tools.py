"""Tests for the tool registry, dispatch chokepoint, and the asset tools."""

from __future__ import annotations

import base64  # noqa: F401 — kept for parity with other test modules
import io

import pytest

import clay.tools.all  # noqa: F401 — register tools
from clay.config import Config
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import REGISTRY, build_input_schema, openai_schemas


@pytest.fixture
def ctx(tmp_path):
    cfg = Config()
    return ToolContext(config=cfg, output_dir=tmp_path)


def test_registry_has_core_tools():
    assert {"generate_asset", "remesh_asset", "list_assets", "list_providers"} <= set(REGISTRY)


def test_openai_schemas_well_formed():
    for schema in openai_schemas():
        assert schema["type"] == "function"
        assert schema["function"]["name"]
        assert schema["function"]["parameters"]["type"] == "object"


def test_param_dsl_required_vs_optional():
    schema = build_input_schema({"a": "string", "b": "integer?"})
    assert schema["required"] == ["a"]
    assert "b" not in schema.get("required", [])


def test_dispatch_unknown_tool(ctx):
    res = dispatch(ctx, "nope", {})
    assert res["ok"] is False
    assert res["error"]["code"] == "unknown_tool"


def test_dispatch_converts_exception_to_error(ctx):
    # remesh_asset on a missing file returns a not_found envelope, never raises.
    res = dispatch(ctx, "remesh_asset", {"input_path": "/no/such.glb", "target_tris": 100})
    assert res["ok"] is False
    assert res["error"]["code"] == "not_found"


def test_list_providers(ctx):
    res = dispatch(ctx, "list_providers", {})
    assert res["ok"] is True
    names = {p["name"] for p in res["providers"]}
    assert "trellis2" in names
    assert res["active"] == ctx.config.providers.model


def test_generate_asset_validates_before_backend(ctx):
    # text mode without a prompt must fail fast — no backend call.
    res = dispatch(ctx, "generate_asset", {"mode": "text"})
    assert res["ok"] is False
    assert res["error"]["code"] == "invalid"


def test_generate_asset_rejects_unsupported_mode(ctx):
    ctx.config.providers.model = "hi3dgen"  # image-only provider
    res = dispatch(ctx, "generate_asset", {"mode": "text", "prompt": "a sword"})
    assert res["ok"] is False
    assert res["error"]["code"] == "unsupported"


def test_remesh_asset_really_decimates(ctx):
    trimesh = pytest.importorskip("trimesh")
    sphere = trimesh.creation.icosphere(subdivisions=4)
    src = ctx.output_dir / "sphere.glb"
    buf = io.BytesIO()
    sphere.export(buf, file_type="glb")
    src.write_bytes(buf.getvalue())

    res = dispatch(ctx, "remesh_asset", {"input_path": str(src), "target_tris": 500})
    assert res["ok"] is True
    assert res["triangles"] <= 500
    assert res["triangles_before"] > 500
