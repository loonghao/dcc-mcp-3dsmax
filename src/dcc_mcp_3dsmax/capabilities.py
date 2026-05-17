"""3ds Max capabilities for the MCP server.

Defines the DCC-specific capabilities that are exposed via the MCP protocol.
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Core 3ds Max capabilities ──────────────────────────────────────────────

CAPABILITY_SCENE_INFO = "scene_info"
CAPABILITY_NODE_CREATION = "node_creation"
CAPABILITY_NODE_QUERY = "node_query"
CAPABILITY_MODIFIER_STACK = "modifier_stack"
CAPABILITY_MATERIAL = "material"
CAPABILITY_ANIMATION = "animation"
CAPABILITY_RENDERING = "rendering"
CAPABILITY_FILE_IO = "file_io"
CAPABILITY_LAYER = "layer"
CAPABILITY_SELECTION = "selection"


def get_3dsmax_capabilities() -> List[str]:
    """Return the list of core 3ds Max capabilities.

    Returns
    -------
    List[str]
        List of capability identifiers.
    """
    return [
        CAPABILITY_SCENE_INFO,
        CAPABILITY_NODE_CREATION,
        CAPABILITY_NODE_QUERY,
        CAPABILITY_MODIFIER_STACK,
        CAPABILITY_MATERIAL,
        CAPABILITY_ANIMATION,
        CAPABILITY_RENDERING,
        CAPABILITY_FILE_IO,
        CAPABILITY_LAYER,
        CAPABILITY_SELECTION,
    ]


def get_3dsmax_capabilities_dict() -> Dict[str, Any]:
    """Return 3ds Max capabilities as a structured dictionary.

    Returns
    -------
    Dict[str, Any]
        Dictionary with capability details.
    """
    return {
        "dcc_name": "3dsmax",
        "dcc_version": _get_version(),
        "capabilities": [
            {
                "name": CAPABILITY_SCENE_INFO,
                "description": "Query scene information (nodes, stats, units)",
            },
            {
                "name": CAPABILITY_NODE_CREATION,
                "description": "Create and modify scene nodes (geometry, lights, cameras)",
            },
            {
                "name": CAPABILITY_NODE_QUERY,
                "description": "Query node properties and hierarchy",
            },
            {
                "name": CAPABILITY_MODIFIER_STACK,
                "description": "Manage modifier stack on objects",
            },
            {
                "name": CAPABILITY_MATERIAL,
                "description": "Create and assign materials",
            },
            {
                "name": CAPABILITY_ANIMATION,
                "description": "Keyframe animation and timeline control",
            },
            {
                "name": CAPABILITY_RENDERING,
                "description": "Render setup and execution",
            },
            {
                "name": CAPABILITY_FILE_IO,
                "description": "File open, save, import, export",
            },
            {
                "name": CAPABILITY_LAYER,
                "description": "Layer management",
            },
            {
                "name": CAPABILITY_SELECTION,
                "description": "Node selection operations",
            },
        ],
    }


def _get_version() -> Optional[str]:
    """Get 3ds Max version if available."""
    try:
        from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string

        ver = get_3dsmax_version_string()
        return ver if ver != "unknown" else None
    except Exception:  # noqa: BLE001
        return None
