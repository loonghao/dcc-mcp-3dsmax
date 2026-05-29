---
name: 3dsmax-scripting
description: >-
  Domain skill - execute ad hoc Python or MaxScript in the current Autodesk
  3ds Max session. Use when typed tools cannot express a custom scene operation
  or diagnostic probe. Not for routine primitive creation or transforms when
  dedicated tools exist.
license: MIT
compatibility: "dcc-mcp-core 0.17+, 3ds Max 2024+"
metadata:
  dcc-mcp:
    dcc: 3dsmax
    version: "1.0.0"
    layer: domain
    stage: authoring
    search-hint: "3ds Max execute Python MaxScript custom code script pymxs runtime"
    tags: "3dsmax, scripting, python, maxscript, custom-code"
    tools: tools.yaml
---

# 3ds Max Scripting Tools

Run custom Python or MaxScript on the 3ds Max main thread when no typed tool
fits the task. Prefer dedicated domain tools for common scene operations.
