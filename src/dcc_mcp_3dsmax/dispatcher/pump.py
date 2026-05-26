"""Idle-event pump schedulers + dispatcher factory helpers for 3ds Max.

This module provides pump implementations that integrate with 3ds Max's
event loop to drain the main-thread job queue.

For 3ds Max, we use a ``dotNet`` timer as the idle-event equivalent,
since 3ds Max doesn't have a direct ``scriptJob(event=['idle', ...])``
equivalent like Maya.

See: https://github.com/loonghao/dcc-mcp-3dsmax/issues/1
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
import time
from typing import Any, Dict, Optional, Tuple

# Import third-party modules
try:
    from dcc_mcp_core.host import QueueDispatcher as CoreQueueDispatcher
except ImportError:
    CoreQueueDispatcher = None

# Import local modules
from dcc_mcp_3dsmax.dispatcher.standalone import MaxStandaloneDispatcher
from dcc_mcp_3dsmax.dispatcher.ui import MaxUiDispatcher

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

#: Default time budget (milliseconds) per pump cycle.
DEFAULT_BUDGET_MS = 8

#: Overrun threshold — any pump tick that spends more than ``budget_ms`` × this
#: multiplier counts as an ``overrun_cycles``.
OVERRUN_MULTIPLIER = 2.0


class MaxUiPump:
    """Cooperative time-slice scheduler driven by 3ds Max idle events.

    Uses a ``dotNet`` timer to periodically drain pending main-thread
    jobs from the attached :class:`MaxUiDispatcher` up to *budget_ms*
    milliseconds.

    Parameters
    ----------
    dispatcher:
        The :class:`MaxUiDispatcher` whose main-thread queue to drain.
    budget_ms:
        Maximum milliseconds to spend draining per tick.
    """

    def __init__(
        self,
        dispatcher: MaxUiDispatcher,
        budget_ms: float = DEFAULT_BUDGET_MS,
    ) -> None:
        self._dispatcher = dispatcher
        self._budget_ms = budget_ms
        self._timer = None
        self._installed = False
        self._stats: Dict[str, float] = {
            "total_executed": 0,
            "total_cycles": 0,
            "total_elapsed_ms": 0.0,
            "overrun_cycles": 0,
            "longest_job_ms": 0.0,
        }

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @property
    def is_installed(self) -> bool:
        """``True`` if the pump timer is currently active."""
        return self._installed

    @property
    def budget_ms(self) -> float:
        """Current time budget per pump cycle."""
        return self._budget_ms

    @budget_ms.setter
    def budget_ms(self, value: float) -> None:
        self._budget_ms = max(1.0, value)

    @property
    def stats(self) -> Dict[str, Any]:
        """Cumulative pump statistics."""
        return dict(self._stats)

    def install(self) -> bool:
        """Install the pump timer with 3ds Max.

        Returns ``True`` if installation succeeded or is already installed.
        """
        if self._installed:
            return True

        try:
            import clr  # noqa: F401, PLC0415
            from System.Windows.Forms import Timer

            self._timer = Timer()
            self._timer.Interval = 100  # 100ms tick
            self._timer.Tick += self._on_timer_tick
            self._timer.Start()

            self._installed = True
            logger.info(
                "MaxUiPump installed (timer interval=%d ms, budget=%.1f ms)",
                self._timer.Interval,
                self._budget_ms,
            )
            return True
        except ImportError:
            logger.warning("MaxUiPump: dotNet not available — install skipped")
            return False
        except Exception as exc:
            logger.error("MaxUiPump: failed to install timer: %s", exc)
            return False

    def uninstall(self) -> None:
        """Remove the pump timer from 3ds Max."""
        if not self._installed:
            return

        try:
            if self._timer is not None:
                self._timer.Stop()
                self._timer.Tick -= self._on_timer_tick
                self._timer.Dispose()
                logger.info("MaxUiPump uninstalled")
        except Exception as exc:
            logger.warning("MaxUiPump: error removing timer: %s", exc)
        finally:
            self._timer = None
            self._installed = False

    # ── Pump implementation ───────────────────────────────────────────────────

    def _on_timer_tick(self, sender, e) -> None:
        """Timer tick handler — drain pending jobs within the budget."""
        start = time.monotonic()
        executed, remaining = self._dispatcher.drain_queue(self._budget_ms)

        elapsed_ms = (time.monotonic() - start) * 1000.0
        self._stats["total_executed"] += executed
        self._stats["total_cycles"] += 1
        self._stats["total_elapsed_ms"] += elapsed_ms

        if elapsed_ms > self._budget_ms * OVERRUN_MULTIPLIER:
            self._stats["overrun_cycles"] += 1

        if executed > 0:
            avg_job_ms = elapsed_ms / executed
            worst_job_ms = elapsed_ms if executed == 1 else max(elapsed_ms, avg_job_ms)
            if worst_job_ms > self._stats["longest_job_ms"]:
                self._stats["longest_job_ms"] = worst_job_ms

        if remaining > 0:
            # Timer will fire again, no need to poke
            pass


# ── Factory helpers ───────────────────────────────────────────────────────────

def create_dispatcher(
    budget_ms: float = DEFAULT_BUDGET_MS,
) -> Tuple[Any, Optional[MaxUiPump]]:
    """Create the appropriate dispatcher for the current 3ds Max environment.

    Returns a ``(dispatcher, pump)`` pair where *dispatcher* is a
    :class:`MaxUiDispatcher` (interactive) or
    :class:`MaxStandaloneDispatcher` (batch), and *pump* is a
    :class:`MaxUiPump` or ``None`` respectively.

    Returns
    -------
    tuple[MaxUiDispatcher | MaxStandaloneDispatcher, MaxUiPump | None]
        A ``(dispatcher, pump)`` pair.  The pump is ``None`` in standalone mode.
    """
    try:
        import pymxs
        getattr(pymxs, "runtime", None)
        # 3ds Max doesn't have a direct "batch" query like Maya's cmds.about(batch=True)
        # For now, assume interactive if pymxs is available
        is_batch = False
    except ImportError:
        is_batch = True

    if is_batch:
        return MaxStandaloneDispatcher(), None

    dispatcher = MaxUiDispatcher()
    pump = MaxUiPump(dispatcher, budget_ms=budget_ms)
    return dispatcher, pump


def create_pumped_dispatcher(
    budget_ms: float = DEFAULT_BUDGET_MS,
) -> Tuple[Any, Optional["_CorePump"]]:
    """Create a Rust-backed dispatcher for the current 3ds Max environment.

    This is an alternative to :func:`create_dispatcher` that returns the
    core's ``QueueDispatcher`` instead of :class:`MaxUiDispatcher`.
    """
    if CoreQueueDispatcher is None:
        logger.warning("create_pumped_dispatcher: core QueueDispatcher not available")
        return MaxStandaloneDispatcher(), None

    try:
        import pymxs
        getattr(pymxs, "runtime", None)
        is_batch = False
    except ImportError:
        is_batch = True

    if is_batch:
        return MaxStandaloneDispatcher(), None

    core_dispatcher = CoreQueueDispatcher()
    pump = _CorePump(core_dispatcher, budget_ms=budget_ms)
    return core_dispatcher, pump


class _CorePump:
    """Idle-event pump adapter for core ``QueueDispatcher`` in 3ds Max.

    Uses a ``dotNet`` timer to periodically call ``QueueDispatcher.tick``.
    """

    def __init__(self, dispatcher: Any, budget_ms: float = DEFAULT_BUDGET_MS) -> None:
        self._dispatcher = dispatcher
        self._budget_ms = budget_ms
        self._timer = None
        self._installed = False

    @property
    def is_installed(self) -> bool:
        """``True`` if the timer is currently active."""
        return self._installed

    def install(self) -> bool:
        """Install the pump timer."""
        if self._installed:
            return True
        try:
            import clr  # noqa: F401, PLC0415
            from System.Windows.Forms import Timer

            self._timer = Timer()
            self._timer.Interval = 100
            self._timer.Tick += self._on_timer_tick
            self._timer.Start()

            self._installed = True
            logger.info(
                "_CorePump installed (timer interval=%d ms, budget=%.1f ms)",
                self._timer.Interval,
                self._budget_ms,
            )
            return True
        except ImportError:
            logger.warning("_CorePump: dotNet not available — install skipped")
            return False
        except Exception as exc:
            logger.error("_CorePump: failed to install timer: %s", exc)
            return False

    def uninstall(self) -> None:
        """Remove the pump timer."""
        if not self._installed:
            return
        try:
            if self._timer is not None:
                self._timer.Stop()
                self._timer.Tick -= self._on_timer_tick
                self._timer.Dispose()
                logger.info("_CorePump uninstalled")
        except Exception as exc:
            logger.warning("_CorePump: error removing timer: %s", exc)
        finally:
            self._timer = None
            self._installed = False

    def _on_timer_tick(self, sender, e) -> None:
        """Timer tick handler — drain pending Rust-side main-thread jobs."""
        try:
            outcome = self._dispatcher.tick(int(self._budget_ms))
            remaining = getattr(outcome, "more_pending", False)
            if isinstance(outcome, dict):
                remaining = bool(outcome.get("more_pending") or outcome.get("remaining"))
            if remaining > 0:
                # Timer will fire again
                pass
        except Exception as exc:
            logger.debug("_CorePump._on_timer_tick error: %s", exc)
