import os
import json
from pathlib import Path
from typing import Dict, List
from fpdf import FPDF
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

class BoothExporter:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.booth_dir = self.output_dir / "booth"
        self.booth_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_booth_metadata(self, character_description: str, genre: str) -> Dict:
        """Generate BOOTH metadata using Gemini"""
        # This would call Gemini API in real implementation
        # For now, return a template
        return {
            "title_ja": "キャラクタースタンプ",
            "title_en": "Character Stamps",
            "description_ja": f"日常会話で使える{genre}系スタンプセットです。",
            "description_en": f"A set of {genre} character stamps for daily conversation.",
            "tags": [genre, "スタンプ", "キャラクター", "LINE", "スタンプ"],
            "price_jpy": 300
        }
    
    def create_pdf(self, set_id: str, stamps: List[Dict], metadata: Dict) -> str:
        """Create BOOTH PDF from stamps"""
        pdf = FPDF()
        pdf.add_page()
        
        # Set font (fallback to default if Japanese font not available)
        try:
            pdf.add_font('NotoSansJP', '', './fonts/NotoSansJP-Regular.ttf', uni=True)
            pdf.set_font('NotoSansJP', size=12)
        except:
            pdf.set_font('Arial', size=12)
        
        # Title page
        pdf.set_font_size(20)
        pdf.cell(0, 15, metadata['title_ja'], ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font_size(12)
        pdf.multi_cell(0, 10, metadata['description_ja'], align='C')
        pdf.ln(20)
        
        # Add stamps in grid layout (4x5 per page)
        PAGE_SIZE = 'A4'  # 210×297mm
        GRID_COLS = 4
        GRID_ROWS = 5
        STAMP_WIDTH = 45  # mm
        STAMP_HEIGHT = 40  # mm
        PADDING = 5  # mm
        
        current_col = 0
        current_row = 0
        
        for i, stamp in enumerate(stamps):
            if current_col == 0 and current_row == 0:
                pdf.add_page()
            
            # Calculate position
            x = 20 + current_col * (STAMP_WIDTH + PADDING)
            y = 30 + current_row * (STAMP_HEIGHT + PADDING)
            
            # Add stamp number
            pdf.set_font_size(8)
            pdf.text(x, y - 5, f"{stamp['number']:02d}")
            
            # Add stamp image if available
            if stamp.get('image_path') and Path(stamp['image_path']).exists():
                try:
                    pdf.image(stamp['image_path'], x, y, STAMP_WIDTH, STAMP_HEIGHT)
                except Exception as e:
                    print(f"Error adding image {stamp['image_path']}: {e}")
                    # Draw placeholder
                    pdf.rect(x, y, STAMP_WIDTH, STAMP_HEIGHT)
                    pdf.set_font_size(6)
                    pdf.text(x + 2, y + STAMP_HEIGHT//2, "No Image")
            
            # Add phrase text
            if stamp.get('phrase'):
                pdf.set_font_size(6)
                # Simple text wrapping
                phrase = stamp['phrase'][:15] + ("..." if len(stamp['phrase']) > 15 else "")
                pdf.text(x, y + STAMP_HEIGHT + 2, phrase)
            
            # Update position
            current_col += 1
            if current_col >= GRID_COLS:
                current_col = 0
                current_row += 1
                if current_row >= GRID_ROWS:
                    current_row = 0
        
        # Add terms page
        pdf.add_page()
        pdf.set_font_size(16)
        pdf.cell(0, 15, "利用規約", ln=True, align='C')
        pdf.ln(15)
        
        pdf.set_font_size(10)
        terms = """
このスタンプセットは個人的利用のみを目的としています。

【利用可能な範囲】
- LINEスタンプとしての利用
- 個人的なSNS投稿
- プライベートなコミュニケーション

【禁止事項】
- 商業利用
- 再販売・配布
- 著作権を侵害する利用
- 法令に違反する利用

【免責事項】
- 本スタンプによるいかなる損害も責任を負いかねます
- 利用規約は予告なく変更することがあります

ご理解の上、ご利用ください。
        """
        pdf.multi_cell(0, 8, terms)
        
        # Save PDF
        pdf_path = self.booth_dir / f"{set_id}.pdf"
        pdf.output(str(pdf_path))
        
        return str(pdf_path)
    
    def export_for_booth(self, set_id: str, stamps: List[Dict], character_description: str, genre: str) -> str:
        """Export stamp set for BOOTH"""
        try:
            # Generate metadata
            metadata = self.generate_booth_metadata(character_description, genre)
            
            # Create PDF
            pdf_path = self.create_pdf(set_id, stamps, metadata)
            
            # Save metadata as JSON
            metadata_path = self.booth_dir / f"{set_id}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"BOOTH export completed: {pdf_path}")
            print(f"Metadata saved: {metadata_path}")
            
            return pdf_path
            
        except Exception as e:
            print(f"Error exporting for BOOTH: {e}")
            return None
