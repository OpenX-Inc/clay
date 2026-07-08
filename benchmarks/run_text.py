"""Validate the TRELLIS-2 text-to-3D runtime on Modal + emit a viewer HTML.

    modal run benchmarks/run_text.py --prompt "a low-poly wooden treasure chest"
    modal run benchmarks/run_text.py --prompt "..." --target-tris 80000 --name matatu

Writes benchmarks/results/text/<name>.glb + <name>.html (self-contained
<model-viewer> — open it in a browser to orbit the result).
"""

from __future__ import annotations

import base64
from pathlib import Path

import modal

from clay.gpu_backend.image import GPU, build_trellis_image

app = modal.App("openx-clay-text")
image = build_trellis_image()
volume = modal.Volume.from_name("clay-bench-weights", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/models": volume}, timeout=2400)
def gen_text(prompt: str, target_tris: int, seed: int) -> dict:
    from clay.gpu_backend import runtime

    mesh_bytes, tris = runtime.generate(
        "trellis2", "text", prompt=prompt, target_tris=target_tris, seed=seed
    )
    return {"mesh_b64": base64.b64encode(mesh_bytes).decode(), "triangles": tris}


@app.local_entrypoint()
def main(prompt: str, target_tris: int = 80000, seed: int = 1, name: str = "text"):
    from clay.preview import make_viewer_html

    print(f"🧊 TRELLIS-2 text→3D on {GPU} — {prompt[:70]}…")
    res = gen_text.remote(prompt, target_tris, seed)

    out = Path("benchmarks/results/text")
    out.mkdir(parents=True, exist_ok=True)
    glb = out / f"{name}.glb"
    glb.write_bytes(base64.b64decode(res["mesh_b64"]))
    html = make_viewer_html(glb, title=name, tris=res["triangles"])
    print(f"✓ {glb} — {res['triangles']} tris")
    print(f"✓ {html} — open in a browser to view")
