"""Tests for the Generator (orchestrator → GPU backend). HTTP is mocked."""

import base64

import pytest

from clay.config import Config
from clay.generator import Generator
from clay.schemas import GenerationRequest, GenMode


def _cfg():
    cfg = Config()
    cfg.gpu_backend.url = "https://backend.example"
    cfg.providers.model = "trellis2"
    return cfg


def test_generate_image_writes_mesh(monkeypatch):
    seen = {}

    def fake_post(self, endpoint, payload):
        seen["endpoint"] = endpoint
        seen["payload"] = payload
        return {
            "mesh_b64": base64.b64encode(b"GLBDATA").decode(),
            "format": "glb", "triangles": 123,
        }

    monkeypatch.setattr(Generator, "_post", fake_post)
    gen = Generator(_cfg())
    asset = gen.generate(GenerationRequest(mode=GenMode.image, image_b64="aW1n", format="glb"))

    assert seen["endpoint"] == "/generate/image-to-3d"
    assert seen["payload"]["provider"] == "trellis2"
    assert seen["payload"]["image_b64"] == "aW1n"
    from pathlib import Path
    assert Path(asset.path).read_bytes() == b"GLBDATA"
    assert asset.format == "glb"
    assert asset.triangles == 123
    assert asset.provider == "trellis2"


def test_generate_text_uses_text_endpoint(monkeypatch):
    seen = {}

    def fake_post(self, ep, p):
        seen["ep"] = ep
        seen["p"] = p
        return {"mesh_b64": base64.b64encode(b"X").decode()}

    monkeypatch.setattr(Generator, "_post", fake_post)
    Generator(_cfg()).generate(GenerationRequest(mode=GenMode.text, prompt="a clay pot"))
    assert seen["ep"] == "/generate/text-to-3d"
    assert seen["p"]["prompt"] == "a clay pot"


def test_no_backend_raises():
    with pytest.raises(RuntimeError, match="No GPU backend"):
        Generator(Config()).generate(GenerationRequest(mode=GenMode.text, prompt="x"))


def test_fetch_asset_b64_and_url(monkeypatch):
    gen = Generator(_cfg())
    assert gen._fetch_asset({"mesh_b64": base64.b64encode(b"AB").decode()}, "mesh") == b"AB"
    monkeypatch.setattr(gen, "_download", lambda url: b"DL:" + url.encode())
    assert gen._fetch_asset({"mesh_url": "/files/x.glb"}, "mesh") == b"DL:https://backend.example/files/x.glb"
    assert gen._fetch_asset({}, "mesh") is None
