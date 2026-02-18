import google.generativeai as genai
import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def generate_character_proposals(self, stamp_type: str, user_request: Optional[str] = None) -> List[Dict[str, str]]:
        """Generate character proposals for LINE stamps"""
        
        # Type-specific prompts
        type_prompts = {
            "animal": "動物キャラクター",
            "original_character": "オリジナルキャラクター（例：飲んだくれおじさん、眠そうな社会人、など）",
            "concept": "コンセプト系（キャラクターなし・モノや抽象的な概念）",
            "ai_free": "完全にAIにおまかせ"
        }
        
        type_description = type_prompts.get(stamp_type, "動物キャラクターか、オリジナルキャラクター")
        
        # Add concept examples for concept type
        concept_examples = ""
        if stamp_type == "concept":
            concept_examples = "\n\nコンセプト系の例：\n- 野菜だけが喜怒哀楽を表現\n- 白い謎の物体がひたすら何かを主張する\n- 食べ物が日常会話する\n- 幾何学図形が感情を持つ\n- 天気現象がキャラクターのように振る舞う\n"
        
        prompt = f"""LINEスタンプ用のキャラクターを提案してください。
タイプ: {type_description}{concept_examples}
ユニークで親しみやすいキャラクターを3案、以下のJSON形式で出力してください。

[
  {{
    "name": "キャラ名",
    "genre": "{stamp_type}",
    "description": "キャラクター説明（外見・性格・特徴を詳細に）",
    "sd_base_prompt": "Stable Diffusion用の英語プロンプト（スタイル・外見を固定する部分）",
    "character_consistency": {str(stamp_type != "concept").lower()}
  }}
]
JSONのみ出力してください。"""
        
        if user_request:
            prompt = f"""ユーザーの要望: {user_request}

{prompt}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Clean up response if it contains markdown
            if result.startswith('```json'):
                result = result[7:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            proposals = json.loads(result)
            return proposals
        except Exception as e:
            print(f"Error generating character proposals: {e}")
            return []
    
    async def generate_phrase_patterns(self, character_description: str, user_request: Optional[str] = None) -> List[str]:
        """Generate phrase patterns for LINE stamps"""
        prompt = f"""以下のキャラクターのLINEスタンプ用フレーズを30個提案してください。
キャラクター: {character_description}

挨拶、返事、感情表現、日常会話、ちょっとしたジョークをバランスよく含めてください。
以下のJSON配列で出力してください。

["おはよう！", "ありがとう", "了解です", ...]
JSONのみ出力してください。"""
        
        if user_request:
            prompt = f"""ユーザーの要望: {user_request}

{prompt}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            
            # Clean up response if it contains markdown
            if result.startswith('```json'):
                result = result[7:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            phrases = json.loads(result)
            return phrases
        except Exception as e:
            print(f"Error generating phrase patterns: {e}")
            return []
    
    async def generate_image_prompt(self, phrase: str, character_description: str, 
                                   base_prompt: str, user_modification: Optional[str] = None) -> str:
        """Generate detailed image prompt for Stable Diffusion"""
        prompt = f"""以下の情報を元に、Stable Diffusion用の詳細な英語プロンプトを生成してください。

キャラクター設定: {character_description}
ベースプロンプト: {base_prompt}
フレーズ: {phrase}

プロンプトには以下の要素を含めてください:
- キャラクターの外見と服装
- フレーズに合った表情やポーズ
- LINEスタンプに適したスタイル（かわいい、シンプル、背景なし）
- 画質指定（high quality, clean lines, transparent background）

英語で出力してください。"""
        
        if user_modification:
            prompt = f"""ユーザーの修正要望: {user_modification}

{prompt}"""
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip()
            return result
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return base_prompt
