"""Export FBX geometry from 3ds Max."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._geometry_io import export_geometry_file, fbx_option_error, resolve_export_file
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    output_path: str,
    selected_only: bool = False,
    overwrite: bool = False,
    units: Optional[str] = None,
    up_axis: Optional[str] = None,
    include_animation: bool = True,
    embed_textures: bool = False,
    ascii: bool = False,  # noqa: A002
) -> Dict[str, Any]:
    """Export selected nodes or the whole scene to FBX."""
    path, error = resolve_export_file(output_path, expected_extension=".fbx", overwrite=overwrite)
    if error is not None:
        return error
    option_error = fbx_option_error(units=units, up_axis=up_axis)
    if option_error is not None:
        return option_error
    return export_geometry_file(
        get_runtime(),
        path,
        format_name="fbx",
        selected_only=selected_only,
        fbx_options={
            "units": units,
            "up_axis": up_axis,
            "include_animation": include_animation,
            "embed_textures": embed_textures,
            "ascii": ascii,
        },
    )
