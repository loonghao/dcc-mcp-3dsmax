"""Inspect render settings."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import render_settings, render_success
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return common render settings."""
    return render_success("Retrieved render settings", settings=render_settings(get_runtime()))
