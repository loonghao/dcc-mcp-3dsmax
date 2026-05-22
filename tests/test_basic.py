"""Basic tests for dcc-mcp-3dsmax."""

# Import built-in modules
import os
import subprocess
import sys
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
