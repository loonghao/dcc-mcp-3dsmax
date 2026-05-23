"""Basic tests for dcc-mcp-3dsmax."""

# Import built-in modules
import os
import subprocess
import sys
import time
import types
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestImports:
    """Test that core modules can be imported."""

    def test_import_package(self):
        """Test importing the main package."""
        import dcc_mcp_3dsmax

        assert hasattr(dcc_mcp_3dsmax, "__version__")
        assert dcc_mcp_3dsmax.__version__ != ""

    def test_import_package_keeps_core_native_extension_lazy(self):
        """Menu-only startup imports should not lock dcc_mcp_core._core.pyd."""
        env = dict(os.environ)
        src = Path(__file__).parent.parent / "src"
        env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "import sys\n"
            "import dcc_mcp_3dsmax\n"
            "dcc_mcp_3dsmax.install_menu\n"
            "dcc_mcp_3dsmax.install_shutdown_callback\n"
            "print('dcc_mcp_core' in sys.modules)\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            env=env,
            text=True,
        )

        assert result.stdout.strip() == "False"

    def test_stop_sidecar_hook_keeps_core_native_extension_lazy(self):
        """Install/uninstall cleanup can stop runtime without loading core."""
        env = dict(os.environ)
        src = Path(__file__).parent.parent / "src"
        env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
        code = (
            "import sys\n"
            "import dcc_mcp_3dsmax\n"
            "dcc_mcp_3dsmax.stop_sidecar_bridge()\n"
            "print('dcc_mcp_core' in sys.modules)\n"
        )

        result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            env=env,
            text=True,
        )

        assert result.stdout.strip() == "False"

    def test_import_server(self):
        """Test importing the server module."""
        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        assert MaxMcpServer is not None
        assert MaxServerOptions is not None

    def test_import_api(self):
        """Test importing the api module."""
        from dcc_mcp_3dsmax.api import max_error, max_success, with_max

        assert max_success is not None
        assert max_error is not None
        assert with_max is not None


class TestServerOptions:
    """Test adapter options passed through the core 0.17 server contract."""

    def test_options_preserve_adapter_skill_paths(self, tmp_path):
        """Configured adapter skill paths are retained for core discovery."""
        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()

        server = MaxMcpServer(
            options=MaxServerOptions(
                port=0,
                extra_skill_paths=[str(skill_dir)],
                enable_gateway_failover=False,
                job_storage_path="",
            )
        )

        paths = server._collect_skill_paths()
        assert str(skill_dir) in paths

    def test_options_wire_core_execution_dispatcher(self):
        """Dispatcher options are converted into core execution settings."""
        from dcc_mcp_3dsmax.dispatcher import MaxStandaloneDispatcher
        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        dispatcher = MaxStandaloneDispatcher()
        server = MaxMcpServer(
            options=MaxServerOptions(
                port=0,
                dispatcher=dispatcher,
                enable_gateway_failover=False,
                job_storage_path="",
            )
        )

        assert server._dcc_dispatcher is dispatcher
        assert server._inprocess_executor_registered is True

    def test_execution_bridge_uses_3dsmax_runner(self):
        """Server registers the adapter runner instead of core's main-only runner."""
        from dcc_mcp_3dsmax import _executor
        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        server = MaxMcpServer(
            options=MaxServerOptions(
                port=0,
                enable_gateway_failover=False,
                job_storage_path="",
            )
        )

        assert server._execution_bridge.runner is _executor.run_skill_script

    def test_custom_execution_bridge_is_registered(self):
        """Explicit execution bridges are passed through to core registration."""
        from dcc_mcp_core import HostExecutionBridge

        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        bridge = HostExecutionBridge(runner=lambda script_path, params: {"success": True})
        server = MaxMcpServer(
            options=MaxServerOptions(
                port=0,
                execution_bridge=bridge,
                enable_gateway_failover=False,
                job_storage_path="",
            )
        )

        assert server._execution_bridge is bridge
        assert server._inprocess_executor_registered is True


class TestExecution:
    """Test 3ds Max adapter execution helpers."""

    def test_executor_runs_main_entrypoint(self, tmp_path):
        """Adapter runner executes the current main(**params) convention."""
        from dcc_mcp_3dsmax._executor import run_skill_script

        script = tmp_path / "action_main.py"
        script.write_text(
            "\n".join(
                [
                    "def main(width=1):",
                    "    return {'success': True, 'message': 'ok', 'data': {'width': width}}",
                ]
            ),
            encoding="utf-8",
        )

        result = run_skill_script(str(script), {"width": 12})
        assert result == {"success": True, "message": "ok", "data": {"width": 12}}

    def test_executor_rejects_non_dict_main_result(self, tmp_path):
        """Adapter runner enforces the current dict envelope contract."""
        from dcc_mcp_3dsmax._executor import run_skill_script

        script = tmp_path / "action_bad.py"
        script.write_text("def main():\n    return 'ok'\n", encoding="utf-8")

        result = run_skill_script(str(script), {})
        assert result["success"] is False
        assert "must return a dict" in result["message"]

    def test_standalone_dispatcher_supports_core_protocol(self):
        """Standalone dispatcher accepts HostExecutionBridge metadata kwargs."""
        from dcc_mcp_3dsmax.dispatcher import MaxStandaloneDispatcher

        dispatcher = MaxStandaloneDispatcher()
        result = dispatcher.dispatch_callable(
            lambda value: value + 1,
            41,
            affinity="main",
            action_name="unit",
            skill_name="test",
        )
        assert result == 42


class TestSidecar:
    """Test structured sidecar dispatch and bridge plumbing."""

    def test_sidecar_server_logs_to_default_file(self, tmp_path, monkeypatch, capsys):
        """Sidecar stdout/stderr are captured in a default operator-visible log."""
        from dcc_mcp_3dsmax import max_bootstrap

        binary = tmp_path / ("dcc-mcp-server.exe" if os.name == "nt" else "dcc-mcp-server")
        binary.write_text("stub", encoding="utf-8")
        log_dir = tmp_path / "logs"
        captured = {}

        class FakeProcess:
            pid = 4321

            def wait(self, timeout):
                raise subprocess.TimeoutExpired("sidecar", timeout)

            def poll(self):
                return None

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            captured.update(kwargs)
            return FakeProcess()

        monkeypatch.delenv("DCC_MCP_3DSMAX_SIDECAR_LOG", raising=False)
        monkeypatch.setenv("DCC_MCP_3DSMAX_SIDECAR_LOG_DIR", str(log_dir))
        monkeypatch.setattr(max_bootstrap, "_server_binary_path", lambda: binary)
        monkeypatch.setattr(max_bootstrap, "qt_bridge_port", lambda: 9876)
        monkeypatch.setattr(max_bootstrap.subprocess, "Popen", fake_popen)
        max_bootstrap._sidecar_process = None
        max_bootstrap._close_sidecar_log()

        try:
            process = max_bootstrap.start_sidecar_server()
            log_path = Path(captured["stdout"].name)
            assert process.pid == 4321
            assert captured["stderr"] is captured["stdout"]
            assert log_path.parent == log_dir
            assert log_path.name.startswith("dcc-mcp-3dsmax-sidecar.")
            assert log_path.name.endswith(".log")
            assert "--display-name" in captured["cmd"]
            output = capsys.readouterr().out
            assert "dcc-mcp-3dsmax sidecar log:" in output
            assert str(log_path) in output
        finally:
            max_bootstrap._sidecar_process = None
            max_bootstrap._close_sidecar_log()

    def test_sidecar_log_override_keeps_explicit_path(self, tmp_path):
        """DCC_MCP_3DSMAX_SIDECAR_LOG keeps its exact path override semantics."""
        from dcc_mcp_3dsmax.max_bootstrap import _open_sidecar_log

        override = tmp_path / "custom" / "sidecar.log"
        path, handle = _open_sidecar_log({"DCC_MCP_3DSMAX_SIDECAR_LOG": str(override)}, 1234)
        try:
            assert path == override
            assert Path(handle.name) == override
        finally:
            handle.close()

    def test_old_default_sidecar_logs_are_pruned(self, tmp_path):
        """Startup cleanup prunes stale default sidecar logs."""
        from dcc_mcp_3dsmax.max_bootstrap import _prune_sidecar_logs

        old_log = tmp_path / "dcc-mcp-3dsmax-sidecar.old.log"
        fresh_log = tmp_path / "dcc-mcp-3dsmax-sidecar.fresh.log"
        old_log.write_text("old", encoding="utf-8")
        fresh_log.write_text("fresh", encoding="utf-8")
        stale = time.time() - (3 * 24 * 60 * 60)
        os.utime(old_log, (stale, stale))

        _prune_sidecar_logs(tmp_path, retention_days=1)

        assert not old_log.exists()
        assert fresh_log.exists()

    def test_server_binary_path_accepts_rez_style_server_root(self, tmp_path, monkeypatch):
        """Pipeline package roots can provide the sidecar binary without pip install."""
        from dcc_mcp_3dsmax.max_bootstrap import _server_binary_path

        binary_name = "dcc-mcp-server.exe" if os.name == "nt" else "dcc-mcp-server"
        binary = tmp_path / "bin" / binary_name
        binary.parent.mkdir()
        binary.write_text("stub", encoding="utf-8")
        monkeypatch.delenv("DCC_MCP_SERVER_BIN", raising=False)
        monkeypatch.setenv("DCC_MCP_SERVER_ROOT", str(tmp_path))

        assert _server_binary_path() == binary

    def test_server_binary_path_prefers_bundled_payload_over_user_scripts(self, tmp_path, monkeypatch):
        """MZP installs must use the bundled sidecar binary before stale user installs."""
        from dcc_mcp_3dsmax import max_bootstrap

        binary_name = "dcc-mcp-server.exe" if os.name == "nt" else "dcc-mcp-server"
        scripts_dir = "Scripts" if os.name == "nt" else "bin"
        package_root = tmp_path / "installed" / "python"
        package_dir = package_root / "dcc_mcp_3dsmax"
        bundled_binary = package_root / "scripts" / binary_name
        stale_binary = tmp_path / "user-base" / scripts_dir / binary_name
        sysconfig_binary = tmp_path / "sysconfig" / scripts_dir / binary_name
        package_dir.mkdir(parents=True)
        bundled_binary.parent.mkdir(parents=True)
        bundled_binary.write_text("bundled", encoding="utf-8")
        stale_binary.parent.mkdir(parents=True)
        stale_binary.write_text("stale", encoding="utf-8")
        sysconfig_binary.parent.mkdir(parents=True)
        sysconfig_binary.write_text("sysconfig", encoding="utf-8")

        monkeypatch.delenv("DCC_MCP_SERVER_BIN", raising=False)
        monkeypatch.delenv("DCC_MCP_SERVER_ROOT", raising=False)
        monkeypatch.setattr(max_bootstrap, "__file__", str(package_dir / "max_bootstrap.py"))
        monkeypatch.setattr(max_bootstrap.sysconfig, "get_path", lambda name: str(sysconfig_binary.parent))
        monkeypatch.setattr(max_bootstrap.site, "USER_BASE", str(stale_binary.parent.parent), raising=False)
        monkeypatch.setattr(
            max_bootstrap.site,
            "getusersitepackages",
            lambda: str(stale_binary.parent.parent / "Python310" / "site-packages"),
        )

        assert max_bootstrap._server_binary_path() == bundled_binary

    def test_sidecar_dispatch_accepts_script_path_payload(self, tmp_path):
        """Sidecar payloads execute explicit script paths."""
        import json

        from dcc_mcp_3dsmax.sidecar import dispatch_payload

        script = tmp_path / "action_echo.py"
        script.write_text(
            "def main(value=None):\n    return {'success': True, 'data': {'value': value}}\n",
            encoding="utf-8",
        )

        raw = dispatch_payload(
            {
                "script_path": str(script),
                "args": {"value": "ok"},
                "request_id": "r1",
            }
        )
        result = json.loads(raw)
        assert result["success"] is True
        assert result["data"]["value"] == "ok"
        assert result["request_id"] == "r1"

    def test_sidecar_dispatch_resolves_bundled_action_name(self):
        """Bundled action names resolve to their package script path."""
        import json

        from dcc_mcp_3dsmax.sidecar import dispatch_payload

        result = json.loads(
            dispatch_payload(
                {
                    "action": "3dsmax-modeling__create_box",
                    "args": {"width": 10},
                    "request_id": "r2",
                }
            )
        )
        assert result["request_id"] == "r2"
        assert result["action"] == "3dsmax-modeling__create_box"
        assert result.get("status") == "error" or result.get("success") is False

    def test_bridge_http_dispatch_roundtrip(self, tmp_path):
        """Bridge accepts structured dispatch requests over localhost HTTP."""
        import json
        import socket
        import urllib.request

        from dcc_mcp_3dsmax.sidecar.bridge import start_bridge, stop_bridge

        script = tmp_path / "action_echo.py"
        script.write_text("def main(value=None):\n    return {'success': True, 'data': {'value': value}}\n", encoding="utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]

        start_bridge(port)
        try:
            body = json.dumps({"script_path": str(script), "args": {"value": 7}}).encode("utf-8")
            request = urllib.request.Request(
                "http://127.0.0.1:{}/dispatch".format(port),
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                result = json.loads(response.read())
            assert result["success"] is True
            assert result["data"]["value"] == 7
        finally:
            stop_bridge()

    def test_bridge_default_port_is_ephemeral(self, monkeypatch):
        """Bridge picks a random localhost port unless explicitly configured."""
        import os

        from dcc_mcp_3dsmax.sidecar.bridge import ENV_BRIDGE_PORT, start_bridge, stop_bridge

        monkeypatch.delenv(ENV_BRIDGE_PORT, raising=False)
        server = start_bridge()
        try:
            port = int(server.server_address[1])
            assert port > 0
            assert os.environ[ENV_BRIDGE_PORT] == str(port)
        finally:
            stop_bridge()

    def test_qt_bridge_json_line_dispatch(self, tmp_path):
        """The qtserver-compatible bridge dispatches JSON-line requests."""
        import json
        import socket

        from dcc_mcp_3dsmax.sidecar.qt_bridge import start_qt_bridge, stop_qt_bridge

        script = tmp_path / "action_echo.py"
        script.write_text("def main(value=None):\n    return {'success': True, 'data': {'value': value}}\n", encoding="utf-8")

        server = start_qt_bridge()
        port = int(server.server_address[1])
        try:
            payload = {
                "id": "req-1",
                "method": "dispatch",
                "params": {
                    "script_path": str(script),
                    "args": {"value": 13},
                    "request_id": "req-1",
                },
            }
            with socket.create_connection(("127.0.0.1", port), timeout=5) as sock:
                sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
                response = sock.makefile("rb").readline()
            result = json.loads(response)
            assert result["id"] == "req-1"
            assert result["result"]["success"] is True
            assert result["result"]["data"]["value"] == 13
        finally:
            stop_qt_bridge()


class TestMenuIntegration:
    """Test generated 3ds Max menu/callback scripts."""

    def test_menu_script_contains_expected_commands(self):
        """Menu script exposes sidecar lifecycle and admin commands."""
        from dcc_mcp_3dsmax.menu import _menu_script

        script = _menu_script()
        assert 'menuMan.findMenu "DCC MCP"' in script
        assert "DccMcp3dsmax_StartSidecar" in script
        assert "DccMcp3dsmax_StopSidecar" in script
        assert "DccMcp3dsmax_OpenAdmin" in script
        assert "http://127.0.0.1:9765/admin?panel=instances" in script

    def test_shutdown_callback_stops_sidecar_before_max_shutdown(self):
        """Shutdown callback uses the early 3ds Max shutdown notification."""
        from dcc_mcp_3dsmax.menu import _shutdown_callback_script

        script = _shutdown_callback_script()
        assert "#preSystemShutdown" in script
        assert "stop_sidecar_bridge" in script
        assert "persistent:false" in script


class TestSkillMetadata:
    """Test bundled skills follow the dcc-mcp-core 0.17 authoring contract."""

    def test_bundled_tools_have_explicit_contracts(self):
        """Every bundled tool declares execution, affinity, schema, and source."""
        from pathlib import Path

        import yaml

        skills_dir = Path(__file__).resolve().parents[1] / "src" / "dcc_mcp_3dsmax" / "skills"
        for tools_path in skills_dir.glob("*/tools.yaml"):
            data = yaml.safe_load(tools_path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            assert data.get("tools"), tools_path
            for tool in data["tools"]:
                source_file = tool.get("source_file")
                assert source_file, (tools_path, tool.get("name"))
                assert (tools_path.parent / source_file).is_file(), (tools_path, source_file)
                assert tool.get("execution") in {"sync", "async"}, (tools_path, tool.get("name"))
                assert tool.get("affinity") == "main", (tools_path, tool.get("name"))
                assert isinstance(tool.get("input_schema"), dict), (tools_path, tool.get("name"))
                assert "read_only" in tool, (tools_path, tool.get("name"))
                assert "destructive" in tool, (tools_path, tool.get("name"))
                assert "idempotent" in tool, (tools_path, tool.get("name"))

    def test_bundled_skill_frontmatter_has_dcc_mcp_stage(self):
        """Each bundled skill declares host, layer, stage, and tools metadata."""
        from pathlib import Path

        import yaml

        skills_dir = Path(__file__).resolve().parents[1] / "src" / "dcc_mcp_3dsmax" / "skills"
        for skill_path in skills_dir.glob("*/SKILL.md"):
            raw = skill_path.read_text(encoding="utf-8")
            assert raw.startswith("---\n"), skill_path
            frontmatter = raw.split("---", 2)[1]
            metadata = yaml.safe_load(frontmatter)
            dcc_mcp = metadata["metadata"]["dcc-mcp"]
            assert dcc_mcp["dcc"] == "3dsmax"
            assert dcc_mcp["layer"] == "domain"
            assert dcc_mcp["stage"] in {"scene", "authoring"}
            assert dcc_mcp["tools"] == "tools.yaml"


class TestVersion:
    """Test version detection."""

    def test_max_version_label_prefers_clean_product_year(self, monkeypatch):
        """MXS array reprs with embedded quotes collapse to a clean Max year."""
        from dcc_mcp_3dsmax.max_bootstrap import _max_version_label

        class MxsArray:
            values = [26000, 64, 0, 26, 2, 11, 20199, 2024, '".2.11 Security Fix"']

            def __getitem__(self, index):
                return self.values[index]

            def __str__(self):
                return '#(26000, 64, 0, 26, 2, 11, 20199, 2024, ".2.11 Security Fix")'

        pymxs = types.SimpleNamespace(
            runtime=types.SimpleNamespace(
                maxVersion=lambda: MxsArray(),
                productVersion="Autodesk 3ds Max 2024",
            )
        )
        monkeypatch.setitem(sys.modules, "pymxs", pymxs)

        assert _max_version_label() == "2024"

    def test_max_version_label_sanitizes_repr_fallback(self, monkeypatch):
        """Fallback labels never preserve shell-sensitive quotes or newlines."""
        from dcc_mcp_3dsmax.max_bootstrap import _max_version_label

        class BrokenMxsArray:
            def __getitem__(self, index):
                raise TypeError("not a Python sequence")

            def __str__(self):
                return '#(26000, "bad"\n\tlabel)'

        pymxs = types.SimpleNamespace(
            runtime=types.SimpleNamespace(
                maxVersion=lambda: BrokenMxsArray(),
            )
        )
        monkeypatch.setitem(sys.modules, "pymxs", pymxs)

        label = _max_version_label()
        assert '"' not in label
        assert "'" not in label
        assert "\n" not in label
        assert "\t" not in label

    def test_max_version_label_falls_back_to_unknown(self, monkeypatch):
        """Version probe failures produce the stable unknown label."""
        from dcc_mcp_3dsmax.max_bootstrap import _max_version_label

        pymxs = types.SimpleNamespace(
            runtime=types.SimpleNamespace(
                maxVersion=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
            )
        )
        monkeypatch.setitem(sys.modules, "pymxs", pymxs)

        assert _max_version_label() == "unknown"

    def test_version_probe_import(self):
        """Test that version probe can be imported."""
        from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string, is_3dsmax_available

        assert get_3dsmax_version_string is not None
        assert is_3dsmax_available is not None

    def test_version_string_not_crash(self):
        """Test that version detection doesn't crash."""
        from dcc_mcp_3dsmax._version_probe import get_3dsmax_version_string

        # Should return a string (either version or "unknown")
        result = get_3dsmax_version_string()
        assert isinstance(result, str)


class TestCapabilities:
    """Test capabilities module."""

    def test_capabilities_import(self):
        """Test that capabilities can be imported."""
        from dcc_mcp_3dsmax.capabilities import get_3dsmax_capabilities, get_3dsmax_capabilities_dict

        assert get_3dsmax_capabilities is not None
        assert get_3dsmax_capabilities_dict is not None

    def test_get_capabilities_list(self):
        """Test getting capabilities as list."""
        from dcc_mcp_3dsmax.capabilities import get_3dsmax_capabilities

        caps = get_3dsmax_capabilities()
        assert isinstance(caps, list)
        assert len(caps) > 0

    def test_get_capabilities_dict(self):
        """Test getting capabilities as dict."""
        from dcc_mcp_3dsmax.capabilities import get_3dsmax_capabilities_dict

        caps_dict = get_3dsmax_capabilities_dict()
        assert isinstance(caps_dict, dict)
        assert "dcc_name" in caps_dict
        assert caps_dict["dcc_name"] == "3dsmax"
