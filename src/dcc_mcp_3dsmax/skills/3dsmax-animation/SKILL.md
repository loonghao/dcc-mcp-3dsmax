---
name: 3dsmax-animation
description: >-
  Domain skill - inspect timeline settings, query and edit transform keyframes,
  bake simple animation curves, exchange curve data, and control viewport
  playback in 3ds Max.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max animation keyframe playback timeline transform controllers bake curve import export"
    tags: "3dsmax, animation, keyframe, timeline, curves"
    tools: tools.yaml
---

# 3ds Max Animation Tools

Inspect timeline state, set transform keyframes, edit key metadata, exchange
simple curve data, bake transform samples, and start viewport playback. All
tools touch the live scene through `pymxs`, so they declare `affinity: main`.

Tool contracts live in `tools.yaml`. Mutating tools require explicit targets or
explicit `use_selection=true`, and return changed-key counts where applicable.
