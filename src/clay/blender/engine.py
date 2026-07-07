"""Headless Blender engine — Clay's mesh-processing backend.

Resolves a Blender binary (config path → ``CLAY_BLENDER`` → ``BLENDER_PATH`` →
``blender`` on PATH) and runs packaged headless scripts over a JSON in/out
contract. FBX export, rigging, retopology, and baking route through here; pure
geometry (decimation, LODs, convex hull) stays in trimesh. When Blender isn't
available, callers **fail visibly** — Clay never fakes output.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_SCRIPTS = Path(__file__).parent / "scripts"


class BlenderError(RuntimeError):
    """Raised when Blender is unavailable or a Blender script fails."""


def resolve_blender(explicit: str | None = None) -> str | None:
    """Find a Blender binary: explicit/config → CLAY_BLENDER → BLENDER_PATH → PATH."""
    for cand in (explicit, os.environ.get("CLAY_BLENDER"), os.environ.get("BLENDER_PATH")):
        if cand and Path(cand).exists():
            return cand
    return shutil.which("blender")


def available(explicit: str | None = None) -> bool:
    return resolve_blender(explicit) is not None


def require_blender(explicit: str | None = None) -> str:
    exe = resolve_blender(explicit)
    if not exe:
        raise BlenderError(
            "Blender not found. Set CLAY_BLENDER=/path/to/blender (or [blender].path in "
            "config, or put `blender` on PATH). Blender powers FBX export, rigging, "
            "retopology, and baking."
        )
    return exe


def run_script(
    script: str,
    payload: dict,
    *,
    blender: str | None = None,
    timeout: int = 900,
) -> dict:
    """Run a packaged headless Blender script with a JSON payload; return its result.

    The script receives two args after ``--``: an input-JSON path and an output-JSON
    path. It must write ``{"ok": true, ...}`` (or ``{"ok": false, "error": ...}``).
    """
    exe = require_blender(blender)
    script_path = _SCRIPTS / script
    if not script_path.exists():
        raise BlenderError(f"blender script missing: {script}")

    with tempfile.TemporaryDirectory(prefix="clay_bl_") as td:
        in_json = Path(td) / "in.json"
        out_json = Path(td) / "out.json"
        in_json.write_text(json.dumps(payload))
        cmd = [
            exe, "-b", "--factory-startup",
            "--python", str(script_path),
            "--", str(in_json), str(out_json),
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as err:
            raise BlenderError(f"blender timed out after {timeout}s") from err

        if not out_json.exists():
            tail = (proc.stderr or proc.stdout or "").strip()[-800:]
            raise BlenderError(
                f"blender script '{script}' produced no result (exit {proc.returncode}). {tail}"
            )
        result: dict = json.loads(out_json.read_text())
        if not result.get("ok", False):
            raise BlenderError(result.get("error", f"blender script '{script}' failed"))
        return result
