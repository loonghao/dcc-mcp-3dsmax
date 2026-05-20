"""Interactive 3ds Max UI-thread dispatcher.

Hosts :class:`MaxUiDispatcher`, the affinity-aware queue used by the
in-process executor when running inside an interactive 3ds Max session
(``Main``-affinity work is funnelled to the UI thread;
``Any``-affinity work runs immediately on the calling thread).

See: https://github.com/loonghao/dcc-mcp-3dsmax/issues/1
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

# Import local modules
from dcc_mcp_3dsmax.dispatcher.job import DEFAULT_JOB_TIMEOUT_MS, _JobEntry

logger = logging.getLogger(__name__)


class MaxUiDispatcher:
    """Thread-affinity aware dispatcher for interactive 3ds Max sessions.

    - ``"main"`` affinity jobs are queued and executed on 3ds Max's UI thread.
    - ``"any"`` affinity jobs run immediately on the background thread.

    This class is **thread-safe**: ``submit()`` can be called from any thread.
    """

    def __init__(self) -> None:
        self._main_queue: Deque[_JobEntry] = deque()
        self._lock = threading.Lock()
        self._cancelled: set = set()
        self._active: Dict[str, _JobEntry] = {}
        self._shutdown = False

    # ── Public API ────────────────────────────────────────────────────────────

    def submit(
        self,
        action_name: str,
        payload: Optional[str] = None,
        affinity: str = "any",
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit a job and block until completion.

        Parameters
        ----------
        action_name:
            Logical action identifier.
        payload:
            Opaque payload string.
        affinity:
            ``"any"`` (default) or ``"main"``.
        timeout_ms:
            Soft timeout in milliseconds.

        Returns
        -------
        dict
            ``{"request_id", "affinity", "success", "output", "error"}``
        """
        affinity = affinity.lower()
        if affinity not in ("any", "main"):
            return {
                "request_id": action_name,
                "affinity": affinity,
                "success": False,
                "output": None,
                "error": f"Unsupported affinity '{affinity}'; expected 'any' or 'main'",
            }

        def _task():
            return payload

        if affinity == "any":
            return self._run_any(action_name, _task, affinity)

        return self._submit_main(action_name, _task, affinity, timeout_ms)

    def submit_callable(
        self,
        request_id: str,
        task: Callable[[], Any],
        affinity: str = "main",
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Submit an arbitrary callable for execution.

        Parameters
        ----------
        request_id:
            Unique request identifier.
        task:
            Zero-argument callable executed on the target thread.
        affinity:
            ``"any"`` or ``"main"``.
        timeout_ms:
            Soft timeout in milliseconds.

        Returns
        -------
        dict
            Same structure as :meth:`submit`.
        """
        affinity = affinity.lower()
        if affinity == "any":
            return self._run_any(request_id, task, affinity)
        return self._submit_main(request_id, task, affinity, timeout_ms)

    def submit_async_callable(
        self,
        request_id: str,
        task: Callable[[], Any],
        *,
        job_id: Optional[str] = None,
        progress_token: Optional[str] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        affinity: str = "main",
        timeout_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Enqueue a callable for main-thread execution without blocking."""
        affinity = affinity.lower()

        if self._shutdown:
            return {
                "request_id": request_id,
                "job_id": job_id,
                "status": "interrupted",
                "success": False,
                "error": "Interrupted",
            }

        if affinity == "any":
            def _bg():
                result = self._run_any(request_id, task, affinity)
                result["job_id"] = job_id
                if on_complete is not None:
                    try:
                        on_complete(result)
                    except Exception as exc:
                        logger.warning("submit_async_callable on_complete raised: %s", exc)

            t = threading.Thread(target=_bg, daemon=True, name=f"mcp-async-{request_id}")
            t.start()
        else:
            job = _JobEntry(
                request_id,
                affinity,
                task,
                timeout_ms,
                job_id=job_id,
                progress_token=progress_token,
                on_complete=on_complete,
            )
            with self._lock:
                self._main_queue.append(job)
            self._maybe_poke_deferred()

        return {
            "request_id": request_id,
            "job_id": job_id,
            "status": "pending",
            "success": True,
            "error": None,
        }

    def cancel(self, request_id: str) -> bool:
        """Signal cancellation for a pending or running main-thread job."""
        with self._lock:
            self._cancelled.add(request_id)

            for job in self._main_queue:
                if job.request_id == request_id:
                    job.cancel()
                    job.outcome = {
                        "request_id": request_id,
                        "affinity": job.affinity,
                        "success": False,
                        "output": None,
                        "error": "Cancelled",
                    }
                    job.event.set()
                    return True

            active_job = self._active.get(request_id)
            if active_job is not None:
                active_job.cancel()
                return True

        return False

    def pending_count(self) -> int:
        """Return the number of jobs waiting in the main-thread queue."""
        return len(self._main_queue)

    def shutdown(self, reason: str = "Interrupted") -> int:
        """Drain the dispatcher — mark every pending and in-flight job as ``Interrupted``."""
        signalled = 0
        with self._lock:
            self._shutdown = True

            while self._main_queue:
                job = self._main_queue.popleft()
                job.cancel()
                if job.outcome is None:
                    job.outcome = {
                        "request_id": job.request_id,
                        "affinity": job.affinity,
                        "success": False,
                        "output": None,
                        "error": reason,
                    }
                job.event.set()
                signalled += 1

            for job in list(self._active.values()):
                job.cancel()
                signalled += 1

        if signalled:
            logger.info(
                "MaxUiDispatcher.shutdown: signalled %d job(s) with reason=%r",
                signalled,
                reason,
            )
        return signalled

    @property
    def is_shutdown(self) -> bool:
        """``True`` once :meth:`shutdown` has been called."""
        return self._shutdown

    def supported(self) -> List[str]:
        """Return supported affinity values."""
        return ["any", "main"]

    def capabilities(self) -> Dict[str, bool]:
        """Return capability flags."""
        return {
            "supports_main_thread": True,
            "supports_named_threads": False,
            "supports_any_thread": True,
            "supports_time_slicing": True,
        }

    # ── Queue access (used by MaxUiPump) ─────────────────────────────────────

    def drain_queue(self, budget_ms: float) -> Tuple[int, int]:
        """Execute queued main-thread jobs up to *budget_ms*."""
        executed = 0
        start = time.monotonic()
        deadline = start + (budget_ms / 1000.0)

        while time.monotonic() < deadline:
            job = self._dequeue()
            if job is None:
                break

            with self._lock:
                if job.request_id in self._cancelled:
                    self._cancelled.discard(job.request_id)
                    if not job.event.is_set():
                        job.outcome = {
                            "request_id": job.request_id,
                            "affinity": job.affinity,
                            "success": False,
                            "output": None,
                            "error": "Cancelled",
                        }
                        job.event.set()
                    continue
                self._active[job.request_id] = job

            try:
                job.execute()
            finally:
                with self._lock:
                    self._active.pop(job.request_id, None)
            executed += 1

        remaining = len(self._main_queue)
        if executed > 0:
            elapsed_ms = (time.monotonic() - start) * 1000
            logger.debug(
                "MaxUiPump: drained %d job(s) in %.1f ms, %d remaining",
                executed,
                elapsed_ms,
                remaining,
            )
        return executed, remaining

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _run_any(request_id: str, task: Callable, affinity: str) -> Dict[str, Any]:
        """Execute a job directly on the current thread (any affinity)."""
        try:
            output = task()
            return {
                "request_id": request_id,
                "affinity": affinity,
                "success": True,
                "output": output,
                "error": None,
            }
        except Exception as exc:
            return {
                "request_id": request_id,
                "affinity": affinity,
                "success": False,
                "output": None,
                "error": str(exc),
            }

    def _submit_main(
        self,
        request_id: str,
        task: Callable,
        affinity: str,
        timeout_ms: Optional[int],
    ) -> Dict[str, Any]:
        """Enqueue a job for main-thread execution and wait for completion."""
        job = _JobEntry(request_id, affinity, task, timeout_ms)

        with self._lock:
            if self._shutdown:
                return {
                    "request_id": request_id,
                    "affinity": affinity,
                    "success": False,
                    "output": None,
                    "error": "Interrupted",
                }
            self._main_queue.append(job)

        self._maybe_poke_deferred()

        timeout_sec = (timeout_ms or DEFAULT_JOB_TIMEOUT_MS) / 1000.0
        if not job.event.wait(timeout=timeout_sec):
            return {
                "request_id": request_id,
                "affinity": affinity,
                "success": False,
                "output": None,
                "error": f"Timeout ({timeout_sec:.1f}s) waiting for main-thread execution",
            }

        return job.outcome or {
            "request_id": request_id,
            "affinity": affinity,
            "success": False,
            "output": None,
            "error": "Job completed but outcome was not set",
        }

    def _dequeue(self) -> Optional[_JobEntry]:
        """Pop the next job from the main queue (thread-safe)."""
        with self._lock:
            if self._main_queue:
                return self._main_queue.popleft()
        return None

    def _maybe_poke_deferred(self) -> None:
        """Nudge 3ds Max to drain the queue if no pump is installed.

        Note: 3ds Max doesn't have a direct equivalent to Maya's
        ``executeDeferred``. This is a placeholder for future implementation.
        For now, jobs will be drained when the pump is installed.
        """
        pass

    # ── BaseDccCallableDispatcher protocol implementation ─────────────────────

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
        """Run *func* on 3ds Max's UI thread and return the result.

        This method satisfies the
        :class:`~dcc_mcp_core._server.inprocess_executor.BaseDccCallableDispatcher`
        protocol consumed by :class:`dcc_mcp_core.HostExecutionBridge`.
        """
        import uuid

        _ = (context, skill_name, execution)
        request_id = action_name or f"dispatch_{uuid.uuid4().hex}"
        timeout_ms = timeout_hint_secs * 1000 if timeout_hint_secs is not None else None
        result = self.submit_callable(
            request_id=request_id,
            task=lambda: func(*args, **kwargs),
            affinity=affinity,
            timeout_ms=timeout_ms,
        )

        if not isinstance(result, dict):
            raise RuntimeError(f"dispatch_callable: unexpected result type {type(result)}")

        if not result.get("success", True):
            error_msg = result.get("error", "Unknown error")
            raise RuntimeError(f"dispatch_callable: {error_msg}")

        return result.get("output")
