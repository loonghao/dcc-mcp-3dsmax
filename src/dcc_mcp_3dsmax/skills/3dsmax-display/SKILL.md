---
name: 3dsmax-display
description: >-
  Domain skill - manage 3ds Max display layers, node display state, and
  user-defined custom properties.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max display layers hidden frozen wire color object color viewport display mode custom user properties metadata"
    tags: "3dsmax, display, layers, custom-properties, metadata"
    tools: tools.yaml
---

# 3ds Max Display And Metadata Tools

Manage display layers, inspect or change node display state, and read/write
user-defined node properties. Mutating tools require explicit node references
or explicit `use_selection=true` and report changed-node or changed-property
counts.
