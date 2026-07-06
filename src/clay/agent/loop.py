"""The agent loop — kimi drives Clay's tools (OpenAI function-calling shape).

A turn appends the user message, then loops: ask the model with the tool
schemas, execute any tool_calls through ``dispatch``, feed results back as
``role:"tool"`` messages, and repeat until the model answers with no tool call.
A max-iteration cap is the safety net. Same tools as the MCP server, so behavior
never drifts between surfaces.
"""

from __future__ import annotations

import json

import clay.tools.all  # noqa: F401 — register all tools
from clay.agent.nvidia import NvidiaClient
from clay.tools.context import ToolContext, dispatch
from clay.tools.registry import openai_schemas

SYSTEM_RULES = (
    "You are Clay's asset agent. You turn images/text into game-ready 3D assets "
    "by calling tools — never claim an asset you did not produce via a tool. "
    "generate_asset needs a deployed GPU backend; if it errors with no backend, "
    "explain that the user must `clay deploy` first. remesh_asset decimates an "
    "existing mesh (CPU-only). Use list_assets/list_providers to inspect state. "
    "Be concise."
)


def build_system_prompt(ctx: ToolContext) -> str:
    cfg = ctx.config
    return (
        f"{SYSTEM_RULES}\n\n"
        f"CONFIG — provider={cfg.providers.model}, target_tris="
        f"{cfg.postprocess.target_tris}, format={cfg.postprocess.format}, "
        f"gpu_backend={'set' if cfg.gpu_backend.url else 'NOT set (deploy first)'}, "
        f"output_dir={ctx.output_dir}."
    )


class Agent:
    def __init__(
        self, client: NvidiaClient, ctx: ToolContext, max_iterations: int = 10
    ) -> None:
        self.client = client
        self.ctx = ctx
        self.max_iterations = max_iterations

    def run(self, user_message: str, history: list[dict] | None = None) -> dict:
        """Run one user turn to completion. Returns {reply, tool_calls}."""
        messages: list[dict] = [
            {"role": "system", "content": build_system_prompt(self.ctx)}
        ]
        messages += history or []
        messages.append({"role": "user", "content": user_message})
        tools = openai_schemas()
        calls_made: list[dict] = []

        for _ in range(self.max_iterations):
            response = self.client.chat(messages, tools=tools)
            msg = self.client.message(response)
            messages.append(msg)
            tool_calls = self.client.parse_tool_calls(msg)

            if not tool_calls:
                return {"reply": msg.get("content", ""), "tool_calls": calls_made}

            for call in tool_calls:
                result = dispatch(self.ctx, call["name"], call["args"])
                calls_made.append({"tool": call["name"], "args": call["args"],
                                   "result": result})
                messages.append({"role": "tool", "tool_call_id": call["id"],
                                 "content": json.dumps(result)})

        return {"reply": "(stopped: max tool iterations reached)", "tool_calls": calls_made}
