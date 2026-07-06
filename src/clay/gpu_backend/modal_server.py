"""GPU backend — Modal deployment of Clay's base64 HTTP contract.

Deploys as a **single FastAPI ASGI app** (the very ``clay.gpu_backend.server``
app), so one deployment = one base URL, no per-endpoint subdomains. Parameterized
via env so you can stand up several **named** instances in one account (an A100
pool, an H100 pool, one per tenant)::

    CLAY_GPU_APP_NAME=clay-gpu-a100 CLAY_GPU_TYPE=A100-80GB CLAY_MODEL=trellis2 \\
        modal deploy -m clay.gpu_backend.modal_server

The deployed base URL is ``https://<workspace>--<app-name>.modal.run``; put it
in ``[gpu_backend].url``. ``clay deploy modal`` wraps this.

Note: TRELLIS-2 is a research pipeline installed from its GitHub repo (not a
single pip package); the image below installs the GPU deps and the TRELLIS
source. GPU-only — validated by a contributor with weights + hardware.
"""

from __future__ import annotations

import os

import modal

from clay.gpu_backend.image import build_trellis_image

# --- Parameterization (read at deploy/import time) ---------------------------
APP_NAME = os.environ.get("CLAY_GPU_APP_NAME", "clay-gpu-backend")
GPU_TYPE = os.environ.get("CLAY_GPU_TYPE", "A100-80GB")
MODEL = os.environ.get("CLAY_MODEL", "trellis2")
SCALEDOWN_WINDOW = int(os.environ.get("CLAY_GPU_SCALEDOWN", "300"))

app = modal.App(APP_NAME)

# Weights volume, namespaced per instance so named deploys don't clobber each other.
volume = modal.Volume.from_name(f"{APP_NAME}-weights", create_if_missing=True)

# The real from-source TRELLIS-2 image (custom CUDA extensions). Shared with the
# benchmark harness so the deploy and benchmark environments are identical.
image = build_trellis_image()


@app.cls(
    image=image,
    gpu=GPU_TYPE,
    volumes={"/models": volume},
    timeout=900,
    scaledown_window=SCALEDOWN_WINDOW,
)
class ClayServer:
    """Serves ``clay.gpu_backend.server:app`` — one base64 contract on Modal."""

    @modal.enter()
    def warm(self):
        # Pre-import the provider runtime so the first request isn't cold.
        os.environ.setdefault("CLAY_MODEL", MODEL)
        try:
            from clay.gpu_backend import runtime

            if MODEL == "trellis2":
                runtime._load_trellis()
        except Exception as err:  # noqa: BLE001 — warm-up is best-effort
            print(f"[clay] model warm-up deferred: {err}")

    @modal.asgi_app(label=APP_NAME)
    def web(self):
        from clay.gpu_backend.server import app as fastapi_app

        return fastapi_app
