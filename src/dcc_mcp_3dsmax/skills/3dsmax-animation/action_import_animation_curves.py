"""Import animation curves."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._animation_utils import import_curve_data
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(curve_data: Dict[str, Any]) -> Dict[str, Any]:
    """Import simple curve data."""
    return import_curve_data(get_runtime(), curve_data)
