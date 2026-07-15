#!/usr/bin/env python3
"""
Standalone MCP server that connects to Blender via socket.
Run this with: python mcp_server.py --host 127.0.0.1 --port 8000
"""
import argparse
import json
import socket
import time
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("Blender MCP Server")

# Socket connection to Blender
blender_socket = None
blender_host = "localhost"
blender_port = 9876

def connect_to_blender():
    """Connect to the Blender socket server"""
    global blender_socket
    try:
        blender_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        blender_socket.settimeout(5.0)  # 5 second timeout
        blender_socket.connect((blender_host, blender_port))
        return True
    except Exception as e:
        print(f"Failed to connect to Blender: {e}")
        blender_socket = None
        return False

def send_to_blender(command: Dict[str, Any]) -> Dict[str, Any]:
    """Send a command to Blender and get response"""
    global blender_socket
    
    # Try to connect if not connected
    if blender_socket is None:
        if not connect_to_blender():
            return {"status": "error", "message": "Failed to connect to Blender"}
    
    try:
        # Send command
        command_json = json.dumps(command)
        blender_socket.sendall(command_json.encode('utf-8'))
        
        # Receive response
        response_data = blender_socket.recv(4096)
        response = json.loads(response_data.decode('utf-8'))
        return response
        
    except Exception as e:
        print(f"Error communicating with Blender: {e}")
        # Try to reconnect
        try:
            blender_socket.close()
        except:
            pass
        blender_socket = None
        return {"status": "error", "message": f"Communication error: {str(e)}"}

# Define MCP tools
@mcp.tool()
def get_scene_info() -> str:
    """Get information about the current Blender scene"""
    response = send_to_blender({"type": "get_scene_info"})
    return json.dumps(response, indent=2)

@mcp.tool()
def create_object(
    object_type: str = "CUBE",
    name: str = None,
    location_x: float = 0.0,
    location_y: float = 0.0,
    location_z: float = 0.0
) -> str:
    """Create a new object in Blender
    
    Args:
        object_type: Type of object (CUBE, SPHERE, CYLINDER, PLANE)
        name: Optional name for the object
        location_x: X position
        location_y: Y position
        location_z: Z position
    """
    response = send_to_blender({
        "type": "create_object",
        "params": {
            "type": object_type,
            "name": name,
            "location": [location_x, location_y, location_z]
        }
    })
    return json.dumps(response, indent=2)

@mcp.tool()
def render_scene(
    output_path: str = None,
    resolution_x: int = 1920,
    resolution_y: int = 1080
) -> str:
    """Render the current scene in Blender
    
    Args:
        output_path: Path to save the rendered image (optional)
        resolution_x: Width of the render
        resolution_y: Height of the render
    """
    params = {
        "resolution_x": resolution_x,
        "resolution_y": resolution_y
    }
    if output_path:
        params["output_path"] = output_path
    
    response = send_to_blender({
        "type": "render_scene",
        "params": params
    })
    return json.dumps(response, indent=2)

@mcp.tool()
def get_object_info(name: str) -> str:
    """Get detailed information about a specific object
    
    Args:
        name: Name of the object to get info for
    """
    response = send_to_blender({
        "type": "get_object_info",
        "params": {
            "name": name
        }
    })
    return json.dumps(response, indent=2)

@mcp.tool()
def list_objects() -> str:
    """List all objects in the current scene"""
    scene_info = send_to_blender({"type": "get_scene_info"})
    if scene_info.get("status") == "success":
        objects = scene_info.get("result", {}).get("objects", [])
        return json.dumps({"objects": objects}, indent=2)
    return json.dumps(scene_info, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Blender MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--blender-host", default="localhost", help="Blender socket host")
    parser.add_argument("--blender-port", type=int, default=9876, help="Blender socket port")
    
    args = parser.parse_args()
    
    # Update blender connection settings
    global blender_host, blender_port
    blender_host = args.blender_host
    blender_port = args.blender_port
    
    print(f"Starting Blender MCP server on {args.host}:{args.port}")
    print(f"Connecting to Blender at {blender_host}:{blender_port}")
    
    # Try to connect to Blender
    if not connect_to_blender():
        print("Warning: Could not connect to Blender. Make sure:")
        print("1. Blender is running with the BlenderMCP addon enabled")
        print("2. The MCP server is started in Blender (in the sidebar)")
        print("3. The port matches (default: 9876)")
    
    # Run MCP server
    mcp.run(
        transport="streamable-http",
        host=args.host,
        port=args.port
    )

if __name__ == "__main__":
    main()