"""Set active camera."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._camera_light_utils import set_active_camera
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(camera_name: Optional[str] = None, camera_handle: Optional[int] = None) -> Dict[str, Any]:
    """Set the active/render camera."""
    return set_active_camera(get_runtime(), camera_name=camera_name, camera_handle=camera_handle)
