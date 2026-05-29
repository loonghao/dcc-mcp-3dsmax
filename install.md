# dcc-mcp-3dsmax Agent Install

Use this page when an agent is asked to install or configure
`loonghao/dcc-mcp-3dsmax` for Autodesk 3ds Max.

3ds Max is Windows-only, so all paths and discovery below assume Windows.

## Agent Instruction

If the user says "帮我参考 loonghao/dcc-mcp-3dsmax/install.md 去安装",
do this:

1. Read `skills/dcc-mcp-3dsmax-setup/SKILL.md`.
2. Run the setup script from the repository root.
3. Help the user start the runtime inside 3ds Max (startup script or `DCC MCP` menu).
4. Configure the MCP host with the generated Streamable HTTP JSON.
5. Run the smoke prompt to prove the connection works.

## One Command

From the repository root:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py
```

For an end-user install from PyPI instead of this checkout:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py --source pypi
```

If `3dsmaxpy.exe` is not auto-detected:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py --maxpy "C:\Program Files\Autodesk\3ds Max 2025\3dsmaxpy.exe"
```

## 3ds Max Load Step

After the script finishes, the user must start the runtime inside 3ds Max.
Either start it from the MAXScript Listener:

```maxscript
python.ExecuteFile @"C:\path\to\dcc-mcp-3dsmax\examples\start_sidecar_bridge.py"
```

Or, once the runtime has been started once, use the installed menu:

```text
DCC MCP > Start Server
```

The runtime registers the 3ds Max instance with the stable gateway. Both the
startup script and the menu call `dcc_mcp_3dsmax.main()`.

The shared gateway exposes MCP at:

```text
http://127.0.0.1:9765/mcp
```

Each 3ds Max instance also listens on its own random localhost port. Connect
MCP hosts to the gateway URL; the direct per-instance port is ephemeral.

## MCP Config

Use this JSON for Cursor, Claude Desktop, or any MCP Streamable HTTP host:

```json
{
  "mcpServers": {
    "3dsmax": {
      "url": "http://127.0.0.1:9765/mcp"
    }
  }
}
```

The setup script also writes a config snippet and a smoke prompt under:

```text
.dcc-mcp/agent-setup/
```
