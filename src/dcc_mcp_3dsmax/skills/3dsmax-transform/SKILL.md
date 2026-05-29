---
name: 3dsmax-transform
description: >-
  Domain skill - move nodes and set positions in the current Autodesk 3ds Max
  scene. Use when the user asks to place, move, offset, translate, or position
  objects. Not for creating new geometry.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max transform position move translate place object node"
    tags: "3dsmax, transform, position, move, translate"
    tools: tools.yaml
---

# 3ds Max Transform Tools

Set absolute positions or apply relative offsets to existing scene nodes.
All tools touch the 3ds Max scene and run on the main thread.
