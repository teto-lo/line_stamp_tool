# LINEスタンプ自動生成ツール

SlackをUIとして使い、Gemini APIとStable Diffusion WebUI APIを組み合わせてLINEスタンプを自動生成するツールです。

## 機能概要

- 🤖 **Slack連携**: Slackコマンドでスタンプ生成を開始
- 🎨 **AI生成**: Geminiでキャラクター設定とフレーズを自動生成
- 🖼️ **画像生成**: Stable Diffusionで高品質なスタンプを生成
- 🔄 **背景除去**: rembgで自動的に背景を透過処理
- 📊 **管理画面**: FastAPIでスタンプセットを管理
- 🤖 **LoRA対応**: 学習用データのエクスポート機能

## セットアップ

### 1. 環境変数の設定

`.env` ファイルを作成し、以下の環境変数を設定してください：

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_CHANNEL_ID=C...

# Google Gemini API
GEMINI_API_KEY=...

# Stable Diffusion WebUI
SD_WEBUI_URL=http://localhost:7860

# Database
DB_PATH=./data/stamps.db

# Output Directories
OUTPUT_DIR=./output
LORA_EXPORT_DIR=./lora_export

# Web UI
WEB_UI_PORT=8080
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. Stable Diffusion WebUIの準備

Stable Diffusion WebUIをAPIモードで起動します：

```bash
cd stable-diffusion-webui
# webui-user.bat に以下を追加:
# set COMMANDLINE_ARGS=--api --nowebui --xformers
webui-user.bat
```

### 4. 起動

```bash
python main.py
```

## 使用方法

### Slackコマンド

- `/stamp new` - 新しいスタンプセットを作成
- `/stamp list` - スタンプセット一覧を表示
- `/stamp help` - ヘルプを表示

### ワークフロー

1. **キャラクター設定**: Geminiがキャラクター案を3件提案
2. **フレーズ生成**: キャラクターに合わせたフレーズを30件生成
3. **サンプル生成**: 代表的な5枚のスタンプを生成
4. **全体生成**: 残りのスタンプをすべて生成
5. **完了**: 透過PNG画像セットとして保存

### 管理画面

`http://localhost:8080` にアクセスして、スタンプセットの管理ができます。

- スタンプセット一覧の表示
- 詳細情報の確認
- LoRA学習用データのエクスポート

## ディレクトリ構成

```
line_stamp_tool/
├── main.py                  # エントリーポイント
├── .env                     # 環境変数設定
├── requirements.txt         # 依存パッケージ
├── data/
│   └── stamps.db            # SQLite DB
├── output/                  # 生成済みスタンプの保存先
│   └── {set_id}/
│       ├── reference.png    # 参照画像
│       ├── stamp_01.png     # スタンプ画像
│       └── grid.png         # 確認用グリッド画像
├── lora_export/             # LoRA学習用データ
├── slack/                   # Slack Bot関連
├── core/                    # コア機能
├── db/                      # データベース関連
└── web/                     # Web UI関連
```

## APIエンドポイント

### Web UI

- `GET /` - スタンプセット一覧
- `GET /set/{id}` - スタンプセット詳細
- `GET /set/{id}/export-lora` - LoRAデータエクスポート

### REST API

- `GET /api/sets` - スタンプセット一覧（JSON）
- `GET /api/set/{id}` - スタンプセット詳細（JSON）

## 注意事項

### Windows環境特有の注意点

1. **rembgのインストール**:
   ```bash
   pip install onnxruntime-gpu
   pip install rembg
   ```

2. **パス区切り文字**: `pathlib.Path` を使用してクロスプラットフォーム対応

3. **SD WebUIの起動**: `--xformers` フラグでVRAM使用量を削減

### トラブルシューティング

1. **SD WebUI接続エラー**:
   - SD WebUIが `--api --nowebui` で起動しているか確認
   - ファイアウォール設定を確認

2. **Slack Bot応答なし**:
   - トークンが正しいか確認
   - Socket Modeが有効になっているか確認

3. **Gemini APIエラー**:
   - APIキーが正しいか確認
   - クォータ残量を確認

## ライセンス

MIT License

## 貢献

IssuesやPull Requestをお待ちしています。
