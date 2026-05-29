"""Set render frame ranges."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import set_frame_range
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(start_frame: int, end_frame: int) -> Dict[str, Any]:
    """Set animation/render frame range."""
    return set_frame_range(get_runtime(), start_frame, end_frame)
