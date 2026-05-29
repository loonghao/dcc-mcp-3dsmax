---
name: dcc-mcp-3dsmax-setup
description: |-
  Set up dcc-mcp-3dsmax for an agent or operator: install 3ds Max Python
  dependencies with 3dsmaxpy, generate MCP host configuration, guide the user
  through starting the runtime inside 3ds Max, and run a first live-tool smoke
  prompt.
license: MIT
allowed-tools: Bash Read
metadata:
  dcc-mcp:
    dcc: 3dsmax
    layer: operator
    stage: bootstrap
    version: 1.0.0
    tags:
    - 3dsmax
    - mcp
    - setup
    - 3dsmaxpy
    - sidecar
---
# dcc-mcp-3dsmax setup

Use this skill when a user wants an agent to prepare a machine so any MCP
host can use `dcc-mcp-3dsmax` with Autodesk 3ds Max.

This is an operator skill, not a 3ds Max runtime skill. Do not load it through
the 3ds Max MCP server. Run it from the repository checkout or copy its steps
into another agent's instructions.

3ds Max is Windows-only, so discovery and paths below assume Windows.

If the user says "帮我参考 `loonghao/dcc-mcp-3dsmax/install.md` 去安装", read the
root `install.md` first, then follow this skill.

## Goal

End with:

- `dcc-mcp-3dsmax` and its pip dependencies installed into the target 3ds Max
  `3dsmaxpy` environment.
- An MCP host config snippet that points to the 3ds Max gateway.
- The user guided to start the runtime inside 3ds Max (startup script or the
  `DCC MCP` menu).
- A live smoke prompt that proves the agent can discover and call 3ds Max tools.

## Fast Path

From the repository root, run:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py
```

The script:

1. Finds `3dsmaxpy.exe` from `--maxpy`, `MAX_PY`, `DCC_MCP_3DSMAX_PYTHON`,
   `DCC_MCP_3DSMAX_MAXPY`, `PATH`, or common Autodesk install locations.
2. Installs this checkout into 3ds Max: `3dsmaxpy -m pip install -e .`.
3. Verifies `import dcc_mcp_3dsmax`.
4. Writes a reusable MCP JSON snippet and a smoke prompt under
   `.dcc-mcp/agent-setup/`.

Use PyPI instead of the local checkout when setting up an end-user machine:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py --source pypi
```

If discovery fails, ask the user for the full `3dsmaxpy.exe` path and re-run:

```bash
python skills/dcc-mcp-3dsmax-setup/scripts/setup_dcc_mcp_3dsmax.py --maxpy "C:\Program Files\Autodesk\3ds Max 2025\3dsmaxpy.exe"
```

## MCP Configuration

The shared gateway is the preferred default. Configure the MCP host with:

```json
{
  "mcpServers": {
    "3dsmax": {
      "url": "http://127.0.0.1:9765/mcp"
    }
  }
}
```

Each 3ds Max instance also listens on its own random localhost port; connect
hosts to the gateway URL rather than the ephemeral per-instance port.

When editing an existing MCP config, preserve unrelated servers. Merge only the
`3dsmax` server entry unless the user asks for a different server name.

## User Hand-Off: Start the Runtime in 3ds Max

After pip setup and MCP JSON generation, tell the user to start the runtime
inside 3ds Max. From the MAXScript Listener:

```maxscript
python.ExecuteFile @"C:\path\to\dcc-mcp-3dsmax\examples\start_sidecar_bridge.py"
```

Once the runtime has started once, the installed `DCC MCP` menu offers a
`Start Server` command. Both call `dcc_mcp_3dsmax.main()` and register the
instance with the gateway at `http://127.0.0.1:9765/mcp`.

## First Live Smoke Prompt

Ask the MCP host to run this prompt after 3ds Max is open and the runtime is
started:

```text
Use the 3ds Max MCP server. First call dcc_capability_manifest with loaded_only=false.
Then load the 3dsmax-modeling skill, create a sphere named mcp_setup_smoke_sphere
with radius 50, and tell me the MCP URL and created node name.
Use typed tools where available and avoid execute_python unless no typed tool fits.
```

Expected behavior:

- The agent discovers capabilities without dumping every schema.
- The agent loads `3dsmax-modeling`.
- The agent calls `3dsmax_modeling__create_sphere`.
- The new node appears in the 3ds Max scene.

## Troubleshooting

- `3dsmaxpy` not found: ask for the exact 3ds Max version and the full
  `3dsmaxpy.exe` path (e.g. `C:\Program Files\Autodesk\3ds Max 2025\3dsmaxpy.exe`).
- Pip bootstrap fails: run `3dsmaxpy -m ensurepip --upgrade`, then repeat install.
- MCP connection refused: 3ds Max is not running, the runtime is not started, or
  the host is not pointing at the gateway URL `http://127.0.0.1:9765/mcp`.
- Tool missing: call `dcc_capability_manifest` or `search_skills`, then
  `load_skill("<skill-name>")`.
- Runtime started but hangs: check the MAXScript Listener output, firewall /
  localhost rules, and whether a blocking 3ds Max dialog is open.
