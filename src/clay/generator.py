"""Generator — orchestrates 3D generation via the GPU backend HTTP contract.

The orchestrator never runs the model itself; it calls the swappable backend
(``POST /generate/image-to-3d|text-to-3d``) and materialises the returned mesh.
The heavy model inference lives in ``clay/gpu_backend``. Assets come back inline
as base64 (serverless-friendly) or as a URL — both are handled.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import httpx

from clay.config import Config
from clay.schemas import Generated3DAsset, GenerationRequest, GenMode, Texture

_ENDPOINTS = {
    GenMode.image: "/generate/image-to-3d",
    GenMode.text: "/generate/text-to-3d",
}


class Generator:
    """Calls the GPU backend to turn an image/prompt into a raw 3D mesh."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.backend_url = config.gpu_backend.url.rstrip("/")
        self.provider = config.providers.model
        self.out_dir = Path(tempfile.mkdtemp(prefix="clay_gen_"))

    def generate(self, request: GenerationRequest) -> Generated3DAsset:
        """Generate a raw mesh for a request (returns before post-processing)."""
        if not self.backend_url:
            raise RuntimeError(
                "No GPU backend configured — set [gpu_backend].url "
                "(deploy one with `clay deploy`)."
            )
        endpoint = _ENDPOINTS[request.mode]
        payload: dict = {
            "provider": self.provider,
            "format": request.format,
        }
        if request.mode == GenMode.image:
            payload["image_b64"] = request.image_b64 or self._encode_image(request.image_path)
        else:
            payload["prompt"] = request.prompt

        result = self._post(endpoint, payload)

        mesh = self._fetch_asset(result, "mesh")
        if mesh is None:
            raise RuntimeError("GPU backend returned no mesh (expected mesh_b64 or mesh_url)")
        fmt = result.get("format", request.format)
        raw_path = self.out_dir / f"raw.{fmt}"
        raw_path.write_bytes(mesh)

        textures = [
            Texture(kind=t.get("kind", "base_color"), path=self._save_texture(t))
            for t in result.get("textures", [])
        ]
        return Generated3DAsset(
            path=str(raw_path), raw_path=str(raw_path), format=fmt,
            triangles=int(result.get("triangles", 0)),
            provider=self.provider, textures=textures,
        )

    # --- HTTP + asset helpers ------------------------------------------------

    def _post(self, endpoint: str, payload: dict) -> dict:
        headers = {}
        if self.config.gpu_backend.api_key:
            headers["Authorization"] = f"Bearer {self.config.gpu_backend.api_key}"
        with httpx.Client(timeout=900) as client:
            resp = client.post(f"{self.backend_url}{endpoint}", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def _fetch_asset(self, result: dict, name: str) -> bytes | None:
        """Materialise an asset from the response: base64 or (relative/absolute) URL."""
        b64 = result.get(f"{name}_b64")
        if b64:
            return base64.b64decode(b64)
        url = result.get(f"{name}_url")
        if url:
            full = url if url.startswith("http") else f"{self.backend_url}{url}"
            return self._download(full)
        return None

    def _save_texture(self, tex: dict) -> str | None:
        b64 = tex.get("b64")
        if not b64:
            return tex.get("url")
        path = self.out_dir / f"tex_{tex.get('kind', 'map')}.png"
        path.write_bytes(base64.b64decode(b64))
        return str(path)

    def _download(self, url: str) -> bytes:
        with httpx.Client(timeout=300) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content

    def _encode_image(self, path: str | None) -> str:
        if not path:
            raise ValueError("image mode requires image_path or image_b64")
        return base64.b64encode(Path(path).read_bytes()).decode()
