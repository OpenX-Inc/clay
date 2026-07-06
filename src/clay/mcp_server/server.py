"""The MCP server: registry → MCP tools, dispatched through the shared chokepoint.

MCP clients (Claude Code, Cursor, Codex) get identical behavior to the in-app
agent — same tools, same ``dispatch``. Transport is streamable HTTP at ``/mcp``,
optionally bearer-guarded via ``CLAY_MCP_TOKEN``.
"""

from __future__ import annotations

import json
import os

import mcp.types as mcp_types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.routing import Mount

import clay.tools.all  # noqa: F401 — populate the registry
from clay.config import load_config
from clay.tools.context import ToolContext
from clay.tools.context import dispatch as dispatch_tool
from clay.tools.registry import REGISTRY

_ctx: ToolContext | None = None


def get_context() -> ToolContext:
    global _ctx
    if _ctx is None:
        cfg = load_config(os.environ.get("CLAY_CONFIG", "config/config.toml"))
        _ctx = ToolContext.from_config(cfg)
    return _ctx


def build_server() -> Server:
    server: Server = Server("clay-mcp")

    @server.list_tools()
    async def _list_tools() -> list[mcp_types.Tool]:
        return [
            mcp_types.Tool(name=t.name, description=t.description, inputSchema=t.input_schema)
            for t in REGISTRY.values()
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict) -> list[mcp_types.ContentBlock]:
        result = dispatch_tool(get_context(), name, arguments or {})
        return [mcp_types.TextContent(type="text", text=json.dumps(result))]

    return server


def create_app() -> Starlette:
    """ASGI app: bearer-auth + DNS-rebinding-protected streamable-HTTP at /mcp."""
    server = build_server()
    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=os.environ.get(
            "CLAY_MCP_ALLOWED_HOSTS", "127.0.0.1,localhost,127.0.0.1:*,localhost:*"
        ).split(","),
        allowed_origins=os.environ.get(
            "CLAY_MCP_ALLOWED_ORIGINS", "http://127.0.0.1:*,http://localhost:*,*"
        ).split(","),
    )
    manager = StreamableHTTPSessionManager(
        app=server, json_response=True, stateless=True, security_settings=security
    )
    token = os.environ.get("CLAY_MCP_TOKEN", "")

    async def _unauthorized(send) -> None:
        await send({"type": "http.response.start", "status": 401,
                    "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})

    async def handle(scope, receive, send) -> None:
        if token:
            headers = dict(scope.get("headers") or [])
            if headers.get(b"authorization", b"").decode() != f"Bearer {token}":
                await _unauthorized(send)
                return
        await manager.handle_request(scope, receive, send)

    from collections.abc import AsyncIterator
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncIterator[None]:
        async with manager.run():
            yield

    return Starlette(routes=[Mount("/mcp", app=handle)], lifespan=lifespan)


def run(host: str | None = None, port: int | None = None) -> None:
    import uvicorn

    host = host or os.environ.get("CLAY_MCP_HOST", "127.0.0.1")
    port = port or int(os.environ.get("CLAY_MCP_PORT", "8770"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    run()
