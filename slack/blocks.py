# This file contains Slack Block Kit UI components
# Currently, blocks are defined inline in bot.py for simplicity
# This file can be extended for reusable block components

from typing import Dict, List

class BlockKitBuilder:
    """Builder for Slack Block Kit components"""
    
    @staticmethod
    def approval_buttons(primary_action_id: str, primary_text: str, 
                        secondary_action_id: str, secondary_text: str,
                        tertiary_action_id: str = None, tertiary_text: str = None,
                        value: str = "") -> List[Dict]:
        """Create standard approval button set"""
        elements = [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": primary_text},
                "action_id": primary_action_id,
                "value": value,
                "style": "primary"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": secondary_text},
                "action_id": secondary_action_id,
                "value": value,
                "style": "danger"
            }
        ]
        
        if tertiary_action_id and tertiary_text:
            elements.append({
                "type": "button",
                "text": {"type": "plain_text", "text": tertiary_text},
                "action_id": tertiary_action_id,
                "value": value
            })
        
        return [{
            "type": "actions",
            "elements": elements
        }]
    
    @staticmethod
    def section_text(text: str) -> Dict:
        """Create a section block with text"""
        return {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text}
        }
    
    @staticmethod
    def image_block(image_url: str, alt_text: str) -> Dict:
        """Create an image block"""
        return {
            "type": "image",
            "image_url": image_url,
            "alt_text": alt_text
        }
    
    @staticmethod
    def context_text(text: str) -> Dict:
        """Create a context block with text"""
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": text
                }
            ]
        }
