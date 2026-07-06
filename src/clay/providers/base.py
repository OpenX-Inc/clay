"""Pluggable 3D model-provider registry (mirrors Flow's TTS provider layer).

A provider is a lightweight *descriptor* — which model to run, its modes and
license. The orchestrator uses it to validate config and to tell the GPU backend
which model to serve; the actual inference lives in the GPU backend
(``clay/gpu_backend``). Swap providers via ``[providers].model`` in config.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProvider:
    name: str
    modes: tuple[str, ...]  # e.g. ("image", "text")
    license: str = ""
    description: str = ""

    def supports(self, mode: str) -> bool:
        return mode in self.modes


_REGISTRY: dict[str, ModelProvider] = {}


def register_provider(provider: ModelProvider) -> ModelProvider:
    _REGISTRY[provider.name] = provider
    return provider


def get_provider(name: str) -> ModelProvider:
    provider = _REGISTRY.get(name)
    if provider is None:
        raise ValueError(
            f"unknown provider {name!r}; available: {available_providers()}"
        )
    return provider


def available_providers() -> list[str]:
    return sorted(_REGISTRY)
