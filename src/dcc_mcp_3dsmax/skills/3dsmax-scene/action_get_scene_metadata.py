"""Get 3ds Max session and scene metadata."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import iter_scene_nodes
from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main() -> Dict[str, Any]:
    """Return session and scene metadata."""
    rt = get_runtime()
    scene_name = str(getattr(rt, "maxFileName", "") or "Untitled")
    scene_path = str(getattr(rt, "maxFilePath", "") or "")
    units = "unknown"
    try:
        units = str(rt.units.SystemType()) if hasattr(rt, "units") else "unknown"
    except Exception:  # noqa: BLE001
        units = "unknown"
    nodes = iter_scene_nodes(rt)
    return {
        "success": True,
        "message": "Retrieved scene metadata",
        "data": {
            "scene_name": scene_name,
            "scene_path": scene_path,
            "node_count": len(nodes),
            "units": units,
            "3dsmax_version": get_3dsmax_version_string(),
        },
    }
