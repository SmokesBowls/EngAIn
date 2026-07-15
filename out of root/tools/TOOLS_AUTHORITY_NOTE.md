# Tools Authority Note

TOOLS_STATUS = NON_CANON_TEST_TOOL_SOURCE

Meaning:
- `tools/` is not active EngAIn runtime authority.
- `tools/` is not EngAInOS truth.
- `tools/` is not the final EngAIn tool package.
- Current files are test tools, smoke scripts, one-off repair scripts, old patch scripts, helper scripts, and model/tool bundle material.
- We may test these files.
- Passing tests does not make them canon.
- Failing tests does not automatically mean delete.
- EngAInOS validators/gates must authorize any runtime-facing packet.

Future direction:
- After organization, build a deliberate EngAIn test/tool package.
- The final package should behave like a Swiss army knife:
  - small named tools
  - clear commands
  - no hidden authority
  - no silent mutation
  - no bundled `.venv` pollution
  - no model bundles mixed with helper scripts
  - each tool has true/false proof

Package rule:
- Current `tools/` is source material only.
- Canon tools must be promoted into the future package deliberately.
- One-off patch scripts must be reviewed before promotion.
- `tools/kimodo/` is a separate model/tool bundle and should not be treated as ordinary test tooling.

Known current test result:
- Clean shell syntax: TRUE
- Clean Python syntax: FALSE
- Broken file: `tools/patch_upbge_bridge_use_position_v1.py`

Do not delete blindly.
Do not promote tool output by filename or presence.
Do not scan `.venv` as project source.
