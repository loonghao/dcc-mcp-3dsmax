"""Small helpers for 3ds Max scene tool scripts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional


def coerce_vector3(value: Any, name: str) -> Optional[List[float]]:
    """Normalize a 3D vector from ``[x, y, z]`` or ``{"x": ..., ...}``."""
    if value is None:
        return None

    if isinstance(value, Mapping):
        raw = [value.get("x"), value.get("y"), value.get("z")]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        raw = list(value)
    else:
        raise ValueError("{} must be an object with x/y/z or a 3-item array".format(name))

    if len(raw) != 3 or any(item is None for item in raw):
        raise ValueError("{} must contain exactly x, y, and z values".format(name))

    try:
        return [float(raw[0]), float(raw[1]), float(raw[2])]
    except (TypeError, ValueError) as exc:
        raise ValueError("{} values must be numbers".format(name)) from exc


def make_point3(runtime: Any, value: Any, name: str = "position") -> Optional[Any]:
    """Create a pymxs Point3 from user input."""
    vector = coerce_vector3(value, name)
    if vector is None:
        return None
    return runtime.Point3(vector[0], vector[1], vector[2])


def point3_to_list(value: Any) -> Optional[List[float]]:
    """Serialize a pymxs Point3-like value into plain floats."""
    if value is None:
        return None
    try:
        return [float(value.x), float(value.y), float(value.z)]
    except Exception:  # noqa: BLE001
        pass
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) >= 3:
        try:
            return [float(value[0]), float(value[1]), float(value[2])]
        except (TypeError, ValueError):
            return None
    return None


def set_node_position(runtime: Any, node: Any, position: Any) -> Optional[List[float]]:
    """Apply a position to a 3ds Max node and return the normalized vector."""
    vector = coerce_vector3(position, "position")
    if vector is None:
        return None
    node.pos = runtime.Point3(vector[0], vector[1], vector[2])
    return vector


def node_identity(node: Any) -> Dict[str, Any]:
    """Return a JSON-safe identity payload for a 3ds Max node."""
    handle = getattr(node, "handle", None)
    try:
        object_id = int(handle) if handle is not None else None
    except (TypeError, ValueError):
        object_id = None
    payload = {
        "node_name": str(getattr(node, "name", "")),
        "object_id": object_id,
    }
    position = point3_to_list(getattr(node, "pos", None))
    if position is not None:
        payload["position"] = position
    return payload


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
