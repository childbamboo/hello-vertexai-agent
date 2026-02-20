"""
マーケットインテリジェンス Multi-Agent System
==============================================
複数の専門エージェントが並列・逐次に連携し、ライブデータから
市場分析と投資推奨を生成するデモです。

アーキテクチャ:
    Phase 1 (並列): News Agent, Financial Agent, Sentiment Agent
    Phase 2 (逐次): Trend Analysis Agent
    Phase 3 (逐次): Strategy Agent

実行方法 (ローカル):
    # 環境変数設定
    source .env

    # 実行
    python -m 05_multi_agent.main

ADK Web UI:
    adk web 05_multi_agent
"""

import asyncio
import os
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from .pipeline import root_agent

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")

# Vertex AI モードを有効化
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "1")
if PROJECT_ID:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", REGION)


def check_api_keys():
    """必要な API キーが設定されているか確認する。"""
    required_keys = {
        "FINNHUB_API_KEY": "Finnhub (株価・ニュース)",
    }
    optional_keys = {
        "MARKETAUX_API_KEY": "Marketaux (センチメント付きニュース)",
        "FRED_API_KEY": "FRED (経済指標)",
        "REDDIT_CLIENT_ID": "Reddit (SNSセンチメント)",
        "REDDIT_CLIENT_SECRET": "Reddit (SNSセンチメント)",
        "FINANCIAL_DATASETS_API_KEY": "Financial Datasets MCP (財務諸表)",
    }

    missing_required = []
    for key, desc in required_keys.items():
        if not os.environ.get(key):
            missing_required.append(f"  {key}: {desc}")

    if missing_required:
        print("エラー: 以下の必須環境変数が未設定です:")
        for m in missing_required:
            print(m)
        print()
        print("設定方法: docs/api-mcp-reference.md を参照してください。")
        sys.exit(1)

    missing_optional = []
    for key, desc in optional_keys.items():
        if not os.environ.get(key):
            missing_optional.append(f"  {key}: {desc}")

    if missing_optional:
        print("注意: 以下のオプション環境変数が未設定です (一部機能が制限されます):")
        for m in missing_optional:
            print(m)
        print()


def run_pipeline(query: str):
    """パイプラインを実行し、マーケットインテリジェンスを生成する。"""
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="market_intelligence",
    )
    user_id = "demo_user"
    session_id = "demo_session"

    # create_session is async in ADK 1.x
    asyncio.run(
        runner.session_service.create_session(
            app_name="market_intelligence",
            user_id=user_id,
            session_id=session_id,
        )
    )

    print(f"\n{'='*60}")
    print("マーケットインテリジェンス パイプライン実行中...")
    print(f"{'='*60}")
    print(f"\nクエリ: {query}\n")

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=query)],
    )

    current_agent = None
    response_text = ""

    for event in runner.run(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        # エージェントの切り替わりを表示
        if hasattr(event, "agent_name") and event.agent_name != current_agent:
            current_agent = event.agent_name
            print(f"\n--- [{current_agent}] ---")

        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
                    print(part.text, end="", flush=True)
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    print(f"  [ツール呼出] {fc.name}({dict(fc.args)})")

    print(f"\n\n{'='*60}")
    print("パイプライン完了")
    print(f"{'='*60}")

    # セッションステートから各フェーズの出力を表示
    session = asyncio.run(
        runner.session_service.get_session(
            app_name="market_intelligence",
            user_id=user_id,
            session_id=session_id,
        )
    )
    state = session.state if session else {}
    print("\n--- Session State Keys ---")
    for key in ["news_data", "financial_data", "sentiment_data", "trend_analysis", "strategy_report"]:
        if key in state:
            preview = str(state[key])[:200]
            print(f"  {key}: {preview}...")
        else:
            print(f"  {key}: (未生成)")


def main():
    print("=" * 60)
    print("マーケットインテリジェンス Multi-Agent System")
    print("=" * 60)
    print()
    print("アーキテクチャ:")
    print("  Phase 1 (並列): News Agent / Financial Agent / Sentiment Agent")
    print("  Phase 2 (逐次): Trend Analysis Agent")
    print("  Phase 3 (逐次): Strategy Agent")
    print()

    check_api_keys()

    # デモクエリ
    queries = [
        "Apple (AAPL) の投資判断を分析してください。"
        "最新のニュース、財務状況、個人投資家のセンチメントを踏まえて、"
        "市場トレンドを分析し、投資戦略を推奨してください。",
    ]

    for query in queries:
        run_pipeline(query)


if __name__ == "__main__":
    main()
