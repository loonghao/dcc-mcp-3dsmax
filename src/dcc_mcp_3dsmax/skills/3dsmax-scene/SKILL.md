---
name: 3dsmax-scene
description: >-
  Domain skill - query scene-level information from the current Autodesk
  3ds Max session. Use when the user asks about scene name, node count, or
  units. Not for mutating scene content.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: scene
    search-hint: "3ds Max scene info nodes statistics units current file"
    tags: "3dsmax, scene, info, query"
    tools: tools.yaml
---

# 3ds Max Scene Info Skill

Query read-only scene metadata through `pymxs`. Tool contracts live in
`tools.yaml`; scene reads still declare `affinity: main` because they enter the
3ds Max host API.
