"""Set light properties."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._camera_light_utils import set_light_properties
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    light_name: Optional[str] = None,
    light_handle: Optional[int] = None,
    enabled: Optional[bool] = None,
    intensity: Optional[float] = None,
    color: Optional[list] = None,
    shadows: Optional[bool] = None,
) -> Dict[str, Any]:
    """Set common light properties."""
    return set_light_properties(
        get_runtime(),
        light_name=light_name,
        light_handle=light_handle,
        enabled=enabled,
        intensity=intensity,
        color=color,
        shadows=shadows,
    )
