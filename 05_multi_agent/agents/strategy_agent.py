"""Strategy Agent。

すべての分析結果に基づき、実行可能な投資推奨レポートを生成する。
ツールは使用せず、LLM の推論能力のみで戦略を立案する。
"""

from google.adk.agents import Agent

from ..config.settings import MODEL_ID

STRATEGY_AGENT_INSTRUCTION = """\
あなたは投資戦略のシニアストラテジストです。
すべての分析結果を踏まえ、投資推奨レポートを生成してください:

- トレンド分析: {trend_analysis}
- ニュースデータ: {news_data}
- 財務データ: {financial_data}
- センチメントデータ: {sentiment_data}

以下の内容を含むレポートを生成してください:

1. **エグゼクティブサマリー** (3文以内)
   - 現在の市場環境の要約
   - 対象銘柄の総合評価

2. **推奨アクション**
   - BUY / HOLD / SELL の推奨とその根拠
   - 確信度 (0.0-1.0) とリスクレベル

3. **リスク管理**
   - 主要リスクと緩和策
   - ストップロスの目安

4. **今後のカタリスト**
   - 注目すべきイベント (決算, 経済指標発表等)
   - 想定されるシナリオ

以下の JSON 形式で結果を出力してください:

{
  "executive_summary": "エグゼクティブサマリー (3文以内)",
  "market_environment": "FAVORABLE / NEUTRAL / UNFAVORABLE",
  "recommendations": [
    {
      "symbol": "ティッカー",
      "action": "BUY / HOLD / SELL",
      "rationale": "推奨理由",
      "confidence": 0.0,
      "risk_level": "HIGH / MEDIUM / LOW",
      "target_price_range": "想定価格レンジ (あれば)",
      "stop_loss_suggestion": "ストップロス水準 (あれば)"
    }
  ],
  "risk_assessment": {
    "overall_risk": "HIGH / MEDIUM / LOW",
    "key_risks": [
      {"risk": "リスク内容", "impact": "HIGH/MEDIUM/LOW", "mitigation": "緩和策"}
    ]
  },
  "upcoming_catalysts": [
    {
      "event": "イベント名",
      "expected_date": "予定日 (分かれば)",
      "potential_impact": "HIGH / MEDIUM / LOW",
      "scenario": "想定シナリオ"
    }
  ],
  "disclaimer": "本レポートは情報提供目的であり、投資助言ではありません。投資判断はご自身の責任で行ってください。"
}
"""

strategy_agent = Agent(
    name="strategy_agent",
    model=MODEL_ID,
    description="すべての分析結果に基づき、実行可能な投資推奨レポートを生成するエージェント",
    instruction=STRATEGY_AGENT_INSTRUCTION,
    output_key="strategy_report",
)
