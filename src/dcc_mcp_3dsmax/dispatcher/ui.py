"""Interactive 3ds Max UI-thread dispatcher.

The queue, cancellation, timeout, active-job, and shutdown lifecycle live in
``dcc-mcp-core``.  This adapter only adds 3ds Max labels plus a hook for the
host pump controller.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional

from dcc_mcp_core import HostUiDispatcherBase


class MaxUiDispatcher(HostUiDispatcherBase):
    """Thin 3ds Max wrapper around the shared core UI dispatcher."""

    def __init__(self, *, fail_fast_on_main_queue_busy: bool = False) -> None:
        super().__init__(
            fail_fast_on_main_queue_busy=fail_fast_on_main_queue_busy,
            label="3dsmax-ui",
        )
        self._pump_controller: Optional[Any] = None

    def attach_pump_controller(self, controller: Any) -> None:
        """Attach the core pump controller used to schedule host ticks."""
        self._pump_controller = controller

    def detach_pump_controller(self, controller: Any = None) -> None:
        """Detach the pump controller when it is stopped."""
        if controller is None or self._pump_controller is controller:
            self._pump_controller = None

    def poke_host_pump(self) -> None:
        """Ask the 3ds Max pump controller to drain queued UI work soon."""
        controller = self._pump_controller
        schedule_soon = getattr(controller, "schedule_soon", None)
        if callable(schedule_soon):
            schedule_soon()

    def format_timeout_error(self, request_id: str, affinity: str, timeout_sec: float) -> str:
        """Keep the existing 3ds Max timeout wording."""
        _ = request_id, affinity
        return "Timeout ({:.1f}s) waiting for main-thread execution".format(timeout_sec)

    def dispatch_callable(
        self,
        func: Callable[..., Any],
        *args: Any,
        affinity: str = "main",
        context: Any = None,
        action_name: Optional[str] = None,
        skill_name: Optional[str] = None,
        execution: Optional[str] = None,
        timeout_hint_secs: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """Run *func* through the core UI dispatcher protocol."""
        _ = (context, skill_name, execution)
        request_id = action_name or "dispatch_{}".format(uuid.uuid4().hex)
        timeout_ms = timeout_hint_secs * 1000 if timeout_hint_secs is not None else None
        result = self.submit_callable(
            request_id=request_id,
            task=lambda: func(*args, **kwargs),
            affinity=affinity,
            timeout_ms=timeout_ms,
        )

        if not isinstance(result, dict):
            raise RuntimeError("dispatch_callable: unexpected result type {}".format(type(result)))
        if not result.get("success", True):
            raise RuntimeError("dispatch_callable: {}".format(result.get("error", "Unknown error")))
        return result.get("output")
