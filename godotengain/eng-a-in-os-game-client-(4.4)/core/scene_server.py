#!/usr/bin/env python3
"""
scene_server.py - HTTP server for scene loading and AP queries

Serves scene data and handles Agnostic Protocol (AP) queries from Godot.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import hashlib
import json
from .scene_loader import SceneLoader, format_for_godot

# ---------------------------------------------------------------------------
# Terrain palette vocabulary -- maps terrain family to pixel colour recipe
# ---------------------------------------------------------------------------

TERRAIN_PALETTES = {
    "beach":    {"top": [135, 206, 235], "bottom": [238, 214, 175],
                 "scatter": [[245, 230, 150], [200, 175, 100]], "label": "Beach Coastal"},
    "forest":   {"top": [34, 139, 34],   "bottom": [20, 80, 20],
                 "scatter": [[100, 180, 60], [60, 120, 30]],    "label": "Forest"},
    "mountain": {"top": [100, 120, 150], "bottom": [80, 70, 60],
                 "scatter": [[130, 110, 90], [160, 150, 140]],  "label": "Mountain"},
    "desert":   {"top": [255, 200, 50],  "bottom": [200, 150, 50],
                 "scatter": [[230, 180, 80], [180, 130, 40]],   "label": "Desert"},
    "tundra":   {"top": [200, 230, 255], "bottom": [170, 200, 220],
                 "scatter": [[220, 240, 255], [150, 180, 200]], "label": "Tundra"},
    "ocean":    {"top": [20, 80, 150],   "bottom": [10, 50, 120],
                 "scatter": [[30, 100, 180], [50, 130, 200]],   "label": "Ocean"},
    "swamp":    {"top": [60, 90, 40],    "bottom": [40, 70, 30],
                 "scatter": [[80, 110, 50], [100, 120, 60]],    "label": "Swamp"},
    "volcano":  {"top": [30, 10, 0],     "bottom": [80, 20, 0],
                 "scatter": [[255, 80, 0], [200, 40, 0]],       "label": "Volcanic"},
    "cave":     {"top": [20, 20, 30],    "bottom": [10, 10, 20],
                 "scatter": [[60, 50, 40], [100, 80, 60]],      "label": "Cave"},
    "default":  {"top": [80, 100, 130],  "bottom": [60, 80, 50],
                 "scatter": [[120, 110, 90], [90, 80, 70]],     "label": "Generic"},
}

# Terrain-specific feature passes inserted between base scatter and entity markers.
# Each entry is a list of pass dicts; seeds are injected at recipe-build time.
#
# Pass vocabulary:
#   h_band             — horizontal colour band (horizon, shoreline, treeline, lava shelf)
#   v_crack            — sinusoidal vertical cracks (lava seams, cliff faces, fissures)
#   tree_silhouette    — trunk + filled-circle canopy silhouettes along treeline
#   ember_scatter      — clustered glow particles (volcanic sparks, fireflies)
#   shoreline_band     — wavy gradient transition band (water/land edge)
#   foam_scatter       — small light clusters near shoreline
#   reed_cluster       — thin vertical reed groups (swamp/wetland)
#   murk_noise         — dense low-visibility scatter (swamp floor)
#   stalactite_silhouette — downward triangular formations from ceiling (cave)
TERRAIN_FEATURES = {
    "volcano":  [
        {"type": "h_band",      "y": 0.50, "thickness": 0.04,  "color": [120, 30, 0]},
        {"type": "v_crack",     "count": 4, "color": [255, 100, 0], "y_start": 0.45, "y_end": 0.95},
        {"type": "ember_scatter","density": 0.04, "spread_radius": 0.3,
         "colors": [[255, 200, 50], [255, 140, 0], [255, 60, 0]]},
    ],
    "beach":    [
        {"type": "shoreline_band","y": 0.55, "waviness": 0.04,
         "palette_gradient": [[80, 160, 200], [200, 220, 240]]},
        {"type": "foam_scatter", "density": 0.04, "cluster_size": 2, "mask_bias": 0.55},
    ],
    "forest":   [
        {"type": "h_band",         "y": 0.45, "thickness": 0.05,  "color": [50, 100, 30]},
        {"type": "tree_silhouette","density": 0.40, "horizon_y": 0.45,
         "colors": [[30, 60, 20], [40, 80, 25], [25, 50, 15]]},
    ],
    "swamp":    [
        {"type": "h_band",      "y": 0.52, "thickness": 0.04,  "color": [40, 80, 30]},
        {"type": "reed_cluster","density": 0.35,
         "colors": [[70, 90, 40], [90, 110, 50], [50, 70, 30]]},
        {"type": "murk_noise",  "density": 0.15,
         "colors": [[50, 70, 35], [40, 60, 25], [60, 80, 40]]},
    ],
    "cave":     [
        {"type": "v_crack",              "count": 5, "color": [70, 60, 50],
         "y_start": 0.0, "y_end": 0.6},
        {"type": "stalactite_silhouette","density": 0.40,
         "colors": [[15, 15, 25], [20, 20, 35]]},
    ],
    "mountain": [
        {"type": "h_band",  "y": 0.40, "thickness": 0.03,  "color": [200, 210, 220]},
        {"type": "v_crack", "count": 3, "color": [80, 90, 100], "y_start": 0.0, "y_end": 0.45},
    ],
    "ocean":    [
        {"type": "h_band",      "y": 0.50, "thickness": 0.08,  "color": [10, 60, 120]},
        {"type": "foam_scatter","density": 0.03, "cluster_size": 2, "mask_bias": 0.50},
    ],
    "desert":   [
        {"type": "h_band",  "y": 0.60, "thickness": 0.03,  "color": [210, 160, 40]},
    ],
    "tundra":   [
        {"type": "h_band",  "y": 0.50, "thickness": 0.04,  "color": [180, 200, 220]},
    ],
}

# Scene-name keywords override the semantic extractor's terrain_family tag
KEYWORD_OVERRIDES = {
    "molten":       "volcano",  "lava":     "volcano",  "fire":     "volcano",
    "inferno":      "volcano",  "magma":    "volcano",  "ember":    "volcano",
    "cinder":       "volcano",  "ashen":    "volcano",
    "frost":        "tundra",   "arctic":   "tundra",   "snow":     "tundra",
    "ice":          "tundra",   "frozen":   "tundra",
    "sand":         "desert",   "dune":     "desert",
    "abyss":        "ocean",    "deep":     "ocean",
    "dungeon":      "cave",     "cavern":   "cave",     "underground": "cave",
    "bog":          "swamp",    "marsh":    "swamp",
    "jungle":       "forest",   "grove":    "forest",   "wood":     "forest",
    "peak":         "mountain", "cliff":    "mountain", "highland": "mountain",
    "summit":       "mountain",
}


def _pass_seed(scene_id: str, pass_type: str) -> int:
    """Stable 31-bit seed from scene_id + pass_type. Same inputs → identical output forever."""
    digest = hashlib.md5(f"{scene_id}:{pass_type}".encode()).digest()
    return int.from_bytes(digest[:4], "little") & 0x7FFFFFFF


def _build_art_recipe(scene_id: str, scene_data: dict) -> dict:
    """Translate scene data into a layered pixel-painting recipe for trixelpixel."""
    # Keyword override takes precedence over semantic extractor tag
    name_lower = scene_id.lower()
    terrain = scene_data.get("terrain_family", "default")
    for keyword, override in KEYWORD_OVERRIDES.items():
        if keyword in name_lower:
            terrain = override
            break

    palette = TERRAIN_PALETTES.get(terrain, TERRAIN_PALETTES["default"])
    entities = scene_data.get("entities", [])

    xs = [e["position"]["x"] for e in entities if "position" in e]
    x_min = min(xs) if xs else 0
    x_max = max(xs) if xs else 1
    x_range = (x_max - x_min) or 1

    entity_markers = [
        {
            "id":   e.get("id", "unknown"),
            "name": e.get("name", "?"),
            "nx":   round((e.get("position", {}).get("x", 0) - x_min) / x_range, 4),
        }
        for e in entities
    ]

    # Inject deterministic seeds into every pass that uses a RNG
    feature_passes = [
        dict(p, seed=p.get("seed", _pass_seed(scene_id, p["type"])))
        for p in TERRAIN_FEATURES.get(terrain, [])
    ]
    passes = [
        {"type": "gradient_fill", "top": palette["top"], "bottom": palette["bottom"]},
        {"type": "noise_scatter",  "density": 0.12, "colors": palette["scatter"],
         "seed": _pass_seed(scene_id, "noise_scatter")},
        *feature_passes,
        {"type": "entity_marker", "entities": entity_markers,
         "color": [255, 255, 100], "marker_y": 0.72},
    ]

    return {
        "scene_id":    scene_id,
        "terrain":     terrain,
        "label":       palette["label"],
        "environment": scene_data.get("environment", "unknown"),
        "entity_count": len(entity_markers),
        "passes":      passes,
    }


class SceneRequestHandler(BaseHTTPRequestHandler):
    """Handle HTTP requests from Godot"""
    
    loader = SceneLoader()
    msg_handler = None # Injected by start_scene_server
    
    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        # Route: AP queries (if sent via GET)
        if parsed.path.startswith('/ap_'):
            msg_dict = {'type': parsed.path[1:]} # e.g., /ap_list_rules -> type: ap_list_rules
            # Add params to msg_dict
            for k, v in params.items():
                msg_dict[k] = v[0]
            
            if self.msg_handler:
                response = self.msg_handler(msg_dict)
                self._send_json(response, 200 if 'error' not in response else 400)
                return

        # Default response structure
        response = {'status': 'error', 'message': 'Unknown error'}
        status_code = 500
        
        try:
            # Route: /load_scene?scene_id=XXX
            if parsed.path == '/load_scene':
                scene_id = params.get('scene_id', [None])[0]
                
                if not scene_id:
                    status_code = 400
                    response = {'status': 'error', 'message': "Missing scene_id parameter"}
                else:
                    try:
                        scene = self.loader.load_scene(scene_id)
                        response = {'status': 'success', 'data': scene}
                        status_code = 200
                        print(f"[SceneServer] Served scene: {scene_id}")
                    except FileNotFoundError as e:
                        status_code = 404
                        response = {'status': 'error', 'message': str(e)}
            
            # Route: /list_scenes
            elif parsed.path == '/list_scenes':
                scenes = self.loader.list_available_scenes()
                response = {'status': 'success', 'scenes': scenes}
                status_code = 200

            # Route: /art_recipe?scene_id=XXX
            elif parsed.path == '/art_recipe':
                scene_id = params.get('scene_id', [None])[0]
                if not scene_id:
                    status_code = 400
                    response = {'status': 'error', 'message': "Missing scene_id parameter"}
                else:
                    try:
                        scene = self.loader.load_scene(scene_id)
                        recipe = _build_art_recipe(scene_id, scene)
                        response = {'status': 'success', 'recipe': recipe}
                        status_code = 200
                        print(f"[SceneServer] Art recipe: {scene_id} → {recipe['terrain']} ({len(recipe['passes'])} passes)")
                    except FileNotFoundError as e:
                        status_code = 404
                        response = {'status': 'error', 'message': str(e)}

            else:
                status_code = 404
                response = {'status': 'error', 'message': "Endpoint not found"}

        except Exception as e:
            import traceback
            traceback.print_exc()
            status_code = 500
            response = {'status': 'error', 'message': f"Server error: {e}"}
        
        self._send_json(response, status_code)

    def do_POST(self):
        """Handle POST requests (primarily for complex AP queries)"""
        parsed = urlparse(self.path)
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            msg_dict = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self._send_json({'error': 'Invalid JSON body'}, 400)
            return

        # Route: AP queries via POST
        msg_type = msg_dict.get('type', '')
        if msg_type.startswith('ap_') or parsed.path.startswith('/ap'):
            if not msg_type and parsed.path.startswith('/ap_'):
                msg_dict['type'] = parsed.path[1:]

            if self.msg_handler:
                result = self.msg_handler(msg_dict)
                if result:
                    self._send_json(result, 200 if 'error' not in result else 400)
                else:
                    self._send_json({'error': 'No response from handler'}, 500)
            else:
                self._send_json({'error': 'AP handler not initialized on server'}, 501)
            return

        self._send_json({'error': 'Endpoint not found or method not supported'}, 404)

    def _send_json(self, data, status_code=200):
        """Helper to send JSON responses"""
        try:
            response_data = json.dumps(data).encode()
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data)
        except Exception as e:
            print(f"[SceneServer] Critical failure sending response: {e}")
    
    def log_message(self, format, *args):
        """Suppress default logging (too verbose)"""
        pass


def start_scene_server(port: int = 8765, msg_handler=None):
    """Start HTTP server for scene loading and AP queries"""
    SceneRequestHandler.msg_handler = msg_handler
    
    server = HTTPServer(('127.0.0.1', port), SceneRequestHandler)
    print(f"[SceneServer] Starting on http://127.0.0.1:{port}")
    if msg_handler:
        print(f"[SceneServer] AP Query Router ACTIVE")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SceneServer] Shutting down")
        server.shutdown()


if __name__ == '__main__':
    start_scene_server()
