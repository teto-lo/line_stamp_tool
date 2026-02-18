import os
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_sdk.web.async_client import AsyncWebClient
from dotenv import load_dotenv
from typing import Dict, List, Optional
from .welcome_message import get_welcome_blocks

load_dotenv()

class SlackBot:
    def __init__(self, workflow_manager):
        self.app = AsyncApp(
            token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET")
        )
        self.client = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        self.channel_id = os.getenv("SLACK_CHANNEL_ID")
        self.workflow_manager = workflow_manager
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up Slack event handlers"""
        
        @self.app.command("/stamp")
        async def handle_stamp_command(ack, body, logger):
            await ack()
            
            # Extract command text
            command_text = body.get("text", "").strip()
            
            if command_text == "new":
                await self._handle_new_command(body)
            elif command_text == "list":
                await self._handle_list_command(body)
            elif command_text == "help":
                await self._handle_help_command(body)
            else:
                await self._handle_help_command(body)
        
        @self.app.action("select_stamp_type")
        async def handle_select_stamp_type(ack, body, logger):
            await ack()
            await self._handle_stamp_type_selection(body)
        
        @self.app.action("create_new_stamp_set")
        async def handle_create_new_stamp_set(ack, body, logger):
            await ack()
            await self._handle_new_command(body)
        
        @self.app.action("show_help")
        async def handle_show_help(ack, body, logger):
            await ack()
            await self._handle_help_command(body)
        
        @self.app.action("show_stamp_list")
        async def handle_show_stamp_list(ack, body, logger):
            await ack()
            await self._handle_list_command(body)
        
        @self.app.action("has_reference_image_yes")
        async def handle_has_reference_yes(ack, body, logger):
            await ack()
            await self._handle_reference_image_response(body, has_image=True)
        
        @self.app.action("has_reference_image_no")
        async def handle_has_reference_no(ack, body, logger):
            await ack()
            await self._handle_reference_image_response(body, has_image=False)
        
        @self.app.action("approve_direction_1")
        async def handle_approve_direction_1(ack, body, logger):
            await ack()
            await self._handle_approve_direction(body, proposal_index=1)
        
        @self.app.action("approve_direction_2")
        async def handle_approve_direction_2(ack, body, logger):
            await ack()
            await self._handle_approve_direction(body, proposal_index=2)
        
        @self.app.action("approve_direction_3")
        async def handle_approve_direction_3(ack, body, logger):
            await ack()
            await self._handle_approve_direction(body, proposal_index=3)
        
        @self.app.action("request_new_proposals")
        async def handle_request_new_proposals(ack, body, logger):
            await ack()
            await self._handle_request_new_proposals(body)
        
        @self.app.action("approve_phrases")
        async def handle_approve_phrases(ack, body, logger):
            await ack()
            await self._handle_approve_phrases(body)
        
        @self.app.action("regenerate_phrases")
        async def handle_regenerate_phrases(ack, body, logger):
            await ack()
            await self._handle_regenerate_phrases(body)
        
        @self.app.action("modify_phrases")
        async def handle_modify_phrases(ack, body, logger):
            await ack()
            await self._handle_modify_phrases(body)
        
        @self.app.action("approve_samples")
        async def handle_approve_samples(ack, body, logger):
            await ack()
            await self._handle_approve_samples(body)
        
        @self.app.action("reject_samples")
        async def handle_reject_samples(ack, body, logger):
            await ack()
            await self._handle_reject_samples(body)
        
        @self.app.action("modify_individual")
        async def handle_modify_individual(ack, body, logger):
            await ack()
            await self._handle_modify_individual(body)
        
        @self.app.view("modify_phrases_modal")
        async def handle_modify_phrases_submit(ack, body, logger):
            await ack()
            await self._handle_modify_phrases_submit(body)
        
        @self.app.view("modify_individual_modal")
        async def handle_modify_individual_submit(ack, body, logger):
            await ack()
            await self._handle_modify_individual_submit(body)
        
        @self.app.event("file_shared")
        async def handle_file_shared(event, logger):
            await self._handle_file_upload(event)
    
    async def _handle_new_command(self, body: Dict):
        """Handle /stamp new command"""
        user_id = body["user"]["id"]
        
        # Create new stamp set
        stamp_set = self.workflow_manager.create_new_set(
            name=f"スタンプセット_{user_id}_{body['action_ts']}",
            slack_ts=body["container"]["message_ts"]
        )
        
        if not stamp_set:
            await self._send_message("❌ スタンプセットの作成に失敗しました。")
            return
        
        # Show stamp type selection
        await self._show_stamp_type_selection(stamp_set.id)
    
    async def _show_stamp_type_selection(self, set_id: str):
        """Show stamp type selection"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🆕 新しいスタンプセットを作成しました (ID: {set_id[:8]}...)\n\n"
                           f"スタンプのタイプを選択してください："
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🐾 動物キャラクター"},
                        "action_id": "select_stamp_type",
                        "value": f"{set_id}:animal",
                        "style": "primary"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "👤 オリジナルキャラクター"},
                        "action_id": "select_stamp_type",
                        "value": f"{set_id}:original_character"
                    }
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🥦 コンセプト系"},
                        "action_id": "select_stamp_type",
                        "value": f"{set_id}:concept"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🎲 AIにおまかせ"},
                        "action_id": "select_stamp_type",
                        "value": f"{set_id}:ai_free"
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 ヒント: コンセプト系はキャラクターなし、AIにおまかせは完全にAIに任せます"
                    }
                ]
            }
        ]
        
        await self._send_message("🎨 スタンプタイプを選択してください", blocks=blocks)
    
    async def _handle_stamp_type_selection(self, body: Dict):
        """Handle stamp type selection"""
        set_id, stamp_type = body["actions"][0]["value"].split(":")
        
        # Update stamp set with type and character_consistency
        from ..db.models import get_session
        from ..db.crud import StampSetCRUD
        
        db = get_session(self.workflow_manager.engine)
        try:
            crud = StampSetCRUD(db)
            stamp_set = crud.get(set_id)
            
            if not stamp_set:
                await self._send_message("❌ スタンプセットが見つかりません。")
                return
            
            # Set character_consistency based on type
            character_consistency = stamp_type != "concept"
            
            # Update stamp set
            stamp_set.genre = stamp_type
            stamp_set.character_consistency = character_consistency
            db.commit()
            
            # Ask about reference image
            await self._ask_reference_image(set_id)
            
        finally:
            db.close()
    
    async def _ask_reference_image(self, set_id: str):
        """Ask about reference image"""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"スタンプタイプを設定しました。\n\n"
                           f"元画像はありますか？"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🖼️ 画像あり"},
                        "action_id": "has_reference_image_yes",
                        "value": set_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✏️ 画像なし"},
                        "action_id": "has_reference_image_no",
                        "value": set_id
                    }
                ]
            }
        ]
        
        await self._send_message("📎 参照画像の確認", blocks=blocks)
    
    async def _handle_list_command(self, body: Dict):
        """Handle /stamp list command"""
        # Get all stamp sets
        from ..db.models import get_session
        from ..db.crud import StampSetCRUD
        
        db = get_session(self.workflow_manager.engine)
        try:
            crud = StampSetCRUD(db)
            stamp_sets = crud.get_all()
            
            if not stamp_sets:
                await self._send_message("📋 スタンプセットがありません。")
                return
            
            # Create list message
            lines = ["📋 スタンプセット一覧:"]
            for stamp_set in stamp_sets[:10]:  # Limit to 10
                status_emoji = {
                    'direction_pending': '⏳',
                    'direction_approved': '✅',
                    'patterns_pending': '📝',
                    'patterns_approved': '📋',
                    'samples_generating': '🎨',
                    'samples_review': '👀',
                    'full_generating': '🚀',
                    'full_review': '🔍',
                    'completed': '🎉'
                }.get(stamp_set.status, '❓')
                
                lines.append(f"{status_emoji} {stamp_set.name} ({stamp_set.status})")
            
            await self._send_message("\n".join(lines))
            
        finally:
            db.close()
    
    async def _handle_help_command(self, body: Dict):
        """Handle /stamp help command"""
        help_text = """
🤖 LINEスタンプ自動生成ツール ヘルプ

📝 コマンド一覧:
• `/stamp new` - 新しいスタンプセットを作成
• `/stamp list` - スタンプセット一覧を表示
• `/stamp help` - このヘルプを表示

🔄 ワークフロー:
1. キャラクター設定の決定
2. フレーズパターンの生成
3. サンプル5枚の作成
4. 全体の生成と完成

💡 ヒント:
• 参照画像があると品質が向上します
• 各ステップで修正や再生成が可能です
• 進捗はこのチャンネルで通知されます
        """
        
        await self._send_message(help_text)
    
    async def _handle_reference_image_response(self, body: Dict, has_image: bool):
        """Handle response about reference image"""
        set_id = body["actions"][0]["value"]
        
        if has_image:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📎 参照画像をこのチャンネルにアップロードしてください。\n\n"
                               "アップロード後、自動で処理を開始します。"
                    }
                }
            ]
            await self._send_message("📎 参照画像をアップロードしてください", blocks=blocks)
        else:
            # Start direction workflow without reference image
            self.workflow_manager.start_direction_workflow(set_id, has_reference_image=False)
    
    async def _handle_approve_direction(self, body: Dict, proposal_index: int):
        """Handle direction approval"""
        set_id = body["actions"][0]["value"].split(":")[0]
        self.workflow_manager.approve_direction(set_id, proposal_index)
    
    async def _handle_request_new_proposals(self, body: Dict):
        """Handle request for new proposals"""
        set_id = body["actions"][0]["value"]
        
        # Open modal for user input
        await self.client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "new_proposals_modal",
                "title": {"type": "plain_text", "text": "新しい案の要望"},
                "submit": {"type": "plain_text", "text": "提案"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "user_request",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "request",
                            "placeholder": {"type": "plain_text", "text": "希望するキャラクターの方向性を入力してください"},
                            "multiline": True
                        },
                        "label": {"type": "plain_text", "text": "要望"}
                    }
                ],
                "private_metadata": set_id
            }
        )
    
    async def _handle_approve_phrases(self, body: Dict):
        """Handle phrase approval"""
        set_id = body["actions"][0]["value"]
        self.workflow_manager.generate_sample_stamps(set_id)
    
    async def _handle_regenerate_phrases(self, body: Dict):
        """Handle phrase regeneration"""
        set_id = body["actions"][0]["value"]
        self.workflow_manager._generate_phrase_patterns(set_id)
    
    async def _handle_modify_phrases(self, body: Dict):
        """Handle phrase modification request"""
        set_id = body["actions"][0]["value"]
        
        # Open modal for modification
        await self.client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "modify_phrases_modal",
                "title": {"type": "plain_text", "text": "フレーズ修正"},
                "submit": {"type": "plain_text", "text": "修正"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "add_phrases",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "add",
                            "placeholder": {"type": "plain_text", "text": "追加したいフレーズ"},
                            "multiline": True
                        },
                        "label": {"type": "plain_text", "text": "追加フレーズ"}
                    },
                    {
                        "type": "input",
                        "block_id": "remove_phrases",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "remove",
                            "placeholder": {"type": "plain_text", "text": "削除したいフレーズ"},
                            "multiline": True
                        },
                        "label": {"type": "plain_text", "text": "削除フレーズ"}
                    },
                    {
                        "type": "input",
                        "block_id": "other_requests",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "other",
                            "placeholder": {"type": "plain_text", "text": "その他の要望"},
                            "multiline": True
                        },
                        "label": {"type": "plain_text", "text": "その他要望"},
                        "optional": True
                    }
                ],
                "private_metadata": set_id
            }
        )
    
    async def _handle_approve_samples(self, body: Dict):
        """Handle sample approval"""
        set_id = body["actions"][0]["value"]
        self.workflow_manager.generate_full_stamps(set_id)
    
    async def _handle_reject_samples(self, body: Dict):
        """Handle sample rejection"""
        set_id = body["actions"][0]["value"]
        self.workflow_manager.generate_sample_stamps(set_id)  # Regenerate
    
    async def _handle_modify_individual(self, body: Dict):
        """Handle individual modification request"""
        set_id = body["actions"][0]["value"]
        
        # Open modal for individual modification
        await self.client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "modify_individual_modal",
                "title": {"type": "plain_text", "text": "個別修正"},
                "submit": {"type": "plain_text", "text": "修正"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "stamp_number",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "number",
                            "placeholder": {"type": "plain_text", "text": "例: 1, 5, 10"}
                        },
                        "label": {"type": "plain_text", "text": "スタンプ番号"}
                    },
                    {
                        "type": "input",
                        "block_id": "modification_type",
                        "element": {
                            "type": "static_select",
                            "action_id": "type",
                            "placeholder": {"type": "plain_text", "text": "修正箇所を選択"},
                            "options": [
                                {"text": {"type": "plain_text", "text": "ポーズ"}, "value": "pose"},
                                {"text": {"type": "plain_text", "text": "表情"}, "value": "expression"},
                                {"text": {"type": "plain_text", "text": "その他"}, "value": "other"}
                            ]
                        },
                        "label": {"type": "plain_text", "text": "修正種別"}
                    },
                    {
                        "type": "input",
                        "block_id": "modification_detail",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "detail",
                            "placeholder": {"type": "plain_text", "text": "具体的な修正内容"},
                            "multiline": True
                        },
                        "label": {"type": "plain_text", "text": "修正詳細"}
                    }
                ],
                "private_metadata": set_id
            }
        )
    
    async def _handle_file_upload(self, event: Dict):
        """Handle file upload event"""
        file_id = event["file_id"]
        user_id = event["user_id"]
        
        try:
            # Get file info
            file_info = await self.client.files_info(file=file_id)
            file_url = file_info["file"]["url_private"]
            
            # Download file
            response = await self.client.files_download(url=file_url)
            
            # Save file and update stamp set
            # This would need to be implemented based on the current workflow state
            
            await self._send_message("✅ 参照画像を受け付けました。処理を開始します...")
            
        except Exception as e:
            await self._send_message(f"❌ 画像の処理に失敗しました: {str(e)}")
    
    async def _send_message(self, text: str, blocks: Optional[List[Dict]] = None):
        """Send message to channel"""
        try:
            await self.client.chat_postMessage(
                channel=self.channel_id,
                text=text,
                blocks=blocks
            )
        except Exception as e:
            print(f"Error sending message: {e}")
    
    async def start(self):
        """Start the Slack bot"""
        handler = AsyncSocketModeHandler(
            self.app,
            os.getenv("SLACK_APP_TOKEN")
        )
        
        # Send welcome message with quick start button
        await self._send_welcome_message()
        
        await handler.start()
    
    async def _send_welcome_message(self):
        """Send welcome message with quick start button"""
        blocks = get_welcome_blocks()
        await self._send_message("🎨 LINEスタンプ自動生成ツールが起動しました！", blocks=blocks)
