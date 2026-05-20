"""3ds Max in-process skill executor.

Core 0.17 routes embedded adapter skills through ``HostExecutionBridge``.
This module keeps the 3ds Max script convention local: skill scripts expose
``main(**params)`` and return plain dictionaries.
"""

from __future__ import annotations

import contextlib
import logging
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping

from dcc_mcp_core.skill import skill_exception

logger = logging.getLogger(__name__)

_busy_lock = threading.Lock()
_busy_count = 0


@contextlib.contextmanager
def _busy_scope() -> Iterator[None]:
    global _busy_count
    with _busy_lock:
        _busy_count += 1
    try:
        yield
    finally:
        with _busy_lock:
            _busy_count = max(0, _busy_count - 1)


def is_busy() -> bool:
    """Return ``True`` while a 3ds Max skill script is executing."""
    with _busy_lock:
        return _busy_count > 0


def run_skill_script(script_path: str, params: Mapping[str, Any]) -> Dict[str, Any]:
    """Load and execute a 3ds Max skill script in-process."""
    with _busy_scope():
        return _run_skill_script_untracked(script_path, dict(params))


def _run_skill_script_untracked(script_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    import importlib.util  # noqa: PLC0415
    import sys  # noqa: PLC0415
    import uuid  # noqa: PLC0415

    path = Path(script_path)
    if not path.is_file():
        return {"success": False, "message": "Skill script not found: {}".format(script_path)}

    mod_name = "_dcc_mcp_3dsmax_skill_{}".format(uuid.uuid4().hex)
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        return {"success": False, "message": "Cannot load skill script: {}".format(script_path)}

    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    try:
        try:
            spec.loader.exec_module(module)
        except SystemExit:
            return _normalise_result(getattr(module, "__mcp_result__", None))
        except Exception as exc:  # noqa: BLE001
            return skill_exception(exc, message="Error loading skill script: {}".format(script_path))

        try:
            main = getattr(module, "main", None)
            if main is None:
                return {
                    "success": False,
                    "message": "Skill script has no main() entry point: {}".format(script_path),
                }
            result = main(**params)
        except SystemExit:
            result = getattr(module, "__mcp_result__", None)
        except Exception as exc:  # noqa: BLE001
            return skill_exception(exc)
        return _normalise_result(result)
    finally:
        sys.modules.pop(mod_name, None)


def _normalise_result(result: Any) -> Dict[str, Any]:
    """Convert common legacy result shapes into dictionaries."""
    if result is None:
        return {"success": True, "message": "Script executed"}
    if isinstance(result, dict):
        return result
    return {"success": True, "message": str(result)}
