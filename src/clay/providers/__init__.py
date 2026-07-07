"""Built-in model providers by category. TRELLIS-2 (MIT) is the primary shape model.

Material/texture providers are **starting points** (picked from known open,
self-hostable, commercially-usable models) — swap in the current SOTA via config.
Inference lives in the GPU backend; these are pluggable descriptors.
"""

from __future__ import annotations

from clay.providers.base import (
    ModelProvider,
    all_providers,
    available_providers,
    get_provider,
    provider_categories,
    register_provider,
)

# --- shape (image/text → 3D) -------------------------------------------------
register_provider(ModelProvider(
    name="trellis2", modes=("image", "text"), license="MIT", category="shape",
    description="TRELLIS-2 — primary, permissively licensed image/text → 3D.",
))
register_provider(ModelProvider(
    name="hunyuan3d", modes=("image", "text"), license="Tencent Hunyuan", category="shape",
    description="Hunyuan3D-2.1 — high-quality image/text → 3D.",
))
register_provider(ModelProvider(
    name="hi3dgen", modes=("image",), license="research", category="shape",
    description="Hi3DGen — high-fidelity geometry from a single image.",
))

# --- material (text/image → tiling PBR set) ----------------------------------
register_provider(ModelProvider(
    name="stablematerials", modes=("text", "image"), license="Apache-2.0", category="material",
    description="StableMaterials — SD-based tileable PBR material generation (verify SOTA).",
))
register_provider(ModelProvider(
    name="matfuse", modes=("text", "image"), license="research", category="material",
    description="MatFuse — diffusion PBR material synthesis (alt).",
))

__all__ = [
    "ModelProvider",
    "register_provider",
    "get_provider",
    "available_providers",
    "provider_categories",
    "all_providers",
]
