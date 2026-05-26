# Bundled 3ds Max Skills

This index lists the default skill families shipped with `dcc-mcp-3dsmax` and
the atomic tools each family exports. Tool names are shown as they are exposed
through the DCC-MCP skill loader.

| Skill family | Stage | Exported tools |
| --- | --- | --- |
| `3dsmax-scene` | scene | `3dsmax-scene__get_scene_info` |
| `3dsmax-modeling` | authoring | `3dsmax-modeling__create_box`, `3dsmax-modeling__create_sphere`, `3dsmax-modeling__create_cylinder`, `3dsmax-modeling__create_plane` |
| `3dsmax-materials` | authoring | `3dsmax-materials__create_standard_material`, `3dsmax-materials__apply_material` |
| `3dsmax-animation` | authoring | `3dsmax-animation__set_keyframe`, `3dsmax-animation__play_animation` |
| `3dsmax-scripting` | authoring | `3dsmax-scripting__execute_python`, `3dsmax-scripting__execute_maxscript`, `3dsmax-scripting__run_python_check`, `3dsmax-scripting__list_runtime_symbols`, `3dsmax-scripting__inspect_runtime_symbol`, `3dsmax-scripting__list_macros`, `3dsmax-scripting__resolve_node_reference`, `3dsmax-scripting__reload_adapter_module` |

Every bundled tool declares:

- a concrete `source_file` inside its skill directory
- explicit `input_schema` and `output_schema` objects
- `execution`, `affinity`, and `timeout_hint_secs`
- MCP safety annotations for read-only, destructive, idempotent, and open-world behavior

The bundled skill contract is enforced by the test suite and does not require
an interactive 3ds Max session.
