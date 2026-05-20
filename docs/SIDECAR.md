# 3ds Max Sidecar Bridge

The sidecar bootstrap runs inside Autodesk 3ds Max. It exposes local bridges
for main-thread scene edits, starts `dcc-mcp-server.exe sidecar`, and registers
a 3ds Max instance with the shared gateway.

## Start Inside 3ds Max

Run:

```maxscript
python.ExecuteFile @"C:\path\to\dcc-mcp-3dsmax\examples\start_sidecar_bridge.py"
```

By default both internal bridges ask the OS for free localhost ports. Startup
prints the HTTP dispatch endpoint and the JSON-line `qtserver://` endpoint used
by `dcc-mcp-server.exe sidecar`, for example:

```text
dcc-mcp-3dsmax bridge listening on http://127.0.0.1:<random-port>/dispatch
dcc-mcp-3dsmax qt bridge listening on qtserver://127.0.0.1:<random-port>
dcc-mcp-3dsmax sidecar server started pid=<pid> (...\dcc-mcp-server.exe)
```

Override the bridge port with `DCC_MCP_3DSMAX_BRIDGE_PORT` when a fixed bridge
port is needed. The public MCP gateway is stable at:

```text
http://127.0.0.1:9765/mcp
```

After startup, `http://127.0.0.1:9765/admin?panel=instances` should list a
`3dsmax` instance on a random localhost port.

The sidecar uses the default `dcc-mcp-server` registry. Set
`DCC_MCP_REGISTRY_DIR` externally only when the whole local gateway stack needs
to share a non-default registry directory.

## 3ds Max Menu

Startup installs a `DCC MCP` menu in the main menu bar with:

- `Start Sidecar`
- `Stop Sidecar`
- `Open Gateway Admin`
- `Print Status`

To install only the menu without starting the sidecar:

```maxscript
python.Execute "import dcc_mcp_3dsmax; dcc_mcp_3dsmax.install_menu(); dcc_mcp_3dsmax.install_shutdown_callback()"
```

The shutdown callback uses `#preSystemShutdown` and calls
`dcc_mcp_3dsmax.stop_sidecar_bridge()`, which terminates the sidecar process and
stops both localhost bridges.

## Dispatch Payload

Send a registered action name:

```json
{
  "action": "3dsmax-modeling__create_box",
  "args": {
    "width": 100,
    "height": 100,
    "depth": 100
  },
  "request_id": "example-1"
}
```

For lower-level tests, send an explicit script path:

```json
{
  "script_path": "C:\\path\\to\\action_create_box.py",
  "args": {
    "width": 100
  },
  "request_id": "example-2"
}
```

## Health

```text
GET http://127.0.0.1:<random-port>/health
```

Returns bridge state, queue size, and whether a 3ds Max main-thread pump is
active.

## Threading Model

The HTTP listener runs on a background thread. When `pymxs` is available, the
bridge queues requests and drains them from a hidden MaxScript timer, keeping
scene edits on the 3ds Max UI thread. Outside 3ds Max, requests execute inline
so unit tests can exercise the protocol without Autodesk binaries.
