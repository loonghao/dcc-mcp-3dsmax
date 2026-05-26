"""Set render resolution."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import set_resolution
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(width: int, height: int) -> Dict[str, Any]:
    """Set render resolution."""
    return set_resolution(get_runtime(), width, height)
