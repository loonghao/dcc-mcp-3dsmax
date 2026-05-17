"""Play animation in 3ds Max viewport."""

# Import future modules
from __future__ import annotations

# Import third-party modules
from dcc_mcp_core.actions import ActionRequest, ActionResponse

# Import local modules
from dcc_mcp_3dsmax.api import get_runtime, max_success, with_max


@with_max
def run(request: ActionRequest) -> ActionResponse:
    """Play animation in the viewport.

    Parameters
    ----------
    request : ActionRequest
        The action request containing parameters.

    Returns
    -------
    ActionResponse
        The action response.
    """
    params = request.params or {}
    from_frame = params.get("from_frame", None)
    to_frame = params.get("to_frame", None)

    rt = get_runtime()

    # Set time range if specified
    if from_frame is not None:
        rt.sliderTime = from_frame

    # Play animation
    rt.playAnimation()

    return ActionResponse(
        success=True,
        message="Animation playback started",
        data={
            "from_frame": from_frame,
            "to_frame": to_frame,
        },
    )
