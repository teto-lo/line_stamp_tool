import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import rembg
from typing import List, Tuple, Optional
import io
from dotenv import load_dotenv

load_dotenv()

class ImageProcessor:
    def __init__(self, output_dir: str, lora_export_dir: str):
        self.output_dir = Path(output_dir)
        self.lora_export_dir = Path(lora_export_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.lora_export_dir.mkdir(parents=True, exist_ok=True)
        
        # Load font
        self.font_path = os.getenv('FONT_PATH', './fonts/NotoSansJP-Regular.ttf')
        self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for text composition"""
        try:
            # Try to load the specified font
            self.font_normal = ImageFont.truetype(self.font_path, 24)
            self.font_small = ImageFont.truetype(self.font_path, 18)
            self.font_large = ImageFont.truetype(self.font_path, 32)
        except Exception as e:
            print(f"Warning: Could not load font {self.font_path}: {e}")
            print("Using default font instead")
            # Fallback to default font
            try:
                self.font_normal = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
            except:
                self.font_normal = self.font_small = self.font_large = None
    
    def remove_background(self, image_data: bytes) -> bytes:
        """Remove background from image using rembg"""
        try:
            # Remove background
            output_data = rembg.remove(image_data)
            return output_data
        except Exception as e:
            print(f"Error removing background: {e}")
            return image_data
    
    def save_stamp_image(self, set_id: str, stamp_number: int, image_data: bytes, 
                        phrase: str = "", is_sample: bool = False) -> str:
        """Save stamp image with transparent background and text composition"""
        # Remove background
        transparent_data = self.remove_background(image_data)
        
        # Create filename
        filename = f"stamp_{stamp_number:02d}.png"
        set_dir = self.output_dir / set_id
        set_dir.mkdir(parents=True, exist_ok=True)
        
        # Save image with text composition
        image_path = set_dir / filename
        with Image.open(io.BytesIO(transparent_data)) as img:
            # Add text if phrase is provided
            if phrase and self.font_normal:
                img = self._add_text_to_image(img, phrase)
            
            img.save(image_path, "PNG")
        
        return str(image_path)
    
    def _add_text_to_image(self, img: Image.Image, text: str) -> Image.Image:
        """Add text to image with white color and black outline"""
        # Convert to RGBA if necessary
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a copy to avoid modifying original
        img_copy = img.copy()
        draw = ImageDraw.Draw(img_copy)
        
        # Choose font size based on text length
        font = self._choose_font_size(text)
        if not font:
            return img_copy
        
        # Get text dimensions
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # Fallback for older PIL versions
            try:
                text_width, text_height = draw.textsize(text, font=font)
            except:
                return img_copy
        
        # Calculate position (bottom center with padding)
        img_width, img_height = img_copy.size
        padding = 20
        x = (img_width - text_width) // 2
        y = img_height - text_height - padding
        
        # Ensure text stays within image bounds
        if x < 0:
            x = 0
        if y < 0:
            y = img_height - text_height - 5
        
        # Draw black outline (multiple times with small offsets)
        outline_width = 2
        outline_color = (0, 0, 0, 255)  # Black with full opacity
        fill_color = (255, 255, 255, 255)  # White with full opacity
        
        # Draw outline
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip center position
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=fill_color)
        
        return img_copy
    
    def _choose_font_size(self, text: str):
        """Choose appropriate font size based on text length"""
        if not self.font_normal:
            return None
        
        # Simple heuristic: shorter text gets larger font
        length = len(text)
        if length <= 5:
            return self.font_large
        elif length <= 15:
            return self.font_normal
        else:
            return self.font_small
    
    def create_grid_image(self, set_id: str, stamps: List[Dict], 
                         is_sample: bool = False) -> str:
        """Create a grid image for review"""
        if not stamps:
            return ""
        
        # Grid configuration
        cols = 5 if is_sample else 8
        rows = (len(stamps) + cols - 1) // cols
        
        stamp_width, stamp_height = 370, 320
        padding = 10
        text_height = 30
        
        grid_width = cols * (stamp_width + padding) + padding
        grid_height = rows * (stamp_height + text_height + padding) + padding
        
        # Create grid image
        grid_img = Image.new('RGBA', (grid_width, grid_height), (240, 240, 240, 255))
        draw = ImageDraw.Draw(grid_img)
        
        # Try to load font
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        for i, stamp in enumerate(stamps):
            row = i // cols
            col = i % cols
            
            x = padding + col * (stamp_width + padding)
            y = padding + row * (stamp_height + text_height + padding)
            
            # Load and paste stamp image
            if stamp.get('image_path') and os.path.exists(stamp['image_path']):
                try:
                    with Image.open(stamp['image_path']) as img:
                        # Resize if necessary
                        img = img.resize((stamp_width, stamp_height), Image.Resampling.LANCZOS)
                        grid_img.paste(img, (x, y), img)
                except Exception as e:
                    print(f"Error loading stamp {stamp.get('number', i)}: {e}")
                    # Draw placeholder
                    draw.rectangle([x, y, x + stamp_width, y + stamp_height], 
                                 fill=(200, 200, 200, 255))
            
            # Draw number
            text_y = y + stamp_height + 5
            number_text = f"{stamp.get('number', i + 1):02d}"
            text_bbox = draw.textbbox((x, text_y), number_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_x = x + (stamp_width - text_width) // 2
            
            # Draw text background
            draw.rectangle([x, text_y, x + stamp_width, text_y + text_height], 
                         fill=(50, 50, 50, 200))
            draw.text((text_x, text_y), number_text, fill=(255, 255, 255, 255), font=font)
        
        # Save grid image
        filename = f"{'sample_' if is_sample else ''}grid.png"
        grid_path = self.output_dir / set_id / filename
        grid_img.save(grid_path, "PNG")
        
        return str(grid_path)
    
    def export_for_lora(self, set_id: str, stamps: List[Dict]) -> None:
        """Export stamps for LoRA training"""
        lora_set_dir = self.lora_export_dir / set_id
        lora_set_dir.mkdir(parents=True, exist_ok=True)
        
        for stamp in stamps:
            if not stamp.get('image_path') or not os.path.exists(stamp['image_path']):
                continue
            
            stamp_number = stamp.get('number', 0)
            phrase = stamp.get('phrase', '')
            prompt = stamp.get('prompt', '')
            
            # Copy image
            image_filename = f"{stamp_number:03d}.png"
            image_path = Path(stamp['image_path'])
            lora_image_path = lora_set_dir / image_filename
            
            try:
                with Image.open(image_path) as img:
                    img.save(lora_image_path, "PNG")
            except Exception as e:
                print(f"Error copying image for LoRA: {e}")
                continue
            
            # Create caption file
            caption_filename = f"{stamp_number:03d}.txt"
            caption_path = lora_set_dir / caption_filename
            
            # Use prompt as caption, fallback to phrase
            caption = prompt if prompt else phrase
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(caption)
    
    def resize_image(self, image_path: str, width: int, height: int) -> str:
        """Resize image to specified dimensions"""
        try:
            with Image.open(image_path) as img:
                resized = img.resize((width, height), Image.Resampling.LANCZOS)
                
                # Save with _resized suffix
                path = Path(image_path)
                resized_path = path.parent / f"{path.stem}_resized{path.suffix}"
                resized.save(resized_path)
                
                return str(resized_path)
        except Exception as e:
            print(f"Error resizing image: {e}")
            return image_path
