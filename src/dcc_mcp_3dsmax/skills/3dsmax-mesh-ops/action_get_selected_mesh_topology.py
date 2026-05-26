"""Summarize selected mesh topology."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._mesh_ops import selected_topology_summary
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return topology summaries for the current selection."""
    return selected_topology_summary(get_runtime())
