"""Create a path helper."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._rigging_utils import create_path_helper
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name: str, points: list, closed: bool = False) -> Dict[str, Any]:
    """Create a curve or path helper."""
    return create_path_helper(get_runtime(), name=name, points=points, closed=closed)
