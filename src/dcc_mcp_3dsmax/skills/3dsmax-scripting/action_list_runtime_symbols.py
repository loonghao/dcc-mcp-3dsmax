"""List available pymxs runtime symbols."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dcc_mcp_3dsmax._scene_utils import runtime_symbol_info
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(prefix: Optional[str] = None, include_private: bool = False, limit: int = 100) -> Dict[str, Any]:
    """List runtime symbols with shallow metadata."""
    rt = get_runtime()
    prefix_text = prefix or ""
    safe_limit = max(1, min(int(limit or 100), 500))
    names: List[str] = []
    for name in dir(rt):
        if not include_private and name.startswith("_"):
            continue
        if prefix_text and not name.lower().startswith(prefix_text.lower()):
            continue
        names.append(name)

    entries = [runtime_symbol_info(rt, name) for name in sorted(names)[:safe_limit]]
    return {
        "success": True,
        "message": "Listed runtime symbols",
        "data": {
            "symbols": entries,
            "count": len(entries),
            "truncated": len(names) > safe_limit,
        },
    }
