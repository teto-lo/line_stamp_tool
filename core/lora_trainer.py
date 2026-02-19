import subprocess
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class LoRATrainer:
    def __init__(self):
        self.kohya_path = os.getenv('KOHYA_PATH', 'C:/kohya_ss/train_network.py')
        self.lora_models_dir = Path(os.getenv('LORA_MODELS_DIR', './data/lora_models'))
        self.lora_models_dir.mkdir(parents=True, exist_ok=True)
    
    def train_lora(self, set_id: str, data_dir: str, base_model_path: str = "models/base_model") -> bool:
        """Train LoRA model using Kohya_ss"""
        try:
            output_dir = self.lora_models_dir / set_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                "python", self.kohya_path,
                "--pretrained_model_name_or_path", base_model_path,
                "--train_data_dir", data_dir,
                "--output_dir", str(output_dir),
                "--output_name", set_id,
                "--network_dim", "32",
                "--max_train_epochs", "10",
                "--save_model_as", "safetensors",
                "--save_every_n_epochs", "5",
                "--mixed_precision", "fp16",
                "--cache_latents",
                "--use_8bit_adam",
                "--xformers",
                "--gradient_checkpointing",
                "--gradient_accumulation_steps", "1"
            ]
            
            print(f"Starting LoRA training for {set_id}...")
            print(f"Command: {' '.join(cmd)}")
            
            # Run training
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            print("LoRA training completed successfully!")
            print(f"Output saved to: {output_dir}")
            
            # Return the path to the trained model
            model_path = output_dir / f"{set_id}.safetensors"
            return str(model_path) if model_path.exists() else None
            
        except subprocess.CalledProcessError as e:
            print(f"LoRA training failed: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error during LoRA training: {e}")
            return None
    
    def build_prompt_with_lora(self, base_prompt: str, set_id: str, lora_path: Optional[str] = None) -> str:
        """Build prompt with LoRA if available"""
        if lora_path and Path(lora_path).exists():
            return f"{base_prompt} <lora:{set_id}:0.8>"
        return base_prompt
    
    def get_lora_path(self, set_id: str) -> Optional[str]:
        """Get LoRA model path for set_id"""
        model_path = self.lora_models_dir / set_id / f"{set_id}.safetensors"
        return str(model_path) if model_path.exists() else None
