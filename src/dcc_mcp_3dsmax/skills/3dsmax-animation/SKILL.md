---
name: 3dsmax-animation
description: >-
  Domain skill - set transform keyframes and control viewport animation
  playback in 3ds Max. Use when the user asks to key position, rotation, scale,
  or preview the timeline. Not for rig creation or simulation baking.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max animation keyframe playback timeline transform"
    tags: "3dsmax, animation, keyframe, timeline"
    tools: tools.yaml
---

# 3ds Max Animation Tools

Set transform keyframes and start viewport playback. All tools touch the live
scene through `pymxs`, so they declare `affinity: main`.

Tool contracts live in `tools.yaml`. `set_keyframe` requires an existing node
and a target frame.
