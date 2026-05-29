"""Evaluate a small Python expression in 3ds Max."""

from __future__ import annotations

import traceback
from typing import Any, Dict

from dcc_mcp_3dsmax._scene_utils import json_safe
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(expression: str) -> Dict[str, Any]:
    """Evaluate one Python expression with ``pymxs``, ``rt``, and ``runtime`` in scope."""
    if not isinstance(expression, str) or not expression.strip():
        return max_error("expression must be a non-empty Python expression")

    import pymxs  # noqa: PLC0415

    rt = get_runtime()
    globals_dict = {"pymxs": pymxs, "rt": rt, "runtime": rt}
    try:
        result = eval(compile(expression, "<dcc_mcp_3dsmax_run_python_check>", "eval"), globals_dict, {})  # noqa: S307
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "message": "Python check failed",
            "data": {
                "error": str(exc),
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        }
    return {"success": True, "message": "Python check completed", "data": {"result": json_safe(result)}}
