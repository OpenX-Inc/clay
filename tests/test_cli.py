"""CLI tests (Typer CliRunner)."""

from typer.testing import CliRunner

from clay.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "game-ready 3D" in result.output


def test_generate_requires_input():
    result = runner.invoke(app, ["generate"])
    assert result.exit_code == 1
    assert "Provide --image or --prompt" in result.output


def test_generate_dry_run_text(tmp_path):
    result = runner.invoke(app, ["generate", "--prompt", "a clay pot", "--dry-run"])
    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert "trellis2" in result.output  # default provider validated


def test_generate_rejects_text_for_image_only_provider(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text('[providers]\nmodel = "hi3dgen"\n')  # image-only
    result = runner.invoke(
        app, ["generate", "--prompt", "x", "--dry-run", "--config-path", str(cfg)]
    )
    assert result.exit_code == 1
    assert "does not support" in result.output
