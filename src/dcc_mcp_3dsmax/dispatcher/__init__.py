"""3ds Max thread-affinity dispatchers.

Public dispatcher symbols are re-exported from their focused submodules
through the :pep:`8`-compliant ``__all__`` below.

The implementation is split per Single Responsibility into:

================  ====================================================
Module            Purpose
================  ====================================================
``job``           ``_JobEntry`` + ``_current_job`` ContextVar
``cancel``        ``check_3dsmax_cancelled`` cooperative checkpoint
``ui``            ``MaxUiDispatcher`` (interactive)
``standalone``    ``MaxStandaloneDispatcher`` (batch)
``pump``          ``MaxUiPump`` / core ``QueueDispatcher`` pump helpers
================  ====================================================

See: https://github.com/loonghao/dcc-mcp-3dsmax/issues/1
"""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.dispatcher.cancel import check_3dsmax_cancelled
from dcc_mcp_3dsmax.dispatcher.job import DEFAULT_JOB_TIMEOUT_MS, _current_job, _JobEntry
from dcc_mcp_3dsmax.dispatcher.pump import (
    DEFAULT_BUDGET_MS,
    OVERRUN_MULTIPLIER,
    CoreQueueDispatcher,
    MaxUiPump,
    _CorePump,
    create_dispatcher,
    create_pumped_dispatcher,
)
from dcc_mcp_3dsmax.dispatcher.standalone import MaxStandaloneDispatcher
from dcc_mcp_3dsmax.dispatcher.ui import MaxUiDispatcher

__all__ = [
    # Cancellation
    "check_3dsmax_cancelled",
    # Constants
    "DEFAULT_BUDGET_MS",
    "DEFAULT_JOB_TIMEOUT_MS",
    "OVERRUN_MULTIPLIER",
    # Dispatchers
    "MaxUiDispatcher",
    "MaxStandaloneDispatcher",
    # Pumps
    "MaxUiPump",
    # Factories
    "create_dispatcher",
    "create_pumped_dispatcher",
    # Core dispatcher used by create_pumped_dispatcher
    "CoreQueueDispatcher",
    # Internals exposed for advanced use
    "_CorePump",
    "_JobEntry",
    "_current_job",
]
