"""Set render output options."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dcc_mcp_3dsmax._render_utils import set_render_output
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(output_path: Optional[str] = None, save_file: Optional[bool] = None) -> Dict[str, Any]:
    """Set common render output options."""
    return set_render_output(get_runtime(), output_path=output_path, save_file=save_file)
