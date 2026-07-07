"""Configuration for Clay (Pydantic models + TOML loader)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class GPUBackendConfig(BaseModel):
    """Where 3D generation runs — reached over the HTTP contract."""

    provider: str = "modal"  # modal | runpod | self-hosted
    url: str = ""            # deployed backend base URL
    api_key: str = ""


class ProvidersConfig(BaseModel):
    """Which 3D model provider to use (swappable)."""

    model: str = "trellis2"  # trellis2 | hunyuan3d | hi3dgen


class PostprocessConfig(BaseModel):
    """Game-ready post-processing defaults."""

    target_tris: int = 60000  # decimate/remesh to this triangle budget
    unwrap_uvs: bool = True    # re-unwrap UVs (xatlas)
    format: str = "glb"        # glb | obj | fbx
    pbr: bool = True           # keep/pack PBR maps


class AgentConfig(BaseModel):
    """The in-app agent (LLM that drives the tools)."""

    provider: str = "nvidia"
    base_url: str = "https://integrate.api.nvidia.com/v1"
    api_key: str = ""  # falls back to CLAY_NVIDIA_API_KEY
    model: str = "kimi"
    max_iterations: int = 12


class MCPConfig(BaseModel):
    """MCP server exposing the tools to external agents."""

    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = 8770
    token: str = ""  # falls back to CLAY_MCP_TOKEN


class DeployConfig(BaseModel):
    """Defaults for ``clay deploy`` (deploy the GPU backend as a named instance)."""

    provider: str = "modal"  # modal | aws | gcp
    name: str = "clay-gpu-backend"
    gpu: str = "A100-80GB"
    scaledown_window: int = 300


class BlenderConfig(BaseModel):
    """Headless Blender — Clay's mesh-processing engine (FBX export, rig, retopo, bake).

    ``path`` points at a Blender binary; if empty, Clay looks at ``CLAY_BLENDER`` /
    ``BLENDER_PATH`` env vars, then ``blender`` on PATH. Blender-backed tools fail
    visibly when none is found.
    """

    path: str = ""


class Config(BaseModel):
    gpu_backend: GPUBackendConfig = GPUBackendConfig()
    providers: ProvidersConfig = ProvidersConfig()
    postprocess: PostprocessConfig = PostprocessConfig()
    agent: AgentConfig = AgentConfig()
    mcp: MCPConfig = MCPConfig()
    deploy: DeployConfig = DeployConfig()
    blender: BlenderConfig = BlenderConfig()
    output_dir: str = "storage/outputs"


def load_config(path: str | Path = "config/config.toml") -> Config:
    """Load configuration from a TOML file (defaults when the file is absent)."""
    config_path = Path(path)
    if not config_path.exists():
        return Config()
    data: dict[str, Any] = tomllib.loads(config_path.read_text())
    return Config(**data)
