"""MCP サーバー接続設定。

Financial Datasets MCP サーバーとの接続を管理する。
ADK の MCPToolset を使用して MCP ツールをエージェントに提供する。
"""

import os

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from mcp import StdioServerParameters

from ..config.settings import FINANCIAL_DATASETS_API_KEY


def get_financial_datasets_mcp() -> MCPToolset:
    """Financial Datasets MCP サーバーのツールセットを生成する。

    提供されるツール:
        - get_income_statements: 損益計算書
        - get_balance_sheets: 貸借対照表
        - get_cash_flow_statements: キャッシュフロー計算書
        - get_current_stock_price: 現在の株価
        - get_historical_stock_prices: 過去の株価推移
        - get_company_news: 企業関連ニュース

    Returns:
        MCPToolset インスタンス
    """
    return MCPToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["-y", "@financial-datasets/mcp-server"],
            env={
                **os.environ,
                "FINANCIAL_DATASETS_API_KEY": FINANCIAL_DATASETS_API_KEY,
            },
        ),
    )
