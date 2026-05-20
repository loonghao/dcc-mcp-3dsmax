"""Structured dispatcher used by the 3ds Max sidecar bridge.

The bridge accepts JSON payloads rather than arbitrary Python source.  A
payload may identify either a registered action name or an explicit script
path supplied by an external sidecar process:

``{"action": "3dsmax-modeling__create_box", "args": {"width": 10}}``
``{"script_path": ".../action_create_box.py", "args": {"width": 10}}``
"""

from __future__ import annotations

import json
import logging
import traceback
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from dcc_mcp_3dsmax import _executor

_BUILTIN_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"

logger = logging.getLogger(__name__)


def dispatch(payload: Mapping[str, Any] | str) -> str:
    """Dispatch a sidecar payload against the currently running server."""
    return dispatch_payload(payload)


def dispatch_payload(
    payload: Mapping[str, Any] | str,
    *,
    server_lookup: Optional[Callable[[], Any]] = None,
) -> str:
    """Dispatch *payload* and return a single-line JSON response."""
    lookup = server_lookup or _default_server_lookup
    try:
        return _dispatch_inner(payload, server_lookup=lookup)
    except Exception as exc:  # noqa: BLE001
        logger.exception("3ds Max sidecar dispatch failed unexpectedly")
        return _json_response(
            _envelope(
                success=False,
                error="dispatch-failed",
                message="unexpected dispatcher error: {}".format(exc),
                traceback=traceback.format_exc(),
                request_id=_safe_request_id(payload),
            )
        )


def _dispatch_inner(
    payload: Mapping[str, Any] | str,
    *,
    server_lookup: Callable[[], Any],
) -> str:
    parsed = _coerce_payload(payload)
    if parsed is None:
        return _json_response(
            _envelope(
                success=False,
                error="payload-malformed",
                message="payload must be a JSON object",
                request_id="",
            )
        )

    args = parsed.get("args") or {}
    if not isinstance(args, Mapping):
        return _json_response(
            _envelope(
                success=False,
                error="payload-malformed",
                message="payload.args must be a JSON object",
                request_id=str(parsed.get("request_id") or ""),
            )
        )

    action_name = parsed.get("action")
    if action_name is not None and not isinstance(action_name, str):
        return _json_response(
            _envelope(
                success=False,
                error="payload-malformed",
                message="payload.action must be a string",
                request_id=str(parsed.get("request_id") or ""),
            )
        )

    script_path = _script_path_from_payload(parsed)
    if script_path is None and action_name:
        script_path = _resolve_script_path(server_lookup(), action_name)
    if script_path is None and action_name:
        script_path = _resolve_bundled_script_path(action_name)

    if script_path is None:
        return _json_response(
            _envelope(
                success=False,
                error="unknown-action",
                message="no script_path provided and action {!r} is not registered".format(action_name),
                request_id=str(parsed.get("request_id") or ""),
                action=action_name,
            )
        )

    result = _executor.run_skill_script(str(script_path), dict(args))
    if not isinstance(result, Mapping):
        result = {"success": True, "message": str(result)}

    body = dict(result)
    body.setdefault("request_id", str(parsed.get("request_id") or ""))
    if action_name:
        body.setdefault("action", action_name)
    return _json_response(body)


def _default_server_lookup() -> Any:
    from dcc_mcp_3dsmax import get_server  # noqa: PLC0415

    return get_server()


def _coerce_payload(payload: Mapping[str, Any] | str) -> Optional[Mapping[str, Any]]:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, Mapping) else None


def _script_path_from_payload(payload: Mapping[str, Any]) -> Optional[Path]:
    raw = payload.get("script_path") or payload.get("source_file")
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw)
    return path if path.is_file() else None


def _resolve_script_path(server: Any, action_name: str) -> Optional[Path]:
    if server is None:
        return None

    try:
        actions = server.list_actions()
    except Exception as exc:  # noqa: BLE001
        logger.debug("list_actions failed while resolving %s: %s", action_name, exc)
        return None

    for action in actions:
        names = {
            _get_value(action, "name"),
            _get_value(action, "action"),
            _get_value(action, "action_name"),
            _get_value(action, "tool_name"),
        }
        if action_name not in names:
            continue
        source = (
            _get_value(action, "source_file")
            or _get_value(action, "script_path")
            or _get_value(action, "path")
        )
        if isinstance(source, str):
            path = Path(source)
            if path.is_file():
                return path
    return None


def _resolve_bundled_script_path(action_name: str) -> Optional[Path]:
    normalised = action_name.replace(".", "__")
    skill_name = ""
    tool_name = normalised
    if "__" in normalised:
        skill_name, tool_name = normalised.split("__", 1)

    candidates = []
    if skill_name:
        candidates.append(_BUILTIN_SKILLS_DIR / skill_name / "action_{}.py".format(tool_name))
    candidates.extend(_BUILTIN_SKILLS_DIR.glob("*/action_{}.py".format(tool_name)))
    candidates.extend(_BUILTIN_SKILLS_DIR.glob("*/{}.py".format(tool_name)))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _get_value(obj: Any, name: str) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name)
    return getattr(obj, name, None)


def _safe_request_id(payload: Any) -> str:
    parsed = _coerce_payload(payload)
    if parsed is None:
        return ""
    return str(parsed.get("request_id") or "")


def _envelope(**kwargs: Any) -> dict:
    return dict(kwargs)


def _json_response(body: Mapping[str, Any]) -> str:
    return json.dumps(dict(body), ensure_ascii=False, separators=(",", ":"))
