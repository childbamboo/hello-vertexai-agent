# 04 - RAG Engine

Vertex AI RAG Engine を使った Retrieval-Augmented Generation のサンプルです。

## 概要

RAG Engine は、LLM のコンテキストをプライベートデータで拡張し、
ハルシネーションを低減して正確な回答を生成するためのマネージドサービスです。

## 処理の流れ

1. RAG コーパスを作成
2. ドキュメントをインポート (GCS / Google Drive / ローカル)
3. コーパスを検索 (Retrieval)
4. Gemini モデルと RAG を組み合わせて回答生成

## 前提条件

```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com \
  --project=$PROJECT_ID
```

## 実行

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
python main.py
```

## gcloud / curl でのリソース管理

```bash
# コーパス一覧
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/ragCorpora" \
  | python -m json.tool

# コーパス削除
curl -X DELETE -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/ragCorpora/CORPUS_ID"
```
