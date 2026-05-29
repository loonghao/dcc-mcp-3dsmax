"""Inspect one material."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._material_utils import find_material, material_error, material_identity, material_success
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(material_name: str) -> Dict[str, Any]:
    """Inspect common material parameters."""
    material = find_material(get_runtime(), material_name)
    if material is None:
        return material_error("Material not found", material_name=material_name)
    return material_success("Inspected material", material=material_identity(material))
