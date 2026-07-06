"""Model runtime for the GPU backend — loads and runs a provider's 3D model.

This runs **on the deployed GPU backend**, not the orchestrator. It needs the
``gpu`` extra, the model weights, and a CUDA device. It lazily loads the model
for the requested provider and returns a mesh as **GLB bytes** plus a triangle
count; the server base64-encodes it into the HTTP contract.

Honesty: TRELLIS-2 (the MIT primary) is wired against its documented pipeline
API. Providers/modes that aren't wired raise a clear ``RuntimeError`` rather
than fabricating output — so a missing integration fails visibly. Contributors
with a GPU wire additional providers here.
"""

from __future__ import annotations

import base64
import functools
import io


@functools.lru_cache(maxsize=1)
def _load_trellis():
    """Load the TRELLIS-2 image-to-3D pipeline (GPU + weights required)."""
    from trellis.pipelines import TrellisImageTo3DPipeline

    pipe = TrellisImageTo3DPipeline.from_pretrained("microsoft/TRELLIS-image-large")
    pipe.cuda()
    return pipe


def _trellis_image_to_3d(image_b64: str) -> tuple[bytes, int]:
    """Run TRELLIS-2 image-to-3D → (glb_bytes, triangle_count).

    Follows the documented microsoft/TRELLIS usage. GPU-only; unverified without
    weights + hardware — a GPU contributor validates this path.
    """
    from PIL import Image
    from trellis.utils import postprocessing_utils

    pipe = _load_trellis()
    image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
    outputs = pipe.run(image)
    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0], outputs["mesh"][0], simplify=0.0, texture_size=1024
    )
    buf = io.BytesIO()
    glb.export(buf, file_type="glb")
    data = buf.getvalue()
    triangles = int(sum(len(g.faces) for g in glb.geometry.values())) if glb.geometry else 0
    return data, triangles


def generate(
    provider: str,
    mode: str,
    *,
    image_b64: str | None = None,
    prompt: str | None = None,
    **opts,
) -> tuple[bytes, int]:
    """Dispatch to a provider's model runtime → (glb_bytes, triangle_count)."""
    if provider == "trellis2":
        if mode == "image":
            if not image_b64:
                raise RuntimeError("image_b64 is required for image-to-3D")
            return _trellis_image_to_3d(image_b64)
        raise RuntimeError(
            "TRELLIS-2 text-to-3D is not wired yet (image-to-3D is). "
            "Wire the TRELLIS text pipeline in clay/gpu_backend/runtime.py."
        )
    raise RuntimeError(
        f"model runtime for provider {provider!r} is not wired yet — "
        "contribute it in clay/gpu_backend/runtime.py (needs the gpu extra + weights)."
    )
