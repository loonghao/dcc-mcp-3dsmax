dcc-mcp-3dsmax - 3ds Max Material Tools
============================================

Material creation and application tools for 3ds Max using pymxs.

Actions
-------

### action_create_standard_material

Create a Standard material.

**Parameters**

| Name         | Type   | Default        | Description                |
|--------------|---------|----------------|----------------------------|
| name        | string  | "StandardMat"  | Material name               |
| diffuse     | array   | [1,1,1]       | Diffuse color [R,G,B]      |
| specular    | array   | [1,1,1]       | Specular color [R,G,B]     |
| glossiness  | float   | 10.0           | Glossiness (0-100)         |

**Returns**

`dict` with `success`, `material_name`.

### action_apply_material

Apply a material to selected objects or specified objects.

**Parameters**

| Name         | Type   | Default        | Description                |
|--------------|---------|----------------|----------------------------|
| material_name| string  | Required       | Material name to apply      |
| node_names   | array   | None           | Target nodes (None = selected)|

**Returns**

`dict` with `success`, `applied_count`.

Examples
--------

.. code-block:: python

    from dcc_mcp_3dsmax.api import with_max, get_runtime

    @with_max
    def create_red_material(name="RedMat"):
        rt = get_runtime()
        mat = rt.StandardMaterial(name=name)
        mat.diffuse = rt.color(255, 0, 0)
        return {"success": True, "material_name": name}

Elicitation
-----------

- ``node_names`` — if not provided, applies to current selection.

Affinity
--------

All actions declare ``affinity: main`` (must run on 3ds Max main thread).
