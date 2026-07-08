"""Tests for the MCP server wiring (same registry as the agent)."""

from __future__ import annotations

from starlette.applications import Starlette

import clay.tools.all  # noqa: F401 — register tools
from clay.mcp_server.server import build_server, create_app
from clay.tools.registry import REGISTRY, mcp_schemas


def test_build_server_returns_named_server():
    server = build_server()
    assert server.name == "clay-mcp"


def test_mcp_schemas_cover_registry():
    schemas = mcp_schemas()
    assert {s["name"] for s in schemas} == set(REGISTRY)
    for s in schemas:
        assert s["inputSchema"]["type"] == "object"


def test_create_app_is_starlette():
    assert isinstance(create_app(), Starlette)


def test_run_single_worker_uses_app_instance(monkeypatch):
    """Default (workers=1) hands uvicorn a built app, no worker/factory kwargs."""
    import uvicorn

    from clay.mcp_server.server import run

    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr(uvicorn, "run", fake_run)
    run(host="127.0.0.1", port=8771)

    assert isinstance(captured["app"], Starlette)
    assert "workers" not in captured["kwargs"]
    assert "factory" not in captured["kwargs"]
    assert captured["kwargs"]["host"] == "127.0.0.1"
    assert captured["kwargs"]["port"] == 8771


def test_run_multi_worker_uses_factory_string(monkeypatch):
    """workers>1 must use the factory import string (an app can't cross processes)."""
    import uvicorn

    from clay.mcp_server.server import run

    captured: dict = {}

    def fake_run(app, **kwargs):
        captured["app"] = app
        captured["kwargs"] = kwargs

    monkeypatch.setattr(uvicorn, "run", fake_run)
    run(host="0.0.0.0", port=8770, workers=4, timeout_keep_alive=120)

    assert captured["app"] == "clay.mcp_server.server:create_app"
    assert captured["kwargs"]["factory"] is True
    assert captured["kwargs"]["workers"] == 4
    assert captured["kwargs"]["timeout_keep_alive"] == 120


def test_run_omits_timeout_when_unset(monkeypatch):
    import uvicorn

    from clay.mcp_server.server import run

    captured: dict = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: captured.update(kw))
    run(port=8772)
    assert "timeout_keep_alive" not in captured
