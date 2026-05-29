"""Execute Python code in 3ds Max."""

from __future__ import annotations

import contextlib
import io
from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._env import resolve_execute_python_disabled
from dcc_mcp_3dsmax._scene_utils import json_safe
from dcc_mcp_3dsmax.api import get_runtime, max_error, with_max


@with_max
def main(code: str, expression: Optional[str] = None) -> Dict[str, Any]:
    """Execute Python code with ``pymxs``, ``rt``, and ``runtime`` in scope."""
    if resolve_execute_python_disabled():
        return max_error("execute_python is disabled by environment configuration")
    if not isinstance(code, str) or not code.strip():
        return max_error("code must be a non-empty Python string")
    if expression is not None and (not isinstance(expression, str) or not expression.strip()):
        return max_error("expression must be a non-empty Python expression when provided")

    import pymxs  # noqa: PLC0415

    rt = get_runtime()
    stdout = io.StringIO()
    globals_dict: Dict[str, Any] = {
        "pymxs": pymxs,
        "rt": rt,
        "runtime": rt,
    }
    locals_dict: Dict[str, Any] = {}

    with contextlib.redirect_stdout(stdout):
        exec(compile(code, "<dcc_mcp_3dsmax_execute_python>", "exec"), globals_dict, locals_dict)  # noqa: S102
        if expression is not None:
            result = eval(  # noqa: S307
                compile(expression, "<dcc_mcp_3dsmax_execute_python_expression>", "eval"),
                globals_dict,
                locals_dict,
            )
        else:
            result = locals_dict.get("result")

    return {
        "success": True,
        "message": "Executed Python code",
        "data": {
            "result": json_safe(result),
            "stdout": stdout.getvalue(),
        },
    }
