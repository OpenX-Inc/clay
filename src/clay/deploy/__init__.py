"""Deployers for the GPU backend (Modal automated; AWS/GCP scaffolded)."""

from __future__ import annotations

from clay.deploy import cloud, modal_deploy  # noqa: F401 — register deployers
from clay.deploy.base import (
    Deployer,
    DeployResult,
    DeploySpec,
    available_providers,
    get_deployer,
)

__all__ = [
    "DeploySpec",
    "DeployResult",
    "Deployer",
    "get_deployer",
    "available_providers",
]
