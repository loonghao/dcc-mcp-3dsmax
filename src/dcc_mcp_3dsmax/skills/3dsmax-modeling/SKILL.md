dcc-mcp-3dsmax - 3ds Max Modeling Tools
=============================================

Basic modeling operations for 3ds Max using pymxs.

Actions
-------

### action_create_box

Create a box primitive.

**Parameters**

| Name   | Type  | Default | Description        |
|--------|--------|---------|--------------------|
| width  | float  | 100.0   | Box width           |
| height | float  | 100.0   | Box height          |
| depth  | float  | 100.0   | Box depth           |
| name   | string | None    | Optional node name  |

**Returns**

`dict` with `success`, `node_name`, `object_id`.

### action_create_sphere

Create a sphere primitive.

**Parameters**

| Name   | Type  | Default | Description        |
|--------|--------|---------|--------------------|
| radius | float  | 50.0    | Sphere radius       |
| name   | string | None    | Optional node name  |

**Returns**

`dict` with `success`, `node_name`, `object_id`.

### action_create_cylinder

Create a cylinder primitive.

**Parameters**

| Name    | Type  | Default | Description        |
|---------|--------|---------|--------------------|
| radius  | float  | 30.0    | Cylinder radius     |
| height  | float  | 100.0   | Cylinder height     |
| name    | string | None    | Optional node name  |

**Returns**

`dict` with `success`, `node_name`, `object_id`.

### action_create_plane

Create a plane primitive.

**Parameters**

| Name      | Type  | Default | Description        |
|-----------|--------|---------|--------------------|
| width     | float  | 100.0   | Plane width         |
| length    | float  | 100.0   | Plane length        |
| name      | string | None    | Optional node name  |

**Returns**

`dict` with `success`, `node_name`, `object_id`.

Examples
--------

.. code-block:: python

    from dcc_mcp_3dsmax import max_success
    from dcc_mcp_3dsmax.api import with_max, get_runtime

    @with_max
    def create_box(width=100.0, height=100.0, depth=100.0, name=None):
        rt = get_runtime()
        box_obj = rt.Box(width=width, height=height, depth=depth)
        if name:
            box_obj.name = name
        return max_success(
            "Created box",
            node_name=str(box_obj.name),
            object_id=int(box_obj.handle) if hasattr(box_obj, 'handle') else None,
        )

Elicitation
-----------

- ``name`` — if provided, the created node is renamed.

Affinity
--------

All actions declare ``affinity: main`` (must run on 3ds Max main thread).
