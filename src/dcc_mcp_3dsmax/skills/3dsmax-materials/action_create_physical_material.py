"""Create Physical materials."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._material_utils import create_material, material_identity, material_success, set_material_attribute
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    name: str,
    base_color: Optional[list] = None,
    roughness: Optional[float] = None,
    metalness: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a Physical material where available."""
    material = create_material(get_runtime(), name=name, kind="physical", color=base_color)
    warnings = []
    if roughness is not None:
        warnings.extend(set_material_attribute(material, "roughness", roughness))
    if metalness is not None:
        warnings.extend(set_material_attribute(material, "metalness", metalness))
    return material_success("Created physical material", material=material_identity(material), warnings=warnings)
