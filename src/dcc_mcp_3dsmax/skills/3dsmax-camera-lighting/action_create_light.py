"""Create a light."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._camera_light_utils import create_light
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    name: str,
    light_type: str = "omni",
    position: Optional[list] = None,
    target_position: Optional[list] = None,
    intensity: Optional[float] = None,
    color: Optional[list] = None,
    shadows: Optional[bool] = None,
) -> Dict[str, Any]:
    """Create a light node."""
    return create_light(
        get_runtime(),
        name=name,
        light_type=light_type,
        position=position,
        target_position=target_position,
        intensity=intensity,
        color=color,
        shadows=shadows,
    )
