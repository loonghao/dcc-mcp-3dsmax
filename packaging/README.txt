DCC-MCP-3dsMax - Drag-and-Drop MZP Installer
============================================

This package installs the dcc-mcp-3dsmax Python adapter and bundled
dcc-mcp-core runtime files into the current user's 3ds Max scripts folder.

Installation
------------
1. Start 3ds Max.
2. Drag dcc-mcp-3dsmax-<version>-win64.mzp into the 3ds Max viewport.
3. Restart 3ds Max after the installer reports success.

The installer copies files to:
  <user scripts>/dcc_mcp_3dsmax

It also writes a startup MaxScript that adds the installed Python package
directory to sys.path on launch.

Smoke Test
----------
Open the MAXScript Listener and run:

  python.Execute "import dcc_mcp_3dsmax; print(dcc_mcp_3dsmax.__version__)"

To start the MCP server:

  python.Execute "import dcc_mcp_3dsmax; dcc_mcp_3dsmax.start_server()"

Uninstall
---------
Delete these paths from your user 3ds Max scripts folders:

  <user scripts>/dcc_mcp_3dsmax
  <user startup scripts>/dcc_mcp_3dsmax_startup.ms

For more information:
https://github.com/loonghao/dcc-mcp-3dsmax
