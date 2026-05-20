r"""Example: Start dcc-mcp-3dsmax server inside 3ds Max.

Run this script in the 3ds Max MAXScript Listener:

    python.ExecuteFile @"G:\PycharmProjects\github\dcc-mcp-3dsmax\examples\start_server.py"
"""

# Import future modules
from __future__ import annotations

# Import local modules
import dcc_mcp_3dsmax

# Start the MCP server
print("Starting dcc-mcp-3dsmax server...")
server = dcc_mcp_3dsmax.start_server()

print(f"Server started on port {server.port}")
print("MCP gateway: http://127.0.0.1:9765/mcp")

# Discover available skills
print("\nDiscovering skills...")
count = server.discover_skills()
print(f"Discovered {count} skills")

print("\nServer is running. Press Ctrl+C to stop.")

# Keep the server running (in real usage, 3ds Max will keep the process alive)
try:
    import time

    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping server...")
    dcc_mcp_3dsmax.stop_server()
    print("Server stopped.")
