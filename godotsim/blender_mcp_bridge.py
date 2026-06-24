# godotsim/blender_mcp_bridge.py
"""
Bridge between EngAIn ZONJ scenes and Blender MCP terrain generation.

Flow:
    ZONJ scene → terrain_profile → Blender MCP → Generated GLB → Godot mount
"""
import asyncio
import httpx
from typing import Dict, Any

class BlenderMCPBridge:
    def __init__(self, mcp_url: str = "http://127.0.0.1:8000"):
        self.mcp_url = mcp_url
    
    async def generate_terrain_from_zonj(
        self,
        scene_id: str,
        terrain_profile: str,
        scene_data: Dict[str, Any],
        output_path: str = None,
    ) -> Dict[str, Any]:
        """
        Generate terrain geometry from ZONJ scene data.
        
        Args:
            scene_id: Scene identifier (e.g., "scene.001_the_ethereal_vigil")
            terrain_profile: Inferred profile (e.g., "coastal", "forest")
            scene_data: Full ZONJ scene document
            output_path: Where to save generated GLB
        
        Returns:
            {
                "status": "complete",
                "mesh_path": "user://blender/scene.001_coastal.glb",
                "object_name": "terrain_scene_001"
            }
        """
        output_path = output_path or f"user://blender/{scene_id}_{terrain_profile}.glb"
        
        # Build Blender prompt from ZONJ data
        prompt = self._build_terrain_prompt(scene_id, terrain_profile, scene_data)
        
        # Send to Blender MCP
        async with httpx.AsyncClient() as client:
            # Step 1: Generate terrain geometry
            result = await client.post(
                f"{self.mcp_url}/tool",
                json={
                    "name": "blender_execute_code",
                    "arguments": {"code": prompt}
                },
                timeout=60.0
            )
            
            if result.status_code != 200:
                return {"status": "failed", "error": result.text}
            
            # Step 2: Export to GLB
            export_result = await client.post(
                f"{self.mcp_url}/tool",
                json={
                    "name": "blender_execute_code",
                    "arguments": {
                        "code": f"""
import bpy
bpy.ops.export_scene.gltf(
    filepath="{output_path}",
    export_format='GLB',
    use_selection=True
)
"""
                    }
                },
                timeout=30.0
            )
            
            return {
                "status": "complete",
                "mesh_path": output_path,
                "object_name": f"terrain_{scene_id}",
                "blender_response": result.json()
            }
    
    def _build_terrain_prompt(
        self,
        scene_id: str,
        terrain_profile: str,
        scene_data: Dict[str, Any]
    ) -> str:
        """
        Convert ZONJ scene data into Blender Python code for terrain generation.
        
        This is where you customize per terrain_profile.
        """
        
        # Extract scene features from ZONJ
        segments = scene_data.get("=segments", [])
        entities = scene_data.get("entities_present", [])
        
        # Build terrain generation code
        code = f"""
import bpy
import math
from mathutils import Vector

# Clear existing terrain
for obj in bpy.context.scene.objects:
    if obj.name.startswith('terrain_'):
        bpy.data.objects.remove(obj, do_unlink=True)

# Terrain profile: {terrain_profile}
"""
        
        # Profile-specific generation
        if terrain_profile == "coastal":
            code += self._generate_coastal_terrain()
        elif terrain_profile == "forest":
            code += self._generate_forest_terrain()
        elif terrain_profile == "volcanic":
            code += self._generate_volcanic_terrain()
        else:
            code += self._generate_generic_terrain()
        
        # Name the terrain object
        code += f"""
# Name and tag
terrain_obj.name = "terrain_{scene_id.replace('.', '_')}"
terrain_obj["scene_id"] = "{scene_id}"
terrain_obj["terrain_profile"] = "{terrain_profile}"

print(f"[BLENDER_MCP] Generated terrain for {scene_id} ({terrain_profile})")
"""
        
        return code
    
    def _generate_coastal_terrain(self) -> str:
        return """
# Coastal terrain: beach + cliffs + water
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object

# Subdivide for detail
bpy.ops.object.modifier_add(type='SUBSURF')
terrain_obj.modifiers["Subdivision"].levels = 4
bpy.ops.object.modifier_apply(modifier="Subdivision")

# Add height variation (cliffs on one side)
import random
random.seed(42)
for poly in terrain_obj.data.polygons:
    x, y, z = poly.center
    if x > 20:  # Cliff side
        height = random.uniform(5, 15)
    elif x < -20:  # Beach side
        height = random.uniform(-0.5, 0.5)
    else:  # Transition
        height = random.uniform(0, 5) * (x + 20) / 40
    
    for vert_idx in poly.vertices:
        terrain_obj.data.vertices[vert_idx].co.z = height

# Add water plane
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.3))
water = bpy.context.active_object
water.name = "water_coastal"
water_mat = bpy.data.materials.new(name="WaterMat")
water_mat.use_nodes = True
water_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.3, 0.5, 1.0)
water_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.7
water.data.materials.append(water_mat)
"""
    
    def _generate_forest_terrain(self) -> str:
        return """
# Forest terrain: rolling hills
bpy.ops.mesh.primitive_grid_add(x_subdivisions=50, y_subdivisions=50, size=100)
terrain_obj = bpy.context.active_object

import random
import math
random.seed(42)

# Rolling hills with Perlin-like noise
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
    
    def _generate_volcanic_terrain(self) -> str:
        return """
# Volcanic terrain: crater + lava flows
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object

bpy.ops.object.modifier_add(type='SUBSURF')
terrain_obj.modifiers["Subdivision"].levels = 5
bpy.ops.object.modifier_apply(modifier="Subdivision")

import math
import random
random.seed(42)

# Central crater
for vert in terrain_obj.data.vertices:
    x, y, z = vert.co
    dist = math.sqrt(x*x + y*y)
    
    if dist < 15:  # Crater
        height = -5 + (dist / 15) * 3
    elif dist < 25:  # Crater rim
        height = 8 - (dist - 15) * 0.8
    else:  # Slope down
        height = max(0, 8 - (dist - 15) * 0.3) + random.uniform(-0.5, 0.5)
    
    vert.co.z = height

terrain_obj.data.update()

# Add lava glow (emission material in crater)
lava_mat = bpy.data.materials.new(name="LavaMat")
lava_mat.use_nodes = True
lava_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 0.2, 0.0, 1.0)
lava_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.3, 0.0, 1.0)
lava_mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 5.0
terrain_obj.data.materials.append(lava_mat)
"""
    
    def _generate_generic_terrain(self) -> str:
        return """
# Generic flat terrain
bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, 0))
terrain_obj = bpy.context.active_object
"""