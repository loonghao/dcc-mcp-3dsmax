"""Cooperative cancellation checkpoint for 3ds Max skill scripts.

Provides :func:`check_3dsmax_cancelled`, a dependency-light probe that
honours both the MCP request-bound cancellation token (from
``dcc_mcp_core.cancellation``) and the per-job flag set by
:meth:`MaxUiDispatcher.cancel` / :meth:`MaxUiDispatcher.shutdown`.

See: https://github.com/loonghao/dcc-mcp-3dsmax/issues/1
"""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.cancellation import CancelledError, check_dcc_cancelled

# Import local modules
from dcc_mcp_3dsmax.dispatcher.job import _current_job


def check_3dsmax_cancelled() -> None:
    """Raise :class:`~dcc_mcp_core.cancellation.CancelledError` on cancellation.

    Used by skill scripts inside long-running loops so the caller can
    preempt work without 3ds Max's UI thread running unbounded. The helper
    respects **both** cancellation sources:

    1. ``dcc_mcp_core.cancellation.check_dcc_cancelled()`` — the MCP request
       token plus any current core job handle.
    2. The per-job :attr:`_JobEntry.cancel_flag`, populated by
       :meth:`MaxUiDispatcher.cancel` / :meth:`MaxUiDispatcher.shutdown`.

    When neither source reports cancellation, the call is a cheap no-op.

    Example::

        from dcc_mcp_3dsmax.dispatcher import check_3dsmax_cancelled

        def process_objects(objects):
            for obj in objects:
                check_3dsmax_cancelled()  # safe checkpoint
                # process obj...

    Raises
    ------
    dcc_mcp_core.cancellation.CancelledError
        When either the MCP request or the owning dispatcher has
        signalled cancellation.
    """
    # Layer 1: honour the core MCP request token and current core job handle.
    check_dcc_cancelled()

    # Layer 2: honour the 3ds Max-side per-job flag
    job = _current_job.get()
    if job is not None and job.cancelled:
        raise CancelledError("3ds Max job cancelled by dispatcher")
