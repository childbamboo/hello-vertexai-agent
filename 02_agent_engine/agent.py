"""
Agent Engine にデプロイするエージェント定義。

このファイルは Agent Engine にアップロードされ、
クラウド上でエージェントとして動作します。
"""

from google.adk.agents import Agent


def get_weather(city: str) -> dict:
    """指定された都市の天気を取得する。

    Args:
        city: 天気を取得したい都市名

    Returns:
        天気情報を含む辞書
    """
    # デモ用のスタブデータ
    weather_data = {
        "東京": {"temp": 15, "condition": "晴れ", "humidity": 45},
        "大阪": {"temp": 17, "condition": "曇り", "humidity": 60},
        "札幌": {"temp": -2, "condition": "雪", "humidity": 70},
        "福岡": {"temp": 18, "condition": "晴れ", "humidity": 50},
    }
    return weather_data.get(city, {"temp": 20, "condition": "不明", "humidity": 50})


def calculate(expression: str) -> dict:
    """数式を計算する。

    Args:
        expression: 計算する数式 (例: "2 + 3 * 4")

    Returns:
        計算結果を含む辞書
    """
    try:
        # 安全な評価のため、許可する演算子を制限
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return {"error": "許可されていない文字が含まれています"}
        result = eval(expression)  # noqa: S307 - デモ用
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


# Agent Engine にデプロイされるルートエージェント
root_agent = Agent(
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
