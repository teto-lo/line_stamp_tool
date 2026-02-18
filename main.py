import os
import asyncio
import threading
import time
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from core.workflow import StampWorkflowManager
from slack.bot import SlackBot
from web.app import app as web_app
import uvicorn

load_dotenv()

class LineStampTool:
    def __init__(self):
        self.workflow_manager = StampWorkflowManager()
        self.slack_bot = None
        self.web_server = None
        self.running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
        
        # Stop web server
        if self.web_server:
            self.web_server.should_exit = True
        
        sys.exit(0)
    
    def setup_slack_callback(self):
        """Set up Slack callback for workflow notifications"""
        async def slack_notification(message: str, blocks: list = None):
            if self.slack_bot:
                try:
                    await self.slack_bot._send_message(message, blocks)
                except Exception as e:
                    print(f"Error sending Slack notification: {e}")
        
        self.workflow_manager.set_slack_callback(slack_notification)
    
    def start_web_server(self):
        """Start FastAPI web server"""
        port = int(os.getenv('WEB_UI_PORT', 8080))
        
        print(f"🌐 Starting web server on http://localhost:{port}")
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=web_app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
        self.web_server = uvicorn.Server(config)
        
        # Run in thread
        def run_web():
            try:
                self.web_server.run()
            except Exception as e:
                print(f"Web server error: {e}")
        
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        return web_thread
    
    async def start_slack_bot(self):
        """Start Slack bot"""
        print("🤖 Starting Slack bot...")
        
        try:
            self.slack_bot = SlackBot(self.workflow_manager)
            self.setup_slack_callback()
            
            # Test SD WebUI connection
            if self.workflow_manager.sd_api.test_connection():
                print("✅ Stable Diffusion WebUI connection successful")
            else:
                print("⚠️  Warning: Could not connect to Stable Diffusion WebUI")
                print("   Make sure SD WebUI is running with --api --nowebui flags")
            
            await self.slack_bot.start()
            
        except Exception as e:
            print(f"❌ Error starting Slack bot: {e}")
            raise
    
    def run(self):
        """Main entry point"""
        print("🎨 LINE Stamp Auto-Generation Tool")
        print("=" * 50)
        
        # Check environment variables
        required_vars = [
            'SLACK_BOT_TOKEN',
            'SLACK_APP_TOKEN', 
            'SLACK_CHANNEL_ID',
            'GEMINI_API_KEY',
            'SD_WEBUI_URL'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease check your .env file.")
            return
        
        # Create necessary directories
        output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
        lora_dir = Path(os.getenv('LORA_EXPORT_DIR', './lora_export'))
        data_dir = Path(os.getenv('DB_PATH', './data')).parent
        
        for directory in [output_dir, lora_dir, data_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directory structure verified")
        
        # Start web server
        try:
            web_thread = self.start_web_server()
            print("✅ Web server started")
        except Exception as e:
            print(f"❌ Failed to start web server: {e}")
            return
        
        # Start Slack bot
        try:
            self.running = True
            asyncio.run(self.start_slack_bot())
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False

def main():
    """Main function"""
    tool = LineStampTool()
    tool.run()

if __name__ == "__main__":
    main()
