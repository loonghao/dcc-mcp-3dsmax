"""Inspect scene render statistics."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import render_success, scene_render_stats
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return scene statistics relevant to rendering."""
    return render_success("Retrieved scene render statistics", statistics=scene_render_stats(get_runtime()))
