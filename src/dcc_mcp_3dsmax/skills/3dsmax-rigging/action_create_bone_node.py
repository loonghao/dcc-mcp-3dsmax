"""Create a bone node."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._rigging_utils import create_bone_node, rig_error, rig_success
from dcc_mcp_3dsmax._scene_utils import node_identity
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(name: str, start: list, end: list, up_axis: Optional[list] = None) -> Dict[str, Any]:
    """Create one bone primitive."""
    bone, warnings = create_bone_node(get_runtime(), name=name, start=start, end=end, up_axis=up_axis)
    if bone is None:
        return rig_error("Could not create bone node", warnings=warnings, changed_node_count=0)
    return rig_success("Created bone node", bone=node_identity(bone), changed_node_count=1, warnings=warnings)
