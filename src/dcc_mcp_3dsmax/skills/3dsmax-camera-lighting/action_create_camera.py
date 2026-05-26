"""Create a camera."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._camera_light_utils import create_camera
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    name: str,
    camera_type: str = "target",
    position: Optional[list] = None,
    target_position: Optional[list] = None,
    focal_length: Optional[float] = None,
) -> Dict[str, Any]:
    """Create a camera node."""
    return create_camera(
        get_runtime(),
        name=name,
        camera_type=camera_type,
        position=position,
        target_position=target_position,
        focal_length=focal_length,
    )
