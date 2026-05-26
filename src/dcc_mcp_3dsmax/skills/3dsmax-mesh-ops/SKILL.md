---
name: 3dsmax-mesh-ops
description: >-
  Domain skill - inspect and mutate 3ds Max mesh topology, cleanup, smoothing
  groups, modifier stacks, proxy meshes, and explicit normals through atomic
  host-native operations.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max mesh cleanup topology normals smoothing groups modifiers triangulate attach detach proxy subdivision"
    tags: "3dsmax, mesh, topology, cleanup, normals, smoothing, modifiers"
    tools: tools.yaml
---

# 3ds Max Mesh Operations Skill

Inspect mesh topology and apply focused mesh cleanup, subdivision, proxy, attach,
detach, smoothing group, and normal operations through `pymxs`.

Mutating tools require explicit node names, stable object handles, or an
explicit `use_selection=true` argument. They return changed-node summaries so
agents can report what changed without relying on opaque macros.
