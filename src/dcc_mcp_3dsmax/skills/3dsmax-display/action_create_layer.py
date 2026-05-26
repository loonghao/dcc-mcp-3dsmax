"""Create a display layer."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._display_utils import create_layer
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name: str) -> Dict[str, Any]:
    """Create a display layer."""
    return create_layer(get_runtime(), name=name)
