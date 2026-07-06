"""Tests for the GPU backend FastAPI contract app.

The model runtime is GPU-only, so generation is tested against a stubbed
runtime; ``/health`` and ``/remesh`` (real CPU decimation) run for real.
"""

from __future__ import annotations

import base64
import io

import pytest
from fastapi.testclient import TestClient

from clay.gpu_backend.server import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "image-to-3d" in body["endpoints"]


def test_image_to_3d_requires_image():
    assert client.post("/generate/image-to-3d", json={}).status_code == 400


def test_text_to_3d_requires_prompt():
    assert client.post("/generate/text-to-3d", json={}).status_code == 400


def test_image_to_3d_returns_contract(monkeypatch):
    fake_glb = b"GLB-BYTES"
    monkeypatch.setattr(
        "clay.gpu_backend.runtime.generate",
        lambda provider, mode, **kw: (fake_glb, 4242),
    )
    resp = client.post(
        "/generate/image-to-3d", json={"image_b64": "Zm9v", "format": "glb"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert base64.b64decode(body["mesh_b64"]) == fake_glb
    assert body["triangles"] == 4242
    assert body["format"] == "glb"
    assert body["textures"] == []


def test_unwired_provider_fails_visibly():
    """An unwired provider must 503 with an honest message, not fake success."""
    resp = client.post(
        "/generate/image-to-3d", json={"image_b64": "Zm9v", "provider": "nope"}
    )
    assert resp.status_code == 503
    assert "not wired" in resp.json()["detail"]


def test_texture_is_honest_503():
    resp = client.post("/texture", json={"mesh_b64": "Zm9v"})
    assert resp.status_code == 503
    assert "not wired" in resp.json()["detail"]


def test_remesh_requires_mesh():
    assert client.post("/remesh", json={}).status_code == 400


def test_remesh_really_decimates():
    """Real CPU decimation: an icosphere reduced to a small triangle budget."""
    trimesh = pytest.importorskip("trimesh")
    sphere = trimesh.creation.icosphere(subdivisions=4)  # ~20k faces
    buf = io.BytesIO()
    sphere.export(buf, file_type="glb")
    mesh_b64 = base64.b64encode(buf.getvalue()).decode()

    resp = client.post("/remesh", json={"mesh_b64": mesh_b64, "target_tris": 500})
    assert resp.status_code == 200
    body = resp.json()
    assert body["triangles"] <= 500
    assert base64.b64decode(body["mesh_b64"])  # decodes to a real mesh
