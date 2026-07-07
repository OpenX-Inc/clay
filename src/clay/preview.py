"""Interactive preview — turn a GLB into a self-contained web viewer.

Meshy/Rodin's "interactive" viewer is just a WebGL ``<model-viewer>`` of a GLB.
Clay outputs GLB, so we can do the same. ``make_viewer_html`` embeds the mesh as
a base64 data URI so the resulting HTML is fully self-contained — open it in any
browser (no file hosting, no server) and orbit/zoom the asset with PBR lighting.
"""

from __future__ import annotations

import base64
from pathlib import Path

_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Clay — {title}</title>
<script type="module"
  src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
<style>
  html, body {{ margin: 0; height: 100%; background: #0f1115; color: #cfd3dc;
    font-family: ui-sans-serif, system-ui, sans-serif; }}
  header {{ padding: 12px 16px; font-size: 14px; letter-spacing: .02em; }}
  header b {{ color: #fff; }}
  model-viewer {{ width: 100%; height: calc(100% - 46px); background: #0f1115; }}
</style>
</head>
<body>
<header>🏺 <b>Clay</b> — {title} ·
  <span>{tris} tris · {fmt}</span> · drag to orbit, scroll to zoom</header>
<model-viewer
  src="data:model/gltf-binary;base64,{b64}"
  alt="{title}"
  camera-controls
  auto-rotate
  shadow-intensity="1"
  exposure="1.0"
  environment-image="neutral">
</model-viewer>
</body>
</html>
"""


def make_viewer_html(
    glb_path: str | Path,
    out_html: str | Path | None = None,
    *,
    title: str = "",
    tris: int | str = "",
    fmt: str = "glb",
) -> Path:
    """Write a self-contained ``<model-viewer>`` HTML for a GLB. Returns the path."""
    glb = Path(glb_path)
    data = base64.b64encode(glb.read_bytes()).decode()
    html = _TEMPLATE.format(
        title=title or glb.stem, tris=tris or "?", fmt=fmt, b64=data
    )
    out = Path(out_html) if out_html else glb.with_suffix(".html")
    out.write_text(html)
    return out
