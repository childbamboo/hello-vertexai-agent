"""News & Social Media Agent。

ニュース記事とSNSから業界トレンド・イベントを収集し、
市場インパクトを評価する。
"""

from google.adk.agents import Agent

from ..config.settings import MODEL_ID
from ..tools.finnhub_tools import get_company_news, get_market_news
from ..tools.marketaux_tools import get_financial_news_with_sentiment

NEWS_AGENT_INSTRUCTION = """\
あなたは市場ニュースの専門アナリストです。
ユーザーが指定した銘柄・セクターについて、以下のタスクを実行してください:

1. get_market_news で最新のマーケット全体ニュースを取得
2. get_company_news で対象銘柄の企業固有ニュースを取得
3. get_financial_news_with_sentiment でセンチメント付きニュースを取得
4. 重要なイベント (決算発表, M&A, 規制変更, 新製品等) を特定
5. 各ニュースの市場インパクトを HIGH / MEDIUM / LOW で評価

以下の JSON 形式で結果を出力してください:

{
  "summary": "市場ニュースの全体サマリー (3文以内)",
  "key_events": [
    {"event": "イベント名", "impact": "HIGH/MEDIUM/LOW", "description": "概要"}
  ],
  "news_items": [
    {
      "headline": "見出し",
      "source": "ソース名",
      "impact": "HIGH/MEDIUM/LOW",
      "sentiment": "positive/neutral/negative",
      "sentiment_score": 0.0,
      "relevance": "対象銘柄との関連性"
    }
  ],
  "market_mood": "RISK_ON / NEUTRAL / RISK_OFF"
}
"""

news_agent = Agent(
    name="news_social_media_agent",
    model=MODEL_ID,
    description="ニュース記事とSNSから業界トレンドとイベントを収集し、市場インパクトを評価するエージェント",
    instruction=NEWS_AGENT_INSTRUCTION,
    output_key="news_data",
    tools=[
        get_market_news,
        get_company_news,
        get_financial_news_with_sentiment,
    ],
)
