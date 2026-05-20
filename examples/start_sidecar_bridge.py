r"""Start the dcc-mcp-3dsmax sidecar bridge from inside 3ds Max.

Run in MAXScript Listener:

    python.ExecuteFile @"C:\path\to\dcc-mcp-3dsmax\examples\start_sidecar_bridge.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    import dcc_mcp_core  # noqa: F401
    import dcc_mcp_server  # noqa: F401
except ModuleNotFoundError as exc:
    if exc.name not in {"dcc_mcp_core", "dcc_mcp_server"}:
        raise
    print(
        "{} is not installed in this 3ds Max Python. "
        "Run `just max-install-core-win` from the repo, then retry this command."
        .format(exc.name)
    )
    raise

from dcc_mcp_3dsmax.max_bootstrap import start_sidecar_bridge  # noqa: E402

start_sidecar_bridge()
