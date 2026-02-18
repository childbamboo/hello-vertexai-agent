"""Financial Analysis Agent。

株価・決算・経済指標を分析し、ファンダメンタルズの強弱を評価する。
"""

from google.adk.agents import Agent

from ..config.settings import MODEL_ID
from ..tools.finnhub_tools import get_basic_financials, get_company_profile, get_stock_quote
from ..tools.fred_tools import get_economic_indicators, get_economic_series

FINANCIAL_AGENT_INSTRUCTION = """\
あなたは定量的な財務アナリストです。
ユーザーが指定した銘柄について、以下のタスクを実行してください:

1. get_stock_quote で現在の株価を取得
2. get_company_profile で企業概要を確認
3. get_basic_financials で主要財務指標 (PER, PBR, ROE, EPS等) を取得
4. get_economic_indicators で主要経済指標 (GDP, CPI, 金利, VIX等) の最新動向を確認
5. ファンダメンタルズの強弱を総合的に評価

以下の JSON 形式で結果を出力してください:

{
  "company_overview": {
    "name": "企業名",
    "symbol": "シンボル",
    "industry": "業種",
    "market_cap": 0
  },
  "stock_analysis": {
    "current_price": 0,
    "change_percent": 0,
    "week_52_high": 0,
    "week_52_low": 0,
    "position_in_range": "52週レンジ内の位置 (上位/中位/下位)"
  },
  "valuation": {
    "pe_ratio": 0,
    "pb_ratio": 0,
    "dividend_yield": 0,
    "assessment": "UNDERVALUED / FAIR / OVERVALUED"
  },
  "profitability": {
    "roe": 0,
    "roa": 0,
    "eps_ttm": 0,
    "revenue_growth": 0,
    "assessment": "STRONG / MODERATE / WEAK"
  },
  "economic_context": {
    "gdp_trend": "成長/鈍化/縮小",
    "inflation": "上昇/安定/低下",
    "interest_rate_environment": "引き締め/中立/緩和",
    "market_volatility": "VIX水準による評価"
  },
  "fundamental_assessment": "STRONG / NEUTRAL / WEAK",
  "assessment_rationale": "評価の根拠 (3文以内)"
}
"""

financial_agent = Agent(
    name="financial_analysis_agent",
    model=MODEL_ID,
    description="株価・決算・経済指標を分析し、ファンダメンタルズの強弱を評価するエージェント",
    instruction=FINANCIAL_AGENT_INSTRUCTION,
    output_key="financial_data",
    tools=[
        get_stock_quote,
        get_company_profile,
        get_basic_financials,
        get_economic_indicators,
        get_economic_series,
    ],
)
