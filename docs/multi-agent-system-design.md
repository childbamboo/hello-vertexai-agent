# マーケットインテリジェンス Multi-Agent System 設計書

## 1. 概要

### 1.1 目的

Google Cloud Agent Development Kit (ADK) を使用して、マーケットインテリジェンスを提供する Multi-Agent System の PoC を構築する。複数の専門エージェントが並列・逐次に連携し、ライブデータを活用して市場分析と投資推奨を生成する。

### 1.2 ユースケース

ヘッジファンド向けの AI 駆動マーケットインテリジェンス。ニュース・SNS・財務データ・経済指標をリアルタイムに分析し、投資判断を支援する。

### 1.3 技術スタック

| コンポーネント | 技術 |
|---|---|
| エージェントフレームワーク | Google ADK (`google-adk`) |
| LLM | Gemini 2.0 Flash |
| ツール連携 | MCP (Model Context Protocol) + Python 関数 |
| デプロイ | Vertex AI Agent Engine |
| 言語 | Python 3.11+ |

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
                          ┌──────────────────────────────┐
                          │     ユーザー (Investor)       │
                          └──────────────┬───────────────┘
                                         │ 質問・分析リクエスト
                                         ▼
                          ┌──────────────────────────────┐
                          │   Orchestrator Agent (Root)   │
                          │   - リクエスト解析            │
                          │   - ワークフロー制御          │
                          │   - 最終レポート生成          │
                          └──────────────┬───────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
    ┌──────────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
    │  Phase 1: 並列収集    │  │ Phase 2: 分析   │  │ Phase 3: 戦略立案   │
    │  (ParallelAgent)     │  │ (LlmAgent)      │  │ (LlmAgent)         │
    └──────────┬───────────┘  └────────┬────────┘  └─────────┬───────────┘
               │                       │                     │
    ┌──────────┼──────────┐            │                     │
    │          │          │            │                     │
    ▼          ▼          ▼            ▼                     ▼
  News    Financial  Sentiment    Trend             Strategy
  Agent    Agent      Agent      Analysis           Agent
                                  Agent
```

### 2.2 処理フロー

ADK のワークフローエージェントを組み合わせた **Sequential + Parallel** パターンを採用する。

```
SequentialAgent (market_intelligence_pipeline)
│
├── Phase 1: ParallelAgent (data_collection)
│   ├── News & Social Media Agent    → output_key: "news_data"
│   ├── Financial Analysis Agent     → output_key: "financial_data"
│   └── Sentiment Agent              → output_key: "sentiment_data"
│
├── Phase 2: LlmAgent (trend_analysis)
│   └── Trend Analysis Agent         → output_key: "trend_analysis"
│       (入力: news_data, financial_data, sentiment_data)
│
└── Phase 3: LlmAgent (strategy)
    └── Strategy Agent               → output_key: "strategy_report"
        (入力: trend_analysis + 全データ)
```

### 2.3 ADK 実装イメージ

```python
from google.adk.agents import Agent, SequentialAgent, ParallelAgent

# Phase 1: 並列データ収集
data_collection = ParallelAgent(
    name="data_collection",
    description="市場データを並列に収集する",
    sub_agents=[news_agent, financial_agent, sentiment_agent],
)

# Phase 2: トレンド分析
trend_analysis_agent = Agent(
    name="trend_analysis",
    model="gemini-2.0-flash",
    description="収集データからトレンドを分析する",
    instruction="""
    以下のデータを統合分析し、市場トレンドを特定せよ:
    - ニュースデータ: {news_data}
    - 財務データ: {financial_data}
    - センチメントデータ: {sentiment_data}
    """,
    output_key="trend_analysis",
)

# Phase 3: 戦略立案
strategy_agent = Agent(
    name="strategy",
    model="gemini-2.0-flash",
    description="トレンド分析に基づき投資戦略を推奨する",
    instruction="""
    以下の分析結果に基づき、実行可能な投資推奨を生成せよ:
    - トレンド分析: {trend_analysis}
    - 生データ: {news_data}, {financial_data}, {sentiment_data}
    """,
    output_key="strategy_report",
)

# パイプライン全体
pipeline = SequentialAgent(
    name="market_intelligence_pipeline",
    description="マーケットインテリジェンスの分析パイプライン",
    sub_agents=[data_collection, trend_analysis_agent, strategy_agent],
)
```

---

## 3. エージェント詳細設計

### 3.1 News & Social Media Agent

**役割:** ニュース記事と SNS から業界トレンド・イベントを収集する

| 項目 | 内容 |
|---|---|
| 名前 | `news_social_media_agent` |
| モデル | `gemini-2.0-flash` |
| output_key | `news_data` |
| ツール | Finnhub Market News API, Marketaux API, Google Search Grounding |

**ツール定義:**

```python
def get_market_news(category: str = "general") -> dict:
    """Finnhub から最新の市場ニュースを取得する。

    Args:
        category: ニュースカテゴリ (general, forex, crypto, merger)
    Returns:
        ニュース記事のリスト (タイトル, 要約, ソース, 日時)
    """

def get_financial_news_with_sentiment(
    symbols: str,
    limit: int = 10
) -> dict:
    """Marketaux から銘柄関連ニュースとセンチメントを取得する。

    Args:
        symbols: カンマ区切りのティッカーシンボル (例: "AAPL,GOOGL")
        limit: 取得件数
    Returns:
        ニュース記事リスト (タイトル, 要約, センチメントスコア, エンティティ)
    """
```

**インストラクション:**

```
あなたは市場ニュースの専門アナリストです。以下のタスクを実行してください:
1. 対象銘柄・セクターに関する最新ニュースを収集
2. 重要なイベント (決算発表, M&A, 規制変更等) を特定
3. 各ニュースの市場インパクトを HIGH / MEDIUM / LOW で評価
4. 結果を構造化された JSON 形式で出力

出力形式:
{
  "summary": "市場ニュースの全体サマリー",
  "key_events": [...],
  "news_items": [
    {"title": "...", "source": "...", "impact": "HIGH", "sentiment": "positive", "relevance": "..."}
  ]
}
```

---

### 3.2 Financial Analysis Agent

**役割:** 株価・決算・経済指標を分析する

| 項目 | 内容 |
|---|---|
| 名前 | `financial_analysis_agent` |
| モデル | `gemini-2.0-flash` |
| output_key | `financial_data` |
| ツール | Finnhub API, Financial Datasets MCP, FRED API |

**ツール定義:**

```python
def get_stock_quote(symbol: str) -> dict:
    """Finnhub からリアルタイム株価を取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL")
    Returns:
        現在価格, 変動率, 高値, 安値, 出来高
    """

def get_company_financials(symbol: str) -> dict:
    """Financial Datasets MCP から決算データを取得する。

    Args:
        symbol: ティッカーシンボル
    Returns:
        損益計算書, 貸借対照表, キャッシュフロー計算書の主要指標
    """

def get_economic_indicators() -> dict:
    """FRED API から主要経済指標を取得する。

    Returns:
        GDP成長率, 失業率, CPI, Fed Funds Rate, 10年国債利回り等
    """
```

**MCP 連携 (Financial Datasets):**

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

financial_datasets_mcp = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@financial-datasets/mcp-server"],
        env={"FINANCIAL_DATASETS_API_KEY": os.getenv("FINANCIAL_DATASETS_API_KEY")},
    ),
)
```

**インストラクション:**

```
あなたは定量的な財務アナリストです。以下のタスクを実行してください:
1. 対象銘柄の現在の株価とバリュエーション指標を取得
2. 直近の決算データ (売上, 利益, EPS) を分析
3. 関連する経済指標 (GDP, CPI, 金利) の最新動向を確認
4. ファンダメンタルズの強弱を評価

出力形式:
{
  "stock_analysis": {
    "symbol": "...",
    "current_price": ...,
    "valuation": {...},
    "earnings_summary": "..."
  },
  "economic_context": {
    "gdp_trend": "...",
    "inflation": "...",
    "interest_rates": "..."
  },
  "fundamental_assessment": "STRONG / NEUTRAL / WEAK"
}
```

---

### 3.3 Sentiment Agent

**役割:** Reddit・SNS のセンチメントを分析する

| 項目 | 内容 |
|---|---|
| 名前 | `sentiment_agent` |
| モデル | `gemini-2.0-flash` |
| output_key | `sentiment_data` |
| ツール | Reddit API (PRAW), Finnhub Social Sentiment |

**ツール定義:**

```python
def get_reddit_sentiment(
    subreddits: list[str],
    query: str,
    limit: int = 50
) -> dict:
    """Reddit から投稿を取得し、センチメント分析を行う。

    Args:
        subreddits: 対象サブレディット (例: ["wallstreetbets", "stocks"])
        query: 検索キーワード
        limit: 取得投稿数
    Returns:
        投稿リスト, 全体センチメントスコア, トレンドトピック
    """

def get_social_sentiment(symbol: str) -> dict:
    """Finnhub からソーシャルセンチメントデータを取得する。

    Args:
        symbol: ティッカーシンボル
    Returns:
        Reddit/Twitter のメンション数, ポジティブ/ネガティブスコア
    """
```

**インストラクション:**

```
あなたは市場センチメント分析の専門家です。以下のタスクを実行してください:
1. Reddit (r/wallstreetbets, r/stocks, r/investing) からの投稿を分析
2. 対象銘柄に対する個人投資家の感情を定量化
3. バズワードやトレンドトピックを特定
4. 異常なセンチメント変化 (急激な盛り上がり等) を検出

出力形式:
{
  "overall_sentiment": "BULLISH / NEUTRAL / BEARISH",
  "sentiment_score": 0.0 ~ 1.0,
  "trending_topics": [...],
  "notable_posts": [...],
  "anomalies": [...]
}
```

---

### 3.4 Trend Analysis Agent

**役割:** 収集データを統合し、市場パターンと競合戦略を特定する

| 項目 | 内容 |
|---|---|
| 名前 | `trend_analysis_agent` |
| モデル | `gemini-2.0-flash` |
| output_key | `trend_analysis` |
| ツール | なし (LLM の推論能力のみ) |
| 入力 | `{news_data}`, `{financial_data}`, `{sentiment_data}` |

**インストラクション:**

```
あなたは市場トレンドの専門アナリストです。
Phase 1 で収集された以下のデータを統合分析してください:

- ニュースデータ: {news_data}
- 財務データ: {financial_data}
- センチメントデータ: {sentiment_data}

以下の分析を実行してください:
1. データソース間の相関関係を特定 (ニュースとセンチメントの一致/乖離)
2. 短期・中期の市場トレンドを予測
3. セクター別の強弱を評価
4. リスク要因を洗い出し

出力形式:
{
  "market_trends": [
    {"trend": "...", "direction": "UP/DOWN/SIDEWAYS", "confidence": 0.0~1.0, "timeframe": "SHORT/MID"}
  ],
  "sector_analysis": {...},
  "correlations": [...],
  "risk_factors": [...],
  "key_insight": "最も重要な発見の要約"
}
```

---

### 3.5 Strategy Agent

**役割:** 分析結果に基づき、実行可能な投資推奨を生成する

| 項目 | 内容 |
|---|---|
| 名前 | `strategy_agent` |
| モデル | `gemini-2.0-flash` |
| output_key | `strategy_report` |
| ツール | なし (LLM の推論能力のみ) |
| 入力 | 全 Phase のデータ |

**インストラクション:**

```
あなたは投資戦略のシニアストラテジストです。
すべての分析結果を踏まえ、投資推奨レポートを生成してください:

- トレンド分析: {trend_analysis}
- ニュースデータ: {news_data}
- 財務データ: {financial_data}
- センチメントデータ: {sentiment_data}

レポートに含める内容:
1. エグゼクティブサマリー (3行以内)
2. 推奨アクション (BUY / HOLD / SELL) とその根拠
3. ポジションサイズの提案 (リスクレベル別)
4. 主要リスクと緩和策
5. 注目すべき今後のイベント・カタリスト

※ これは投資助言ではなく、情報提供目的の分析です。

出力形式:
{
  "executive_summary": "...",
  "recommendations": [
    {
      "symbol": "...",
      "action": "BUY/HOLD/SELL",
      "rationale": "...",
      "confidence": 0.0~1.0,
      "risk_level": "HIGH/MEDIUM/LOW"
    }
  ],
  "risk_assessment": {...},
  "upcoming_catalysts": [...],
  "disclaimer": "本レポートは情報提供目的であり、投資助言ではありません。"
}
```

---

## 4. データフロー

### 4.1 Session State を介したデータ共有

ADK の `session.state` を使用して、エージェント間でデータを共有する。各エージェントは `output_key` で指定されたキーに結果を書き込む。

```
session.state = {
  "news_data":       Phase1 - News Agent の出力,
  "financial_data":  Phase1 - Financial Agent の出力,
  "sentiment_data":  Phase1 - Sentiment Agent の出力,
  "trend_analysis":  Phase2 - Trend Agent の出力,
  "strategy_report": Phase3 - Strategy Agent の出力,
}
```

### 4.2 シーケンス図

```
User          Orchestrator    News Agent   Financial Agent  Sentiment Agent  Trend Agent  Strategy Agent
 │                │               │              │               │              │              │
 │  分析リクエスト  │               │              │               │              │              │
 │───────────────>│               │              │               │              │              │
 │                │               │              │               │              │              │
 │                │ Phase 1: 並列データ収集        │               │              │              │
 │                │──────────────>│              │               │              │              │
 │                │──────────────────────────────>│               │              │              │
 │                │──────────────────────────────────────────────>│              │              │
 │                │               │              │               │              │              │
 │                │  news_data    │              │               │              │              │
 │                │<──────────────│              │               │              │              │
 │                │  financial_data              │               │              │              │
 │                │<─────────────────────────────│               │              │              │
 │                │  sentiment_data              │               │              │              │
 │                │<─────────────────────────────────────────────│              │              │
 │                │               │              │               │              │              │
 │                │ Phase 2: トレンド分析         │               │              │              │
 │                │────────────────────────────────────────────────────────────>│              │
 │                │  trend_analysis              │               │              │              │
 │                │<────────────────────────────────────────────────────────────│              │
 │                │               │              │               │              │              │
 │                │ Phase 3: 戦略立案             │               │              │              │
 │                │──────────────────────────────────────────────────────────────────────────>│
 │                │  strategy_report             │               │              │              │
 │                │<─────────────────────────────────────────────────────────────────────────│
 │                │               │              │               │              │              │
 │  最終レポート   │               │              │               │              │              │
 │<───────────────│               │              │               │              │              │
```

---

## 5. ディレクトリ構成

```
05_multi_agent/
├── README.md                      # モジュール説明
├── __init__.py
├── main.py                        # エントリーポイント (ローカル実行 & デモ)
├── pipeline.py                    # SequentialAgent パイプライン定義
├── agents/
│   ├── __init__.py
│   ├── news_agent.py              # News & Social Media Agent
│   ├── financial_agent.py         # Financial Analysis Agent
│   ├── sentiment_agent.py         # Sentiment Agent
│   ├── trend_agent.py             # Trend Analysis Agent
│   └── strategy_agent.py          # Strategy Agent
├── tools/
│   ├── __init__.py
│   ├── finnhub_tools.py           # Finnhub API ラッパー
│   ├── marketaux_tools.py         # Marketaux API ラッパー
│   ├── fred_tools.py              # FRED API ラッパー
│   ├── reddit_tools.py            # Reddit API ラッパー
│   └── mcp_config.py              # MCP サーバー接続設定
└── config/
    └── settings.py                # API キー・設定管理
```

---

## 6. デプロイ

### 6.1 ローカル実行

```bash
# 環境変数設定
export FINNHUB_API_KEY="your_key"
export MARKETAUX_API_KEY="your_key"
export FRED_API_KEY="your_key"
export REDDIT_CLIENT_ID="your_id"
export REDDIT_CLIENT_SECRET="your_secret"

# 実行
python -m 05_multi_agent.main --symbol AAPL --query "Apple 業績"
```

### 6.2 ADK Web UI でのテスト

```bash
adk web 05_multi_agent
```

ブラウザで `http://localhost:8000` にアクセスし、エージェントと対話的にテスト可能。

### 6.3 Vertex AI Agent Engine へのデプロイ

```bash
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$REGION \
  --staging_bucket=$STAGING_BUCKET \
  --agent_folder=05_multi_agent
```

---

## 7. API レート制限と対策

| API | 無料枠レート制限 | 日次制限 | 対策 |
|---|---|---|---|
| Finnhub | 60 req/min | なし | メインの株価・ニュースソース |
| Marketaux | - | 100 req/day | ニュースのセンチメント補完用 |
| FRED | 120 req/min | なし | 経済指標は低頻度アクセス |
| Reddit (PRAW) | 100 req/min | なし | キャッシュ活用 |
| Financial Datasets | - | - | MCP 経由でファンダメンタル取得 |
| Alpha Vantage | 5 req/min | 25 req/day | バックアップ用、制限が厳しい |

**対策:**

- レスポンスのインメモリキャッシュ (TTL: 5分)
- レート制限に達した場合のエクスポネンシャルバックオフ
- デモ用のモックデータフォールバック

---

## 8. 拡張案

| 拡張 | 説明 |
|---|---|
| **LoopAgent の導入** | Strategy Agent の推奨を Trend Agent が再評価するフィードバックループ |
| **A2A Protocol** | 他組織のエージェントとの連携 (例: 外部リサーチファーム) |
| **Memory Bank** | Agent Engine の長期記憶を使い、過去の分析結果と予測精度を蓄積 |
| **Cloud Run デプロイ** | Agent Engine の代替として Cloud Run 上でのスケーラブルデプロイ |
| **Slack/Teams 連携** | 分析レポートのリアルタイム通知 |
| **BigQuery 連携** | 分析結果の蓄積とダッシュボード化 |
