import unittest
from unittest.mock import patch, MagicMock
import os
import base64
import json
import sys

# Mock PIL and requests before they are imported by VisionAgent
mock_pil = MagicMock()
mock_image = MagicMock()
mock_pil.Image = mock_image
sys.modules['PIL'] = mock_pil
sys.modules['PIL.Image'] = mock_image
sys.modules['requests'] = MagicMock()

# Now we can import VisionAgent
from VisionAgent import VisionAgent

class TestVisionAgent(unittest.TestCase):
    def setUp(self):
        # Create a dummy image path
        self.test_image_path = "test_image.png"
        # We don't actually need to create the file if we mock open()

    def tearDown(self):
        pass

    @patch.dict(os.environ, {
        "OPENAI_API_KEY": "sk-test-openai",
        "ANTHROPIC_API_KEY": "at-test-anthropic",
        "GOOGLE_API_KEY": "test-google-key"
    })
    def test_setup_cloud_vision(self):
        vision = VisionAgent(use_local_model=False)
        self.assertEqual(vision.api_keys["openai"], "sk-test-openai")
        self.assertEqual(vision.api_keys["anthropic"], "at-test-anthropic")
        self.assertEqual(vision.api_keys["google"], "test-google-key")

    @patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-openai"})
    @patch('requests.post')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake_image_data"))
    @patch('os.path.exists', return_value=True)
    def test_analyze_openai(self, mock_exists, mock_post):
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'I see a red square.'}}]
        }
        mock_post.return_value = mock_response

        vision = VisionAgent(use_local_model=False)
        result = vision.analyze_cloud(self.test_image_path)

        self.assertEqual(result, 'I see a red square.')
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(kwargs['json']['model'], "gpt-4o")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "at-test-anthropic"})
    @patch('requests.post')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake_image_data"))
    @patch('os.path.exists', return_value=True)
    def test_analyze_anthropic(self, mock_exists, mock_post):
        # Mock Anthropic response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'content': [{'text': 'A red image.'}]
        }
        mock_post.return_value = mock_response

        vision = VisionAgent(use_local_model=False)
        # Manually clear OpenAI key to force Anthropic
        vision.api_keys["openai"] = None
        result = vision.analyze_cloud(self.test_image_path)

        self.assertEqual(result, 'A red image.')
        self.assertEqual(mock_post.call_args[0][0], "https://api.anthropic.com/v1/messages")

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-google-key"})
    @patch('requests.post')
    @patch('builtins.open', unittest.mock.mock_open(read_data=b"fake_image_data"))
    @patch('os.path.exists', return_value=True)
    def test_analyze_google(self, mock_exists, mock_post):
        # Mock Google response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Red pixels.'}]}}]
        }
        mock_post.return_value = mock_response

        vision = VisionAgent(use_local_model=False)
        # Manually clear other keys
        vision.api_keys["openai"] = None
        vision.api_keys["anthropic"] = None
        result = vision.analyze_cloud(self.test_image_path)

        self.assertEqual(result, 'Red pixels.')
        self.assertIn("googleapis.com", mock_post.call_args[0][0])

    @patch.dict(os.environ, {}, clear=True)
    def test_no_keys(self):
        vision = VisionAgent(use_local_model=False)
        result = vision.analyze_cloud(self.test_image_path)
        self.assertIn("Error: No cloud vision API keys configured", result)

if __name__ == '__main__':
    unittest.main()
