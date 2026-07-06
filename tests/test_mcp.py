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
