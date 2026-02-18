# Welcome message utilities for Slack bot

def get_welcome_blocks():
    """Get welcome message blocks for Slack"""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🎨 LINEスタンプ自動生成ツール"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "ようこそ！LINEスタンプの自動生成を開始できます。\n\n"
                       "📝 *コマンド:*\n"
                       "• `/stamp new` - 新しいスタンプセットを作成\n"
                       "• `/stamp list` - スタンプセット一覧を表示\n"
                       "• `/stamp help` - ヘルプを表示\n\n"
                       "🚀 *または、下のボタンからすぐに始められます！*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🆕 新しいスタンプセットを作成"
                    },
                    "action_id": "create_new_stamp_set",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 スタンプセット一覧"
                    },
                    "action_id": "show_stamp_list"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 ヒント: 参照画像があると、より高品質なスタンプが生成できます。"
                }
            ]
        }
    ]

def get_quick_start_blocks():
    """Get quick start blocks for easy access"""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "🚀 *クイックスタート*\n"
                       "新しいスタンプセットを作成する準備ができましたか？"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "🆕 /stamp new"
                    },
                    "action_id": "create_new_stamp_set",
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 /stamp list"
                    },
                    "action_id": "show_stamp_list"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "❓ /stamp help"
                    },
                    "action_id": "show_help"
                }
            ]
        }
    ]
