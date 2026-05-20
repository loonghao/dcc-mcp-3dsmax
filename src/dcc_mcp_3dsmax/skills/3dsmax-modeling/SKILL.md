---
name: 3dsmax-modeling
description: >-
  Domain skill - create basic 3ds Max primitive geometry on the main thread.
  Use when adding boxes, spheres, cylinders, or planes. Not for mesh editing,
  import/export, or material assignment.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max create box sphere cylinder plane primitive geometry modeling"
    tags: "3dsmax, modeling, geometry, primitives"
    tools: tools.yaml
---

# 3ds Max Modeling Tools

Create basic primitive geometry in the current 3ds Max scene. All tools touch
the live scene through `pymxs`, so they declare `affinity: main`.

Tool contracts live in `tools.yaml`. Scripts keep host API access behind
adapter helpers so metadata discovery remains safe outside 3ds Max.
