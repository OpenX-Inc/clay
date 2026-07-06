"""AWS and GCP deployers — honest scaffolds.

These are **not** automated yet, and they do not pretend to be: they return a
``manual_required`` result with the concrete steps to stand up the GPU backend
on that cloud. First-class AWS/GCP automation is on the roadmap. No fake
success.
"""

from __future__ import annotations

from clay.deploy.base import Deployer, DeployResult, DeploySpec, register

_CONTRACT = (
    "exposing POST /generate/image-to-3d|text-to-3d, /texture, /remesh and "
    "GET /health (base64 contract), then put the endpoint URL in [gpu_backend].url"
)


@register
class AWSDeployer(Deployer):
    provider = "aws"

    def deploy(self, spec: DeploySpec) -> DeployResult:
        return DeployResult(
            spec.name, self.provider, "manual_required",
            detail=(
                "AWS deploy is not automated yet. Manual path: build the GPU "
                "backend image (Dockerfile.gpu), push to ECR, and deploy as a "
                "SageMaker async endpoint or an ECS/EKS GPU service "
                f"{_CONTRACT}. Region: " + (spec.region or "us-east-1") + "."
            ),
        )


@register
class GCPDeployer(Deployer):
    provider = "gcp"

    def deploy(self, spec: DeploySpec) -> DeployResult:
        return DeployResult(
            spec.name, self.provider, "manual_required",
            detail=(
                "GCP deploy is not automated yet. Manual path: build the GPU "
                "backend image (Dockerfile.gpu), push to Artifact Registry, and "
                "deploy to Cloud Run (GPU) or GKE "
                f"{_CONTRACT}. Region: " + (spec.region or "us-central1") + "."
            ),
        )
