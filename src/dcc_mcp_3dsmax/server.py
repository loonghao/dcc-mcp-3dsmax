"""3ds Max MCP server — embeds a Streamable HTTP MCP server inside 3ds Max.

Extends :class:`dcc_mcp_core.server_base.DccServerBase` with 3ds Max-specific
skill path discovery and version detection.

All generic logic (skill registration, hot-reload, gateway failover,
action registry, lifecycle) is provided by the base class.

Usage (inside 3ds Max MAXScript Listener or startup script)::

    import dcc_mcp_3dsmax

    # Start with default port (auto-gateway: first instance wins 8765)
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
from dcc_mcp_core import DccServerOptions
from dcc_mcp_core.server_base import DccServerBase

# Import local modules
from dcc_mcp_3dsmax import _env
from dcc_mcp_3dsmax.__version__ import __version__
from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string

logger = logging.getLogger(__name__)

# ── constants ──────────────────────────────────────────────────────────────

SERVER_NAME = "dcc-mcp-3dsmax"
SERVER_VERSION = __version__
DEFAULT_PORT = 8765

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
    gateway_port: Optional[int] = None
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
    dcc-mcp-core implements an **auto-gateway** with first-wins port competition:
    the first 3ds Max process to bind the well-known port (8765) becomes the
    gateway; subsequent instances start on ephemeral ports and register
    themselves automatically.

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
        gateway_port: Optional[int] = None,
        registry_dir: Optional[str] = None,
        dcc_version: Optional[str] = None,
        scene: Optional[str] = None,
        enable_gateway_failover: Optional[bool] = None,
        metrics_enabled: Optional[bool] = None,
        job_storage_path: Optional[str] = None,
        job_recovery: Optional[str] = None,
        enable_workflows: Optional[bool] = None,
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
            )

        super().__init__(options=options.to_core_options())

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
        extra_paths = list(self._options.extra_skill_paths or []) if hasattr(self._options, "extra_skill_paths") else []
        return self.collect_skill_search_paths(
            extra_paths=extra_paths,
            filter_existing=True,
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self) -> "MaxMcpServer":
        """Start the MCP HTTP server.  Returns *self* for chaining."""
        super().start()
        return self

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

    def load_skill(self, skill_name: str) -> List[str]:
        """Load a skill by name — imports scripts and registers tools.

        Args:
            skill_name: Skill name as declared in ``SKILL.md`` (e.g. ``"3dsmax-scene"``).

        Returns:
            List of action names that were registered.

        Raises:
            RuntimeError: If the server is not running.
        """
        if self._handle is None:
            raise RuntimeError("Server is not running — call start() first")
        actions = self._server.load_skill(skill_name)
        logger.debug("MaxMcpServer: loaded skill %r → actions: %s", skill_name, actions)
        return actions

    def unload_skill(self, skill_name: str) -> int:
        """Unload a skill, removing its tools from the registry.

        Args:
            skill_name: Skill name to unload.

        Returns:
            Number of actions removed.

        Raises:
            RuntimeError: If the server is not running.
        """
        if self._handle is None:
            raise RuntimeError("Server is not running — call start() first")
        count = self._server.unload_skill(skill_name)
        logger.debug("MaxMcpServer: unloaded skill %r (%d action(s) removed)", skill_name, count)
        return count

    def list_skills(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all discovered skills with their load status."""
        if self._handle is None:
            return []
        return list(self._server.list_skills(status=status))

    def find_skills(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        dcc: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for skills matching the given criteria."""
        if self._handle is None:
            return []
        tags_list: List[str] = tags if tags is not None else []
        dcc_name: str = dcc if dcc is not None else _DCC_NAME
        return list(self._server.search_skills(query=query, tags=tags_list, dcc=dcc_name))

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
    register_builtins: bool = True,
    include_bundled: bool = True,
    enable_hot_reload: bool = False,
    gateway_port: Optional[int] = None,
    registry_dir: Optional[str] = None,
    dcc_version: Optional[str] = None,
    scene: Optional[str] = None,
    enable_gateway_failover: Optional[bool] = None,
    metrics_enabled: Optional[bool] = None,
    job_storage_path: Optional[str] = None,
    job_recovery: Optional[str] = None,
    enable_workflows: Optional[bool] = None,
) -> MaxMcpServer:
    """Start the 3ds Max MCP server (creates a process-level singleton).

    The first call creates and starts the server.  Subsequent calls return the
    existing instance without restarting it.

    Args:
        port: Preferred TCP port (default 8765; use 0 for a random port).
        extra_skill_paths: Additional skill directories beyond built-ins.
        register_builtins: If ``True``, discover and load all skills.
        include_bundled: Include dcc-mcp-core bundled skills.
        enable_hot_reload: Enable skill hot-reload on file changes.
        gateway_port: Gateway competition port.
        registry_dir: Shared registry directory.
        dcc_version: 3ds Max version for gateway registry.
        scene: Currently open scene file path for the gateway registry.
        enable_gateway_failover: Enable automatic gateway failover.
        metrics_enabled: Force Prometheus ``/metrics`` (``None`` = env ``DCC_MCP_3DSMAX_METRICS``).
        job_storage_path: SQLite job DB path (``None`` = env / default).
        job_recovery: Job recovery policy (``"drop"`` or ``"requeue"``).
        enable_workflows: Enable workflow MCP tools (``None`` = env).

    Returns:
        The running :class:`MaxMcpServer` instance.
    """
    global _server_instance  # noqa: PLW0603
    if _server_instance is not None and _server_instance.is_running:
        return _server_instance

    _server_instance = MaxMcpServer(
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
    )
    if register_builtins:
        _server_instance.register_builtin_actions(include_bundled=include_bundled)
    if enable_hot_reload:
        _server_instance.enable_hot_reload()
    _server_instance.start()
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
