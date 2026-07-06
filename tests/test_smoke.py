"""Smoke test: the package imports and exposes a version."""

import clay


def test_version():
    assert isinstance(clay.__version__, str)
    assert clay.__version__.count(".") >= 2
