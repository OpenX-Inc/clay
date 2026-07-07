"""Import side-effect module: registers every Clay tool into the registry."""

from __future__ import annotations

import clay.tools.asset_tools  # noqa: F401 — registers the asset tools
import clay.tools.blender_tools  # noqa: F401 — registers the Blender-backed tools
import clay.tools.material_tools  # noqa: F401 — registers material/texture tools
import clay.tools.mesh_tools  # noqa: F401 — registers the CPU geometry tools
