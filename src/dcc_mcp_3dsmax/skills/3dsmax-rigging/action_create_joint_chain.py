"""Create a simple joint chain."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._rigging_utils import create_joint_chain
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(base_name: str, positions: list) -> Dict[str, Any]:
    """Create a parented bone chain from point positions."""
    return create_joint_chain(get_runtime(), base_name=base_name, positions=positions)
