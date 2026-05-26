"""Small helpers shared by 3ds Max skill scripts."""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional


def json_safe(value: Any, depth: int = 0) -> Any:
    """Best-effort conversion of pymxs/Python values into JSON-safe data."""
    if depth > 4:
        return str(value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): json_safe(item, depth + 1) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [json_safe(item, depth + 1) for item in value]

    identity = node_identity(value)
    if identity["node_name"] or identity["object_id"] is not None:
        return identity
    return str(value)


def node_identity(node: Any) -> Dict[str, Any]:
    """Return a JSON-safe identity payload for a 3ds Max node-like object."""
    handle = getattr(node, "handle", None)
    try:
        object_id = int(handle) if handle is not None else None
    except (TypeError, ValueError):
        object_id = None
    payload = {
        "node_name": str(getattr(node, "name", "")),
        "object_id": object_id,
    }
    return payload


def iter_scene_nodes(runtime: Any) -> List[Any]:
    """Return scene nodes from ``runtime.objects`` as a plain list."""
    try:
        return list(runtime.objects)
    except Exception:  # noqa: BLE001
        return []


def resolve_node(runtime: Any, *, node_name: Optional[str] = None, handle: Optional[int] = None) -> Dict[str, Any]:
    """Resolve one node by name or handle and return a structured envelope."""
    if not node_name and handle is None:
        return {"success": False, "message": "node_name or handle is required", "matches": []}

    matches: List[Any] = []
    if node_name:
        try:
            node = runtime.getNodeByName(node_name)
        except Exception:  # noqa: BLE001
            node = None
        if node is not None:
            matches.append(node)
        else:
            matches.extend(node for node in iter_scene_nodes(runtime) if str(getattr(node, "name", "")) == node_name)

    if handle is not None:
        resolved = []
        for node in iter_scene_nodes(runtime):
            try:
                if int(getattr(node, "handle")) == int(handle):
                    resolved.append(node)
            except Exception:  # noqa: BLE001
                continue
        matches = resolved

    identities = [node_identity(node) for node in matches]
    if not identities:
        return {"success": False, "message": "No matching node found", "matches": []}
    if len(identities) > 1:
        return {"success": False, "message": "Node reference is ambiguous", "matches": identities}
    return {"success": True, "message": "Resolved node", "node": identities[0], "matches": identities}


def runtime_symbol_info(runtime: Any, name: str) -> Dict[str, Any]:
    """Return safe metadata for one runtime symbol."""
    try:
        value = getattr(runtime, name)
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "available": False, "error": str(exc)}

    signature = None
    try:
        signature = str(inspect.signature(value)) if callable(value) else None
    except (TypeError, ValueError):
        signature = None

    doc = getattr(value, "__doc__", None)
    if isinstance(doc, str):
        doc = doc.strip().splitlines()[0] if doc.strip() else None
    return {
        "name": name,
        "available": True,
        "type": type(value).__name__,
        "callable": callable(value),
        "signature": signature,
        "doc": doc,
    }
