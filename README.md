# dcc-mcp-3dsmax

3ds Max plugin for the DCC Model Context Protocol (MCP) ecosystem — embeds a Streamable HTTP MCP server directly inside 3ds Max.

> **Status:** This project is under active development. APIs, packaging, and 3ds Max integration details may change quickly while the adapter tracks the latest `dcc-mcp-core` releases.

## Features

- **Embedded MCP Server**: No external gateway or IPC required
- **Progressive Skill Loading**: Discover skills without loading them immediately
- **Gateway Failover**: Multi-instance support with automatic gateway election
- **Job Persistence**: SQLite-based job storage for long-running operations
- **Prometheus Metrics**: Optional `/metrics` endpoint for monitoring

## Installation

```bash
pip install dcc-mcp-3dsmax
```

## Quickstart (inside 3ds Max MAXScript Listener)

```python
import dcc_mcp_3dsmax

# Start with default port (auto-gateway: first instance wins 8765)
server = dcc_mcp_3dsmax.start_server()

# Progressive loading — discover skills without loading them immediately
n = server.discover_skills()        # scan paths, register tool metadata
server.load_skill("3dsmax-scene")  # lazy-load a specific skill

dcc_mcp_3dsmax.stop_server()
```

## Skill Development

Create a skill with `SKILL.md` metadata file and Python scripts:

```python
# my_skill/action_create_box.py
from dcc_mcp_3dsmax.api import max_success, with_max

@with_max
def execute(params: dict) -> dict:
    import pymxs
    rt = pymxs.runtime

    width = params.get("width", 100.0)
    height = params.get("height", 100.0)
    depth = params.get("depth", 100.0)

    box_obj = rt.Box(width=width, height=height, depth=depth)
    return max_success("Created box", object_name=str(box_obj))
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DCC_MCP_3DSMAX_METRICS` | Enable Prometheus `/metrics` endpoint | `0` |
| `DCC_MCP_3DSMAX_JOB_STORAGE` | Path to SQLite job database | platform default |
| `DCC_MCP_3DSMAX_DISABLE_EXECUTE_PYTHON` | Disable `execute_python` tool | `0` |
| `DCC_MCP_3DSMAX_DISABLE_ARBITRARY_SCRIPT` | Disable all arbitrary script execution | `0` |
| `DCC_MCP_3DSMAX_ENABLE_GATEWAY_FAILOVER` | Enable gateway failover | `1` |
| `DCC_MCP_3DSMAX_SKILL_PATHS` | Extra skill search paths (semicolon-separated) | None |

## Requirements

- 3ds Max 2017 or later (Python 3.x with pymxs support)
- Python >= 3.7
- dcc-mcp-core >= 0.17.5

## License

MIT
