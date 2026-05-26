---
name: 3dsmax-rigging
description: >-
  Domain skill - create and inspect host-native 3ds Max rig helpers, bones,
  constraints, path helpers, and common deformer modifiers.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max rigging helper bone joint chain constraint deformer skin modifier path helper"
    tags: "3dsmax, rigging, bones, constraints, deformers"
    tools: tools.yaml
---

# 3ds Max Rigging Tools

Create lightweight rig helper primitives, build simple bone chains, inspect
constraints and deformer state, and apply or remove common host-native
modifiers. Tools operate on explicit node references or explicit
`use_selection=true` and declare `affinity: main` for 3ds Max scene access.

Character-system helpers are limited to availability checks so optional biped
or CAT support can fail gracefully when the host installation does not expose
those APIs.
