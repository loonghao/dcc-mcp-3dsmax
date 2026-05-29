"""Get animation time settings."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._animation_utils import anim_success, time_settings
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return timeline settings."""
    return anim_success("Retrieved time settings", settings=time_settings(get_runtime()))
