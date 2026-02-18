# API & MCP インテグレーション リファレンス

本ドキュメントでは、マーケットインテリジェンス Multi-Agent System で使用する外部 API と MCP サーバーの詳細を整理する。

---

## 1. API 一覧

### 1.1 Finnhub (メイン: 株価・ニュース)

| 項目 | 内容 |
|---|---|
| 公式サイト | https://finnhub.io/ |
| 無料枠 | あり (API キー登録制) |
| レート制限 | **60 req/min** |
| 認証 | API キー (クエリパラメータ `token` またはヘッダー `X-Finnhub-Token`) |
| MCP サーバー | あり (コミュニティ製: [finnhub-mcp](https://github.com/SalZaki/finnhub-mcp)) |

**利用するエンドポイント:**

| エンドポイント | 用途 | エージェント |
|---|---|---|
| `GET /api/v1/quote?symbol={symbol}` | リアルタイム株価 | Financial Agent |
| `GET /api/v1/company-profile2?symbol={symbol}` | 企業プロフィール | Financial Agent |
| `GET /api/v1/stock/metric?symbol={symbol}&metric=all` | 財務指標 | Financial Agent |
| `GET /api/v1/news?category={category}` | マーケットニュース | News Agent |
| `GET /api/v1/company-news?symbol={symbol}&from={date}&to={date}` | 企業ニュース | News Agent |
| `GET /api/v1/stock/social-sentiment?symbol={symbol}` | SNS センチメント | Sentiment Agent |

**Python 実装例:**

```python
import requests

FINNHUB_BASE = "https://finnhub.io/api/v1"

def get_stock_quote(symbol: str, api_key: str) -> dict:
    """リアルタイム株価を取得する。"""
    resp = requests.get(
        f"{FINNHUB_BASE}/quote",
        params={"symbol": symbol, "token": api_key},
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "symbol": symbol,
        "current_price": data["c"],
        "change": data["d"],
        "percent_change": data["dp"],
        "high": data["h"],
        "low": data["l"],
        "open": data["o"],
        "previous_close": data["pc"],
    }

def get_market_news(category: str, api_key: str, limit: int = 10) -> list:
    """マーケットニュースを取得する。"""
    resp = requests.get(
        f"{FINNHUB_BASE}/news",
        params={"category": category, "token": api_key},
    )
    resp.raise_for_status()
    return resp.json()[:limit]
```

---

### 1.2 Marketaux (ニュース + センチメント)

| 項目 | 内容 |
|---|---|
| 公式サイト | https://www.marketaux.com/ |
| 無料枠 | あり (API キー登録制、クレジットカード不要) |
| レート制限 | **100 req/day** |
| 認証 | API キー (クエリパラメータ `api_token`) |
| MCP サーバー | なし |

**利用するエンドポイント:**

| エンドポイント | 用途 | エージェント |
|---|---|---|
| `GET /v1/news/all` | ニュース全文検索 | News Agent |
| `GET /v1/entity/stats/{symbol}` | エンティティ統計 | News Agent |

**特徴:**

- 80+ グローバル市場、5,000+ ソース、30+ 言語をカバー
- 記事ごとに**センチメントスコア**と**エンティティタグ**が自動付与される
- 株式、指数、ETF、コモディティ、暗号通貨を横断検索可能

**Python 実装例:**

```python
def get_news_with_sentiment(
    symbols: str,
    api_key: str,
    limit: int = 10
) -> dict:
    """銘柄関連ニュースをセンチメント付きで取得する。"""
    resp = requests.get(
        "https://api.marketaux.com/v1/news/all",
        params={
            "symbols": symbols,
            "filter_entities": "true",
            "language": "en",
            "limit": limit,
            "api_token": api_key,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "articles": [
            {
                "title": article["title"],
                "description": article["description"],
                "source": article["source"],
                "published_at": article["published_at"],
                "sentiment": article.get("entities", [{}])[0].get("sentiment_score"),
            }
            for article in data.get("data", [])
        ],
        "total": data.get("meta", {}).get("found"),
    }
```

---

### 1.3 FRED (経済指標)

| 項目 | 内容 |
|---|---|
| 公式サイト | https://fred.stlouisfed.org/docs/api/fred/ |
| 無料枠 | **完全無料** |
| レート制限 | **120 req/min** |
| 認証 | API キー (登録: https://fredaccount.stlouisfed.org/apikeys) |
| Python ライブラリ | `fredapi` (`pip install fredapi`) |
| MCP サーバー | なし |

**主要なデータ系列:**

| シリーズ ID | 指標 | 用途 |
|---|---|---|
| `GDP` | 米国 GDP | マクロ経済分析 |
| `UNRATE` | 失業率 | 雇用動向 |
| `CPIAUCSL` | 消費者物価指数 (CPI) | インフレ分析 |
| `FEDFUNDS` | FF 金利 | 金融政策 |
| `DGS10` | 10年国債利回り | 金利環境 |
| `SP500` | S&P 500 指数 | 市場ベンチマーク |
| `VIXCLS` | VIX (恐怖指数) | ボラティリティ |

**Python 実装例:**

```python
from fredapi import Fred

def get_economic_indicators(api_key: str) -> dict:
    """主要経済指標の最新値を取得する。"""
    fred = Fred(api_key=api_key)

    indicators = {
        "gdp_growth": "GDP",
        "unemployment_rate": "UNRATE",
        "cpi": "CPIAUCSL",
        "fed_funds_rate": "FEDFUNDS",
        "treasury_10y": "DGS10",
        "vix": "VIXCLS",
    }

    results = {}
    for name, series_id in indicators.items():
        series = fred.get_series(series_id, observation_start="2024-01-01")
        latest = series.dropna().iloc[-1]
        results[name] = {
            "value": float(latest),
            "date": str(series.dropna().index[-1].date()),
            "series_id": series_id,
        }

    return results
```

---

### 1.4 Reddit API (SNS センチメント)

| 項目 | 内容 |
|---|---|
| 公式サイト | https://www.reddit.com/dev/api/ |
| 無料枠 | あり (非商用 / 個人 / 学術用途) |
| レート制限 | **100 req/min** (OAuth 認証時) |
| 認証 | OAuth2 (reddit.com/prefs/apps で登録) |
| Python ライブラリ | `praw` (`pip install praw`) |
| MCP サーバー | 複数あり (後述) |

**対象サブレディット:**

| サブレディット | 特徴 | 購読者数 |
|---|---|---|
| r/wallstreetbets | 個人投資家のセンチメント、ミーム株 | 16M+ |
| r/stocks | 一般的な株式議論 | 7M+ |
| r/investing | 長期投資議論 | 2M+ |
| r/options | オプション取引 | 1M+ |
| r/SecurityAnalysis | ファンダメンタル分析 | 200K+ |

**Python 実装例:**

```python
import praw

def get_reddit_posts(
    client_id: str,
    client_secret: str,
    subreddits: list[str],
    query: str,
    limit: int = 50,
) -> dict:
    """Reddit から投稿を取得する。"""
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent="market-intelligence-agent/1.0",
    )

    posts = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for post in subreddit.search(query, sort="new", limit=limit):
            posts.append({
                "subreddit": subreddit_name,
                "title": post.title,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "created_utc": post.created_utc,
                "selftext": post.selftext[:500],
            })

    return {
        "total_posts": len(posts),
        "posts": sorted(posts, key=lambda x: x["score"], reverse=True),
    }
```

---

### 1.5 Financial Datasets (ファンダメンタルデータ)

| 項目 | 内容 |
|---|---|
| 公式サイト | https://financialdatasets.ai/ |
| 無料枠 | あり (API キー登録制) |
| 認証 | API キーまたは OAuth 2.1 |
| MCP サーバー | **あり (公式)**: [financial-datasets/mcp-server](https://github.com/financial-datasets/mcp-server) |

**MCP ツール:**

| ツール名 | 説明 |
|---|---|
| `get_income_statements` | 損益計算書 |
| `get_balance_sheets` | 貸借対照表 |
| `get_cash_flow_statements` | キャッシュフロー計算書 |
| `get_current_stock_price` | 現在の株価 |
| `get_historical_stock_prices` | 過去の株価推移 |
| `get_company_news` | 企業関連ニュース |

---

### 1.6 Google Search Grounding (バックアップ)

既存の `03_tools` モジュールで実装済み。Gemini の `Tool.from_google_search_retrieval()` を使用し、リアルタイム Web 検索結果でモデルの回答をグラウンディングする。

他 API のレート制限に達した場合のフォールバックとして利用可能。

---

## 2. MCP サーバー設定

### 2.1 ADK での MCP 統合パターン

```python
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

# Stdio トランスポート (ローカル MCP サーバー)
financial_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@financial-datasets/mcp-server"],
        env={"FINANCIAL_DATASETS_API_KEY": "your_key"},
    ),
)

# エージェントにMCPツールを追加
financial_agent = Agent(
    name="financial_analysis_agent",
    model="gemini-2.0-flash",
    instruction="...",
    tools=[financial_mcp, get_stock_quote, get_economic_indicators],
)
```

### 2.2 利用可能な MCP サーバー一覧

| MCP サーバー | 種別 | データ内容 | 接続方式 | 優先度 |
|---|---|---|---|---|
| Financial Datasets MCP | 公式 | 財務諸表、株価、ニュース | Stdio (npx) | **高** |
| Alpha Vantage MCP | 公式 | 株価、テクニカル指標 | SSE | 低 (25 req/day) |
| Finnhub MCP | コミュニティ | リアルタイム株価、企業データ | Stdio / SSE | 中 |
| Reddit Sentiment MCP | コミュニティ | Reddit センチメント分析 | Stdio | 中 |
| MCP Server Reddit | コミュニティ | Reddit 投稿取得 | Stdio | 中 |
| News API MCP (Pipedream) | 公式 | ニュース検索 | SSE | 低 (100 req/day) |

### 2.3 推奨構成

PoC ではシンプルさを優先し、以下の組み合わせを推奨する:

```
[MCP で接続]
  └── Financial Datasets MCP Server   → ファンダメンタルデータ

[Python 関数で直接実装]
  ├── Finnhub API (requests)          → 株価・ニュース (60 req/min で十分)
  ├── FRED API (fredapi)              → 経済指標 (Python ライブラリが便利)
  ├── Reddit API (praw)               → センチメント (Python ライブラリが便利)
  └── Marketaux API (requests)        → ニュースセンチメント補完
```

**理由:**

- MCP サーバーは ADK との統合を示すデモとして Financial Datasets で 1 つ導入
- 残りは Python 関数の方がデバッグ容易でレート制限の制御もしやすい
- 本番移行時に段階的に MCP サーバーに移行可能

---

## 3. 環境変数

```bash
# Google Cloud
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export STAGING_BUCKET="gs://your-bucket-vertexai-staging"

# Finnhub
export FINNHUB_API_KEY="your_finnhub_api_key"

# Marketaux
export MARKETAUX_API_KEY="your_marketaux_api_key"

# FRED
export FRED_API_KEY="your_fred_api_key"

# Reddit
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"

# Financial Datasets (MCP)
export FINANCIAL_DATASETS_API_KEY="your_financial_datasets_api_key"
```

---

## 4. 追加依存パッケージ

```
# requirements.txt に追加
google-cloud-aiplatform[agent_engines,adk]>=1.112
google-adk>=1.0.0
google-auth>=2.0.0
requests>=2.31.0
fredapi>=0.5.0
praw>=7.7.0
```

---

## 5. API キー取得手順

| API | 取得 URL | 所要ステップ |
|---|---|---|
| Finnhub | https://finnhub.io/register | メール登録 → ダッシュボードでキー取得 |
| Marketaux | https://www.marketaux.com/register | メール登録 → ダッシュボードでキー取得 |
| FRED | https://fredaccount.stlouisfed.org/apikeys | メール登録 → API キー申請 |
| Reddit | https://www.reddit.com/prefs/apps | Reddit アカウント → "create app" → script 型で登録 |
| Financial Datasets | https://financialdatasets.ai/ | メール登録 → API キー取得 |
