#!/usr/bin/env python3
"""
scene_server.py - HTTP server for scene loading and AP queries

Serves scene data and handles Agnostic Protocol (AP) queries from Godot.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from scene_loader import SceneLoader, format_for_godot


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
                        formatted = format_for_godot(scene)
                        response = {'status': 'success', 'data': formatted}
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
