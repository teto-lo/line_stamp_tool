import requests
import json
import base64
import io
from typing import Optional, Dict, Any
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

class StableDiffusionAPI:
    def __init__(self):
        self.base_url = os.getenv('SD_WEBUI_URL', 'http://localhost:7860')
        self.txt2img_endpoint = f"{self.base_url}/sdapi/v1/txt2img"
        self.img2img_endpoint = f"{self.base_url}/sdapi/v1/img2img"
    
    def generate_image(self, prompt: str, negative_prompt: str = "", 
                      width: int = 370, height: int = 320, 
                      cfg_scale: float = 7.0, steps: int = 30,
                      sampler_name: str = "DPM++ 2M Karras",
                      seed: int = -1, reference_image_path: Optional[str] = None,
                      denoising_strength: float = 0.6) -> Optional[bytes]:
        """Generate image using Stable Diffusion API"""
        
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "cfg_scale": cfg_scale,
            "steps": steps,
            "sampler_name": sampler_name,
            "seed": seed,
            "save_images": False,
            "send_images": True
        }
        
        # Use img2img if reference image is provided
        if reference_image_path and os.path.exists(reference_image_path):
            try:
                with Image.open(reference_image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Resize to target dimensions
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Convert to bytes
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    img_b64 = base64.b64encode(img_bytes.getvalue()).decode()
                    
                    payload.update({
                        "init_images": [img_b64],
                        "denoising_strength": denoising_strength
                    })
                    
                    endpoint = self.img2img_endpoint
            except Exception as e:
                print(f"Error processing reference image: {e}")
                return None
        else:
            endpoint = self.txt2img_endpoint
        
        try:
            response = requests.post(endpoint, json=payload, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                # Get the generated image
                image_data = base64.b64decode(result['images'][0])
                return image_data
            else:
                print("No images in response")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error calling Stable Diffusion API: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing API response: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def get_available_samplers(self) -> list:
        """Get list of available samplers from SD WebUI"""
        try:
            response = requests.get(f"{self.base_url}/sdapi/v1/samplers", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting samplers: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test connection to SD WebUI"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False
