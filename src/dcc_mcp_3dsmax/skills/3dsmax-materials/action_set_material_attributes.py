"""Set material attributes."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._material_utils import (
    find_material,
    material_error,
    material_identity,
    material_success,
    set_material_attribute,
)
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(material_name: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Set common material attributes."""
    material = find_material(get_runtime(), material_name)
    if material is None:
        return material_error("Material not found", material_name=material_name)
    warnings = []
    for attr, value in attributes.items():
        warnings.extend(set_material_attribute(material, attr, value))
    return material_success("Updated material attributes", material=material_identity(material), warnings=warnings)
