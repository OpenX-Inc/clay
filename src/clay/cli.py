"""CLI entry point for Clay."""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="clay",
    help="OpenX Clay — image/text → game-ready 3D assets.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def generate(
    image: str = typer.Option("", help="Input image path (image → 3D)"),
    prompt: str = typer.Option("", help="Text prompt (text → 3D)"),
    fmt: str = typer.Option("glb", "--format", help="Output format: glb | obj"),
    target_tris: int = typer.Option(60000, help="Triangle budget for the game-ready mesh"),
    output: str = typer.Option("", help="Output path (auto-generated if empty)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
    collision: bool = typer.Option(False, "--collision", help="Also emit a convex collision proxy"),
    with_lods: bool = typer.Option(False, "--with-lods", help="Also emit an LOD chain"),
    retopo: bool = typer.Option(False, "--retopo", help="Also emit a retopologized (quad) copy"),
    bake: bool = typer.Option(False, "--bake", help="Also bake a normal map (decimated low-poly)"),
    rig: bool = typer.Option(False, "--rig", help="Also auto-rig the asset (FBX)"),
    rig_type: str = typer.Option("generic", "--rig-type", help="humanoid|quadruped|vehicle|generic"),  # noqa: E501
    material: bool = typer.Option(False, "--material", help="Also generate a PBR material set (from the prompt)"),  # noqa: E501
    texture: str = typer.Option("", "--texture", help="Also re-texture the mesh with this prompt"),
    dry_run: bool = typer.Option(False, help="Validate + print the plan; no backend call"),
) -> None:
    """Generate a game-ready 3D asset from an image or a prompt."""
    from clay.config import load_config
    from clay.pipeline import Pipeline
    from clay.providers import get_provider
    from clay.schemas import GenerationRequest, GenMode

    if not image and not prompt:
        console.print("[red]Provide --image or --prompt.[/]")
        raise typer.Exit(1)

    cfg = load_config(config_path)
    mode = GenMode.image if image else GenMode.text
    try:
        provider = get_provider(cfg.providers.model)
    except ValueError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    if not provider.supports(mode):
        console.print(f"[red]Provider '{provider.name}' does not support {mode} → 3D.[/]")
        raise typer.Exit(1)

    console.print(
        f"[bold green]Clay[/] — {mode} → 3D via [cyan]{provider.name}[/] · "
        f"{target_tris} tris · {fmt}"
    )
    if dry_run:
        console.print("  [yellow]dry-run[/] — validated, no backend call.")
        console.print(f"  input: {image or prompt!r}")
        return

    request = GenerationRequest(
        mode=mode, image_path=image or None, prompt=prompt, format=fmt,
        target_tris=target_tris, unwrap_uvs=cfg.postprocess.unwrap_uvs, pbr=cfg.postprocess.pbr,
    )
    asset = Pipeline(cfg).run(request, out_path=output or None)
    console.print(
        f"[bold green]✓[/] saved [bold]{asset.path}[/] "
        f"— {asset.triangles} tris, {asset.format}"
    )
    # Opt-in stages fold in here (reusing the same core functions the tools use).
    if collision:
        from pathlib import Path

        from clay.collision import make_collision

        res = make_collision(asset.path, kind="convex", out_dir=Path(cfg.output_dir))
        console.print(
            f"  [green]+ collider[/] {res['path']} — {res['hulls']} hull, {res['faces']} faces"
        )
    if with_lods:
        from pathlib import Path

        from clay.lods import make_lods

        res = make_lods(asset.path, out_dir=Path(cfg.output_dir))
        console.print(f"  [green]+ {res['count']} LODs[/] (base {res['base_faces']} faces)")
    if retopo:
        from pathlib import Path

        from clay.blender import BlenderError
        from clay.blender import retopo as _retopo

        out = Path(cfg.output_dir) / f"{Path(asset.path).stem}_retopo.glb"
        try:
            res = _retopo(
                asset.path, out, target_faces=asset.triangles or 5000,
                blender=cfg.blender.path or None,
            )
            console.print(
                f"  [green]+ retopo[/] {out} — {res['faces']} faces, "
                f"{res['quad_ratio']:.0%} quads"
            )
        except BlenderError as err:
            console.print(f"  [yellow]retopo skipped[/] — {err}")
    if bake:
        from pathlib import Path

        from clay.blender import BlenderError
        from clay.blender import bake_normals as _bake

        stem = Path(asset.path).stem
        out_mesh = Path(cfg.output_dir) / f"{stem}_baked.glb"
        normal = Path(cfg.output_dir) / f"{stem}_normal.png"
        try:
            res = _bake(asset.path, out_mesh, normal, blender=cfg.blender.path or None)
            console.print(
                f"  [green]+ normal bake[/] {res['normal_map']} "
                f"({res['resolution']}², low {res['low_faces']} faces)"
            )
        except BlenderError as err:
            console.print(f"  [yellow]bake skipped[/] — {err}")
    if rig:
        from pathlib import Path

        from clay.blender import BlenderError
        from clay.blender import rig_asset as _rig

        out = Path(cfg.output_dir) / f"{Path(asset.path).stem}_rigged.fbx"
        try:
            res = _rig(asset.path, out, rig_type=rig_type, blender=cfg.blender.path or None)
            extra = f", {res['wheels']} wheels" if res.get("wheels") is not None else ""
            console.print(
                f"  [green]+ rig[/] {out} — {res['rig_type']}, {res['bones']} bones{extra}"
            )
        except BlenderError as err:
            console.print(f"  [yellow]rig skipped[/] — {err}")
    if material and (prompt or image):
        from pathlib import Path

        from clay.material import MaterialGenerator

        try:
            res = MaterialGenerator(cfg).generate(
                kind="generic", prompt=prompt or None, image_path=image or None,
                out_dir=Path(cfg.output_dir), stem=f"{Path(asset.path).stem}_material",
            )
            console.print(f"  [green]+ material[/] {res['manifest']} ({len(res['maps'])} maps)")
        except Exception as err:  # noqa: BLE001 — GPU-gated; report, don't fail the mesh
            console.print(f"  [yellow]material skipped[/] — {err}")
    if texture:
        from pathlib import Path

        from clay.texture import TextureAssetGenerator

        try:
            res = TextureAssetGenerator(cfg).texture(
                asset.path, prompt=texture, out_dir=Path(cfg.output_dir),
            )
            console.print(f"  [green]+ texture[/] {res['manifest']} ({len(res['maps'])} maps)")
        except Exception as err:  # noqa: BLE001 — GPU-gated; report, don't fail the mesh
            console.print(f"  [yellow]texture skipped[/] — {err}")


@app.command()
def deploy(
    provider: str = typer.Argument(help="Where to deploy: modal | aws | gcp"),
    name: str = typer.Option("", help="Named instance (default from config)"),
    gpu: str = typer.Option("", help="GPU type, e.g. A100-80GB (default from config)"),
    model: str = typer.Option("", help="3D provider the backend serves (default from config)"),
    scaledown: int = typer.Option(0, help="Idle seconds before scaledown (default from config)"),
    region: str = typer.Option("", help="Cloud region (aws/gcp)"),
    modal_token_id: str = typer.Option("", help="Modal token id (scoped to this deploy only)"),
    modal_token_secret: str = typer.Option(
        "", help="Modal token secret (scoped to this deploy only)"
    ),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Deploy the GPU backend as a named instance, then print its base URL."""
    from clay.config import load_config
    from clay.deploy import DeploySpec, available_providers, get_deployer

    cfg = load_config(config_path)
    try:
        deployer = get_deployer(provider)
    except ValueError:
        console.print(
            f"[red]Unknown provider '{provider}'.[/] Available: "
            f"{', '.join(available_providers())}"
        )
        raise typer.Exit(1) from None

    creds = {}
    if modal_token_id:
        creds["token_id"] = modal_token_id
    if modal_token_secret:
        creds["token_secret"] = modal_token_secret

    spec = DeploySpec(
        name=name or cfg.deploy.name,
        gpu=gpu or cfg.deploy.gpu,
        model=model or cfg.providers.model,
        scaledown_window=scaledown or cfg.deploy.scaledown_window,
        region=region,
        credentials=creds,
    )
    console.print(f"[bold green]Clay[/] — deploying [cyan]{spec.name}[/] to {provider}…")
    result = deployer.deploy(spec)

    if result.ok:
        console.print(f"[bold green]✓ deployed[/] — {result.detail}")
        if result.endpoint_url:
            console.print(f"  base URL: [bold]{result.endpoint_url}[/]")
    elif result.status == "manual_required":
        console.print(f"[yellow]manual steps required[/] — {result.detail}")
    else:
        console.print(f"[red]deploy failed[/] — {result.detail}")
        raise typer.Exit(1)


@app.command()
def agent(
    message: str = typer.Option("", "--message", "-m", help="One-shot message (else REPL)"),
    model: str = typer.Option("", help="Model (default from config, e.g. kimi)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Chat with the Clay agent — kimi drives the tool registry."""
    from clay.agent import Agent, NvidiaClient
    from clay.config import load_config
    from clay.tools.context import ToolContext

    cfg = load_config(config_path)
    client = NvidiaClient(
        api_key=cfg.agent.api_key or None,
        base_url=cfg.agent.base_url,
        model=model or cfg.agent.model,
    )
    if not client.api_key:
        console.print("[red]No API key.[/] Set CLAY_NVIDIA_API_KEY or [agent].api_key.")
        raise typer.Exit(1)
    ctx = ToolContext.from_config(cfg)
    agent_ = Agent(client, ctx, max_iterations=cfg.agent.max_iterations)

    def _turn(text: str) -> None:
        result = agent_.run(text)
        for call in result["tool_calls"]:
            console.print(f"  [dim]· {call['tool']}({call['args']})[/]")
        console.print(f"[bold cyan]clay[/] {result['reply']}")

    if message:
        _turn(message)
        return
    console.print("[bold green]Clay agent[/] — type a message, Ctrl-D to exit.")
    history: list[dict] = []  # noqa: F841 — reserved for multi-turn history
    while True:
        try:
            text = console.input("[bold]you[/] ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye[/]")
            return
        if text.strip():
            _turn(text)


@app.command()
def mcp(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(0, help="Bind port (default from config)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Serve the Clay tools over MCP (streamable HTTP at /mcp)."""
    import os

    import clay.tools.all  # noqa: F401 — register tools so the count is accurate
    from clay.config import load_config
    from clay.mcp_server import run
    from clay.tools.registry import REGISTRY

    cfg = load_config(config_path)
    os.environ.setdefault("CLAY_CONFIG", config_path)
    resolved_port = port or cfg.mcp.port
    console.print(
        f"[bold green]Clay MCP[/] — http://{host}:{resolved_port}/mcp "
        f"({len(REGISTRY)} tools loaded)"
    )
    run(host=host, port=resolved_port)


@app.command()
def preview(
    mesh: str = typer.Argument(help="Path to a .glb asset"),
    output: str = typer.Option("", help="Output HTML path (default: alongside the mesh)"),
) -> None:
    """Build a self-contained interactive web viewer for a GLB (orbit/zoom, like Meshy)."""
    from pathlib import Path

    from clay.preview import make_viewer_html

    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)

    tris = ""
    try:
        import trimesh

        loaded = trimesh.load(src, force="mesh")
        tris = int(len(loaded.faces))
    except Exception:  # noqa: BLE001 — tri count is cosmetic
        pass

    out = make_viewer_html(
        src, output or None, title=src.stem, tris=tris, fmt=src.suffix.lstrip(".")
    )
    console.print(
        f"[bold green]✓[/] viewer → [bold]{out}[/] — open it in any browser to spin it."
    )


@app.command(name="export-fbx")
def export_fbx_cmd(
    mesh: str = typer.Argument(help="Input mesh (glb/obj/ply/stl/fbx)"),
    output: str = typer.Option("", help="Output .fbx path (default: alongside output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Convert a mesh to FBX via headless Blender (preserves meshes + UVs)."""
    from pathlib import Path

    from clay.blender import BlenderError, export_fbx
    from clay.config import load_config

    cfg = load_config(config_path)
    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    out = output or str(Path(cfg.output_dir) / f"{src.stem}.fbx")
    try:
        res = export_fbx(src, out, blender=cfg.blender.path or None)
    except BlenderError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(
        f"[bold green]✓[/] {out} — {res.get('faces')} faces, {res.get('mesh_count')} mesh(es)"
    )


@app.command()
def variations(
    image: str = typer.Option("", help="Input image (image → 3D)"),
    prompt: str = typer.Option("", help="Text prompt (text → 3D)"),
    count: int = typer.Option(4, help="Number of variations"),
    seed: int = typer.Option(0, help="Base seed (variations use seed, seed+1, …)"),
    fmt: str = typer.Option("glb", "--format", help="Output format"),
    output_dir: str = typer.Option("", help="Output directory (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Generate N seed-varied variations of a prop/livery. GPU-gated."""
    from clay.config import load_config
    from clay.variations import generate_variations

    if not image and not prompt:
        console.print("[red]Provide --image or --prompt.[/]")
        raise typer.Exit(1)
    cfg = load_config(config_path)
    mode = "image" if image else "text"
    try:
        res = generate_variations(
            cfg, mode=mode, prompt=prompt or None, image_path=image or None,
            count=count, seed=seed, fmt=fmt, out_dir=output_dir or cfg.output_dir,
        )
    except (RuntimeError, ValueError) as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(f"[bold green]✓[/] {res['count']} variations:")
    for v in res["variations"]:
        console.print(f"  seed {v['seed']} · {v['triangles']} tris · {v['path']}")


@app.command()
def texture(
    mesh: str = typer.Argument(help="Input mesh to (re)texture"),
    prompt: str = typer.Option("", help="Texture/livery prompt"),
    image: str = typer.Option("", help="Optional reference image"),
    resolution: int = typer.Option(1024, help="Texture resolution"),
    decals: bool = typer.Option(False, "--decals", help="Also emit transparent decal PNGs"),
    output_dir: str = typer.Option("", help="Output directory (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Paint / re-skin a mesh from a prompt/image onto its UVs. GPU-gated."""
    from pathlib import Path

    from clay.config import load_config
    from clay.texture import TextureAssetGenerator

    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    if not prompt and not image:
        console.print("[red]Provide --prompt or --image.[/]")
        raise typer.Exit(1)
    cfg = load_config(config_path)
    try:
        res = TextureAssetGenerator(cfg).texture(
            src, prompt=prompt or None, image_path=image or None,
            resolution=resolution, emit_decals=decals,
            out_dir=output_dir or cfg.output_dir,
        )
    except Exception as err:  # noqa: BLE001 — surface backend/gating errors cleanly
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(
        f"[bold green]✓[/] {res['manifest']} — maps: {', '.join(res['maps']) or 'none'}"
    )


@app.command()
def material(
    kind: str = typer.Option("generic", help="facade|road|ground|concrete|glass|generic"),
    prompt: str = typer.Option("", help="Material prompt, e.g. 'Nairobi CBD glass facade'"),
    image: str = typer.Option("", help="Optional reference image"),
    resolution: int = typer.Option(1024, help="Map resolution"),
    output_dir: str = typer.Option("", help="Output directory (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Generate a tiling PBR material set (+ manifest). GPU-gated."""
    from clay.config import load_config
    from clay.material import MaterialGenerator

    if not prompt and not image:
        console.print("[red]Provide --prompt or --image.[/]")
        raise typer.Exit(1)
    cfg = load_config(config_path)
    try:
        res = MaterialGenerator(cfg).generate(
            kind=kind, prompt=prompt or None, image_path=image or None,
            resolution=resolution, out_dir=output_dir or cfg.output_dir,
            stem=f"{kind}_material",
        )
    except Exception as err:  # noqa: BLE001 — surface backend/gating errors cleanly
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(f"[bold green]✓[/] {res['manifest']} — maps: {', '.join(res['maps']) or 'none'}")


@app.command()
def rig(
    mesh: str = typer.Argument(help="Input mesh"),
    rig_type: str = typer.Option("generic", "--type", help="humanoid|quadruped|vehicle|generic"),
    output: str = typer.Option("", help="Output FBX path (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Auto-rig a mesh per profile → skinned/parented FBX (heuristic). Via Blender."""
    from pathlib import Path

    from clay.blender import BlenderError
    from clay.blender import rig_asset as _rig
    from clay.config import load_config

    cfg = load_config(config_path)
    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    out = output or str(Path(cfg.output_dir) / f"{src.stem}_rigged.fbx")
    try:
        res = _rig(src, out, rig_type=rig_type, blender=cfg.blender.path or None)
    except BlenderError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    extra = f", {res['wheels']} wheels" if res.get("wheels") is not None else ""
    console.print(
        f"[bold green]✓[/] {out} — {res['rig_type']} rig, {res['bones']} bones{extra}"
    )


@app.command()
def bake(
    high: str = typer.Argument(help="High-poly mesh"),
    low: str = typer.Option("", help="Low-poly mesh (decimated from high if omitted)"),
    resolution: int = typer.Option(1024, help="Normal map resolution"),
    ao: bool = typer.Option(False, "--ao", help="Also bake an ambient-occlusion map"),
    output: str = typer.Option("", help="Output low mesh path (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Bake high→low tangent-space normal map (+ optional AO) via Blender."""
    from pathlib import Path

    from clay.blender import BlenderError
    from clay.blender import bake_normals as _bake
    from clay.config import load_config

    cfg = load_config(config_path)
    src = Path(high)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    out_dir = Path(cfg.output_dir)
    out_mesh = output or str(out_dir / f"{src.stem}_baked.glb")
    normal = str(out_dir / f"{src.stem}_normal.png")
    ao_map = str(out_dir / f"{src.stem}_ao.png") if ao else None
    try:
        res = _bake(
            src, out_mesh, normal, low_path=low or None,
            resolution=resolution, ao=ao, ao_map=ao_map,
            blender=cfg.blender.path or None,
        )
    except BlenderError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(
        f"[bold green]✓[/] {res['normal_map']} ({res['resolution']}²) · "
        f"low {res['low_faces']} faces → {out_mesh}"
    )


@app.command()
def retopo(
    mesh: str = typer.Argument(help="Input mesh"),
    target_faces: int = typer.Option(5000, help="Target face count for the quad remesh"),
    output: str = typer.Option("", help="Output path (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Retopologize a mesh to clean quad topology (Quadriflow) via Blender."""
    from pathlib import Path

    from clay.blender import BlenderError
    from clay.blender import retopo as _retopo
    from clay.config import load_config

    cfg = load_config(config_path)
    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    out = output or str(Path(cfg.output_dir) / f"{src.stem}_retopo.glb")
    try:
        res = _retopo(src, out, target_faces=target_faces, blender=cfg.blender.path or None)
    except BlenderError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(
        f"[bold green]✓[/] {out} — {res['faces']} faces, {res['quad_ratio']:.0%} quads"
    )


@app.command()
def lods(
    mesh: str = typer.Argument(help="Input mesh"),
    ratios: str = typer.Option("1.0,0.5,0.25,0.1", help="Comma-separated LOD ratios"),
    output_dir: str = typer.Option("", help="Output directory (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Build an LOD chain (decimated copies) for a mesh."""
    from pathlib import Path

    from clay.config import load_config
    from clay.lods import make_lods

    cfg = load_config(config_path)
    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    try:
        parsed = [float(r) for r in ratios.split(",") if r.strip()]
    except ValueError:
        console.print("[red]--ratios must be comma-separated numbers, e.g. 1.0,0.5,0.25[/]")
        raise typer.Exit(1) from None
    try:
        res = make_lods(src, ratios=parsed, out_dir=output_dir or cfg.output_dir)
    except ValueError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(f"[bold green]✓[/] {res['count']} LODs (base {res['base_faces']} faces):")
    for lod in res["lods"]:
        console.print(f"  LOD{lod['level']} · {lod['faces']} faces · {lod['path']}")


@app.command()
def collision(
    mesh: str = typer.Argument(help="Input mesh"),
    kind: str = typer.Option("convex", help="convex | box | simplified | compound"),
    max_hulls: int = typer.Option(32, help="Max hulls for compound (VHACD)"),
    output: str = typer.Option("", help="Output collider path (default: output_dir)"),
    config_path: str = typer.Option("config/config.toml", help="Path to config file"),
) -> None:
    """Build a physics collider (convex / box / simplified / compound) for a mesh."""
    from pathlib import Path

    from clay.collision import make_collision
    from clay.config import load_config

    cfg = load_config(config_path)
    src = Path(mesh)
    if not src.exists():
        console.print(f"[red]No mesh at {src}[/]")
        raise typer.Exit(1)
    try:
        res = make_collision(
            src, kind=kind, max_hulls=max_hulls,
            out_path=output or None, out_dir=Path(cfg.output_dir),
        )
    except ValueError as err:
        console.print(f"[red]{err}[/]")
        raise typer.Exit(1) from None
    console.print(
        f"[bold green]✓[/] {res['path']} — {res['kind']} collider, "
        f"{res['hulls']} hull(s), {res['faces']} faces"
    )


@app.command()
def providers() -> None:
    """List the available 3D model providers."""
    from clay.providers import available_providers, get_provider
    for name in available_providers():
        p = get_provider(name)
        console.print(
            f"[cyan]{name}[/] — {', '.join(p.modes)} · {p.license or 'n/a'} — {p.description}"
        )


if __name__ == "__main__":
    app()
