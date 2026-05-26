---
name: 3dsmax-validation
description: >-
  Domain skill - run generic 3ds Max scene and asset-readiness validation
  checks before export, render, or handoff.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max validation asset readiness naming transform pivot topology material texture UV overlap"
    tags: "3dsmax, validation, asset-readiness, topology, uv"
    tools: tools.yaml
---

# 3ds Max Validation Tools

Run read-only asset-readiness checks over explicit nodes, selection, or the
current scene. Validators return per-node pass, fail, or warning results with
remediation hints and aggregate summaries that can be composed into larger
workflows.

These tools use generic checks only: naming, transforms, pivots, topology,
smoothing groups, materials, texture paths, UV channels, and UV overlaps.
