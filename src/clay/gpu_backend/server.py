"""GPU backend — FastAPI HTTP server exposing Clay's one base64 contract.

Run this directly on any GPU host (self-hosted, RunPod, …)::

    uvicorn clay.gpu_backend.server:app --host 0.0.0.0 --port 8000

and point ``[gpu_backend].url`` at it. Modal deploys the same contract via
``modal_server.py``. The consumer is ``clay.generator.Generator``.

Contract:
    GET  /health                 → liveness + which provider is served
    POST /generate/image-to-3d   → {image_b64|image, provider?, format?}
    POST /generate/text-to-3d    → {prompt, provider?, format?}
    POST /remesh                 → {mesh_b64, target_tris} (real, CPU-only)
    POST /texture                → {mesh_b64, ...} (GPU; honest 503 until wired)

Responses carry the mesh inline as base64 (serverless containers can't reliably
serve files back): ``{mesh_b64, format, triangles, textures: []}``.
"""

from __future__ import annotations

import base64
import io
import os

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Clay GPU Backend", version="0.1.0")

DEFAULT_PROVIDER = os.environ.get("CLAY_MODEL", "trellis2")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "provider": DEFAULT_PROVIDER,
        "endpoints": ["image-to-3d", "text-to-3d", "remesh", "texture"],
    }


@app.post("/generate/image-to-3d")
def image_to_3d(body: dict) -> dict:
    image_b64 = body.get("image_b64") or body.get("image")
    if not image_b64:
        raise HTTPException(400, "image_b64 is required")
    return _run(
        body.get("provider", DEFAULT_PROVIDER),
        "image",
        image_b64=image_b64,
        fmt=body.get("format", "glb"),
        target_tris=body.get("target_tris"),
    )


@app.post("/generate/text-to-3d")
def text_to_3d(body: dict) -> dict:
    prompt = body.get("prompt")
    if not prompt:
        raise HTTPException(400, "prompt is required")
    return _run(
        body.get("provider", DEFAULT_PROVIDER),
        "text",
        prompt=prompt,
        fmt=body.get("format", "glb"),
        target_tris=body.get("target_tris"),
    )


@app.post("/remesh")
def remesh(body: dict) -> dict:
    """Decimate a mesh to a triangle budget. Real, CPU-only (no GPU needed)."""
    mesh_b64 = body.get("mesh_b64")
    if not mesh_b64:
        raise HTTPException(400, "mesh_b64 is required")
    target_tris = int(body.get("target_tris", 60000))
    fmt = body.get("format", "glb")
    try:
        import trimesh
    except ImportError as err:
        raise HTTPException(503, f"remesh needs the postprocess extra: {err}") from err

    mesh = trimesh.load(io.BytesIO(base64.b64decode(mesh_b64)), file_type="glb", force="mesh")
    if len(mesh.faces) > target_tris:
        mesh = mesh.simplify_quadric_decimation(face_count=target_tris)
    out = io.BytesIO()
    mesh.export(out, file_type=fmt)
    return {
        "mesh_b64": base64.b64encode(out.getvalue()).decode(),
        "format": fmt,
        "triangles": int(len(mesh.faces)),
        "textures": [],
    }


@app.post("/texture")
def texture(body: dict) -> dict:
    raise HTTPException(
        503,
        "texture generation is not wired yet — contribute it in "
        "clay/gpu_backend/runtime.py (needs the gpu extra + weights).",
    )


@app.post("/material")
def material(body: dict) -> dict:
    """Tiling PBR material set. GPU-gated: 503 with an honest message until wired."""
    prompt = body.get("prompt")
    image_b64 = body.get("image_b64")
    if not prompt and not image_b64:
        raise HTTPException(400, "prompt or image_b64 is required")
    from clay.gpu_backend import runtime

    try:
        return runtime.generate_material(
            body.get("provider", "stablematerials"),
            kind=body.get("kind", "generic"),
            prompt=prompt,
            image_b64=image_b64,
            resolution=int(body.get("resolution", 1024)),
            tiling=bool(body.get("tiling", True)),
        )
    except RuntimeError as err:
        raise HTTPException(503, str(err)) from err
    except ImportError as err:
        raise HTTPException(503, f"material deps missing (gpu extra): {err}") from err


def _run(provider: str, mode: str, *, image_b64=None, prompt=None, fmt="glb",
         target_tris=None) -> dict:
    from clay.gpu_backend import runtime

    try:
        mesh_bytes, triangles = runtime.generate(
            provider, mode, image_b64=image_b64, prompt=prompt, fmt=fmt,
            target_tris=target_tris,
        )
    except RuntimeError as err:
        raise HTTPException(503, str(err)) from err
    except ImportError as err:
        raise HTTPException(503, f"model runtime deps missing (gpu extra): {err}") from err
    return {
        "mesh_b64": base64.b64encode(mesh_bytes).decode(),
        "format": fmt,
        "triangles": triangles,
        "textures": [],
    }
