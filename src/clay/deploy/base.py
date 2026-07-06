"""Deployers — push Clay's GPU backend to a provider as a NAMED instance.

A token alone can't generate: the open-source backend must be *deployed* into the
target account, which yields the endpoint URL jobs route to. Parameterized by a
:class:`DeploySpec` (CLI args and/or config), so several named instances can be
stood up (e.g. an A100 pool and an H100 pool).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class DeploySpec:
    name: str = "clay-gpu-backend"
    gpu: str = "A100-80GB"
    model: str = "trellis2"          # which 3D provider the backend serves
    scaledown_window: int = 300
    region: str = ""
    # Credentials passed per-invocation (e.g. Modal token) — injected into the
    # deploy subprocess env only, never the ambient env.
    credentials: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)


@dataclass
class DeployResult:
    name: str
    provider: str
    status: str  # "deployed" | "manual_required" | "failed"
    endpoint_url: str = ""
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "deployed"


class Deployer(ABC):
    provider: str = "base"

    @abstractmethod
    def deploy(self, spec: DeploySpec) -> DeployResult:
        ...


_REGISTRY: dict[str, type[Deployer]] = {}


def register(cls: type[Deployer]) -> type[Deployer]:
    _REGISTRY[cls.provider] = cls
    return cls


def get_deployer(provider: str) -> Deployer:
    cls = _REGISTRY.get(provider)
    if cls is None:
        raise ValueError(f"unknown provider {provider!r}; available: {available_providers()}")
    return cls()


def available_providers() -> list[str]:
    return sorted(_REGISTRY)
