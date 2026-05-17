"""Basic tests for dcc-mcp-3dsmax."""

# Import built-in modules
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

    def test_import_server(self):
        """Test importing the server module."""
        from dcc_mcp_3dsmax.server import MaxMcpServer, MaxServerOptions

        assert MaxMcpServer is not None
        assert MaxServerOptions is not None

    def test_import_api(self):
        """Test importing the api module."""
        from dcc_mcp_3dsmax.api import max_success, max_error, with_max

        assert max_success is not None
        assert max_error is not None
        assert with_max is not None


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
