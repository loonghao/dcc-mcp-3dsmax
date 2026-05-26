"""Create a helper node."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._rigging_utils import create_helper_node
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name: str, helper_type: str = "point", size: float = 10.0, position: Optional[list] = None) -> Dict[str, Any]:
    """Create a host-native helper node."""
    return create_helper_node(get_runtime(), name=name, helper_type=helper_type, size=size, position=position)
