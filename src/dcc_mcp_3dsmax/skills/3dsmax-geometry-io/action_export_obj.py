"""Export OBJ geometry from 3ds Max."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._geometry_io import export_geometry_file, resolve_export_file
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(output_path: str, selected_only: bool = False, overwrite: bool = False) -> Dict[str, Any]:
    """Export selected nodes or the whole scene to OBJ."""
    path, error = resolve_export_file(output_path, expected_extension=".obj", overwrite=overwrite)
    if error is not None:
        return error
    return export_geometry_file(get_runtime(), path, format_name="obj", selected_only=selected_only)
