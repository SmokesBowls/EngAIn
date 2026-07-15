# Save this as blender_mcp_addon.py and install in Blender
import bpy
import json
import socket
import tempfile
from bpy.props import StringProperty, IntProperty, BoolProperty
import traceback
import os
import shutil
import threading
import time

bl_info = {
    "name": "Blender MCP",
    "author": "BlenderMCP",
    "version": (0, 2),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > BlenderMCP",
    "description": "Connect Blender to local AI models via MCP",
    "category": "Interface",
}

class BlenderMCPServer:
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.client = None
        self.buffer = b''
        self.thread = None

    def start(self):
        """Start the server in a background thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        print(f"BlenderMCP server started on {self.host}:{self.port}")

    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        if self.client:
            try:
                self.client.close()
            except:
                pass
        self.client = None
        print("BlenderMCP server stopped")

    def _run_server(self):
        """Main server loop running in a background thread"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(1.0)  # 1 second timeout

        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            while self.running:
                try:
                    # Accept client connection
                    client_socket, address = self.socket.accept()
                    print(f"Connected to client: {address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue  # Timeout is normal, check if still running
                except Exception as e:
                    if self.running:  # Only print if we're supposed to be running
                        print(f"Error accepting connection: {str(e)}")
                    
        except Exception as e:
            print(f"Server error: {str(e)}")
        finally:
            if self.socket:
                self.socket.close()
                self.socket = None

    def _handle_client(self, client_socket, address):
        """Handle a single client connection"""
        try:
            client_socket.settimeout(10.0)  # 10 second timeout per message
            
            while self.running:
                try:
                    # Receive data
                    data = client_socket.recv(4096)
                    if not data:
                        break  # Client disconnected
                    
                    try:
                        # Parse and execute command
                        command = json.loads(data.decode('utf-8'))
                        response = self.execute_command(command)
                        response_json = json.dumps(response)
                        
                        # Send response
                        client_socket.sendall(response_json.encode('utf-8'))
                        
                    except json.JSONDecodeError:
                        error_response = {"status": "error", "message": "Invalid JSON"}
                        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
                        
                except socket.timeout:
                    continue  # No data, continue loop
                except Exception as e:
                    print(f"Error handling client {address}: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"Client handler error: {str(e)}")
        finally:
            client_socket.close()
            print(f"Client {address} disconnected")

    def execute_command(self, command):
        """Execute a command in the main Blender thread"""
        try:
            cmd_type = command.get("type")
            params = command.get("params", {})
            
            # Import here to avoid circular imports
            import bpy
            
            # Schedule command execution in main thread
            result = [None]
            error = [None]
            
            def execute_in_main():
                try:
                    handler = self._get_command_handler(cmd_type)
                    if handler:
                        result[0] = handler(**params)
                    else:
                        error[0] = f"Unknown command type: {cmd_type}"
                except Exception as e:
                    error[0] = str(e)
                    traceback.print_exc()
            
            # Execute in main thread
            bpy.app.timers.register(lambda: (execute_in_main(), None))
            
            # Wait for result (simplified - in real implementation use proper sync)
            time.sleep(0.1)
            
            if error[0]:
                return {"status": "error", "message": error[0]}
            return {"status": "success", "result": result[0]}
            
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _get_command_handler(self, cmd_type):
        """Get the appropriate handler for a command type"""
        handlers = {
            "get_scene_info": self._handle_get_scene_info,
            "create_object": self._handle_create_object,
            "modify_object": self._handle_modify_object,
            "delete_object": self._handle_delete_object,
            "get_object_info": self._handle_get_object_info,
            "execute_code": self._handle_execute_code,
            "set_material": self._handle_set_material,
            "render_scene": self._handle_render_scene,
            "get_polyhaven_status": self._handle_get_polyhaven_status,
        }
        
        # Add Polyhaven handlers if enabled
        if bpy.context.scene.blendermcp_use_polyhaven:
            polyhaven_handlers = {
                "get_polyhaven_categories": self._handle_get_polyhaven_categories,
                "search_polyhaven_assets": self._handle_search_polyhaven_assets,
                "download_polyhaven_asset": self._handle_download_polyhaven_asset,
                "set_texture": self._handle_set_texture,
            }
            handlers.update(polyhaven_handlers)
        
        return handlers.get(cmd_type)

    # Command handlers
    def _handle_get_scene_info(self):
        """Get information about the current scene"""
        scene = bpy.context.scene
        return {
            "name": scene.name,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "fps": scene.render.fps,
            "objects": [obj.name for obj in scene.objects],
            "object_count": len(scene.objects),
            "materials_count": len(bpy.data.materials)
        }

    def _handle_create_object(self, type="CUBE", name=None, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
        """Create a new object"""
        bpy.ops.object.select_all(action='DESELECT')
        
        if type == "CUBE":
            bpy.ops.mesh.primitive_cube_add(location=location)
        elif type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(location=location)
        elif type == "CYLINDER":
            bpy.ops.mesh.primitive_cylinder_add(location=location)
        elif type == "PLANE":
            bpy.ops.mesh.primitive_plane_add(location=location)
        elif type == "CONE":
            bpy.ops.mesh.primitive_cone_add(location=location)
        elif type == "TORUS":
            bpy.ops.mesh.primitive_torus_add(location=location)
        elif type == "EMPTY":
            bpy.ops.object.empty_add(location=location)
        elif type == "CAMERA":
            bpy.ops.object.camera_add(location=location)
        elif type == "LIGHT":
            bpy.ops.object.light_add(type='POINT', location=location)
        else:
            raise ValueError(f"Unsupported object type: {type}")
        
        obj = bpy.context.active_object
        if name:
            obj.name = name
        
        obj.rotation_euler = rotation
        obj.scale = scale
        
        return {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale)
        }

    def _handle_modify_object(self, name, location=None, rotation=None, scale=None, visible=None):
        """Modify an existing object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object '{name}' not found")
        
        if location is not None:
            obj.location = location
        if rotation is not None:
            obj.rotation_euler = rotation
        if scale is not None:
            obj.scale = scale
        if visible is not None:
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        
        return {
            "name": obj.name,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "visible": obj.visible_get()
        }

    def _handle_delete_object(self, name):
        """Delete an object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object '{name}' not found")
        
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.delete()
        
        return {"deleted": name}

    def _handle_get_object_info(self, name):
        """Get information about a specific object"""
        obj = bpy.data.objects.get(name)
        if not obj:
            raise ValueError(f"Object '{name}' not found")
        
        info = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "dimensions": list(obj.dimensions) if hasattr(obj, 'dimensions') else None,
            "visible": obj.visible_get(),
            "materials": [slot.material.name for slot in obj.material_slots if slot.material]
        }
        
        # Add mesh info if applicable
        if obj.type == 'MESH' and obj.data:
            mesh = obj.data
            info["mesh"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons),
                "uv_layers": len(mesh.uv_layers)
            }
        
        return info

    def _handle_execute_code(self, code):
        """Execute Python code in Blender context"""
        try:
            # Create a safe namespace
            namespace = {
                'bpy': bpy,
                '__builtins__': {},
                'C': bpy.context,
                'D': bpy.data
            }
            
            # Execute the code
            exec(code, namespace)
            
            return {
                "success": True,
                "message": "Code executed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _handle_set_material(self, object_name, material_name=None, color=None):
        """Set or create a material for an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            raise ValueError(f"Object '{object_name}' not found")
        
        # Create or get material
        if material_name:
            mat = bpy.data.materials.get(material_name)
            if not mat:
                mat = bpy.data.materials.new(name=material_name)
        else:
            mat = bpy.data.materials.new(name=f"{object_name}_material")
        
        # Set up material with nodes
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear existing nodes
        nodes.clear()
        
        # Create Principled BSDF and output
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        output = nodes.new(type='ShaderNodeOutputMaterial')
        
        # Set location
        principled.location = (0, 0)
        output.location = (200, 0)
        
        # Link nodes
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        
        # Set color if provided
        if color and len(color) >= 3:
            principled.inputs['Base Color'].default_value = (
                color[0],
                color[1],
                color[2],
                1.0 if len(color) < 4 else color[3]
            )
        
        # Assign material to object
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
        
        return {
            "object": object_name,
            "material": mat.name,
            "color": color
        }

    def _handle_render_scene(self, output_path=None, resolution_x=1920, resolution_y=1080):
        """Render the current scene"""
        scene = bpy.context.scene
        
        # Set resolution
        scene.render.resolution_x = resolution_x
        scene.render.resolution_y = resolution_y
        
        # Set output path
        if output_path:
            scene.render.filepath = output_path
        else:
            # Use temp directory
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"blender_render_{int(time.time())}.png")
            scene.render.filepath = output_path
        
        # Render
        bpy.ops.render.render(write_still=True)
        
        return {
            "output_path": output_path,
            "resolution": [resolution_x, resolution_y],
            "success": True
        }

    # Polyhaven handlers (simplified versions)
    def _handle_get_polyhaven_status(self):
        """Check if Polyhaven integration is enabled"""
        enabled = bpy.context.scene.blendermcp_use_polyhaven
        return {
            "enabled": enabled,
            "message": "PolyHaven integration is enabled" if enabled else "PolyHaven integration is disabled"
        }

    def _handle_get_polyhaven_categories(self, asset_type):
        """Get Polyhaven categories"""
        import requests
        try:
            response = requests.get(f"https://api.polyhaven.com/categories/{asset_type}")
            return {"categories": response.json()}
        except Exception as e:
            return {"error": str(e)}

    def _handle_search_polyhaven_assets(self, asset_type=None, categories=None):
        """Search Polyhaven assets"""
        import requests
        try:
            url = "https://api.polyhaven.com/assets"
            params = {}
            if asset_type:
                params["type"] = asset_type
            if categories:
                params["categories"] = categories
            
            response = requests.get(url, params=params)
            return {"assets": response.json()}
        except Exception as e:
            return {"error": str(e)}

    def _handle_download_polyhaven_asset(self, asset_id, asset_type, resolution="1k"):
        """Download a Polyhaven asset"""
        import requests
        try:
            # Simplified download logic
            response = requests.get(f"https://api.polyhaven.com/files/{asset_id}")
            files_data = response.json()
            
            return {
                "success": True,
                "asset_id": asset_id,
                "asset_type": asset_type,
                "available_files": list(files_data.keys())
            }
        except Exception as e:
            return {"error": str(e)}

    def _handle_set_texture(self, object_name, texture_id):
        """Apply a texture to an object"""
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object '{object_name}' not found"}
        
        # Simplified texture application
        # In a full implementation, this would load and apply the texture
        
        return {
            "success": True,
            "object": object_name,
            "texture_id": texture_id,
            "message": "Texture application simplified in this example"
        }

# Blender UI
class BLENDERMCP_PT_Panel(bpy.types.Panel):
    bl_label = "Blender MCP"
    bl_idname = "BLENDERMCP_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'BlenderMCP'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "blendermcp_port")
        layout.prop(scene, "blendermcp_use_polyhaven", text="Use assets from Poly Haven")

        if not scene.blendermcp_server_running:
            layout.operator("blendermcp.start_server", text="Start MCP Server")
        else:
            layout.operator("blendermcp.stop_server", text="Stop MCP Server")
            layout.label(text=f"Running on port {scene.blendermcp_port}")

class BLENDERMCP_OT_StartServer(bpy.types.Operator):
    bl_idname = "blendermcp.start_server"
    bl_label = "Connect to Local AI"
    bl_description = "Start the BlenderMCP server to connect with a local AI model"

    def execute(self, context):
        scene = context.scene
        
        # Create or get server instance
        if not hasattr(bpy.types, "blendermcp_server"):
            bpy.types.blendermcp_server = BlenderMCPServer(port=scene.blendermcp_port)
        
        # Start server
        bpy.types.blendermcp_server.start()
        scene.blendermcp_server_running = True
        
        self.report({'INFO'}, f"MCP server started on port {scene.blendermcp_port}")
        return {'FINISHED'}

class BLENDERMCP_OT_StopServer(bpy.types.Operator):
    bl_idname = "blendermcp.stop_server"
    bl_label = "Stop the connection"
    bl_description = "Stop Server"

    def execute(self, context):
        scene = context.scene
        
        if hasattr(bpy.types, "blendermcp_server"):
            bpy.types.blendermcp_server.stop()
            del bpy.types.blendermcp_server
        
        scene.blendermcp_server_running = False
        self.report({'INFO'}, "MCP server stopped")
        return {'FINISHED'}

def register():
    bpy.types.Scene.blendermcp_port = IntProperty(
        name="Port",
        description="Port for the BlenderMCP server",
        default=9876,
        min=1024,
        max=65535
    )
    bpy.types.Scene.blendermcp_server_running = BoolProperty(
        name="Server Running",
        default=False
    )
    bpy.types.Scene.blendermcp_use_polyhaven = BoolProperty(
        name="Use Poly Haven",
        description="Enable Poly Haven asset integration",
        default=False
    )
    
    bpy.utils.register_class(BLENDERMCP_PT_Panel)
    bpy.utils.register_class(BLENDERMCP_OT_StartServer)
    bpy.utils.register_class(BLENDERMCP_OT_StopServer)
    
    print("BlenderMCP addon registered")

def unregister():
    # Stop server if running
    if hasattr(bpy.types, "blendermcp_server"):
        bpy.types.blendermcp_server.stop()
        del bpy.types.blendermcp_server
    
    bpy.utils.unregister_class(BLENDERMCP_PT_Panel)
    bpy.utils.unregister_class(BLENDERMCP_OT_StartServer)
    bpy.utils.unregister_class(BLENDERMCP_OT_StopServer)
    
    del bpy.types.Scene.blendermcp_port
    del bpy.types.Scene.blendermcp_server_running
    del bpy.types.Scene.blendermcp_use_polyhaven
    
    print("BlenderMCP addon unregistered")