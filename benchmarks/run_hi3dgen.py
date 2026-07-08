"""Validate the Hi3DGen (Stable-X, MIT) shape runtime on Modal.

    modal run benchmarks/run_hi3dgen.py            # uses benchmarks/assets/pot.png
    modal run benchmarks/run_hi3dgen.py --image benchmarks/assets/chair.png
"""

from __future__ import annotations

import base64
from pathlib import Path

import modal

from clay.gpu_backend.image import GPU, build_hi3dgen_image

app = modal.App("openx-clay-hi3dgen")
image = build_hi3dgen_image()
volume = modal.Volume.from_name("clay-hi3dgen-weights", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/models": volume}, timeout=2400)
def gen_shape(image_b64: str, target_tris: int) -> dict:
    from clay.gpu_backend import runtime

    mesh_bytes, tris = runtime.generate(
        "hi3dgen", "image", image_b64=image_b64, target_tris=target_tris
    )
    return {"mesh_b64": base64.b64encode(mesh_bytes).decode(), "triangles": tris}


@app.local_entrypoint()
def main(image: str = "benchmarks/assets/pot.png", target_tris: int = 60000):
    img_b64 = base64.b64encode(Path(image).read_bytes()).decode()
    print(f"🧊 Hi3DGen shape — {image} on {GPU}")
    res = gen_shape.remote(img_b64, target_tris)
    out = Path("benchmarks/results/hi3dgen")
    out.mkdir(parents=True, exist_ok=True)
    dst = out / f"{Path(image).stem}_hi3dgen.glb"
    dst.write_bytes(base64.b64decode(res["mesh_b64"]))
    print(f"✓ {dst} — {res['triangles']} tris")
