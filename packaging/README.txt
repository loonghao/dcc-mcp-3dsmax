DCC-MCP-3dsMax - Drag-and-Drop MZP Installer
============================================

This package installs the dcc-mcp-3dsmax Python adapter plus bundled
dcc-mcp-core and dcc-mcp-server runtime files into the current user's
3ds Max scripts folder.

Installation
------------
1. Start 3ds Max.
2. Drag dcc-mcp-3dsmax-<version>-win64.mzp into the 3ds Max viewport.
3. Restart 3ds Max after the installer reports success.
4. Use the DCC MCP menu to start or stop the sidecar bridge.

The installer copies each payload into an isolated version directory:
  <user scripts>/dcc_mcp_3dsmax/versions/<version-id>

The active version is recorded in:
  <user scripts>/dcc_mcp_3dsmax/current.txt

It also writes a startup MaxScript that adds the installed Python package
directory to sys.path on launch and installs the DCC MCP menu.

Rez / pipeline deployments
--------------------------
The startup script can also use package roots supplied by the launch
environment instead of copied MZP payloads. Set one or more of:

  DCC_MCP_3DSMAX_BOOTSTRAP_PATHS  Semicolon-separated Python import roots.
  DCC_MCP_PYTHONPATHS             Shared semicolon-separated Python import roots.
  DCC_MCP_3DSMAX_ROOT             Adapter package root.
  DCC_MCP_CORE_ROOT               dcc-mcp-core package root.
  DCC_MCP_SERVER_ROOT             dcc-mcp-server package root.
  DCC_MCP_SERVER_BIN              Explicit dcc-mcp-server executable.

For example, a Rez package can point these roots at package-cache paths such as:

  <package-cache>/dcc_mcp_core
  <package-cache>/dcc_mcp_3dsmax
  <package-cache>/dcc_mcp_server

When a root contains a python/, python37/, src/, or package-parent layout, the
startup script adds the appropriate existing directories to sys.path.

Smoke Test
----------
Open the MAXScript Listener and run:

  python.Execute "import dcc_mcp_3dsmax; print(dcc_mcp_3dsmax.__version__)"

To start the sidecar bridge:

  DCC MCP > Start Sidecar

Uninstall
---------
Delete these paths from your user 3ds Max scripts folders:

  <user scripts>/dcc_mcp_3dsmax
  <user startup scripts>/dcc_mcp_3dsmax_startup.ms

For more information:
https://github.com/loonghao/dcc-mcp-3dsmax
