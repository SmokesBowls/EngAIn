# filename: mcp_servers/mcp_hub_asgi.py
from starlette.applications import Starlette
from starlette.routing import Mount

from mcp_servers.engain_runtime_mcp import mcp as runtime_mcp
from mcp_servers.engain_blender_mcp import mcp as blender_mcp

# IMPORTANT: pass mount_path into sse_app so the internal /messages path is correct when mounted.
app = Starlette(
    routes=[
        Mount("/runtime", app=runtime_mcp.sse_app("/runtime")),
        Mount("/blender", app=blender_mcp.sse_app("/blender")),
    ]
)
