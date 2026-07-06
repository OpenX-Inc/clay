"""Tests for game-ready post-processing (real decimation/unwrap/export)."""

from pathlib import Path

import pytest
import trimesh

from clay.config import PostprocessConfig
from clay.postprocess import PostProcessor
from clay.schemas import Generated3DAsset


def _raw_asset(tmp_path, subdiv=4):
    mesh = trimesh.creation.icosphere(subdivisions=subdiv)
    raw = tmp_path / "raw.glb"
    mesh.export(str(raw))
    return Generated3DAsset(path=str(raw), format="glb", triangles=len(mesh.faces),
                            provider="trellis2"), len(mesh.faces)


def test_decimates_to_budget(tmp_path):
    asset, n = _raw_asset(tmp_path)
    assert n > 1000  # ~5120-face sphere
    pp = PostProcessor(PostprocessConfig(target_tris=1000, unwrap_uvs=False, format="glb"))
    out = pp.process(asset, out_path=str(tmp_path / "out.glb"))
    assert Path(out.path).exists()
    assert out.triangles < n           # actually reduced
    assert out.triangles <= 1200       # ~ the target budget
    reloaded = trimesh.load(out.path, force="mesh")
    assert len(reloaded.faces) == out.triangles


def test_decimate_noop_when_under_budget():
    mesh = trimesh.creation.icosphere(subdivisions=1)  # ~80 faces
    pp = PostProcessor(PostprocessConfig(target_tris=100000))
    assert len(pp.decimate(mesh, 100000).faces) == len(mesh.faces)


def test_unwrap_produces_uvs():
    mesh = trimesh.creation.icosphere(subdivisions=2)
    m = PostProcessor(PostprocessConfig()).unwrap(mesh)
    assert m.visual.uv is not None
    assert len(m.visual.uv) == len(m.vertices)


def test_fbx_export_is_honest(tmp_path):
    asset, _ = _raw_asset(tmp_path, subdiv=2)
    pp = PostProcessor(PostprocessConfig(target_tris=100000, format="fbx"))
    with pytest.raises(RuntimeError, match="FBX"):
        pp.process(asset, out_path=str(tmp_path / "out.fbx"))
