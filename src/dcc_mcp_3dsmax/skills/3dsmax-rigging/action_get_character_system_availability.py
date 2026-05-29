"""Check optional character-system availability."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._rigging_utils import character_system_availability
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Check whether optional character rig helpers are available."""
    return character_system_availability(get_runtime())
