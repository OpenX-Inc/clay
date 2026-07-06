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
