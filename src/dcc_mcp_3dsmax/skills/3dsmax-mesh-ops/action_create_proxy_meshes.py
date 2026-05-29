"""Create proxy mesh duplicates."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._mesh_ops import create_proxy, mesh_success, resolve_targets, topology_summary
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(
    node_names: Optional[list] = None,
    handles: Optional[list] = None,
    use_selection: bool = False,
    reduction_percent: float = 50,
    name_suffix: str = "_proxy",
) -> Dict[str, Any]:
    """Create reduced proxy meshes from explicit targets."""
    rt = get_runtime()
    targets = resolve_targets(rt, node_names=node_names, handles=handles, use_selection=use_selection)
    if not targets.get("success"):
        return targets
    proxies = []
    warnings = []
    safe_percent = max(1.0, min(float(reduction_percent), 100.0))
    for node in targets["objects"]:
        proxy, node_warnings = create_proxy(rt, node, reduction_percent=safe_percent, name_suffix=name_suffix)
        warnings.extend(node_warnings)
        if proxy is not None:
            proxies.append(topology_summary(rt, proxy))
    return mesh_success("Created proxy meshes", proxies=proxies, count=len(proxies), warnings=warnings)
