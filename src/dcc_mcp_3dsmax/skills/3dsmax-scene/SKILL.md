# 3ds Max Scene Info Skill

Query information about the current 3ds Max scene.

## Metadata

```yaml
name: 3dsmax-scene
description: Query 3ds Max scene information (nodes, stats, units)
dcc:
  - 3dsmax
tags:
  - scene
  - info
  - query
```

## Actions

### action_get_scene_info.py

Get basic information about the current scene.

**Parameters**: None

**Returns**:
- `node_count`: Number of nodes in scene
- `scene_name`: Current scene file name
- `units`: Current scene units

### action_list_nodes.py

List all nodes in the scene with optional filtering.

**Parameters**:
- `type` (optional): Filter by node type (e.g., "Geometry", "Light", "Camera")
- `name_contains` (optional): Filter by name substring

**Returns**:
- `nodes`: List of node names matching criteria
- `count`: Number of nodes found
