dcc-mcp-3dsmax - 3ds Max Animation Tools
=============================================

Keyframe animation tools for 3ds Max using pymxs.

Actions
-------

### action_set_keyframe

Set a keyframe on an object's transform or property.

**Parameters**

| Name       | Type   | Default     | Description                      |
|------------|--------|-------------|----------------------------------|
| node_name  | string | Required    | Node name to animate             |
| time       | float  | Required    | Frame time                       |
| property   | string | "position"  | Property to keyframe             |
| value      | array  | None        | Value [x,y,z] for position/rotation/scale |

**Returns**

`dict` with `success`, `node_name`, `time`.

### action_play_animation

Play the animation in the viewport.

**Parameters**

| Name       | Type   | Default     | Description                      |
|------------|--------|-------------|----------------------------------|
| from_frame | float  | None        | Start frame (None = current)      |
| to_frame   | float  | None        | End frame (None = animation end)  |

**Returns**

`dict` with `success`.

Examples
--------

.. code-block:: python

    from dcc_mcp_3dsmax.api import with_max, get_runtime

    @with_max
    def set_position_key(node_name, frame, x, y, z):
        rt = get_runtime()
        obj = rt.getNodeByName(node_name)
        rt.animate(obj.position, frame)
        obj.position = rt.point3(x, y, z)
        rt.setKey(obj.position, frame)

Elicitation
-----------

- ``node_name`` — must exist in scene.

Affinity
--------

All actions declare ``affinity: main`` (must run on 3ds Max main thread).
