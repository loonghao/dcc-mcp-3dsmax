"""List 3ds Max macro/action entries when the host exposes them."""

from __future__ import annotations

from typing import Any, Dict, List

from dcc_mcp_3dsmax._scene_utils import json_safe
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(limit: int = 100) -> Dict[str, Any]:
    """Return macro/action entries from ``pymxs.runtime.macros`` when available."""
    rt = get_runtime()
    safe_limit = max(1, min(int(limit or 100), 500))
    macros = getattr(rt, "macros", None)
    if macros is None:
        return {
            "success": True,
            "message": "Runtime does not expose macros",
            "data": {"macros": [], "count": 0, "available": False},
        }

    try:
        raw_entries = macros.list()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": "Could not list macros",
            "data": {"error": str(exc), "available": True},
        }

    raw_list: List[Any] = list(raw_entries)
    entries = raw_list[:safe_limit]
    return {
        "success": True,
        "message": "Listed macros",
        "data": {
            "macros": [json_safe(entry) for entry in entries],
            "count": len(entries),
            "available": True,
            "truncated": len(raw_list) > safe_limit,
        },
    }
