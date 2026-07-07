"""Model runtime for the GPU backend — loads and runs a provider's 3D model.

This runs **on the deployed GPU backend**, not the orchestrator. It needs the
model weights and a CUDA device. It lazily loads the model for the requested
provider and returns a mesh as **GLB bytes** plus a triangle count; the server
base64-encodes it into the HTTP contract.

TRELLIS-2 (the MIT primary) is run in-place from its cloned repo (it is *not*
pip-installable and depends on custom CUDA extensions — see the GPU image in
``modal_server.py`` / ``benchmarks/run_benchmark.py``). Providers/modes that
aren't wired raise a clear ``RuntimeError`` rather than fabricating output.
"""

from __future__ import annotations

import base64
import functools
import io
import os


def _count_faces(mesh) -> int:
    """Triangle count for a trimesh ``Trimesh`` or a multi-geometry ``Scene``."""
    if hasattr(mesh, "geometry") and mesh.geometry:
        return int(sum(len(g.faces) for g in mesh.geometry.values()))
    return int(len(getattr(mesh, "faces", [])))


@functools.lru_cache(maxsize=1)
def _load_trellis():
    """Load the TRELLIS-2 image-to-3D pipeline (GPU + weights required).

    Env vars must be set before importing ``trellis``: ``ATTN_BACKEND``
    (xformers|flash-attn) and ``SPCONV_ALGO`` (native for single runs).
    """
    os.environ.setdefault("ATTN_BACKEND", "xformers")
    os.environ.setdefault("SPCONV_ALGO", "native")

    from trellis.pipelines import TrellisImageTo3DPipeline

    model_id = os.environ.get("CLAY_TRELLIS_MODEL", "microsoft/TRELLIS-image-large")
    pipe = TrellisImageTo3DPipeline.from_pretrained(model_id)
    pipe.cuda()
    return pipe


def _trellis_image_to_3d(image_b64: str, target_tris: int | None = None) -> tuple[bytes, int]:
    """Run TRELLIS-2 image-to-3D → (glb_bytes, triangle_count).

    Follows the documented microsoft/TRELLIS usage: ``pipeline.run(image)`` then
    ``postprocessing_utils.to_glb(gaussian, mesh, simplify=..., texture_size=...)``.
    ``to_glb`` decimates *and re-bakes the texture* onto the reduced mesh (via the
    rasterizer), so we drive its ``simplify`` ratio from the caller's triangle
    budget — that keeps the baked PBR texture instead of clobbering it later.
    """
    from PIL import Image
    from trellis.utils import postprocessing_utils

    pipe = _load_trellis()
    image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
    outputs = pipe.run(image, seed=int(os.environ.get("CLAY_TRELLIS_SEED", "1")))
    mesh = outputs["mesh"][0]

    # Compute the simplify ratio to hit the tri budget (to_glb bakes texture onto
    # the simplified mesh). Fall back to the TRELLIS demo default when no budget.
    raw_faces = _extract_face_count(mesh)
    if target_tris and raw_faces and raw_faces > target_tris:
        simplify = max(0.0, min(0.98, 1.0 - target_tris / raw_faces))
    else:
        simplify = float(os.environ.get("CLAY_TRELLIS_SIMPLIFY", "0.0"))

    glb = postprocessing_utils.to_glb(
        outputs["gaussian"][0],
        mesh,
        simplify=simplify,
        texture_size=int(os.environ.get("CLAY_TRELLIS_TEXSIZE", "1024")),
    )
    buf = io.BytesIO()
    glb.export(buf, file_type="glb")
    return buf.getvalue(), _count_faces(glb)


def _extract_face_count(mesh) -> int:
    """Face count of a TRELLIS mesh-extract result (``.faces`` is a tensor/array)."""
    faces = getattr(mesh, "faces", None)
    if faces is None:
        return 0
    shape = getattr(faces, "shape", None)
    return int(shape[0]) if shape is not None else int(len(faces))


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
            return _trellis_image_to_3d(image_b64, target_tris=opts.get("target_tris"))
        raise RuntimeError(
            "TRELLIS-2 text-to-3D is not wired yet (image-to-3D is). "
            "Wire the TRELLIS text pipeline in clay/gpu_backend/runtime.py."
        )
    raise RuntimeError(
        f"model runtime for provider {provider!r} is not wired yet — "
        "contribute it in clay/gpu_backend/runtime.py (needs the gpu extra + weights)."
    )


def generate_material(
    provider: str,
    *,
    kind: str = "generic",
    prompt: str | None = None,
    image_b64: str | None = None,
    resolution: int = 1024,
    tiling: bool = True,
    **opts,
) -> dict:
    """Synthesise a tiling PBR material set. GPU-gated: fails visibly until wired.

    Wire a current-SOTA open, self-hostable, commercially-usable tiling-PBR model
    here (e.g. StableMaterials-style SD + PBR decompose) and return base64 maps:
    ``{base_color_b64, normal_b64, roughness_b64, metallic_b64, ao_b64}``.
    """
    raise RuntimeError(
        f"material runtime for provider {provider!r} is not wired yet — contribute it "
        "in clay/gpu_backend/runtime.py (needs the gpu extra + a tiling-PBR material "
        "model + weights)."
    )
