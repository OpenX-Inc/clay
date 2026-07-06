"""Built-in 3D model providers. TRELLIS-2 (MIT) is the primary."""

from __future__ import annotations

from clay.providers.base import (
    ModelProvider,
    available_providers,
    get_provider,
    register_provider,
)

register_provider(ModelProvider(
    name="trellis2", modes=("image", "text"), license="MIT",
    description="TRELLIS-2 — primary, permissively licensed image/text → 3D.",
))
register_provider(ModelProvider(
    name="hunyuan3d", modes=("image", "text"), license="Tencent Hunyuan",
    description="Hunyuan3D-2.1 — high-quality image/text → 3D.",
))
register_provider(ModelProvider(
    name="hi3dgen", modes=("image",), license="research",
    description="Hi3DGen — high-fidelity geometry from a single image.",
))

__all__ = ["ModelProvider", "register_provider", "get_provider", "available_providers"]
