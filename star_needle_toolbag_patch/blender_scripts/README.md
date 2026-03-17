How to run / test (two straightforward modes):

A) Local “stdio mode” (most local MCP clients launch the server as a subprocess; stdio is a standard MCP transport).
You typically just point your client at the command to start each script, and it handles stdin/stdout.

B) HTTP mode for easy inspection (Streamable HTTP is the other standard transport).
The Python SDK docs show connecting to an MCP endpoint like http://localhost:8000/mcp (for their examples/inspector flow).
To do that with these servers:

Runtime server:

MCP_TRANSPORT=streamable-http uv run --with mcp mcp_servers/engain_runtime_mcp.py

Git server:

ENGAIN_REPO_ROOT=/absolute/path/to/your/repo MCP_TRANSPORT=streamable-http uv run --with mcp mcp_servers/engain_git_mcp.py

Notes that matter:

If you use stdio transport, do not print() debug text to stdout or you’ll corrupt JSON-RPC; stderr logging is safe.

The runtime server is allowlist-locked (ENGAIN_ALLOW_PATHS) so the agent can’t “invent” endpoints and start poking random routes.

If you tell me what the two MCP servers are meant to control (runtime only + filesystem, runtime + vault, runtime + git, etc.), I can align the tool surface exactly to that shape without adding extra knobs.
