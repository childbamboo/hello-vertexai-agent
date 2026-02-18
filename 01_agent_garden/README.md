# 01 - Agent Garden

Agent Garden は Vertex AI Agent Builder の **Preview** 機能で、
事前構築済みのエージェントやツールを閲覧・利用できるカタログです。

## 概要

- **エージェント**: カスタマーサービス、データ分析、クリエイティブライティングなどの
  ユースケースに対応したプリビルトソリューション
- **ツール**: データベース操作、外部 API 呼び出しなど、個別の機能コンポーネント
- **Cloud API Registry**: 組織内で承認されたツール (MCP サーバー) を一元管理

## 前提条件

```bash
gcloud services enable cloudapiregistry.googleapis.com apihub.googleapis.com \
  --project=$PROJECT_ID
```

必要な IAM ロール: `roles/apiregistry.viewer`

## 実行

```bash
export PROJECT_ID="your-project-id"
python main.py
```
