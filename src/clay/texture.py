"""Texture (re-)painting — UV-aware texturing of an existing mesh via /texture.

Paints/re-skins a mesh from a prompt/image onto its own UVs (character skins,
prop variants, vehicle liveries). Writes the texture map set, the re-textured
mesh, an optional set of transparent decal PNGs, and a manifest. Inference lives
in ``clay/gpu_backend`` and is GPU-gated — no backend ⇒ a visible error.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx

from clay.config import Config

MAPS = ("base_color", "normal", "roughness", "metallic", "ao")


class TextureAssetGenerator:
    """Calls the GPU backend to paint a texture set onto a mesh's UVs."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.backend_url = config.gpu_backend.url.rstrip("/")
        self.provider = config.providers.texture

    def texture(
        self,
        input_path: str | Path,
        *,
        prompt: str | None = None,
        image_path: str | None = None,
        resolution: int = 1024,
        keep_uvs: bool = True,
        emit_decals: bool = False,
        out_dir: str | Path = ".",
        stem: str | None = None,
    ) -> dict:
        if not self.backend_url:
            raise RuntimeError(
                "No GPU backend configured — set [gpu_backend].url "
                "(deploy one with `clay deploy`)."
            )
        src = Path(input_path)
        if not src.exists():
            raise FileNotFoundError(f"no mesh at {src}")
        if not prompt and not image_path:
            raise ValueError("texture_asset needs a prompt or an image_path")

        payload: dict = {
            "provider": self.provider,
            "mesh_b64": base64.b64encode(src.read_bytes()).decode(),
            "mesh_format": src.suffix.lstrip("."),
            "resolution": int(resolution),
            "keep_uvs": bool(keep_uvs),
            "emit_decals": bool(emit_decals),
        }
        if prompt:
            payload["prompt"] = prompt
        if image_path:
            payload["image_b64"] = base64.b64encode(Path(image_path).read_bytes()).decode()

        result = self._post("/texture", payload)

        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = stem or f"{src.stem}_textured"
        result_maps = result.get("maps") or {}
        maps: dict[str, str] = {}
        for m in MAPS:
            b64 = result.get(f"{m}_b64") or result_maps.get(m)
            if b64:
                p = out / f"{stem}_{m}.png"
                p.write_bytes(base64.b64decode(b64))
                maps[m] = str(p)

        mesh_out = None
        mesh_b64 = result.get("mesh_b64")
        if mesh_b64:
            mesh_out = out / f"{stem}{src.suffix or '.glb'}"
            mesh_out.write_bytes(base64.b64decode(mesh_b64))

        decals = []
        for i, d in enumerate(result.get("decals", [])):
            b64 = d.get("b64") if isinstance(d, dict) else d
            if b64:
                dp = out / f"{stem}_decal{i}.png"
                dp.write_bytes(base64.b64decode(b64))
                decals.append(str(dp))

        manifest = {
            "input": str(src), "provider": self.provider, "prompt": prompt,
            "resolution": int(resolution), "keep_uvs": bool(keep_uvs),
            "maps": maps, "mesh": str(mesh_out) if mesh_out else None, "decals": decals,
        }
        man_path = out / f"{stem}.texture.json"
        man_path.write_text(json.dumps(manifest, indent=2))
        return {
            "manifest": str(man_path), "maps": maps,
            "mesh": str(mesh_out) if mesh_out else None, "decals": decals,
            "provider": self.provider,
        }

    def _post(self, endpoint: str, payload: dict) -> dict:
        headers = {}
        if self.config.gpu_backend.api_key:
            headers["Authorization"] = f"Bearer {self.config.gpu_backend.api_key}"
        with httpx.Client(timeout=900) as client:
            resp = client.post(f"{self.backend_url}{endpoint}", json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()
