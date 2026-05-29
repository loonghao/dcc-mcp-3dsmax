"""Set render quality presets."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import set_quality_preset
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(preset: str) -> Dict[str, Any]:
    """Set a render quality preset."""
    return set_quality_preset(get_runtime(), preset)
