"""Tests for the agent loop with a stubbed OpenAI-compatible client."""

from __future__ import annotations

from clay.agent.loop import Agent
from clay.agent.nvidia import NvidiaClient
from clay.config import Config
from clay.tools.context import ToolContext


class FakeClient(NvidiaClient):
    """Scripts a sequence of chat responses; message()/parse_tool_calls() are real."""

    def __init__(self, responses):
        super().__init__(api_key="test")
        self._responses = list(responses)

    def chat(self, messages, tools=None, temperature=0.6, max_tokens=4096):
        return self._responses.pop(0)


def _assistant(content="", tool_calls=None):
    msg = {"role": "assistant", "content": content}
    if tool_calls:
        msg["tool_calls"] = tool_calls
    return {"choices": [{"message": msg}]}


def _ctx(tmp_path):
    return ToolContext(config=Config(), output_dir=tmp_path)


def test_parse_tool_calls_handles_bad_json():
    msg = {"tool_calls": [{"id": "1", "function": {"name": "x", "arguments": "{bad"}}]}
    calls = NvidiaClient.parse_tool_calls(msg)
    assert calls == [{"id": "1", "name": "x", "args": {}}]


def test_agent_runs_tool_then_replies(tmp_path):
    tool_call = [{"id": "c1", "type": "function",
                  "function": {"name": "list_providers", "arguments": "{}"}}]
    client = FakeClient([
        _assistant(tool_calls=tool_call),           # first: call the tool
        _assistant(content="Here are the providers."),  # then: final answer
    ])
    agent = Agent(client, _ctx(tmp_path))
    result = agent.run("what providers exist?")

    assert result["reply"] == "Here are the providers."
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool"] == "list_providers"
    assert result["tool_calls"][0]["result"]["ok"] is True


def test_agent_replies_without_tools(tmp_path):
    client = FakeClient([_assistant(content="Hi!")])
    result = Agent(client, _ctx(tmp_path)).run("hello")
    assert result["reply"] == "Hi!"
    assert result["tool_calls"] == []


def test_agent_respects_max_iterations(tmp_path):
    always_tool = _assistant(tool_calls=[
        {"id": "c", "type": "function",
         "function": {"name": "list_providers", "arguments": "{}"}}
    ])
    client = FakeClient([always_tool] * 5)
    result = Agent(client, _ctx(tmp_path), max_iterations=3).run("loop")
    assert "max tool iterations" in result["reply"]
    assert len(result["tool_calls"]) == 3
