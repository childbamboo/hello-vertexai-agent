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


def deploy_agent():
    """エージェントを Agent Engine にデプロイする。"""
    client = vertexai.Client(project=PROJECT_ID, location=REGION)

    print("エージェントをデプロイ中...")
    remote_agent = client.agent_engines.create(
        config={
            "display_name": "hello-vertexai-demo-agent",
            "description": "天気と計算のデモエージェント",
            "source_packages": ["02_agent_engine"],
            "entrypoint_module": "02_agent_engine.agent",
            "entrypoint_object": "root_agent",
            "requirements": [
                "google-cloud-aiplatform[agent_engines,adk]>=1.112",
                "google-adk>=1.0.0",
            ],
            "staging_bucket": STAGING_BUCKET,
        },
    )
    print(f"デプロイ完了: {remote_agent.name}")
    return remote_agent


def query_agent(remote_agent):
    """デプロイ済みエージェントにクエリを送信する。"""
    print("\n--- セッションを作成 ---")
    session = remote_agent.create_session(user_id="demo_user")
    print(f"セッション ID: {session.id}")

    queries = [
        "東京の天気を教えてください",
        "123 * 456 を計算してください",
    ]

    for query in queries:
        print(f"\nユーザー: {query}")
        response = remote_agent.stream_query(
            user_id="demo_user",
            session_id=session.id,
            message=query,
        )
        for chunk in response:
            if hasattr(chunk, "content") and chunk.content:
                for part in chunk.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"エージェント: {part.text}")


def list_agents():
    """デプロイ済みエージェント一覧を表示する。"""
    client = vertexai.Client(project=PROJECT_ID, location=REGION)
    agents = client.agent_engines.list()
    print("\n=== デプロイ済みエージェント一覧 ===")
    for agent in agents:
        print(f"  - {agent.name} ({getattr(agent, 'display_name', 'N/A')})")


def cleanup(remote_agent):
    """デプロイしたエージェントを削除する。"""
    print(f"\nエージェントを削除中: {remote_agent.name}")
    client = vertexai.Client(project=PROJECT_ID, location=REGION)
    client.agent_engines.delete(name=remote_agent.name, force=True)
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
