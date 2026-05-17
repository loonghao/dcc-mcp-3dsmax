"""3ds Max version detection helpers.

Detects the running 3ds Max version via ``pymxs.runtime.maxVersion()``.
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# 3ds Max version mapping (major version -> marketing version)
VERSION_MAP = {
    25000: "2023",
    24000: "2022",
    23000: "2021",
    22000: "2020",
    21000: "2019",
    20000: "2018",
    19000: "2017",
    18000: "2016",
    17000: "2015",
    16000: "2014",
    15000: "2013",
}


def get_3dsmax_version_string() -> str:
    """Return the 3ds Max version as a human-readable string.

    Uses ``pymxs.runtime.maxVersion()`` to detect the version.
    Returns ``"unknown"`` when 3ds Max is not available.

    Returns
    -------
    str
        Version string like ``"2023"`` or ``"unknown"``.
    """
    try:
        import pymxs  # noqa: PLC0415

        rt = pymxs.runtime
        version_num = rt.maxVersion()[0]  # Returns (version, build) tuple
        marketing_version = _parse_version(version_num)
        return marketing_version
    except ImportError:
        logger.debug("pymxs not available - not running inside 3ds Max")
        return "unknown"
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to detect 3ds Max version: %s", exc)
        return "unknown"


def get_3dsmax_version_number() -> Optional[int]:
    """Return the raw 3ds Max version number.

    Returns
    -------
    Optional[int]
        Version number like ``25000`` (for 2023) or ``None``.
    """
    try:
        import pymxs  # noqa: PLC0415

        rt = pymxs.runtime
        return int(rt.maxVersion()[0])
    except ImportError:
        return None
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to get 3ds Max version number: %s", exc)
        return None


def is_3dsmax_available() -> bool:
    """Check if 3ds Max Python API (pymxs) is available.

    Returns
    -------
    bool
        ``True`` if running inside 3ds Max.
    """
    try:
        import pymxs  # noqa: PLC0415

        return True
    except ImportError:
        return False


def _parse_version(version_num: int) -> str:
    """Convert raw version number to marketing version string.

    Parameters
    ----------
    version_num : int
        Raw version number from ``maxVersion()``.

    Returns
    -------
    str
        Marketing version like ``"2023"``.
    """
    # Check exact match first
    if version_num in VERSION_MAP:
        return VERSION_MAP[version_num]

    # Try to parse year from version number
    # Version numbers are typically X000 where X is year offset
    # 25000 = 2023, 24000 = 2022, etc.
    for raw_ver, marketing in VERSION_MAP.items():
        if version_num >= raw_ver:
            return marketing

    return f"version_{version_num}"
