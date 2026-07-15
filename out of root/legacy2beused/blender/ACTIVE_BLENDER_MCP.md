# Active Blender MCP Selection

ACTIVE_BLENDER_MCP = blender/blender-open-mcp-main

ARCHIVE_REFERENCE = /mnt/data-drive/EngAIn_Recovery/01_ARCHIVES_ORIGINAL/blender-open-mcp

Decision:
- Active EngAIn Blender MCP work uses `blender/blender-open-mcp-main`.
- The archived `blender-open-mcp` copy is reference-only.
- The archive contains usable client-side files:
  - `client.py`
  - `src/blender_open_mcp/client_entry.py`
- Client files are not active by existence alone.
- Do not merge by similar filenames.
- Do not copy archive client files into active Blender MCP unless a gate proves the active lane needs a client.

Active import proof:
- `blender_open_mcp.server` imports from active path.
- `blender_open_mcp.mcp_server` imports from active path.

Archive import proof:
- `blender_open_mcp.server` imports with `PYTHONPATH=src`.
- `blender_open_mcp.client_entry` imports with `PYTHONPATH=src`.
- `client` imports from archive root.

Authority:
- Blender MCP may execute Blender-facing bridge work.
- Blender MCP does not authorize EngAIn runtime truth.
- EngAInOS must authorize any world/runtime-facing packet before it is accepted.
