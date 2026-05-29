"""3ds Max thread-affinity dispatcher helpers.

Core owns the shared UI queue, cancellation, shutdown, and pump controller
behavior.  This package exports only the 3ds Max-specific wrappers and factory
helpers that bind those core abstractions to the host.
"""

# Import future modules
from __future__ import annotations

from dcc_mcp_3dsmax.dispatcher.cancel import check_3dsmax_cancelled
from dcc_mcp_3dsmax.dispatcher.pump import (
    DEFAULT_BUDGET_MS,
    OVERRUN_MULTIPLIER,
    MaxDotNetTimerAdapter,
    MaxUiPump,
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
    "OVERRUN_MULTIPLIER",
    # Dispatchers
    "MaxUiDispatcher",
    "MaxStandaloneDispatcher",
    # Pumps
    "MaxDotNetTimerAdapter",
    "MaxUiPump",
    # Factories
    "create_dispatcher",
    "create_pumped_dispatcher",
]
