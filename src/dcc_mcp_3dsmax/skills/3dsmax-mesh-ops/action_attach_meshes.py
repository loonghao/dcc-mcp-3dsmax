"""Attach mesh sources into one target."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import (
    attach_sources,
    changed_summary,
    mesh_error,
    mesh_success,
    resolve_one,
    resolve_targets,
)
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    target_name: Optional[str] = None,
    target_handle: Optional[int] = None,
    source_names: Optional[list] = None,
    source_handles: Optional[list] = None,
) -> Dict[str, Any]:
    """Attach source meshes into one target mesh."""
    rt = get_runtime()
    target_result, target = resolve_one(rt, node_name=target_name, handle=target_handle)
    if target is None:
        return target_result
    sources = resolve_targets(rt, node_names=source_names, handles=source_handles)
    if not sources.get("success"):
        return sources
    if target in sources["objects"]:
        return mesh_error("Target mesh cannot also be a source", target=target_result.get("node"))
    warnings = attach_sources(rt, target, sources["objects"])
    return mesh_success(
        "Attached meshes",
        target=changed_summary(rt, [target])[0],
        sources=changed_summary(rt, sources["objects"]),
        warnings=warnings,
    )
