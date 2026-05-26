"""Cooperative cancellation checkpoint for 3ds Max skill scripts."""

from __future__ import annotations

from dcc_mcp_core.cancellation import check_dcc_cancelled


def check_3dsmax_cancelled() -> None:
    """Raise ``CancelledError`` when the active MCP or host UI job is cancelled."""
    check_dcc_cancelled()
