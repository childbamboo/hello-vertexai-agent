#!/usr/bin/env bash
# =============================================================================
# Vertex AI Agent Builder セットアップスクリプト
#
# 使い方:
#   export PROJECT_ID="your-project-id"
#   export REGION="us-central1"
#   bash setup.sh
# =============================================================================
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?'環境変数 PROJECT_ID を設定してください'}"
REGION="${REGION:-us-central1}"
BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-vertexai-staging}"

echo "==== プロジェクト: ${PROJECT_ID} / リージョン: ${REGION} ===="

# ---------------------------------------------------------
# 1. gcloud プロジェクト設定
# ---------------------------------------------------------
echo "[1/6] プロジェクトを設定..."
gcloud config set project "${PROJECT_ID}"

# ---------------------------------------------------------
# 2. 必要な API を有効化
# ---------------------------------------------------------
echo "[2/6] API を有効化..."
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  cloudresourcemanager.googleapis.com \
  --project="${PROJECT_ID}"

# Agent Garden (Cloud API Registry) 用 ── Preview 機能
echo "  - Cloud API Registry API を有効化..."
gcloud services enable \
  cloudapiregistry.googleapis.com \
  apihub.googleapis.com \
  --project="${PROJECT_ID}" 2>/dev/null || \
  echo "  (Cloud API Registry API は Preview のため有効化できない場合があります)"

# ---------------------------------------------------------
# 3. サービスアイデンティティ作成
# ---------------------------------------------------------
echo "[3/6] AI Platform サービスアイデンティティを作成..."
gcloud beta services identity create \
  --service=aiplatform.googleapis.com \
  --project="${PROJECT_ID}" 2>/dev/null || true

# ---------------------------------------------------------
# 4. IAM ロール付与 (現在のユーザー)
# ---------------------------------------------------------
echo "[4/6] IAM ロールを付与..."
CURRENT_USER=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
if [ -n "${CURRENT_USER}" ]; then
  for ROLE in roles/aiplatform.user roles/storage.objectAdmin; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="user:${CURRENT_USER}" \
      --role="${ROLE}" \
      --condition=None \
      --quiet 2>/dev/null || true
  done
  echo "  ロール付与先: ${CURRENT_USER}"
else
  echo "  (アクティブなアカウントが見つかりません。手動で IAM を設定してください)"
fi

# ---------------------------------------------------------
# 5. GCS ステージングバケット作成
# ---------------------------------------------------------
echo "[5/6] GCS ステージングバケットを作成..."
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
  echo "  バケット作成: gs://${BUCKET_NAME}"
else
  echo "  バケットは既に存在: gs://${BUCKET_NAME}"
fi

# ---------------------------------------------------------
# 6. Python 依存関係インストール
# ---------------------------------------------------------
echo "[6/6] Python パッケージをインストール..."
pip install -r requirements.txt --quiet

echo ""
echo "==== セットアップ完了 ===="
echo ""
echo "環境変数を確認:"
echo "  export PROJECT_ID=${PROJECT_ID}"
echo "  export REGION=${REGION}"
echo "  export STAGING_BUCKET=gs://${BUCKET_NAME}"
echo ""
echo "各サンプルの実行:"
echo "  python 01_agent_garden/main.py"
echo "  python 02_agent_engine/main.py"
echo "  python 03_tools/main.py"
echo "  python 04_rag_engine/main.py"
