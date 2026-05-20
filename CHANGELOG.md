# Changelog

## [0.1.2](https://github.com/loonghao/dcc-mcp-3dsmax/compare/v0.1.1...v0.1.2) (2026-05-20)


### Features

* align 3dsmax sidecar with latest core ([a626fa0](https://github.com/loonghao/dcc-mcp-3dsmax/commit/a626fa06d7f0368401c4666d4b4459b0bc5aafa0))


### Bug Fixes

* tighten 3dsmax sidecar startup ([3b78607](https://github.com/loonghao/dcc-mcp-3dsmax/commit/3b78607c38a52f644176c7ef2415fa147447a4a6))

## [0.1.1](https://github.com/loonghao/dcc-mcp-3dsmax/compare/v0.1.0...v0.1.1) (2026-05-17)


### Features

* add max-dev-build-link-core-win (align with Maya/Blender) ([de06a52](https://github.com/loonghao/dcc-mcp-3dsmax/commit/de06a521352862aba5bcabe08905c80bef3db281))
* align with dcc-mcp-core 0.17.2 API (add diagnostics/execution options) ([2d220ad](https://github.com/loonghao/dcc-mcp-3dsmax/commit/2d220ad00fe4c85168764af3ca32372774b8557e))
* initial 3ds max adapter ([e3f2175](https://github.com/loonghao/dcc-mcp-3dsmax/commit/e3f2175a5faa124b74f9bf0d37d29bed9be4a034))

## [0.1.0] - 2026-05-16

### Added
- Initial release of dcc-mcp-3dsmax
- Basic MCP server implementation for 3ds Max
- Version detection via `pymxs.runtime.maxVersion()`
- Skill management (discover, load, unload)
- Environment variable configuration
- Basic API helpers for skill development
- Example `3dsmax-scene` skill
