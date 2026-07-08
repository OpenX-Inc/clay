"""Validate the StableMaterials material runtime on Modal.

Runs the actual shipped ``clay.gpu_backend.runtime.generate_material`` on a GPU
and writes the returned PBR maps locally — the same validate-real-output loop we
used for TRELLIS-2.

    modal run benchmarks/run_material.py
    modal run benchmarks/run_material.py --prompt "weathered concrete" --kind concrete
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import modal

from clay.gpu_backend.image import build_material_image

GPU = os.environ.get("CLAY_MATERIAL_GPU", "A10G")

app = modal.App("openx-clay-material")
image = build_material_image()
volume = modal.Volume.from_name("clay-material-weights", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/models": volume}, timeout=1800)
def gen_material(kind: str, prompt: str, resolution: int) -> dict:
    from clay.gpu_backend import runtime

    return runtime.generate_material(
        "stablematerials", kind=kind, prompt=prompt, resolution=resolution, tiling=True
    )


@app.local_entrypoint()
def main(
    prompt: str = "Nairobi CBD glass office facade, seamless PBR material",
    kind: str = "facade",
    resolution: int = 1024,
):
    print(f"🎨 material — {kind}: {prompt} on {GPU}")
    result = gen_material.remote(kind, prompt, resolution)
    out = Path("benchmarks/results/material")
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for key, val in result.items():
        if key.endswith("_b64"):
            path = out / f"{kind}_{key[:-4]}.png"
            path.write_bytes(base64.b64decode(val))
            saved.append(path.name)
    print(f"✓ saved {len(saved)} maps: {', '.join(saved)}" if saved else "✗ no maps returned")
