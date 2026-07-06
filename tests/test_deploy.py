"""Tests for the deployer registry, Modal deployer, and honest cloud scaffolds."""

from __future__ import annotations

import os
import subprocess

import pytest

from clay.deploy import DeploySpec, available_providers, get_deployer
from clay.deploy.base import DeployResult
from clay.deploy.modal_deploy import ModalDeployer


def test_registry_has_providers():
    assert set(available_providers()) >= {"modal", "aws", "gcp"}


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_deployer("nope")


def test_modal_missing_cli_fails_honestly(monkeypatch):
    monkeypatch.setattr("clay.deploy.modal_deploy.shutil.which", lambda _: None)
    result = ModalDeployer().deploy(DeploySpec())
    assert result.status == "failed"
    assert "modal CLI not found" in result.detail
    assert not result.ok


def test_modal_token_scoped_to_subprocess(monkeypatch, tmp_path):
    """Per-invocation Modal token must go into the subprocess env, not os.environ."""
    server = tmp_path / "modal_server.py"
    server.write_text("# stub")
    captured = {}

    def fake_run(cmd, env=None, **kwargs):
        captured["env"] = env
        return subprocess.CompletedProcess(
            cmd, 0, stdout="Deployed https://ws--clay-gpu-backend.modal.run", stderr=""
        )

    monkeypatch.setattr("clay.deploy.modal_deploy.shutil.which", lambda _: "/usr/bin/modal")
    monkeypatch.setattr(ModalDeployer, "_server_path", lambda self: server)
    monkeypatch.setattr("clay.deploy.modal_deploy.subprocess.run", fake_run)
    monkeypatch.delenv("MODAL_TOKEN_ID", raising=False)

    spec = DeploySpec(credentials={"token_id": "tid", "token_secret": "tsec"})
    result = ModalDeployer().deploy(spec)

    assert result.ok
    assert result.endpoint_url == "https://ws--clay-gpu-backend.modal.run"
    assert captured["env"]["MODAL_TOKEN_ID"] == "tid"
    assert captured["env"]["MODAL_TOKEN_SECRET"] == "tsec"
    # The ambient process env must remain untouched.
    assert "MODAL_TOKEN_ID" not in os.environ


def test_modal_passes_spec_as_env(monkeypatch, tmp_path):
    server = tmp_path / "modal_server.py"
    server.write_text("# stub")
    captured = {}

    def fake_run(cmd, env=None, **kwargs):
        captured["env"] = env
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("clay.deploy.modal_deploy.shutil.which", lambda _: "/usr/bin/modal")
    monkeypatch.setattr(ModalDeployer, "_server_path", lambda self: server)
    monkeypatch.setattr("clay.deploy.modal_deploy.subprocess.run", fake_run)

    ModalDeployer().deploy(DeploySpec(name="clay-a100", gpu="H100", model="trellis2"))
    assert captured["env"]["CLAY_GPU_APP_NAME"] == "clay-a100"
    assert captured["env"]["CLAY_GPU_TYPE"] == "H100"
    assert captured["env"]["CLAY_MODEL"] == "trellis2"


def test_modal_deploy_failure_surfaces_detail(monkeypatch, tmp_path):
    server = tmp_path / "modal_server.py"
    server.write_text("# stub")

    def fake_run(cmd, env=None, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom: quota exceeded")

    monkeypatch.setattr("clay.deploy.modal_deploy.shutil.which", lambda _: "/usr/bin/modal")
    monkeypatch.setattr(ModalDeployer, "_server_path", lambda self: server)
    monkeypatch.setattr("clay.deploy.modal_deploy.subprocess.run", fake_run)

    result = ModalDeployer().deploy(DeploySpec())
    assert result.status == "failed"
    assert "quota exceeded" in result.detail


@pytest.mark.parametrize("provider", ["aws", "gcp"])
def test_cloud_scaffolds_are_honest(provider):
    result = get_deployer(provider).deploy(DeploySpec())
    assert isinstance(result, DeployResult)
    assert result.status == "manual_required"
    assert not result.ok
    assert "not automated yet" in result.detail
