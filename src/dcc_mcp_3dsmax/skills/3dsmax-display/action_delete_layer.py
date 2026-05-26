"""Delete a display layer."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._display_utils import delete_layer
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name: str, delete_nodes: bool = False) -> Dict[str, Any]:
    """Delete a display layer."""
    return delete_layer(get_runtime(), name=name, delete_nodes=delete_nodes)
