# hello-vertexai-agent

Google Cloud Vertex AI Agent Builder の主要機能を試すサンプル集です。

## サンプル一覧

| ディレクトリ | 機能 | ステータス | 説明 |
|---|---|---|---|
| `01_agent_garden/` | Agent Garden | Preview | Cloud API Registry を使ったツール統合 |
| `02_agent_engine/` | Agent Engine | GA | エージェントのデプロイ・管理・クエリ |
| `03_tools/` | ツール | GA | Function Calling / Code Execution / Google Search Grounding |
| `04_rag_engine/` | RAG Engine | GA | コーパス作成・ドキュメントインポート・検索・生成 |

## クイックスタート

### 1. 前提条件

- Google Cloud プロジェクト
- `gcloud` CLI がインストール・認証済み
- Python 3.10+

### 2. セットアップ

```bash
# プロジェクトIDを設定
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# API有効化・IAM設定・依存関係インストールを一括実行
bash setup.sh
```

`setup.sh` が行うこと:

- `gcloud config set project` でプロジェクト設定
- 必要な API を有効化 (`aiplatform`, `storage`, `logging`, `monitoring` 等)
- AI Platform サービスアイデンティティ作成
- 現在のユーザーに `aiplatform.user` / `storage.objectAdmin` ロールを付与
- GCS ステージングバケットを作成
- `pip install -r requirements.txt` で Python パッケージインストール

### 3. 各サンプルの実行

```bash
# Agent Garden: API Registry からツールを取得してエージェントに統合
python 01_agent_garden/main.py

# Agent Engine: エージェントをクラウドにデプロイ・クエリ
export STAGING_BUCKET="gs://${PROJECT_ID}-vertexai-staging"
python 02_agent_engine/main.py

# ツール: Function Calling / Code Execution / Search Grounding
python 03_tools/main.py

# RAG Engine: コーパス作成・ドキュメントインポート・検索・生成
python 04_rag_engine/main.py
```

## 構成

```
.
├── README.md
├── setup.sh              # gcloud セットアップスクリプト
├── requirements.txt      # Python 依存関係
├── 01_agent_garden/
│   ├── README.md
│   └── main.py           # Agent Garden (Cloud API Registry) サンプル
├── 02_agent_engine/
│   ├── README.md
│   ├── agent.py           # デプロイ用エージェント定義
│   └── main.py           # デプロイ・クエリ・クリーンアップ
├── 03_tools/
│   ├── README.md
│   └── main.py           # Function Calling / Code Exec / Grounding
└── 04_rag_engine/
    ├── README.md
    └── main.py           # RAG コーパス作成・インポート・検索・生成
```

## 環境変数

| 変数 | 必須 | 説明 | 例 |
|---|---|---|---|
| `PROJECT_ID` | Yes | Google Cloud プロジェクト ID | `my-project-123` |
| `REGION` | No | リージョン (デフォルト: `us-central1`) | `us-central1` |
| `STAGING_BUCKET` | 02 のみ | Agent Engine 用 GCS バケット | `gs://my-bucket` |
| `BUCKET_NAME` | No | setup.sh 用バケット名 | `my-staging-bucket` |

## gcloud コマンドリファレンス

```bash
# ----- API 有効化 -----
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID

# ----- デプロイ済み Agent Engine (ReasoningEngine) 一覧 -----
gcloud asset search-all-resources \
  --scope=projects/$PROJECT_ID \
  --asset-types='aiplatform.googleapis.com/ReasoningEngine'

# ----- RAG コーパス一覧 (REST API) -----
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/ragCorpora"

# ----- RAG コーパス削除 -----
curl -X DELETE -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/ragCorpora/CORPUS_ID"
```
