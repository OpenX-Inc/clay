"""Pluggable model-provider registry (mirrors Flow's TTS provider layer).

A provider is a lightweight *descriptor* — which model to run, its category
(shape / material / texture), modes, and license. The orchestrator uses it to
validate config and tell the GPU backend which model to serve; the actual
inference lives in ``clay/gpu_backend``. Swap providers via config
(``[providers].model`` / ``.material`` / ``.texture``).

Categories:
- **shape**    — image/text → 3D mesh (TRELLIS-2, Hunyuan3D, Hi3DGen)
- **material** — text/image → tiling PBR material set (generate_material)
- **texture**  — UV-aware paint onto an existing mesh (texture_asset)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelProvider:
    name: str
    modes: tuple[str, ...] = ()  # e.g. ("image", "text")
    license: str = ""
    description: str = ""
    category: str = "shape"  # shape | material | texture

    def supports(self, mode: str) -> bool:
        return mode in self.modes


# Keyed by (category, name) so the same name could exist across categories.
_REGISTRY: dict[tuple[str, str], ModelProvider] = {}


def register_provider(provider: ModelProvider) -> ModelProvider:
    _REGISTRY[(provider.category, provider.name)] = provider
    return provider


def get_provider(name: str, category: str = "shape") -> ModelProvider:
    provider = _REGISTRY.get((category, name))
    if provider is None:
        raise ValueError(
            f"unknown {category} provider {name!r}; "
            f"available: {available_providers(category)}"
        )
    return provider


def available_providers(category: str = "shape") -> list[str]:
    return sorted(n for (c, n) in _REGISTRY if c == category)


def provider_categories() -> list[str]:
    return sorted({c for (c, _) in _REGISTRY})


def all_providers() -> list[ModelProvider]:
    return [_REGISTRY[k] for k in sorted(_REGISTRY)]
