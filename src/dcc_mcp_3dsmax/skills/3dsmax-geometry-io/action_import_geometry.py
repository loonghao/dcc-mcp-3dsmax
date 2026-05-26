"""Import supported geometry files into 3ds Max."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._geometry_io import (
    SUPPORTED_IMPORT_FORMATS,
    fbx_option_error,
    import_geometry_file,
    resolve_import_file,
)
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(file_path: str, format: Optional[str] = None, mode: str = "merge") -> Dict[str, Any]:  # noqa: A002
    """Import a supported geometry file using extension-based dispatch."""
    path, error = resolve_import_file(file_path, expected_format=format)
    if error is not None:
        return error
    format_name = SUPPORTED_IMPORT_FORMATS[path.suffix.lower()]
    fbx_options = {}
    if format_name == "fbx":
        option_error = fbx_option_error(mode=mode)
        if option_error is not None:
            return option_error
        fbx_options["mode"] = mode
    return import_geometry_file(get_runtime(), path, format_name=format_name, fbx_options=fbx_options)
