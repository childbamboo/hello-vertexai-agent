"""マーケットインテリジェンス パイプライン。

Sequential + Parallel パターンで複数エージェントを連携させる:
  Phase 1 (並列): News, Financial, Sentiment の3エージェントが同時にデータ収集
  Phase 2 (逐次): Trend Analysis エージェントが統合分析
  Phase 3 (逐次): Strategy エージェントが投資推奨を生成
"""

from google.adk.agents import ParallelAgent, SequentialAgent

from .agents.financial_agent import financial_agent
from .agents.news_agent import news_agent
from .agents.sentiment_agent import sentiment_agent
from .agents.strategy_agent import strategy_agent
from .agents.trend_agent import trend_analysis_agent

# Phase 1: 並列データ収集
# 3つのエージェントが同時に外部APIからデータを収集する
data_collection = ParallelAgent(
    name="data_collection",
    description="市場データを並列に収集する (ニュース, 財務, センチメント)",
    sub_agents=[news_agent, financial_agent, sentiment_agent],
)

# パイプライン全体: Phase 1 → Phase 2 → Phase 3
# session.state の output_key を介してエージェント間でデータを共有する
#
# データフロー:
#   Phase 1 → news_data, financial_data, sentiment_data
#   Phase 2 → trend_analysis (Phase 1 のデータを参照)
#   Phase 3 → strategy_report (Phase 1 + Phase 2 のデータを参照)
root_agent = SequentialAgent(
    name="market_intelligence_pipeline",
    description="マーケットインテリジェンスの分析パイプライン。"
    "ニュース・財務データ・センチメントを並列収集し、"
    "トレンド分析を経て投資戦略を生成する。",
    sub_agents=[data_collection, trend_analysis_agent, strategy_agent],
)
