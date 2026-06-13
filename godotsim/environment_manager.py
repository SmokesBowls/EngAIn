"""
Environment Manager — Orchestrates terrain generation from ZONJ scenes.

Authority chain:
    ZONJ scene → terrain_profile → Blender MCP → Generated GLB → Godot mount
"""
import asyncio
import httpx
from typing import Dict, Any, Optional

class EnvironmentManager:
    def __init__(self, mcp_url: str = "http://127.0.0.1:8000"):
        self.mcp_url = mcp_url
        self.generated_terrains: Dict[str, Dict[str, Any]] = {}
        self.session_id: Optional[str] = None
    
    async def initialize_session(self) -> bool:
        """Initialize MCP session with Blender server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/mcp",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2025-03-26",
                            "capabilities": {},
                            "clientInfo": {"name": "engain-runtime", "version": "1.0.0"}
                        }
                    },
                    timeout=10.0
                )
                
                # Extract session ID from response headers
                self.session_id = response.headers.get("mcp-session-id")
                if self.session_id:
                    print(f"[ENV_MANAGER] MCP session initialized: {self.session_id}")
                    return True
                return False
        except Exception as e:
            print(f"[ENV_MANAGER] Failed to initialize MCP session: {e}")
            return False
    
    async def generate_scene_environment(
        self,
        scene_id: str,
        scene_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate terrain for a scene from ZONJ data.
        
        Returns:
            {
                "status": "complete",
                "mesh_path": "/path/to/generated.glb",
                "terrain_profile": "coastal"
            }
        """
        if not self.session_id:
            if not await self.initialize_session():
                return None
        
        # Extract terrain profile from ZONJ
        terrain_profile = self._infer_terrain_profile(scene_data)
        print(f"[ENV_MANAGER] Scene {scene_id} -> profile {terrain_profile}")
        
        # Generate terrain via Blender MCP
        mesh_path = await self._generate_terrain_via_mcp(
            scene_id=scene_id,
            terrain_profile=terrain_profile
        )
        
        if mesh_path:
            result = {
                "status": "complete",
                "mesh_path": mesh_path,
                "terrain_profile": terrain_profile,
                "scene_id": scene_id
            }
            self.generated_terrains[scene_id] = result
            print(f"[ENV_MANAGER] ✅ Generated terrain: {mesh_path}")
            return result
        
        return None
    
    def _infer_terrain_profile(self, scene_data: Dict[str, Any]) -> str:
        """Extract terrain profile from ZONJ scene segments."""
        segments = scene_data.get("=segments", [])
        for seg in segments:
            where = seg.get("where", "").lower()
            if any(word in where for word in ["coast", "beach", "shore", "ocean"]):
                return "coastal"
            elif any(word in where for word in ["forest", "wood", "tree"]):
                return "forest"
            elif any(word in where for word in ["volcano", "lava", "crater"]):
                return "volcanic"
            elif any(word in where for word in ["mountain", "peak", "cliff"]):
                return "mountain"
        
        return "generic"
    
    async def _generate_terrain_via_mcp(
        self,
        scene_id: str,
        terrain_profile: str
    ) -> Optional[str]:
        """Send terrain generation code to Blender via MCP."""
        
        # Build Blender Python code for terrain generation
        terrain_code = self._build_terrain_code(scene_id, terrain_profile)
        
        # Execute code in Blender
        result = await self._mcp_call("blender_execute_code", {"code": terrain_code})
        if not result:
            return None
        
        # Export to GLB
        output_path = f"/tmp/engain/{scene_id}_{terrain_profile}.glb"
        export_code = f"""
import bpy
bpy.ops.object.select_all(action='DESELECT')
for obj in bpy.context.scene.objects:
    if obj.name.startswith('terrain_'):
        obj.select_set(True)
bpy.ops.export_scene.gltf(
    filepath="{output_path}",
    export_format='GLB',
    use_selection=True
)
print("[BLENDER_MCP] Exported terrain to {output_path}")
"""
        
        export_result = await self._mcp_call("blender_execute_code", {"code": export_code})
        if not export_result:
            return None
        
        return output_path
    
    def _build_terrain_code(self, scene_id: str, terrain_profile: str) -> str:
        """Build Blender Python code for terrain generation."""
        
        code = f"""
import bpy
import math
import random

# Clear existing terrain
for obj in bpy.context.scene.objects:
    if obj.name.startswith('terrain_'):
        bpy.data.objects.remove(obj, do_unlink=True)

# Terrain profile: {terrain_profile}
"""
        
        if terrain_profile == "coastal":
            code += self._coastal_terrain_code()
        elif terrain_profile == "forest":
            code += self._forest_terrain_code()
        elif terrain_profile == "volcanic":
            code += self._volcanic_terrain_code()
        else:
            code += self._generic_terrain_code()
        
        code += f"""
# Name and tag
terrain_obj.name = "terrain_{scene_id.replace('.', '_')}"
terrain_obj["scene_id"] = "{scene_id}"
terrain_obj["terrain_profile"] = "{terrain_profile}"
print("[BLENDER_MCP] Generated {terrain_profile} terrain for {scene_id}")
"""
        
        return code
    
    def _coastal_terrain_code(self) -> str:
        return """
# Coastal: beach + cliffs + water
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object

bpy.ops.object.modifier_add(type='SUBSURF')
terrain_obj.modifiers["Subdivision"].levels = 4
bpy.ops.object.modifier_apply(modifier="Subdivision")

random.seed(42)
for poly in terrain_obj.data.polygons:
    x, y, z = poly.center
    if x > 20:
        height = random.uniform(5, 15)
    elif x < -20:
        height = random.uniform(-0.5, 0.5)
    else:
        height = random.uniform(0, 5) * (x + 20) / 40
    
    for vert_idx in poly.vertices:
        terrain_obj.data.vertices[vert_idx].co.z = height

terrain_obj.data.update()

# Water plane
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.3))
water = bpy.context.active_object
water.name = "water_coastal"
"""
    
    def _forest_terrain_code(self) -> str:
        return """
# Forest: rolling hills
bpy.ops.mesh.primitive_grid_add(x_subdivisions=50, y_subdivisions=50, size=100)
terrain_obj = bpy.context.active_object

random.seed(42)
for vert in terrain_obj.data.vertices:
    x, y, z = vert.co
    height = (
        math.sin(x * 0.1) * 2 +
        math.cos(y * 0.15) * 1.5 +
        random.uniform(-0.5, 0.5)
    )
    vert.co.z = height

terrain_obj.data.update()
"""
    
    def _volcanic_terrain_code(self) -> str:
        return """
# Volcanic: crater + lava flows
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object

bpy.ops.object.modifier_add(type='SUBSURF')
terrain_obj.modifiers["Subdivision"].levels = 5
bpy.ops.object.modifier_apply(modifier="Subdivision")

random.seed(42)
for vert in terrain_obj.data.vertices:
    x, y, z = vert.co
    dist = math.sqrt(x*x + y*y)
    
    if dist < 15:
        height = -5 + (dist / 15) * 3
    elif dist < 25:
        height = 8 - (dist - 15) * 0.8
    else:
        height = max(0, 8 - (dist - 15) * 0.3) + random.uniform(-0.5, 0.5)
    
    vert.co.z = height

terrain_obj.data.update()
"""
    
    def _generic_terrain_code(self) -> str:
        return """
# Generic flat terrain
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object
"""
    
    async def _mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make MCP tool call to Blender server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/mcp",
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "Mcp-Session-Id": self.session_id
                    },
                    json={
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": {
                                "params": arguments
                            }
                        }
                    },
                    timeout=60.0
                )
                
                response.raise_for_status()

                try:
                    data = response.json()
                except Exception:
                    data = {
                        "status": "ok",
                        "raw": response.text,
                    }

                if isinstance(data, dict) and "error" in data:
                    print(f"[ENV_MANAGER] MCP tool error: {data['error']}")
                    return None

                return data

        except Exception as e:
            print(f"[ENV_MANAGER] MCP call failed for {tool_name}: {e}")
            return None
