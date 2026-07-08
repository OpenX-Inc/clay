"""Validate the Hunyuan3D-Paint texture runtime on Modal (NON-COMMERCIAL weights).

    modal run benchmarks/run_texture.py
    modal run benchmarks/run_texture.py --mesh <mesh.glb> --image <ref.png>
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import modal

from clay.gpu_backend.image import build_hunyuan_paint_image

GPU = os.environ.get("CLAY_TEXTURE_GPU", "A10G")

app = modal.App("openx-clay-texture")
image = build_hunyuan_paint_image()
volume = modal.Volume.from_name("clay-hunyuan-weights", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/models": volume}, timeout=3000)
def tex(mesh_b64: str, image_b64: str, resolution: int) -> dict:
    from clay.gpu_backend import runtime

    return runtime.generate_texture(
        "hunyuanpaint", mesh_b64=mesh_b64, image_b64=image_b64, resolution=resolution
    )


@app.local_entrypoint()
def main(
    mesh: str = "benchmarks/results/samples/pot.glb",
    image: str = "benchmarks/assets/pot.png",
    resolution: int = 1024,
):
    mesh_b64 = base64.b64encode(Path(mesh).read_bytes()).decode()
    image_b64 = base64.b64encode(Path(image).read_bytes()).decode()
    print(f"🎨 Hunyuan3D-Paint texture — {mesh} + {image} on {GPU}")
    res = tex.remote(mesh_b64, image_b64, resolution)
    out = Path("benchmarks/results/texture")
    out.mkdir(parents=True, exist_ok=True)
    dst = out / f"{Path(mesh).stem}_textured.glb"
    dst.write_bytes(base64.b64decode(res["mesh_b64"]))
    print(f"✓ {dst}")
