"""Variations — N seed-varied generations of a prop/livery via the shape pipeline.

Loops the standard ``Pipeline`` with incrementing seeds to populate streets or
build a livery catalogue. GPU-gated (needs a deployed shape backend, like
``generate``).
"""

from __future__ import annotations

from pathlib import Path

from clay.config import Config
from clay.pipeline import Pipeline
from clay.schemas import GenerationRequest, GenMode


def generate_variations(
    config: Config,
    *,
    mode: str = "image",
    prompt: str | None = None,
    image_path: str | None = None,
    count: int = 4,
    seed: int = 0,
    target_tris: int | None = None,
    fmt: str = "glb",
    out_dir: str | Path | None = None,
    stem: str = "variation",
) -> dict:
    """Generate ``count`` variations (seed, seed+1, …). Returns a list of assets."""
    if count < 1:
        raise ValueError("count must be >= 1")
    gen_mode = GenMode(mode)
    if gen_mode == GenMode.image and not image_path:
        raise ValueError("image mode needs image_path")
    if gen_mode == GenMode.text and not prompt:
        raise ValueError("text mode needs prompt")

    pipe = Pipeline(config)
    out = Path(out_dir or config.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    variations = []
    for i in range(count):
        req = GenerationRequest(
            mode=gen_mode,
            prompt=prompt or "",
            image_path=image_path,
            format=fmt,
            target_tris=target_tris or config.postprocess.target_tris,
            unwrap_uvs=config.postprocess.unwrap_uvs,
            pbr=config.postprocess.pbr,
            seed=seed + i,
        )
        asset = pipe.run(req, out_path=str(out / f"{stem}_{i}.{fmt}"))
        variations.append(
            {"path": asset.path, "seed": seed + i, "triangles": asset.triangles}
        )
    return {"variations": variations, "count": len(variations)}
