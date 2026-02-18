# 02 - Agent Engine

Agent Engine (旧: Reasoning Engine) は、AI エージェントを
Google Cloud 上にデプロイ・管理・スケールするためのマネージドサービスです。

## 概要

- エージェントをクラウドにデプロイし、REST API でアクセス可能にする
- セッション管理 (短期記憶) と Memory Bank (長期記憶) を提供
- ADK, LangChain, LangGraph, LlamaIndex など主要フレームワークをサポート

## 前提条件

```bash
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID
```

## 実行

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export STAGING_BUCKET="gs://your-bucket"
python main.py
```

## gcloud でのリソース確認

```bash
# デプロイ済みエージェント (ReasoningEngine) 一覧
gcloud asset search-all-resources \
  --scope=projects/$PROJECT_ID \
  --asset-types='aiplatform.googleapis.com/ReasoningEngine' \
  --format="table(name,assetType,location)"
```
