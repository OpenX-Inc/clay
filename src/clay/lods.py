"""LOD chains — decimated copies at descending ratios. Pure geometry (trimesh), CPU.

Populating a scene needs level-of-detail. LOD0 is the full mesh; each subsequent
ratio is quadric-decimated to ``ratio * base_faces``. Reuses the same decimation
as the game-ready pipeline.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_RATIOS = (1.0, 0.5, 0.25, 0.1)


def make_lods(
    input_path: str | Path,
    ratios: tuple[float, ...] | list[float] = DEFAULT_RATIOS,
    *,
    out_dir: str | Path | None = None,
    out_stem: str | None = None,
    fmt: str | None = None,
) -> dict:
    """Build an LOD chain. Returns ``{lods: [{level, ratio, path, faces}], ...}``."""
    import trimesh

    src = Path(input_path)
    try:
        mesh = trimesh.load(src, force="mesh")
    except Exception as err:  # noqa: BLE001 — clean message (e.g. FBX unsupported)
        raise ValueError(
            f"cannot load {src.suffix or 'file'} for LODs — use glb/obj/ply/stl. {err}"
        ) from err

    if not ratios:
        raise ValueError("ratios must be a non-empty list")

    base_faces = int(len(mesh.faces))
    fmt = fmt or src.suffix.lstrip(".") or "glb"
    out = Path(out_dir or src.parent)
    out.mkdir(parents=True, exist_ok=True)
    stem = out_stem or src.stem

    lods = []
    for i, ratio in enumerate(ratios):
        target = max(4, int(base_faces * ratio))
        if ratio >= 1.0 or target >= base_faces:
            lod = mesh
        else:
            lod = mesh.simplify_quadric_decimation(face_count=target)
        path = out / f"{stem}_LOD{i}.{fmt}"
        lod.export(str(path))
        lods.append(
            {"level": i, "ratio": float(ratio), "path": str(path), "faces": int(len(lod.faces))}
        )
    return {"lods": lods, "count": len(lods), "base_faces": base_faces}
