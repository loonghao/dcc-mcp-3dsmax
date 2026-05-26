"""Execute explicit MaxScript in 3ds Max."""

from __future__ import annotations

import traceback
from typing import Any, Dict

from dcc_mcp_3dsmax._env import resolve_execute_maxscript_disabled
from dcc_mcp_3dsmax._scene_utils import json_safe
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(script: str, confirm_execution: bool) -> Dict[str, Any]:
    """Execute a MaxScript string through ``pymxs.runtime.execute``."""
    if resolve_execute_maxscript_disabled():
        return max_error("execute_maxscript is disabled by environment configuration")
    if confirm_execution is not True:
        return max_error("confirm_execution must be true for arbitrary MaxScript execution")
    if not isinstance(script, str) or not script.strip():
        return max_error("script must be a non-empty MaxScript string")

    rt = get_runtime()
    try:
        result = rt.execute(script)
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": "MaxScript execution failed",
            "data": {
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        }
    return {
        "success": True,
        "message": "Executed MaxScript",
        "data": {
            "result": json_safe(result),
            "result_text": str(result) if result is not None else None,
        },
    }
