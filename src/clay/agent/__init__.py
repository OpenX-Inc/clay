"""Clay agent — kimi (or any OpenAI-compatible model) driving the tool registry."""

from __future__ import annotations

from clay.agent.loop import Agent, build_system_prompt
from clay.agent.nvidia import NvidiaClient

__all__ = ["Agent", "NvidiaClient", "build_system_prompt"]
