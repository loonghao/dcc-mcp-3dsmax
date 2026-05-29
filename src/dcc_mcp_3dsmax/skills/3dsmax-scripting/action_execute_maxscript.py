"""Execute MaxScript in 3ds Max."""

from __future__ import annotations

from typing import Any, Dict

from dcc_mcp_3dsmax._env import resolve_execute_maxscript_disabled
from dcc_mcp_3dsmax._scene_utils import json_safe
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(script: str) -> Dict[str, Any]:
    """Execute a MaxScript string through pymxs.runtime.execute."""
    if resolve_execute_maxscript_disabled():
        return max_error("execute_maxscript is disabled by environment configuration")
    if not isinstance(script, str) or not script.strip():
        return max_error("script must be a non-empty MaxScript string")

    rt = get_runtime()
    result = rt.execute(script)
    return {
        "success": True,
        "message": "Executed MaxScript",
        "data": {
            "result": json_safe(result),
            "result_text": str(result) if result is not None else None,
        },
    }
