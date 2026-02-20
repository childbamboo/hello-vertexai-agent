"""
Agent Engine サンプル
=====================
エージェントを Vertex AI Agent Engine にデプロイし、
クエリを実行するデモです。

実行方法:
    export PROJECT_ID="your-project-id"
    export REGION="us-central1"
    export STAGING_BUCKET="gs://your-bucket"
    python 02_agent_engine/main.py
"""

import os
import sys

import vertexai

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
STAGING_BUCKET = os.environ.get("STAGING_BUCKET")

if not PROJECT_ID:
    sys.exit("環境変数 PROJECT_ID を設定してください")
if not STAGING_BUCKET:
    sys.exit("環境変数 STAGING_BUCKET を設定してください (例: gs://my-bucket)")


def _create_agent():
    """デプロイ用のエージェントを定義する。

    Agent Engine は cloudpickle でエージェントをシリアライズするため、
    外部モジュール (agent.py) に依存させず、ここで直接定義する。
    """
    from google.adk.agents import Agent

    def get_weather(city: str) -> dict:
        """指定された都市の天気を取得する。"""
        weather_data = {
            "東京": {"temp": 15, "condition": "晴れ", "humidity": 45},
            "大阪": {"temp": 17, "condition": "曇り", "humidity": 60},
            "札幌": {"temp": -2, "condition": "雪", "humidity": 70},
            "福岡": {"temp": 18, "condition": "晴れ", "humidity": 50},
        }
        return weather_data.get(
            city, {"temp": 20, "condition": "不明", "humidity": 50}
        )

    def calculate(expression: str) -> dict:
        """数式を計算する (例: '2 + 3 * 4')。"""
        try:
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return {"error": "許可されていない文字が含まれています"}
            result = eval(expression)  # noqa: S307 - デモ用
            return {"expression": expression, "result": result}
        except Exception as e:
            return {"error": str(e)}

    return Agent(
        name="demo_agent",
        model="gemini-2.0-flash",
        description="天気と計算のデモエージェント",
        instruction=(
            "あなたは親切なアシスタントです。"
            "天気の質問には get_weather ツールを、"
            "計算の質問には calculate ツールを使ってください。"
            "日本語で回答してください。"
        ),
        tools=[get_weather, calculate],
    )


def deploy_agent():
    """エージェントを Agent Engine にデプロイする。"""
    agent = _create_agent()
    client = vertexai.Client(project=PROJECT_ID, location=REGION)

    print("エージェントをデプロイ中...")
    remote_agent = client.agent_engines.create(
        agent=agent,
        config={
            "display_name": "hello-vertexai-demo-agent",
            "description": "天気と計算のデモエージェント",
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112",
                "google-adk>=1.0.0",
                "cloudpickle>=3.0.0",
                "pydantic>=2.0.0",
            ],
            "staging_bucket": STAGING_BUCKET,
        },
    )
    print(f"デプロイ完了: {remote_agent.api_resource.name}")
    return remote_agent


def query_agent(remote_agent):
    """デプロイ済みエージェントにクエリを送信する。"""
    print("\n--- セッションを作成 ---")
    session = remote_agent.create_session(user_id="demo_user")
    # SDK バージョンにより dict またはオブジェクトが返る
    session_id = session["id"] if isinstance(session, dict) else session.id
    print(f"セッション ID: {session_id}")

    queries = [
        "東京の天気を教えてください",
        "123 * 456 を計算してください",
    ]

    for query in queries:
        print(f"\nユーザー: {query}")
        response = remote_agent.stream_query(
            user_id="demo_user",
            session_id=session_id,
            message=query,
        )
        for chunk in response:
            if isinstance(chunk, dict):
                # dict レスポンスの場合
                content = chunk.get("content")
                if content and content.get("parts"):
                    for part in content["parts"]:
                        if part.get("text"):
                            print(f"エージェント: {part['text']}")
            elif hasattr(chunk, "content") and chunk.content:
                for part in chunk.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"エージェント: {part.text}")


def list_agents():
    """デプロイ済みエージェント一覧を表示する。"""
    client = vertexai.Client(project=PROJECT_ID, location=REGION)
    agents = client.agent_engines.list()
    print("\n=== デプロイ済みエージェント一覧 ===")
    for agent in agents:
        res = agent.api_resource
        print(f"  - {res.name} ({getattr(res, 'display_name', 'N/A')})")


def cleanup(remote_agent):
    """デプロイしたエージェントを削除する。"""
    agent_name = remote_agent.api_resource.name
    print(f"\nエージェントを削除中: {agent_name}")
    client = vertexai.Client(project=PROJECT_ID, location=REGION)
    client.agent_engines.delete(name=agent_name, force=True)
    print("削除完了")


def main():
    print("=" * 60)
    print("Agent Engine サンプル")
    print("=" * 60)
    print(f"プロジェクト: {PROJECT_ID}")
    print(f"リージョン:   {REGION}")
    print(f"バケット:     {STAGING_BUCKET}")
    print()

    # 1. エージェントをデプロイ
    remote_agent = deploy_agent()

    try:
        # 2. エージェント一覧を表示
        list_agents()

        # 3. エージェントにクエリ
        query_agent(remote_agent)
    finally:
        # 4. クリーンアップ
        cleanup(remote_agent)

    print("\n完了!")


if __name__ == "__main__":
    main()
