---
name: 3dsmax-geometry-io
description: >-
  Domain skill - validate geometry files and run host-native geometry import
  and export operations in Autodesk 3ds Max. Use for FBX/OBJ/3DS import checks,
  FBX import, FBX export, OBJ export, and structured import/export stats.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max geometry import export FBX OBJ 3DS file validation selected scene"
    tags: "3dsmax, geometry, io, import, export, fbx, obj"
    tools: tools.yaml
---

# 3ds Max Geometry I/O Skill

Validate geometry paths and run host-native import/export operations through
`pymxs`. Tool contracts live in `tools.yaml`; import/export tools declare
`affinity: main` because they call the 3ds Max file I/O APIs.

Use the validation tool before import to check supported formats and file
existence. Use the FBX and OBJ tools for explicit export behavior, including
selected-only versus whole-scene export and overwrite handling. Import tools
return created node identities, warnings, and recoverable failure details.
