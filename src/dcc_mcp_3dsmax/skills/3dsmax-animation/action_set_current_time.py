"""Set current animation time."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._animation_utils import set_current_time
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(frame: float) -> Dict[str, Any]:
    """Set current timeline time."""
    return set_current_time(get_runtime(), frame)
