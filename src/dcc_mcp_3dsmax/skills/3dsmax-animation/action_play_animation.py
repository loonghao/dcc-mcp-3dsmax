"""Play animation in 3ds Max viewport."""

# Import future modules
from __future__ import annotations

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, with_max


@with_max
def main(from_frame: int = None, to_frame: int = None) -> dict:
    """Play animation in the viewport.

    Returns
    -------
    dict
        The action response.
    """
    rt = get_runtime()

    # Set time range if specified
    if from_frame is not None:
        rt.sliderTime = from_frame

    # Play animation
    rt.playAnimation()

    return {
        "success": True,
        "message": "Animation playback started",
        "data": {
            "from_frame": from_frame,
            "to_frame": to_frame,
        },
    }
