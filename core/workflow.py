import asyncio
import threading
import random
from typing import Dict, List, Optional, Callable
from pathlib import Path
import os

from .gemini import GeminiClient
from .sd_api import StableDiffusionAPI
from .image_utils import ImageProcessor
from .lora_trainer import LoRATrainer
from .booth_exporter import BoothExporter
from ..db.models import StampSet, Stamp
from ..db.crud import StampSetCRUD, StampCRUD
from ..db.models import init_db, get_session
from dotenv import load_dotenv

load_dotenv()

class StampWorkflowManager:
    def __init__(self):
        self.gemini = GeminiClient()
        self.sd_api = StableDiffusionAPI()
        self.image_processor = ImageProcessor(
            os.getenv('OUTPUT_DIR', './output'),
            os.getenv('LORA_EXPORT_DIR', './lora_export')
        )
        self.lora_trainer = LoRATrainer()
        self.booth_exporter = BoothExporter(
            os.getenv('OUTPUT_DIR', './output')
        )
        
        # Initialize database
        db_path = os.getenv('DB_PATH', './data/stamps.db')
        self.engine = init_db(db_path)
        
        # Callback functions for Slack notifications
        self.slack_callback: Optional[Callable] = None
    
    def set_slack_callback(self, callback: Callable):
        """Set callback function for Slack notifications"""
        self.slack_callback = callback
    
    def _notify_slack(self, message: str, blocks: Optional[List[Dict]] = None):
        """Send notification to Slack"""
        if self.slack_callback:
            try:
                if asyncio.iscoroutinefunction(self.slack_callback):
                    asyncio.create_task(self.slack_callback(message, blocks))
                else:
                    self.slack_callback(message, blocks)
            except Exception as e:
                print(f"Error sending Slack notification: {e}")
    
    def create_new_set(self, name: str, slack_ts: str) -> Optional[StampSet]:
        """Create new stamp set"""
        db = get_session(self.engine)
        try:
            crud = StampSetCRUD(db)
            stamp_set = crud.create(name=name, genre="", slack_ts=slack_ts)
            return stamp_set
        finally:
            db.close()
    
    def start_direction_workflow(self, set_id: str, has_reference_image: bool = False) -> bool:
        """Start direction determination workflow"""
        db = get_session(self.engine)
        try:
            crud = StampSetCRUD(db)
            stamp_set = crud.get(set_id)
            if not stamp_set:
                return False
            
            if has_reference_image:
                # Ask for reference image
                self._notify_slack(
                    f"📎 参照画像を添付してください。",
                    [{
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"スタンプセット「{stamp_set.name}」の参照画像をアップロードしてください。"}
                    }]
                )
            else:
                # Generate character proposals
                self._generate_character_proposals(set_id)
            
            return True
        finally:
            db.close()
    
    def _generate_character_proposals(self, set_id: str, user_request: Optional[str] = None):
        """Generate character proposals using Gemini"""
        def run_in_background():
            try:
                # Get stamp set to determine type
                db = get_session(self.engine)
                try:
                    crud = StampSetCRUD(db)
                    stamp_set = crud.get(set_id)
                    if not stamp_set:
                        self._notify_slack("❌ スタンプセットが見つかりません。")
                        return
                    
                    stamp_type = stamp_set.genre
                    
                finally:
                    db.close()
                
                proposals = asyncio.run(self.gemini.generate_character_proposals(stamp_type, user_request))
                
                if not proposals:
                    self._notify_slack("❌ キャラクター案の生成に失敗しました。")
                    return
                
                # Create Slack blocks for proposals
                blocks = [{
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🎨 {stamp_type}タイプのキャラクター案を3件提案します:"}
                }]
                
                for i, proposal in enumerate(proposals, 1):
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*案{i}: {proposal.get('name', '不明')}*\n"
                                   f"ジャンル: {proposal.get('genre', '不明')}\n"
                                   f"説明: {proposal.get('description', '不明')}\n"
                                   f"キャラクター一貫性: {'✅' if proposal.get('character_consistency', True) else '❌'}"
                        }
                    })
                    blocks.append({
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": f"✅ 案{i}で決定"},
                                "action_id": f"approve_direction_{i}",
                                "value": f"{set_id}:{i}"
                            },
                            {
                                "type": "button", 
                                "text": {"type": "plain_text", "text": "✏️ 別の案を提案"},
                                "action_id": "request_new_proposals",
                                "value": set_id
                            }
                        ]
                    })
                
                self._notify_slack("🎨 キャラクター案を生成しました", blocks)
                
            except Exception as e:
                print(f"Error generating character proposals: {e}")
                self._notify_slack("❌ キャラクター案の生成中にエラーが発生しました。")
        
        threading.Thread(target=run_in_background, daemon=True).start()
    
    def approve_direction(self, set_id: str, proposal_index: int):
        """Approve character direction and update stamp set"""
        db = get_session(self.engine)
        try:
            crud = StampSetCRUD(db)
            stamp_set = crud.get(set_id)
            if not stamp_set:
                return False
            
            # Get the approved proposal (would need to store proposals temporarily)
            # For now, proceed to phrase generation
            crud.update_status(set_id, 'direction_approved')
            
            # Generate phrase patterns
            self._generate_phrase_patterns(set_id)
            
            return True
        finally:
            db.close()
    
    def _generate_phrase_patterns(self, set_id: str, user_request: Optional[str] = None):
        """Generate phrase patterns using Gemini"""
        def run_in_background():
            db = get_session(self.engine)
            try:
                crud = StampSetCRUD(db)
                stamp_set = crud.get(set_id)
                if not stamp_set or not stamp_set.character_description:
                    self._notify_slack("❌ キャラクター設定が見つかりません。")
                    return
                
                phrases = asyncio.run(self.gemini.generate_phrase_patterns(
                    stamp_set.character_description, user_request
                ))
                
                if not phrases:
                    self._notify_slack("❌ フレーズの生成に失敗しました。")
                    return
                
                # Create Slack blocks for phrases
                phrase_text = "\n".join([f"{i+1}. {phrase}" for i, phrase in enumerate(phrases)])
                
                blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"📝 フレーズ案を{len(phrases)}件生成しました:"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": phrase_text}
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "✅ 承認"},
                                "action_id": "approve_phrases",
                                "value": set_id
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "❌ 再生成"},
                                "action_id": "regenerate_phrases", 
                                "value": set_id
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "✏️ 修正提案"},
                                "action_id": "modify_phrases",
                                "value": set_id
                            }
                        ]
                    }
                ]
                
                self._notify_slack("📝 フレーズ案を生成しました", blocks)
                
            except Exception as e:
                print(f"Error generating phrase patterns: {e}")
                self._notify_slack("❌ フレーズ生成中にエラーが発生しました。")
            finally:
                db.close()
        
        threading.Thread(target=run_in_background, daemon=True).start()
    
    def generate_sample_stamps(self, set_id: str):
        """Generate sample 5 stamps"""
        def run_in_background():
            db = get_session(self.engine)
            try:
                crud = StampSetCRUD(db)
                stamp_crud = StampCRUD(db)
                
                stamp_set = crud.get(set_id)
                if not stamp_set:
                    return
                
                # Update status
                crud.update_status(set_id, 'samples_generating')
                
                # Get first 5 phrases (would need to store them)
                stamps = stamp_crud.get_by_set(set_id)
                sample_stamps = stamps[:5] if len(stamps) >= 5 else stamps
                
                if not sample_stamps:
                    self._notify_slack("❌ フレーズが見つかりません。")
                    crud.update_status(set_id, 'patterns_approved')
                    return
                
                # Generate images for sample stamps
                generated_stamps = []
                
                # Use seed only if character consistency is required
                if stamp_set.character_consistency:
                    seed = random.randint(1, 1000000)
                    crud.update_seed(set_id, seed)
                else:
                    seed = None  # Random seed for each stamp
                
                for i, stamp in enumerate(sample_stamps):
                    self._notify_slack(f"🎨 サンプル{i+1}/5を生成中...")
                    
                    # Use different seed for each stamp if no character consistency
                    current_seed = seed + i if seed else random.randint(1, 1000000)
                    
                    # Check for existing LoRA
                    lora_path = self.lora_trainer.get_lora_path(set_id)
                    prompt = self.lora_trainer.build_prompt_with_lora(stamp.prompt, set_id, lora_path)
                    
                    image_data = self.sd_api.generate_image(
                        prompt=prompt,
                        negative_prompt=stamp.negative_prompt or "",
                        seed=current_seed,
                        reference_image_path=stamp_set.reference_image_path if stamp_set.character_consistency else None
                    )
                    
                    if image_data:
                        image_path = self.image_processor.save_stamp_image(
                            set_id, stamp.number, image_data, stamp.phrase, is_sample=True
                        )
                        stamp_crud.update_image_path(stamp.id, image_path)
                        
                        generated_stamps.append({
                            'id': stamp.id,
                            'number': stamp.number,
                            'image_path': image_path,
                            'phrase': stamp.phrase
                        })
                
                # Create grid image
                grid_path = self.image_processor.create_grid_image(set_id, generated_stamps, is_sample=True)
                
                # Update status and notify with retry buttons
                crud.update_status(set_id, 'samples_review')
                
                # Build blocks with individual retry buttons
                blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"🎨 サンプルスタンプを{len(generated_stamps)}枚生成しました"}
                    },
                    {
                        "type": "image",
                        "image_url": f"file://{grid_path}",
                        "alt_text": "Sample stamps grid"
                    }
                ]
                
                # Add individual stamp blocks with retry buttons
                for stamp in generated_stamps:
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*スタンプ {stamp['number']:02d}*: {stamp['phrase']}"
                        }
                    })
                    blocks.append({
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "✅ OK"},
                                "action_id": "approve_sample_stamp",
                                "value": f"{set_id}:{stamp['id']}"
                            },
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "🔄 再生成"},
                                "action_id": "regenerate_stamp",
                                "value": f"{set_id}:{stamp['id']}"
                            }
                        ]
                    })
                
                # Add overall action buttons
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ このスタイルで全部作る"},
                            "action_id": "approve_samples",
                            "value": set_id
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ やり直し"},
                            "action_id": "reject_samples",
                            "value": set_id
                        }
                    ]
                })
                
                self._notify_slack("🎨 サンプルスタンプが完成しました", blocks)
                
            except Exception as e:
                print(f"Error generating sample stamps: {e}")
                self._notify_slack("❌ サンプル生成中にエラーが発生しました。")
            finally:
                db.close()
        
        threading.Thread(target=run_in_background, daemon=True).start()
    
    def generate_full_stamps(self, set_id: str):
        """Generate all remaining stamps"""
        def run_in_background():
            db = get_session(self.engine)
            try:
                crud = StampSetCRUD(db)
                stamp_crud = StampCRUD(db)
                
                stamp_set = crud.get(set_id)
                if not stamp_set:
                    return
                
                # Update status
                crud.update_status(set_id, 'full_generating')
                
                # Get all stamps
                stamps = stamp_crud.get_by_set(set_id)
                
                # Generate images for all stamps
                generated_count = 0
                total_count = len(stamps)
                
                # Use seed only if character consistency is required
                if stamp_set.character_consistency:
                    seed = stamp_set.seed or random.randint(1, 1000000)
                else:
                    seed = None  # Random seed for each stamp
                
                for i, stamp in enumerate(stamps):
                    if stamp.image_path:  # Skip already generated
                        generated_count += 1
                        continue
                    
                    # Progress notification
                    if (i + 1) % 5 == 0 or i == len(stamps) - 1:
                        self._notify_slack(f"🎨 進捗: {i+1}/{total_count}枚完了...")
                    
                    # Use different seed for each stamp if no character consistency
                    current_seed = seed + stamp.number if seed else random.randint(1, 1000000)
                    
                    image_data = self.sd_api.generate_image(
                        prompt=stamp.prompt,
                        negative_prompt=stamp.negative_prompt or "",
                        seed=current_seed,
                        reference_image_path=stamp_set.reference_image_path if stamp_set.character_consistency else None
                    )
                    
                    if image_data:
                        image_path = self.image_processor.save_stamp_image(
                            set_id, stamp.number, image_data, stamp.phrase
                        )
                        stamp_crud.update_image_path(stamp.id, image_path)
                        generated_count += 1
                
                # Create grid image
                all_stamps = []
                for stamp in stamp_crud.get_by_set(set_id):
                    if stamp.image_path:
                        all_stamps.append({
                            'number': stamp.number,
                            'image_path': stamp.image_path,
                            'phrase': stamp.phrase
                        })
                
                grid_path = self.image_processor.create_grid_image(set_id, all_stamps, is_sample=False)
                
                # Export for LoRA
                self.image_processor.export_for_lora(set_id, all_stamps)
                crud.mark_lora_exported(set_id)
                
                # Update status and notify
                crud.update_status(set_id, 'completed')
                
                blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"✅ スタンプセット「{stamp_set.name}」が完成しました！"}
                    },
                    {
                        "type": "section", 
                        "text": {"type": "mrkdwn", "text": f"📁 保存先: `output/{set_id}/`"}
                    },
                    {
                        "type": "image",
                        "image_url": f"file://{grid_path}",
                        "alt_text": "Complete stamps grid"
                    }
                ]
                
                self._notify_slack("✅ スタンプセットが完成しました！", blocks)
                
            except Exception as e:
                print(f"Error generating full stamps: {e}")
                self._notify_slack("❌ 全体生成中にエラーが発生しました。")
            finally:
                db.close()
        
        threading.Thread(target=run_in_background, daemon=True).start()
