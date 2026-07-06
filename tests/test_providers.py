"""Tests for the model-provider registry."""

import pytest

from clay.providers import available_providers, get_provider


def test_builtin_providers_registered():
    assert set(available_providers()) >= {"trellis2", "hunyuan3d", "hi3dgen"}


def test_trellis2_is_the_mit_primary():
    p = get_provider("trellis2")
    assert p.license == "MIT"
    assert p.supports("image") and p.supports("text")


def test_hi3dgen_is_image_only():
    p = get_provider("hi3dgen")
    assert p.supports("image")
    assert not p.supports("text")


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        get_provider("nope")
