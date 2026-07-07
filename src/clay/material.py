"""Material generation — tiling PBR material sets via the GPU backend /material route.

The orchestrator calls the swappable backend (``POST /material``) and writes the
returned PBR maps (base_color / normal / roughness / metallic / ao) as PNGs plus
a ``material.json`` manifest. Inference lives in ``clay/gpu_backend`` and is
GPU-gated — no backend ⇒ a visible error, never fake maps.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from clay.config import Config

MAPS = ("base_color", "normal", "roughness", "metallic", "ao")
TILING_KINDS = ("facade", "road", "ground")


class MaterialGenerator:
    """Calls the GPU backend to synthesise a tiling PBR material set."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.backend_url = config.gpu_backend.url.rstrip("/")
        self.provider = config.providers.material

    def generate(
        self,
        *,
        kind: str = "generic",
        prompt: str | None = None,
        image_path: str | None = None,
        resolution: int = 1024,
        tiling: bool | None = None,
        out_dir: str | Path = ".",
        stem: str | None = None,
    ) -> dict:
        if not self.backend_url:
            raise RuntimeError(
                "No GPU backend configured — set [gpu_backend].url "
                "(deploy one with `clay deploy`)."
            )
        if not prompt and not image_path:
            raise ValueError("generate_material needs a prompt or an image_path")
        if tiling is None:
            tiling = kind in TILING_KINDS

        payload: dict = {
            "provider": self.provider,
            "kind": kind,
            "resolution": int(resolution),
            "tiling": bool(tiling),
        }
        if prompt:
            payload["prompt"] = prompt
        if image_path:
            payload["image_b64"] = base64.b64encode(Path(image_path).read_bytes()).decode()

        result = self._post("/material", payload)

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = stem or f"{kind}_material"
        result_maps = result.get("maps") or {}
        maps: dict[str, str] = {}
        for m in MAPS:
            b64 = result.get(f"{m}_b64") or result_maps.get(m)
            if b64:
                path = out / f"{stem}_{m}.png"
                path.write_bytes(base64.b64decode(b64))
                maps[m] = str(path)

        manifest = {
            "kind": kind, "resolution": int(resolution), "tiling": bool(tiling),
            "provider": self.provider, "maps": maps,
        }
        man_path = out / f"{stem}.material.json"
        man_path.write_text(json.dumps(manifest, indent=2))
        return {"manifest": str(man_path), "maps": maps, "kind": kind, "provider": self.provider}

    def _post(self, endpoint: str, payload: dict) -> dict:
        headers = {}
        if self.config.gpu_backend.api_key:
            headers["Authorization"] = f"Bearer {self.config.gpu_backend.api_key}"
        with httpx.Client(timeout=900) as client:
            resp = client.post(f"{self.backend_url}{endpoint}", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
