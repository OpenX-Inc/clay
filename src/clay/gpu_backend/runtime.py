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
from pathlib import Path


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


def _trellis_image_to_3d(
    image_b64: str, target_tris: int | None = None, seed: int | None = None
) -> tuple[bytes, int]:
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
    if seed is None:
        seed = int(os.environ.get("CLAY_TRELLIS_SEED", "1"))
    outputs = pipe.run(image, seed=int(seed))
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


@functools.lru_cache(maxsize=1)
def _load_hunyuan3d():
    """Load the Hunyuan3D-2.1 shape (DiT flow-matching) pipeline. GPU + weights."""
    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

    model_id = os.environ.get("CLAY_HUNYUAN_MODEL", "tencent/Hunyuan3D-2.1")
    return Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_id)


def _hunyuan3d_image_to_3d(image_b64: str, target_tris: int | None = None) -> tuple[bytes, int]:
    """Run Hunyuan3D-2.1 image→3D (shape) → (glb_bytes, triangle_count)."""
    from PIL import Image

    pipe = _load_hunyuan3d()
    image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
    try:
        from hy3dshape.rembg import BackgroundRemover

        image = BackgroundRemover()(image)
    except Exception:  # noqa: BLE001 — bg removal optional; pipeline may handle it
        pass

    result = pipe(image=image, mc_algo="mc")
    mesh = result[0] if isinstance(result, (list, tuple)) else result
    if target_tris and hasattr(mesh, "faces") and len(mesh.faces) > target_tris:
        try:
            mesh = mesh.simplify_quadric_decimation(target_tris)
        except Exception:  # noqa: BLE001 — decimation best-effort
            pass
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    return buf.getvalue(), _count_faces(mesh)


@functools.lru_cache(maxsize=1)
def _load_hi3dgen():
    """Load Hi3DGen (MIT) — TRELLIS-normal geometry pipeline + StableNormal predictor."""
    import torch
    from hi3dgen.pipelines import Hi3DGenPipeline

    model_id = os.environ.get("CLAY_HI3DGEN_MODEL", "Stable-X/trellis-normal-v0-1")
    pipe = Hi3DGenPipeline.from_pretrained(model_id)
    pipe.cuda()
    # StableNormal loads yoso + BiRefNet from a "weights/<name>" dir relative to
    # CWD — stage both under a persistent run dir and run from there.
    from huggingface_hub import snapshot_download

    run_dir = "/models/hi3dgen_run"
    os.makedirs(run_dir, exist_ok=True)
    os.chdir(run_dir)
    snapshot_download("Stable-X/yoso-normal-v1-8-1", local_dir="weights/yoso-normal-v1-8-1")
    snapshot_download("ZhengPeng7/BiRefNet", local_dir="weights/BiRefNet")
    normal_predictor = torch.hub.load(
        "hugoycj/StableNormal", "StableNormal_turbo", trust_repo=True,
        yoso_version="yoso-normal-v1-8-1", local_cache_dir="weights",
    )
    return pipe, normal_predictor


def _hi3dgen_image_to_3d(
    image_b64: str, target_tris: int | None = None, seed: int | None = None
) -> tuple[bytes, int]:
    """Run Hi3DGen image→normal→3D → (glb_bytes, triangle_count)."""
    from PIL import Image

    pipe, normal_predictor = _load_hi3dgen()
    image = Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB")
    image = pipe.preprocess_image(image, resolution=1024)
    # Hi3DGen's preprocess already removes the background, so skip StableNormal's
    # BiRefNet masking (data_type "indoor" → no extra mask), avoiding its heavy
    # backbone-weight download. Override via CLAY_HI3DGEN_DATATYPE.
    data_type = os.environ.get("CLAY_HI3DGEN_DATATYPE", "indoor")
    normal_image = normal_predictor(
        image, resolution=768, match_input_resolution=True, data_type=data_type
    )
    if seed is None:
        seed = int(os.environ.get("CLAY_HI3DGEN_SEED", "42"))
    outputs = pipe.run(
        normal_image,
        seed=int(seed),
        formats=["mesh"],
        preprocess_image=False,
        sparse_structure_sampler_params={
            "steps": int(os.environ.get("CLAY_HI3DGEN_SS_STEPS", "50")), "cfg_strength": 3,
        },
        slat_sampler_params={
            "steps": int(os.environ.get("CLAY_HI3DGEN_SLAT_STEPS", "6")), "cfg_strength": 3,
        },
    )
    mesh = outputs["mesh"][0].to_trimesh(transform_pose=True)
    if target_tris and hasattr(mesh, "faces") and len(mesh.faces) > target_tris:
        try:
            mesh = mesh.simplify_quadric_decimation(target_tris)
        except Exception:  # noqa: BLE001 — decimation best-effort
            pass
    buf = io.BytesIO()
    mesh.export(buf, file_type="glb")
    return buf.getvalue(), _count_faces(mesh)


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
            return _trellis_image_to_3d(
                image_b64, target_tris=opts.get("target_tris"), seed=opts.get("seed")
            )
        raise RuntimeError(
            "TRELLIS-2 text-to-3D is not wired yet (image-to-3D is). "
            "Wire the TRELLIS text pipeline in clay/gpu_backend/runtime.py."
        )
    if provider == "hunyuan3d":
        if mode == "image":
            if not image_b64:
                raise RuntimeError("image_b64 is required for image-to-3D")
            return _hunyuan3d_image_to_3d(image_b64, target_tris=opts.get("target_tris"))
        raise RuntimeError(
            "Hunyuan3D text-to-3D is not wired yet (image-to-3D is)."
        )
    if provider == "hi3dgen":
        if mode == "image":
            if not image_b64:
                raise RuntimeError("image_b64 is required for image-to-3D")
            return _hi3dgen_image_to_3d(
                image_b64, target_tris=opts.get("target_tris"), seed=opts.get("seed")
            )
        raise RuntimeError("Hi3DGen is image-only (no text-to-3D).")
    raise RuntimeError(
        f"model runtime for provider {provider!r} is not wired yet — "
        "contribute it in clay/gpu_backend/runtime.py (needs the gpu extra + weights)."
    )


@functools.lru_cache(maxsize=1)
def _load_stablematerials():
    """Load the StableMaterials tiling-PBR pipeline (diffusers, trust_remote_code)."""
    import torch
    from diffusers import DiffusionPipeline

    model_id = os.environ.get("CLAY_MATERIAL_MODEL", "gvecchio/StableMaterials")
    pipe = DiffusionPipeline.from_pretrained(
        model_id, trust_remote_code=True, torch_dtype=torch.float16
    )
    pipe.to("cuda")
    return pipe


def _map_to_png_b64(img, resolution: int) -> str:
    """Encode a material map (PIL image or CHW/HWC tensor/array) to a base64 PNG."""
    import numpy as np
    from PIL import Image

    if not isinstance(img, Image.Image):
        try:
            import torch

            if isinstance(img, torch.Tensor):
                img = img.detach().float().cpu().clamp(0, 1).numpy()
        except Exception:  # noqa: BLE001 — torch optional at encode time
            pass
        arr = np.asarray(img)
        if arr.dtype != np.uint8:
            arr = (arr.clip(0, 1) * 255).round().astype("uint8")
        if arr.ndim == 3 and arr.shape[0] in (1, 3, 4) and arr.shape[2] not in (1, 3, 4):
            arr = np.transpose(arr, (1, 2, 0))  # CHW → HWC
        if arr.ndim == 3 and arr.shape[2] == 1:
            arr = arr[:, :, 0]
        img = Image.fromarray(arr)

    img = img.convert("RGB").resize((resolution, resolution), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _extract_material_maps(material) -> dict:
    """Pull standard PBR channels off a StableMaterials Material (attrs or dict)."""
    aliases = {
        "base_color": ("basecolor", "base_color", "albedo", "diffuse"),
        "normal": ("normal", "normals"),
        "roughness": ("roughness", "rough"),
        "metallic": ("metallic", "metalness", "metal"),
        "height": ("height", "displacement", "disp"),
    }
    as_dict = material.as_dict() if hasattr(material, "as_dict") else None
    maps: dict = {}
    for out_name, names in aliases.items():
        for n in names:
            val = getattr(material, n, None)
            if val is None and isinstance(as_dict, dict):
                val = as_dict.get(n)
            if val is not None:
                maps[out_name] = val
                break
    return maps


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
    """Synthesise a tiling PBR material set (base_color/normal/roughness/metallic/height).

    Wired for **StableMaterials** (Apache-2.0, SD-based, seamless PBR). Other
    material providers fail visibly. Returns base64 maps per the /material contract.
    """
    if provider != "stablematerials":
        raise RuntimeError(
            f"material runtime for provider {provider!r} is not wired — only "
            "'stablematerials' is. Contribute others in clay/gpu_backend/runtime.py."
        )
    if not prompt:
        raise RuntimeError("stablematerials requires a text prompt")

    pipe = _load_stablematerials()
    steps = int(opts.get("steps", os.environ.get("CLAY_MATERIAL_STEPS", "50")))
    guidance = float(os.environ.get("CLAY_MATERIAL_GUIDANCE", "10.0"))
    result = pipe(
        prompt=prompt,
        tileable=bool(tiling),
        num_inference_steps=steps,
        guidance_scale=guidance,
    )
    material = result.images[0]
    channels = _extract_material_maps(material)
    if not channels:
        raise RuntimeError(
            "StableMaterials returned no recognizable maps — verify the pipeline API "
            "(clay/gpu_backend/runtime.py:_extract_material_maps)."
        )

    out = {
        "provider": "stablematerials", "kind": kind,
        "resolution": int(resolution), "tiling": bool(tiling),
    }
    for name, img in channels.items():
        out[f"{name}_b64"] = _map_to_png_b64(img, int(resolution))
    return out


@functools.lru_cache(maxsize=1)
def _load_hunyuanpaint():
    """Load the Hunyuan3D-2.1 Paint pipeline (image-conditioned texturing).

    NON-COMMERCIAL weights (Tencent Hunyuan) — a self-host option, not for the
    managed service. Config uses repo-relative paths, so we run from the repo root.
    """
    os.chdir("/hunyuan3d")
    try:
        from utils.torchvision_fix import apply_fix

        apply_fix()
    except Exception:  # noqa: BLE001 — compat shim optional
        pass
    from textureGenPipeline import Hunyuan3DPaintConfig, Hunyuan3DPaintPipeline

    views = int(os.environ.get("CLAY_PAINT_VIEWS", "6"))
    res = int(os.environ.get("CLAY_PAINT_RES", "512"))
    return Hunyuan3DPaintPipeline(Hunyuan3DPaintConfig(views, res))


def _hunyuanpaint_texture(mesh_b64: str, image_b64: str, resolution: int) -> dict:
    import tempfile

    pipe = _load_hunyuanpaint()
    tmp = Path(tempfile.mkdtemp(prefix="clay_tex_"))
    mesh_in = tmp / "mesh.glb"
    mesh_in.write_bytes(base64.b64decode(mesh_b64))
    img_in = tmp / "image.png"
    img_in.write_bytes(base64.b64decode(image_b64))
    out_path = pipe(mesh_path=str(mesh_in), image_path=str(img_in))
    # Hunyuan-Paint writes a textured OBJ (+ .mtl + texture PNG in the same dir).
    # Load it with its textures and re-export a self-contained GLB.
    import trimesh

    loaded = trimesh.load(out_path)
    buf = io.BytesIO()
    loaded.export(buf, file_type="glb")
    data = buf.getvalue()
    return {
        "provider": "hunyuanpaint",
        "resolution": int(resolution),
        "mesh_b64": base64.b64encode(data).decode(),
    }


def generate_texture(
    provider: str,
    *,
    mesh_b64: str,
    prompt: str | None = None,
    image_b64: str | None = None,
    resolution: int = 1024,
    keep_uvs: bool = True,
    emit_decals: bool = False,
    **opts,
) -> dict:
    """UV-aware (re)texture a mesh. Wired for Hunyuan3D-Paint (image-conditioned,
    NON-COMMERCIAL — self-host only). Commercial-OK providers (paint3d/syncmvd)
    remain pluggable slots and fail visibly until wired."""
    if provider == "hunyuanpaint":
        if not image_b64:
            raise RuntimeError(
                "hunyuanpaint is image-conditioned — provide image_b64 (a reference "
                "image). For prompt-only texturing, wire a text provider (paint3d/syncmvd)."
            )
        return _hunyuanpaint_texture(mesh_b64, image_b64, resolution)
    raise RuntimeError(
        f"texture runtime for provider {provider!r} is not wired yet — 'hunyuanpaint' is "
        "(non-commercial). Contribute a commercial-OK provider (paint3d/syncmvd) in "
        "clay/gpu_backend/runtime.py."
    )
