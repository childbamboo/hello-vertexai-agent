"""
Agent Garden サンプル
=====================
Cloud API Registry を使って Agent Garden のツール (MCP サーバー) を
エージェントに統合するデモです。

実行方法:
    export PROJECT_ID="your-project-id"
    python 01_agent_garden/main.py
"""

import os
import sys

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools.google_api_registry import ApiRegistry
from google.genai import types


PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")

if not PROJECT_ID:
    sys.exit("環境変数 PROJECT_ID を設定してください")


def list_available_toolsets():
    """Cloud API Registry に登録されている MCP サーバー一覧を表示する。"""
    api_registry = ApiRegistry(
        api_registry_project_id=PROJECT_ID,
        location="global",
    )
    print("=== Cloud API Registry: 利用可能なツールセット ===")
    print(f"  プロジェクト: {PROJECT_ID}")
    print(f"  API Registry 接続先: global")
    print()
    return api_registry


def create_agent_with_registry_tool(api_registry: ApiRegistry):
    """
    Agent Garden から取得したツールセットを使ってエージェントを作成する。

    注意: 実際に動作させるには Cloud API Registry に MCP サーバーが
    登録されている必要があります。
    """
    # -----------------------------------------------------------
    # Agent Garden / API Registry からツールセットを取得する例
    #
    # 利用可能な MCP サーバー名は Cloud Console の
    # Agent Garden > ツール で確認できます。
    #
    #   toolset = api_registry.get_toolset("bigquery-mcp-server")
    #
    # 以下はローカル関数をフォールバックとして使うデモです。
    # -----------------------------------------------------------

    def search_documents(query: str) -> dict:
        """ドキュメントを検索する (デモ用スタブ)。"""
        return {
            "results": [
                {"title": "Vertex AI 概要", "snippet": f"'{query}' に関する情報..."},
                {"title": "Agent Builder ガイド", "snippet": f"'{query}' の使い方..."},
            ]
        }

    def get_project_info() -> dict:
        """プロジェクト情報を取得する (デモ用スタブ)。"""
        return {
            "project_id": PROJECT_ID,
            "region": REGION,
            "status": "ACTIVE",
        }

    agent = Agent(
        name="agent_garden_demo",
        model="gemini-2.0-flash",
        description="Agent Garden のツールを活用するデモエージェント",
        instruction=(
            "あなたは Google Cloud のアシスタントです。"
            "ユーザーの質問に対して、利用可能なツールを使って回答してください。"
            "日本語で回答してください。"
        ),
        tools=[search_documents, get_project_info],
    )
    return agent


def main():
    print("=" * 60)
    print("Agent Garden サンプル")
    print("=" * 60)
    print()

    # 1. API Registry 接続
    api_registry = list_available_toolsets()

    # 2. エージェント作成
    agent = create_agent_with_registry_tool(api_registry)

    # 3. エージェントに問い合わせ
    runner = InMemoryRunner(agent=agent, app_name="agent_garden_demo")
    user_id = "demo_user"
    session = runner.session_service.create_session(
        app_name="agent_garden_demo", user_id=user_id
    )

    queries = [
        "このプロジェクトの情報を教えてください",
        "Vertex AI について検索してください",
    ]

    for query in queries:
        print(f"\n--- ユーザー: {query} ---")
        content = types.Content(
            role="user", parts=[types.Part.from_text(text=query)]
        )
        response_text = ""
        for event in runner.run(
            user_id=user_id, session_id=session.id, new_message=content
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        print(f"エージェント: {response_text}")

    print("\n完了!")


if __name__ == "__main__":
    main()
