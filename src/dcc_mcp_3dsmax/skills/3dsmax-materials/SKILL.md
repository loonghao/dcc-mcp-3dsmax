---
name: 3dsmax-materials
description: >-
  Domain skill - create and assign 3ds Max Standard materials on the main
  thread. Use when authoring simple materials or assigning existing materials.
  Not for renderer-specific shader graphs.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max material create standard material apply assign diffuse specular"
    tags: "3dsmax, materials, shader, assignment"
    tools: tools.yaml
---

# 3ds Max Material Tools

Create and assign Standard materials in the current scene. All tools touch the
live scene through `pymxs`, so they declare `affinity: main`.

Tool contracts live in `tools.yaml`. `apply_material` uses current selection
when `node_names` is omitted.
