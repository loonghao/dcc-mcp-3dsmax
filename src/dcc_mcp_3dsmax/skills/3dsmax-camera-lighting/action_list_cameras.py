"""List cameras."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._camera_light_utils import list_cameras
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """List camera nodes."""
    return list_cameras(get_runtime())
