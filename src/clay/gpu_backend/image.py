"""The GPU image for TRELLIS-2 — the real from-source build.

TRELLIS is **not** pip-installable: it runs in-place from its cloned repo and
depends on custom CUDA extensions that must be compiled (``nvdiffrast``,
``diffoctreerast``, ``diff-gaussian-rasterization``, ``vox2seq``) plus prebuilt
wheels (``xformers``, ``spconv``, ``kaolin``). This module builds that image once
so the Modal deploy server and the benchmark harness share one definition.

Pinned to CUDA 12.1 + torch 2.4.0 (the combo with kaolin/xformers wheels). The
extensions compile on Modal's CPU builder using ``TORCH_CUDA_ARCH_LIST`` (A100 =
sm_80); no GPU is needed to build, only to run.
"""

from __future__ import annotations

import os

import modal

GPU = os.environ.get("CLAY_BENCH_GPU", "A10G")
# Target GPU compute capabilities for the CUDA extension builds — multi-arch so
# one image runs on A10G (8.6), A100 (8.0) and L40S (8.9) without a rebuild.
CUDA_ARCH = os.environ.get("CLAY_CUDA_ARCH", "8.0;8.6;8.9")
TORCH_INDEX = "https://download.pytorch.org/whl/cu121"
KAOLIN_LINKS = "https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.0_cu121.html"
# utils3d pinned to the commit TRELLIS requires.
UTILS3D = "git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8"


def build_trellis_image() -> modal.Image:
    return (
        modal.Image.from_registry(
            "nvidia/cuda:12.1.1-devel-ubuntu22.04", add_python="3.11"
        )
        .apt_install(
            "git", "build-essential", "ninja-build", "ffmpeg",
            "libgl1", "libglib2.0-0", "libegl1", "libgles2",
        )
        .env(
            {
                "TORCH_CUDA_ARCH_LIST": CUDA_ARCH,
                "ATTN_BACKEND": "xformers",
                "SPCONV_ALGO": "native",
                "PYTHONPATH": "/trellis",
                "HF_HOME": "/models",
                "U2NET_HOME": "/models/u2net",
            }
        )
        # torch first (matched to CUDA 12.1).
        .pip_install("torch==2.4.0", "torchvision==0.19.0", index_url=TORCH_INDEX)
        # TRELLIS "basic" deps.
        .pip_install(
            "numpy<2", "pillow", "imageio", "imageio-ffmpeg", "tqdm", "easydict",
            "opencv-python-headless", "scipy", "ninja", "rembg", "onnxruntime",
            "trimesh", "xatlas", "pyvista", "pymeshfix", "igraph", "transformers",
            "safetensors", "einops", "open3d", "fastapi[standard]", UTILS3D,
        )
        # Prebuilt wheels: attention backend, sparse conv, kaolin.
        .pip_install("xformers==0.0.27.post2", index_url=TORCH_INDEX)
        .pip_install("spconv-cu120")
        .pip_install("kaolin", find_links=KAOLIN_LINKS)
        # Clone TRELLIS (run in-place) + the extension sources.
        .run_commands(
            "git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git /trellis"
        )
        # Custom CUDA extensions (compiled with nvcc on the CPU builder).
        # --no-build-isolation so the builds see the already-installed torch;
        # that means the build backend (setuptools/wheel) must be present too.
        # CC/CXX are forced to gcc/g++ (Modal's standalone Python reports clang
        # via sysconfig, but only build-essential's gcc is installed).
        .run_commands("pip install -U pip setuptools wheel")
        .run_commands(
            "CC=gcc CXX=g++ pip install --no-build-isolation "
            "git+https://github.com/NVlabs/nvdiffrast.git",
            "git clone --recurse-submodules https://github.com/JeffreyXiang/diffoctreerast.git "
            "/tmp/diffoctreerast && CC=gcc CXX=g++ pip install --no-build-isolation "
            "/tmp/diffoctreerast",
            "git clone https://github.com/autonomousvision/mip-splatting.git /tmp/mip-splatting "
            "&& CC=gcc CXX=g++ pip install --no-build-isolation "
            "/tmp/mip-splatting/submodules/diff-gaussian-rasterization/",
        )
        # Clay's post-processing needs fast-simplification for decimation. Added
        # as a late layer so the compiled CUDA extensions above stay cached.
        .pip_install("fast-simplification>=0.1.7", "pygltflib>=1.16.0")
        .add_local_python_source("clay")
    )


def build_material_image() -> modal.Image:
    """Image for the material runtime (StableMaterials — diffusers, no custom CUDA)."""
    return (
        modal.Image.debian_slim(python_version="3.12")
        .apt_install("git", "libgl1", "libglib2.0-0")
        .pip_install(
            "torch>=2.2.0",
            "torchvision",
            "diffusers>=0.27.0",
            "transformers>=4.40.0",
            "accelerate>=0.29.0",
            "safetensors",
            "huggingface_hub",
            "einops",
            "pillow",
            "numpy<2",
        )
        .env({"HF_HOME": "/models"})
        .add_local_python_source("clay")
    )
