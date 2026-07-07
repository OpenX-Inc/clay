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
