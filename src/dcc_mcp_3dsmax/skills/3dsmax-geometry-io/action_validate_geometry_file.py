"""Validate geometry files for import."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._geometry_io import SUPPORTED_IMPORT_FORMATS, file_info, io_success, resolve_import_file


def main(file_path: str, expected_format: Optional[str] = None) -> Dict[str, Any]:
    """Validate that a geometry file exists and has a supported import format."""
    path, error = resolve_import_file(file_path, expected_format=expected_format)
    if error is not None:
        return error
    return io_success(
        "Geometry file is valid",
        file=file_info(path),
        format=SUPPORTED_IMPORT_FORMATS[path.suffix.lower()],
        supported_formats=sorted(set(SUPPORTED_IMPORT_FORMATS.values())),
    )
