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

すべて無料で取得可能。所要時間は各 API とも 2〜5 分程度。

---

### 5.1 Finnhub

> **環境変数:** `FINNHUB_API_KEY`

1. https://finnhub.io/register にアクセス
2. メールアドレスとパスワードで **Sign Up**
3. メール認証を完了
4. ログイン後、ダッシュボード (https://finnhub.io/dashboard) を開く
5. **API Key** セクションにキーが表示されている（自動発行済み）
6. キーをコピーして環境変数にセット

```bash
export FINNHUB_API_KEY="c1234567890abcdef"
```

**確認コマンド:**

```bash
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=$FINNHUB_API_KEY"
```

---

### 5.2 Marketaux

> **環境変数:** `MARKETAUX_API_KEY`

1. https://www.marketaux.com/register にアクセス
2. メールアドレスとパスワードで **Create Account**（クレジットカード不要）
3. メール認証を完了
4. ログイン後、ダッシュボード (https://www.marketaux.com/dashboard) を開く
5. **Your API Token** セクションにトークンが表示される
6. トークンをコピーして環境変数にセット

```bash
export MARKETAUX_API_KEY="abcdefg1234567890"
```

**確認コマンド:**

```bash
curl "https://api.marketaux.com/v1/news/all?symbols=AAPL&filter_entities=true&limit=1&api_token=$MARKETAUX_API_KEY"
```

---

### 5.3 FRED (Federal Reserve Economic Data)

> **環境変数:** `FRED_API_KEY`

1. https://fredaccount.stlouisfed.org/apikeys にアクセス
2. 初めての場合は **Create Account** からアカウント作成（メール + パスワード）
3. ログイン後、**API Keys** ページで **Request API Key** をクリック
4. 用途の説明を入力（例: `Market intelligence research project`）
5. 利用規約に同意して **Request API Key**
6. 発行されたキーをコピーして環境変数にセット

```bash
export FRED_API_KEY="abcdefghijklmnop1234567890"
```

**確認コマンド:**

```bash
curl "https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=$FRED_API_KEY&file_type=json&limit=1&sort_order=desc"
```

---

### 5.4 Reddit

> **環境変数:** `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`

1. Reddit アカウントでログイン（なければ https://www.reddit.com/register で作成）
2. https://www.reddit.com/prefs/apps にアクセス
3. ページ下部の **create another app...** をクリック
4. 以下を入力:
   - **name:** `market-intelligence-agent`（任意）
   - **App type:** **script** を選択（個人利用・開発用）
   - **description:** `Market intelligence PoC`（任意）
   - **about url:** 空欄で OK
   - **redirect uri:** `http://localhost:8080`（script 型では使わないが必須項目）
5. **create app** をクリック
6. 作成されたアプリ情報を確認:
   - **client_id:** アプリ名の直下に表示される短い文字列（例: `Ab1Cd2Ef3Gh4Ij`）
   - **secret:** `secret` の横に表示される文字列
7. それぞれを環境変数にセット

```bash
export REDDIT_CLIENT_ID="Ab1Cd2Ef3Gh4Ij"
export REDDIT_CLIENT_SECRET="KlMnOpQrStUvWxYz1234567890"
```

**確認コマンド (Python):**

```python
import praw
reddit = praw.Reddit(
    client_id="$REDDIT_CLIENT_ID",
    client_secret="$REDDIT_CLIENT_SECRET",
    user_agent="market-intelligence-agent/1.0",
)
print(list(reddit.subreddit("stocks").hot(limit=1)))
```

---

### 5.5 Financial Datasets (MCP 用)

> **環境変数:** `FINANCIAL_DATASETS_API_KEY`

1. https://financialdatasets.ai/ にアクセス
2. **Sign Up** からメールアドレスとパスワードで登録
3. メール認証を完了
4. ログイン後、ダッシュボードで API キーを確認
5. キーをコピーして環境変数にセット

```bash
export FINANCIAL_DATASETS_API_KEY="fd_abcdefg1234567890"
```

**確認コマンド:**

```bash
curl -H "X-API-Key: $FINANCIAL_DATASETS_API_KEY" \
  "https://api.financialdatasets.ai/financial-statements/income-statements?ticker=AAPL&period=annual&limit=1"
```

---

### 5.6 一括設定用テンプレート

すべてのキーを取得後、以下を `.env` ファイルとして保存し `source` で読み込む:

```bash
# .env (このファイルは .gitignore に追加すること)

# Google Cloud
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"
export STAGING_BUCKET="gs://your-bucket-vertexai-staging"

# Finnhub - https://finnhub.io/dashboard
export FINNHUB_API_KEY=""

# Marketaux - https://www.marketaux.com/dashboard
export MARKETAUX_API_KEY=""

# FRED - https://fredaccount.stlouisfed.org/apikeys
export FRED_API_KEY=""

# Reddit - https://www.reddit.com/prefs/apps
export REDDIT_CLIENT_ID=""
export REDDIT_CLIENT_SECRET=""

# Financial Datasets - https://financialdatasets.ai/
export FINANCIAL_DATASETS_API_KEY=""
```

```bash
source .env
```
