"""設定管理モジュール。

環境変数から API キーとプロジェクト設定を読み込む。
"""

import os


# Google Cloud
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET")

# LLM
MODEL_ID = "gemini-2.0-flash"

# Finnhub
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Marketaux
MARKETAUX_API_KEY = os.environ.get("MARKETAUX_API_KEY", "")
MARKETAUX_BASE_URL = "https://api.marketaux.com/v1"

# FRED
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# Reddit
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = "market-intelligence-agent/1.0"

# Financial Datasets (MCP)
FINANCIAL_DATASETS_API_KEY = os.environ.get("FINANCIAL_DATASETS_API_KEY", "")
