"""Capture the active viewport."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._render_utils import IMAGE_EXTENSIONS, capture_viewport, validate_output_path
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(output_path: str, overwrite: bool = False) -> Dict[str, Any]:
    """Capture the active viewport to an image file."""
    path, error = validate_output_path(output_path, allowed_extensions=IMAGE_EXTENSIONS, overwrite=overwrite)
    if error is not None:
        return error
    return capture_viewport(get_runtime(), path)
