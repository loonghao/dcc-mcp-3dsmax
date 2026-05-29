"""List scene materials."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._material_utils import iter_scene_materials, material_identity, material_success
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """List known scene materials."""
    rt = get_runtime()
    materials = [material_identity(material) for material in iter_scene_materials(rt)]
    return material_success("Listed scene materials", materials=materials, count=len(materials))
