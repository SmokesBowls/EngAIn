# VisionAgent.py - Visual analysis system for ZW Protocol
import os
import time
import base64
import json
from PIL import Image
import requests

class VisionAgent:
    VISION_PROMPT = "Describe what you see in this game screenshot in detail, focusing on the interface, characters, and environment."

    def __init__(self, use_local_model=True):
        self.use_local_model = use_local_model
        self.last_analyzed_image = None
        
        if use_local_model:
            self.setup_local_vision()
        else:
            self.setup_cloud_vision()
    
    def setup_local_vision(self):
        """Setup local vision model (placeholder for now)"""
        print("VisionAgent: Local vision model ready")
        # TODO: Initialize local model like LLaVA or CLIP
        
    def setup_cloud_vision(self):
        """Setup cloud vision API"""
        self.api_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY")
        }

        available = [k for k, v in self.api_keys.items() if v]
        if available:
            print(f"VisionAgent: Cloud vision API ready (Available: {', '.join(available)})")
        else:
            print("VisionAgent: Cloud vision API warning - No API keys found in environment variables")
    
    def analyze_screenshot(self, image_path):
        """Analyze a screenshot and return description"""
        if not os.path.exists(image_path):
            return "Error: Screenshot not found"
        
        try:
            if self.use_local_model:
                return self.analyze_local(image_path)
            else:
                return self.analyze_cloud(image_path)
        except Exception as e:
            return f"Vision analysis error: {str(e)}"
    
    def analyze_local(self, image_path):
        """Local image analysis (basic implementation)"""
        # For now, return a basic analysis
        # TODO: Replace with actual local vision model
        
        # Load image to get basic info
        with Image.open(image_path) as img:
            width, height = img.size
            
        # Basic pattern recognition (placeholder)
        if "reality" in image_path.lower() or "cosmic" in image_path.lower():
            return self.describe_cosmic_interface()
        else:
            return self.describe_unknown_interface(width, height)
    
    def analyze_cloud(self, image_path):
        """Cloud-based image analysis using vision API"""
        if self.api_keys.get("openai"):
            return self._analyze_openai(image_path)
        elif self.api_keys.get("anthropic"):
            return self._analyze_anthropic(image_path)
        elif self.api_keys.get("google"):
            return self._analyze_google(image_path)
        else:
            return "Error: No cloud vision API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY."

    def _encode_image(self, image_path):
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _analyze_openai(self, image_path):
        """Analyze image using OpenAI GPT-4o"""
        base64_image = self._encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_keys['openai']}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.VISION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            return f"OpenAI Vision error: {str(e)}"

    def _analyze_anthropic(self, image_path):
        """Analyze image using Anthropic Claude 3.5 Sonnet"""
        base64_image = self._encode_image(image_path)

        headers = {
            "content-type": "application/json",
            "x-api-key": self.api_keys['anthropic'],
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": self.VISION_PROMPT
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
        except Exception as e:
            return f"Anthropic Vision error: {str(e)}"

    def _analyze_google(self, image_path):
        """Analyze image using Google Gemini 1.5 Flash"""
        base64_image = self._encode_image(image_path)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_keys['google']}"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self.VISION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Google Gemini Vision error: {str(e)}"
    
    def describe_cosmic_interface(self):
        """Specialized description for cosmic/reality interfaces"""
        return """I observe a sophisticated reality manipulation interface with:
        - Central compass-like navigation system with directional controls
        - Entropy and selection dials for temporal adjustments  
        - Reality/Memory/Echo/Fracture control panels
        - Timeline anchor systems and Mandela Lock controls
        - Complex geometric patterns suggesting dimensional mapping
        - Warning indicators for reality stability and inversion risks
        - Multiple control layers for dream states and consciousness manipulation
        This appears to be a high-level command center for cosmic-scale reality engineering."""
    
    def describe_unknown_interface(self, width, height):
        """Generic interface description"""
        return f"""I see a complex interface display ({width}x{height} resolution) with:
        - Multiple control panels and monitoring systems
        - Geometric patterns and navigation elements
        - Various status indicators and warning systems
        - What appears to be a sophisticated command interface
        The overall design suggests an advanced technological or metaphysical control system."""
    
    def get_visual_context(self, latest_screenshot):
        """Get visual context for ZW Protocol"""
        if not latest_screenshot:
            return "No visual data available"
        
        description = self.analyze_screenshot(latest_screenshot)
        
        return {
            "visual_description": description,
            "image_path": latest_screenshot,
            "analysis_timestamp": os.path.getmtime(latest_screenshot),
            "has_visual_data": True
        }


class VisualZWBridge:
    """Enhanced ZW Bridge with vision capabilities"""
    
    def __init__(self):
        self.vision_agent = VisionAgent(use_local_model=True)
        self.snapshots_dir = "snapshots/"  # Project-relative path
    
    def get_latest_screenshot(self):
        """Find the most recent screenshot"""
        if not os.path.exists(self.snapshots_dir):
            return None
        
        png_files = [f for f in os.listdir(self.snapshots_dir) if f.endswith('.png')]
        if not png_files:
            return None
        
        # Sort by modification time, get latest
        png_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.snapshots_dir, x)))
        latest_file = os.path.join(self.snapshots_dir, png_files[-1])
        
        return latest_file
    
    def create_visual_zw_packet(self, player_input, text_context=""):
        """Create ZW packet with both text and visual context"""
        
        # Get latest visual data
        latest_screenshot = self.get_latest_screenshot()
        visual_context = self.vision_agent.get_visual_context(latest_screenshot)
        
        # Combine text and visual context
        enhanced_context = text_context
        if visual_context["has_visual_data"]:
            enhanced_context += f"\n\nVISUAL CONTEXT: {visual_context['visual_description']}"
        
        # Create enhanced ZW packet
        zw_packet = {
            "type": "ZW-REQUEST",
            "SCOPE": "Player", 
            "CONTEXT": {
                "text_context": text_context,
                "visual_context": visual_context,
                "enhanced_prompt": enhanced_context
            },
            "ACTION": {
                "verb": player_input.split()[0] if player_input.split() else "unknown",
                "target": " ".join(player_input.split()[1:]) if len(player_input.split()) > 1 else "implicit"
            },
            "timestamp": time.time()
        }
        
        return zw_packet, enhanced_context


# Integration with existing ZW system
def process_visual_command(player_input, text_context=""):
    """Process player input with visual awareness"""
    bridge = VisualZWBridge()
    zw_packet, enhanced_context = bridge.create_visual_zw_packet(player_input, text_context)
    
    print(f"VisionAgent: Enhanced context length: {len(enhanced_context)} characters")
    print(f"VisionAgent: Visual data included: {zw_packet['CONTEXT']['visual_context']['has_visual_data']}")
    
    return enhanced_context


# Test function
if __name__ == "__main__":
    # Test visual analysis
    vision = VisionAgent()
    
    # Simulate screenshot analysis
    test_result = vision.describe_cosmic_interface()
    print("Vision Test Result:")
    print(test_result)
    
    # Test enhanced ZW packet creation
    bridge = VisualZWBridge()
    packet, context = bridge.create_visual_zw_packet(
        "what do you see", 
        "Currently in reality control interface"
    )
    
    print("\nEnhanced Context:")
    print(context)
