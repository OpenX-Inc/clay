"""Physics colliders — convex hull / box / simplified / VHACD compound.

Pure geometry (trimesh), CPU-only. "Game-ready" isn't complete without a
collider; UE needs one to make an asset usable in the world. Compound
(convex-decomposition) uses ``coacd`` when installed (``clay[collision]``) and
falls back to per-connected-component convex hulls otherwise — always producing
a valid, low-hull, physics-cheap proxy.
"""

from __future__ import annotations

from pathlib import Path

_KINDS = ("convex", "box", "simplified", "compound")


def make_collision(
    input_path: str | Path,
    kind: str = "convex",
    *,
    max_hulls: int = 32,
    out_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    fmt: str | None = None,
) -> dict:
    """Build a collision proxy for a mesh. Returns ``{path, kind, hulls, faces}``."""
    import trimesh

    kind = kind or "convex"
    if kind not in _KINDS:
        raise ValueError(f"unknown collider kind {kind!r}; use {', '.join(_KINDS)}")

    src = Path(input_path)
    try:
        mesh = trimesh.load(src, force="mesh")
    except Exception as err:  # noqa: BLE001 — surface a clean message (e.g. FBX unsupported)
        raise ValueError(
            f"cannot load {src.suffix or 'file'} for collision — use glb/obj/ply/stl "
            f"(FBX isn't loadable here; convert it first). {err}"
        ) from err
    if fmt is None:
        ext = Path(out_path).suffix.lstrip(".") if out_path else ""
        fmt = ext or src.suffix.lstrip(".") or "glb"

    hulls = 1
    if kind == "box":
        lo, hi = mesh.bounds
        proxy = trimesh.creation.box(extents=(hi - lo))
        proxy.apply_translation((lo + hi) / 2.0)
    elif kind in ("convex", "simplified"):
        proxy = mesh.convex_hull
    else:  # compound
        proxy, hulls = _compound(mesh, max_hulls)

    out = (
        Path(out_path)
        if out_path
        else Path(out_dir or src.parent) / f"{src.stem}_collision.{fmt}"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    proxy.export(str(out))
    return {"path": str(out), "kind": kind, "hulls": int(hulls), "faces": int(len(proxy.faces))}


def _compound(mesh, max_hulls: int):
    """Convex decomposition → combined hulls. coacd if available, else per-component."""
    import trimesh

    pieces = []
    try:
        import coacd

        cmesh = coacd.Mesh(mesh.vertices, mesh.faces)
        parts = coacd.run_coacd(cmesh, max_convex_hull=max_hulls)
        for v, f in parts:
            try:
                pieces.append(trimesh.Trimesh(vertices=v, faces=f).convex_hull)
            except Exception:  # noqa: BLE001 — skip degenerate part
                continue
    except Exception:  # noqa: BLE001 — coacd absent/failed → per-component hulls
        comps = mesh.split(only_watertight=False)
        comps = list(comps) if len(comps) else [mesh]
        for c in comps[:max_hulls]:
            try:
                pieces.append(c.convex_hull)
            except Exception:  # noqa: BLE001 — skip degenerate component
                continue

    if not pieces:
        return mesh.convex_hull, 1
    return trimesh.util.concatenate(pieces), len(pieces)
