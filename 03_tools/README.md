# 03 - ツール (Tools)

Vertex AI Agent Builder で利用可能な各種ツールのサンプルです。

## 対象ツール

| ツール | 説明 |
|--------|------|
| **Function Calling** | カスタム関数を Gemini モデルに呼び出させる |
| **Code Execution** | Python コードを安全なサンドボックスで実行 |
| **Google Search Grounding** | Google 検索でモデルの回答を裏付ける |
| **RAG Retrieval Tool** | RAG Engine のコーパスを検索ツールとして利用 |

## 前提条件

```bash
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
```

## 実行

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
python main.py
```
