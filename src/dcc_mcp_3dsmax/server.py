"""3ds Max MCP server — embeds a Streamable HTTP MCP server inside 3ds Max.

Extends :class:`dcc_mcp_core.server_base.DccServerBase` with 3ds Max-specific
skill path discovery and version detection.

All generic logic (skill registration, hot-reload, gateway failover,
action registry, lifecycle) is provided by the base class.

Usage (inside 3ds Max MAXScript Listener or startup script)::

    import dcc_mcp_3dsmax

    # Start on a random instance port and publish through the stable gateway.
    server = dcc_mcp_3dsmax.start_server()

    # Progressive loading — discover skills without loading them immediately
    n = server.discover_skills()        # scan paths, register tool metadata
    server.load_skill("3dsmax-scene")  # lazy-load a specific skill

    dcc_mcp_3dsmax.stop_server()
"""

# Import future modules
from __future__ import annotations

# Import built-in modules
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import third-party modules
from dcc_mcp_core import DccServerOptions, HostExecutionBridge, MinimalModeConfig, scan_and_load_strict
from dcc_mcp_core.server_base import DccServerBase

# Import local modules
from dcc_mcp_3dsmax import _env, _executor
from dcc_mcp_3dsmax.__version__ import __version__
from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string

logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────

SERVER_NAME = "dcc-mcp-3dsmax"
SERVER_VERSION = __version__
DEFAULT_PORT = 0
DEFAULT_GATEWAY_PORT = 9765

# Built-in skills directory shipped with this package
_BUILTIN_SKILLS_DIR = Path(__file__).resolve().parent / "skills"

# Environment variable for extra skill paths (colon/semicolon separated)
_ENV_EXTRA_SKILL_PATHS = "DCC_MCP_3DSMAX_SKILL_PATHS"
_ENV_GENERIC_SKILL_PATHS = "DCC_MCP_SKILL_PATHS"

_DCC_NAME = "3dsmax"


# ── options ─────────────────────────────────────────────────────────────────


@dataclass
class MaxServerOptions:
    """Adapter-local options collapsed for the dcc-mcp-core 0.17+ server contract."""

    port: int = DEFAULT_PORT
    extra_skill_paths: Optional[List[str]] = None
    server_name: str = SERVER_NAME
    server_version: str = SERVER_VERSION
    # Gateway options
    gateway_port: Optional[int] = DEFAULT_GATEWAY_PORT
    registry_dir: Optional[str] = None
    dcc_version: Optional[str] = None
    scene: Optional[str] = None
    enable_gateway_failover: Optional[bool] = None
    # Observability options
    metrics_enabled: Optional[bool] = None
    job_storage_path: Optional[str] = None
    job_recovery: Optional[str] = None
    enable_workflows: Optional[bool] = None
    # Diagnostics options (new in 0.17+)
    dcc_pid: Optional[int] = None
    dcc_window_title: Optional[str] = None
    dcc_window_handle: Optional[int] = None
    snapshot_provider: Optional[Any] = None
    # Execution options (new in 0.17+)
    dispatcher: Optional[Any] = None  # BaseDccCallableDispatcher
    execution_bridge: Optional[Any] = None  # HostExecutionBridge

    def to_core_options(self) -> DccServerOptions:
        """Convert to core DccServerOptions using from_env()."""
        return DccServerOptions.from_env(
            dcc_name=_DCC_NAME,
            builtin_skills_dir=_BUILTIN_SKILLS_DIR,
            port=self.port,
            server_name=self.server_name,
            server_version=self.server_version,
            # Gateway kwargs
            gateway_port=self.gateway_port,
            registry_dir=self.registry_dir,
            dcc_version=self.dcc_version,
            scene=self.scene,
            enable_gateway_failover=_env.resolve_enable_gateway_failover(
                self.enable_gateway_failover,
                default=True,
            ),
            # Observability kwargs
            enable_file_logging=True,  # default
            enable_job_persistence=self.job_storage_path is not None,
            enable_telemetry=True,  # default
            # Diagnostics kwargs (new in 0.17+)
            dcc_pid=self.dcc_pid,
            dcc_window_title=self.dcc_window_title,
            dcc_window_handle=self.dcc_window_handle,
            snapshot_provider=self.snapshot_provider,
            # Execution kwargs (new in 0.17+)
            dispatcher=self.dispatcher,
            execution_bridge=self.execution_bridge,
        )


# ── server class ─────────────────────────────────────────────────────────────


class MaxMcpServer(DccServerBase):
    """MCP server embedded inside 3ds Max.

    Thin subclass of :class:`~dcc_mcp_core.server_base.DccServerBase`.
    All skill management, hot-reload, and gateway election logic is
    inherited.  This class adds only:

    - 3ds Max built-in skills directory (``skills/``)
    - 3ds Max version detection via ``pymxs.runtime.maxVersion()``
    - Progressive loading helpers: :meth:`discover_skills`, :meth:`loaded_skill_count`

    Multi-instance / gateway
    ------------------------
    dcc-mcp-core exposes the stable gateway at http://127.0.0.1:9765/mcp while
    each 3ds Max instance listens on its own ephemeral localhost port.

    Progressive loading
    -------------------
    Skills can be discovered (metadata only, no Python import) and loaded
    on demand::

        server.discover_skills()             # fast: scan SKILL.md files
        server.load_skill("3dsmax-scene")   # lazy: import scripts only now
        server.unload_skill("3dsmax-scene") # unload to free memory

    Attributes:
        port: TCP port the server is listening on (updated after :meth:`start`).
    """

    def __init__(
        self,
        port: int = DEFAULT_PORT,
        extra_skill_paths: Optional[List[str]] = None,
        server_name: str = SERVER_NAME,
        server_version: str = SERVER_VERSION,
        gateway_port: Optional[int] = DEFAULT_GATEWAY_PORT,
        registry_dir: Optional[str] = None,
        dcc_version: Optional[str] = None,
        scene: Optional[str] = None,
        enable_gateway_failover: Optional[bool] = None,
        metrics_enabled: Optional[bool] = None,
        job_storage_path: Optional[str] = None,
        job_recovery: Optional[str] = None,
        enable_workflows: Optional[bool] = None,
        dcc_pid: Optional[int] = None,
        dcc_window_title: Optional[str] = None,
        dcc_window_handle: Optional[int] = None,
        snapshot_provider: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
        execution_bridge: Optional[Any] = None,
        options: Optional[MaxServerOptions] = None,
    ) -> None:
        if options is None:
            options = MaxServerOptions(
                port=port,
                extra_skill_paths=extra_skill_paths,
                server_name=server_name,
                server_version=server_version,
                gateway_port=gateway_port,
                registry_dir=registry_dir,
                dcc_version=dcc_version,
                scene=scene,
                enable_gateway_failover=enable_gateway_failover,
                metrics_enabled=metrics_enabled,
                job_storage_path=job_storage_path,
                job_recovery=job_recovery,
                enable_workflows=enable_workflows,
                dcc_pid=dcc_pid,
                dcc_window_title=dcc_window_title,
                dcc_window_handle=dcc_window_handle,
                snapshot_provider=snapshot_provider,
                dispatcher=dispatcher,
                execution_bridge=execution_bridge,
            )

        super().__init__(options=options.to_core_options())
        self._extra_skill_paths: List[str] = list(options.extra_skill_paths or [])
        self._max_dispatcher: Any = None
        self._execution_bridge: HostExecutionBridge
        if options.execution_bridge is not None:
            self._execution_bridge = options.execution_bridge
            self.register_host_execution_bridge(self._execution_bridge)
        else:
            self.attach_dispatcher(options.dispatcher)

        # ── Prometheus metrics ──────────────────────────────────────
        if _env.resolve_metrics_enabled(options.metrics_enabled):
            self._config.enable_prometheus = True
            logger.info("[%s] Prometheus /metrics endpoint enabled", _DCC_NAME)

        # ── Job persistence ─────────────────────────────────────────
        effective_job_path = _env.resolve_job_storage(options.job_storage_path)
        if effective_job_path:
            self._config.job_storage_path = effective_job_path
            logger.info("[%s] Job storage: %s", _DCC_NAME, effective_job_path)
        elif effective_job_path == "":
            self._config.job_storage_path = ""

        self._job_recovery: str = _env.resolve_job_recovery(options.job_recovery)
        self._config.job_recovery = self._job_recovery
        if self._job_recovery == "requeue":
            logger.info("[%s] Job recovery policy: requeue idempotent interrupted jobs", _DCC_NAME)

        # ── Workflow engine ──────────────────────────────────────────
        if _env.resolve_enable_workflows(options.enable_workflows):
            try:
                self._config.enable_workflows = True
                logger.info(
                    "[%s] Workflow engine enabled (workflows.run / .resume / .list_runs)",
                    _DCC_NAME,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "[%s] Could not enable workflows on inner config: %s",
                    _DCC_NAME,
                    exc,
                )

        if options.gateway_port == 0 or (
            options.gateway_port is None
            and not _env.resolve_enable_gateway_failover(
                options.enable_gateway_failover,
                default=True,
            )
        ):
            self._config.gateway_port = 0

        logger.info("[%s] MaxMcpServer initialized (port=%s)", _DCC_NAME, options.port)

    def attach_dispatcher(self, dispatcher: Any) -> None:
        """Attach or replace the 3ds Max host dispatcher used by skill execution."""
        self._max_dispatcher = dispatcher
        self._register_execution_bridge(dispatcher)

    def _register_execution_bridge(self, dispatcher: Any) -> None:
        self._execution_bridge = HostExecutionBridge(
            dispatcher=dispatcher,
            runner=_executor.run_skill_script,
            default_thread_affinity="main",
        )
        self.register_host_execution_bridge(self._execution_bridge)

    # ── 3ds Max version detection ──────────────────────────────────────

    def _version_string(self) -> str:
        """Return the 3ds Max version via ``pymxs.runtime.maxVersion()``."""
        return get_3dsmax_version_string()

    # ── Port property ──────────────────────────────────────────────────

    @property
    def port(self) -> int:
        """TCP port the server is listening on."""
        if self._handle is not None:
            try:
                return int(self._handle.port)
            except Exception:
                pass
        return int(self._options.port)

    # ── Skill search path helpers ──────────────────────────────────────────────

    def _collect_skill_paths(self) -> List[str]:
        """Collect and deduplicate existing skill paths."""
        return self.collect_skill_search_paths(
            extra_paths=self._extra_skill_paths,
            filter_existing=True,
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self, *, install_atexit_hook: bool = True) -> "MaxMcpServer":
        """Start the MCP HTTP server.  Returns *self* for chaining."""
        super().start(install_atexit_hook=install_atexit_hook)
        return self

    def stop(self) -> None:
        """Stop the MCP server and drain any attached 3ds Max dispatcher."""
        dispatcher = getattr(self, "_dcc_dispatcher", None)
        if dispatcher is not None:
            shutdown = getattr(dispatcher, "shutdown", None)
            if callable(shutdown):
                try:
                    try:
                        signalled = shutdown("Interrupted")
                    except TypeError:
                        signalled = shutdown()
                    logger.info("[%s] dispatcher.shutdown signalled %s job(s)", _DCC_NAME, signalled)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("[%s] Error draining dispatcher during stop(): %s", _DCC_NAME, exc)
        super().stop()

    def register_builtin_actions(
        self,
        extra_skill_paths: Optional[List[str]] = None,
        include_bundled: bool = True,
        minimal_mode: Optional["MinimalModeConfig"] = None,
        strict_scan: Optional[bool] = None,
    ) -> "MaxMcpServer":
        """Discover built-in skills using the core 0.17 composition contract."""
        paths = list(extra_skill_paths or []) + self._extra_skill_paths
        super().register_builtin_actions(
            extra_skill_paths=paths,
            include_bundled=include_bundled,
            minimal_mode=minimal_mode,
        )
        if _env.resolve_strict_skill_scan(strict_scan):
            self._strict_skill_scan(paths, include_bundled=include_bundled)
        return self

    def _strict_skill_scan(
        self,
        extra_skill_paths: Optional[List[str]] = None,
        include_bundled: bool = True,
    ) -> None:
        """Re-scan skill paths with core strict validation enabled."""
        scan_paths = self.collect_skill_search_paths(
            extra_paths=extra_skill_paths,
            include_bundled=include_bundled,
            filter_existing=True,
        )
        scan_and_load_strict(extra_paths=scan_paths, dcc_name=_DCC_NAME)

    # ── Progressive skill loading ──────────────────────────────────────────────

    def discover_skills(
        self,
        extra_paths: Optional[List[str]] = None,
    ) -> int:
        """Scan skill directories and register tool metadata without importing scripts.

        Args:
            extra_paths: Additional directories to scan beyond the configured paths.

        Returns:
            Number of newly discovered skills (0 if server is not running).
        """
        if self._handle is None:
            logger.warning("discover_skills called before server was started")
            return 0
        paths = self._collect_skill_paths()
        if extra_paths:
            paths = list(extra_paths) + paths
        count = self._server.discover(extra_paths=paths, dcc_name=_DCC_NAME)
        logger.debug("MaxMcpServer: discovered %d new skill(s)", count)
        return count

    def load_skill(self, skill_name: str) -> bool:
        """Load a skill by name.

        Args:
            skill_name: Skill name as declared in ``SKILL.md`` (e.g. ``"3dsmax-scene"``).

        Returns:
            ``True`` when the core server accepted the load request.
        """
        if self._handle is None:
            return False
        try:
            self._server.load_skill(skill_name)
        except Exception as exc:  # noqa: BLE001
            logger.debug("MaxMcpServer: load_skill(%r) failed: %s", skill_name, exc)
            return False
        return True

    def unload_skill(self, skill_name: str) -> bool:
        """Unload a skill, removing its tools from the registry.

        Args:
            skill_name: Skill name to unload.

        Returns:
            ``True`` when the core server accepted the unload request.
        """
        if self._handle is None:
            return False
        try:
            self._server.unload_skill(skill_name)
        except Exception as exc:  # noqa: BLE001
            logger.debug("MaxMcpServer: unload_skill(%r) failed: %s", skill_name, exc)
            return False
        return True

    def list_skills(self, status: Optional[str] = None) -> List[Dict[str, Any]]:  # type: ignore[override]
        """List all discovered skills with their load status."""
        if self._handle is None:
            return []
        return list(self._server.list_skills(status=status))

    def search_skills(  # type: ignore[override]
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        dcc: Optional[str] = None,
        scope: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for skills matching the given criteria."""
        if self._handle is None:
            return []
        try:
            return list(
                self._server.search_skills(
                    query=query,
                    tags=tags or [],
                    dcc=dcc or _DCC_NAME,
                    scope=scope,
                    limit=limit,
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("MaxMcpServer: search_skills failed: %s", exc)
            return []

    def is_skill_loaded(self, skill_name: str) -> bool:
        """Return ``True`` if the named skill is currently loaded."""
        if self._handle is None:
            return False
        return self._server.is_loaded(skill_name)

    def loaded_skill_count(self) -> int:
        """Return the number of currently loaded skills."""
        if self._handle is None:
            return 0
        return self._server.loaded_count()


# ── module-level singleton helpers ────────────────────────────────────────────

_server_instance: Optional[MaxMcpServer] = None


def start_server(
    port: int = DEFAULT_PORT,
    extra_skill_paths: Optional[List[str]] = None,
    options: Optional[MaxServerOptions] = None,
    register_builtins: bool = True,
    include_bundled: bool = True,
    enable_hot_reload: bool = False,
    gateway_port: Optional[int] = DEFAULT_GATEWAY_PORT,
    registry_dir: Optional[str] = None,
    dcc_version: Optional[str] = None,
    scene: Optional[str] = None,
    enable_gateway_failover: Optional[bool] = None,
    metrics_enabled: Optional[bool] = None,
    job_storage_path: Optional[str] = None,
    job_recovery: Optional[str] = None,
    enable_workflows: Optional[bool] = None,
    dcc_pid: Optional[int] = None,
    dcc_window_title: Optional[str] = None,
    dcc_window_handle: Optional[int] = None,
    snapshot_provider: Optional[Any] = None,
    dispatcher: Optional[Any] = None,
    execution_bridge: Optional[Any] = None,
    minimal_mode: Optional["MinimalModeConfig"] = None,
    strict_scan: Optional[bool] = None,
) -> MaxMcpServer:
    """Start the 3ds Max MCP server (creates a process-level singleton).

    The first call creates and starts the server.  Subsequent calls return the
    existing instance without restarting it.

    Args:
        port: Preferred TCP port (default 0 = random instance port).
        extra_skill_paths: Additional skill directories beyond built-ins.
        register_builtins: If ``True``, discover and load all skills.
        include_bundled: Include dcc-mcp-core bundled skills.
        enable_hot_reload: Enable skill hot-reload on file changes.
        gateway_port: Stable gateway port (default 9765).
        registry_dir: Shared registry directory.
        dcc_version: 3ds Max version for gateway registry.
        scene: Currently open scene file path for the gateway registry.
        enable_gateway_failover: Enable automatic gateway failover.
        metrics_enabled: Force Prometheus ``/metrics`` (``None`` = env ``DCC_MCP_3DSMAX_METRICS``).
        job_storage_path: SQLite job DB path (``None`` = env / default).
        job_recovery: Job recovery policy (``"drop"`` or ``"requeue"``).
        enable_workflows: Enable workflow MCP tools (``None`` = env).
        dispatcher: Optional host dispatcher for main-thread execution.
        execution_bridge: Optional execution bridge supplied by dcc-mcp-core.
        minimal_mode: Optional core progressive-loading configuration.
        strict_scan: Validate skill directories after discovery.

    Returns:
        The running :class:`MaxMcpServer` instance.
    """
    global _server_instance  # noqa: PLW0603
    if _server_instance is not None and _server_instance.is_running:
        return _server_instance

    if options is None:
        options = MaxServerOptions(
            port=port,
            extra_skill_paths=extra_skill_paths,
            gateway_port=gateway_port,
            registry_dir=registry_dir,
            dcc_version=dcc_version,
            scene=scene,
            enable_gateway_failover=enable_gateway_failover,
            metrics_enabled=metrics_enabled,
            job_storage_path=job_storage_path,
            job_recovery=job_recovery,
            enable_workflows=enable_workflows,
            dcc_pid=dcc_pid,
            dcc_window_title=dcc_window_title,
            dcc_window_handle=dcc_window_handle,
            snapshot_provider=snapshot_provider,
            dispatcher=dispatcher,
            execution_bridge=execution_bridge,
        )

    _server_instance = MaxMcpServer(options=options)
    if register_builtins:
        _server_instance.register_builtin_actions(
            include_bundled=include_bundled,
            minimal_mode=minimal_mode,
            strict_scan=strict_scan,
        )
    if enable_hot_reload:
        _server_instance.enable_hot_reload()
    _server_instance.start()
    return _server_instance


def prepare_server(
    extra_skill_paths: Optional[List[str]] = None,
    register_builtins: bool = True,
    include_bundled: bool = True,
    options: Optional[MaxServerOptions] = None,
) -> MaxMcpServer:
    """Create the singleton server and register tools without starting HTTP."""
    global _server_instance  # noqa: PLW0603
    if _server_instance is not None:
        return _server_instance

    if options is None:
        options = MaxServerOptions(
            port=0,
            gateway_port=DEFAULT_GATEWAY_PORT,
            extra_skill_paths=extra_skill_paths,
            enable_gateway_failover=False,
            job_storage_path="",
        )

    _server_instance = MaxMcpServer(options=options)
    if register_builtins:
        _server_instance.register_builtin_actions(include_bundled=include_bundled)
    return _server_instance


def stop_server() -> None:
    """Stop the running 3ds Max MCP server."""
    global _server_instance  # noqa: PLW0603
    if _server_instance is None:
        return
    _server_instance.stop()
    _server_instance = None


def get_server() -> Optional[MaxMcpServer]:
    """Return the current server instance, or ``None`` if not started."""
    return _server_instance
