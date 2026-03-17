import requests
import json
import os

URL = "http://localhost:8080/command"
SCENE_PATH = os.path.abspath("godotsim/data/beach_scene.json")

def trigger():
    payload = {
        "command": "load_scene_from_file",
        "path": SCENE_PATH,
        "scene_id": "scene.04_the_convergence"
    }
    
    print(f"Sending command to load MVP scene from: {SCENE_PATH}")
    try:
        response = requests.post(URL, json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    trigger()
