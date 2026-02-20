"""
ツール (Tools) サンプル
========================
Vertex AI で利用可能な各種ツールのデモ:
  1. Function Calling
  2. Code Execution
  3. Google Search Grounding

実行方法:
    export PROJECT_ID="your-project-id"
    export REGION="us-central1"
    python 03_tools/main.py
"""

import os
import sys

import vertexai
from vertexai.generative_models import (
    FunctionDeclaration,
    GenerativeModel,
    Tool,
)

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")

if not PROJECT_ID:
    sys.exit("環境変数 PROJECT_ID を設定してください")

vertexai.init(project=PROJECT_ID, location=REGION)


# =====================================================================
# 1. Function Calling
# =====================================================================
def demo_function_calling():
    """Function Calling のデモ。

    Gemini モデルにカスタム関数のスキーマを渡し、
    モデルが適切な関数を選択・呼び出しする仕組みを確認します。
    """
    print("\n" + "=" * 60)
    print("1. Function Calling")
    print("=" * 60)

    # 関数宣言を定義
    get_product_info = FunctionDeclaration(
        name="get_product_info",
        description="商品名から商品情報を取得する",
        parameters={
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "商品名",
                }
            },
            "required": ["product_name"],
        },
    )

    search_orders = FunctionDeclaration(
        name="search_orders",
        description="注文を検索する",
        parameters={
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "顧客ID",
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "shipped", "delivered"],
                    "description": "注文ステータス",
                },
            },
            "required": ["customer_id"],
        },
    )

    tool = Tool(function_declarations=[get_product_info, search_orders])

    model = GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[tool],
    )

    # モデルに問い合わせ ── モデルが関数呼び出しを返す
    response = model.generate_content(
        "顧客ID C-001 の配送済み注文を調べてください"
    )

    print(f"  プロンプト: 顧客ID C-001 の配送済み注文を調べてください")
    print(f"  レスポンス:")
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.function_call:
                fc = part.function_call
                print(f"    -> Function Call: {fc.name}")
                print(f"       引数: {dict(fc.args)}")
            elif part.text:
                print(f"    -> テキスト: {part.text}")


# =====================================================================
# 2. Code Execution
# =====================================================================
def demo_code_execution():
    """Code Execution のデモ。

    Gemini モデルに Python コードを生成・実行させます。
    コードはサーバーサイドのサンドボックスで安全に実行されます。
    google.genai API を使用します。
    """
    print("\n" + "=" * 60)
    print("2. Code Execution")
    print("=" * 60)

    from google import genai
    from google.genai import types as genai_types

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION,
        http_options=genai_types.HttpOptions(timeout=120_000),
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="フィボナッチ数列の最初の 20 項を計算して、"
        "偶数の項だけを抽出してリスト表示してください。"
        "Python コードを書いて実行してください。",
        config=genai_types.GenerateContentConfig(
            tools=[genai_types.Tool(code_execution={})],
        ),
    )

    print(f"  プロンプト: フィボナッチ数列 (偶数フィルタ)")
    print(f"  レスポンス:")
    for part in response.candidates[0].content.parts:
        if part.executable_code:
            print(f"    [実行コード]")
            print(f"    {part.executable_code.code}")
        elif part.code_execution_result:
            print(f"    [実行結果]")
            print(f"    {part.code_execution_result.output}")
        elif part.text:
            print(f"    {part.text[:200]}")


# =====================================================================
# 3. Google Search Grounding
# =====================================================================
def demo_google_search_grounding():
    """Google Search Grounding のデモ。

    モデルの回答を Google 検索結果で裏付け (グラウンディング) します。
    google.genai API の google_search ツールを使用します。
    """
    print("\n" + "=" * 60)
    print("3. Google Search Grounding")
    print("=" * 60)

    from google import genai
    from google.genai import types as genai_types

    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=REGION,
        http_options=genai_types.HttpOptions(timeout=120_000),
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="2026年の日本の最新ニュースを3つ教えてください",
        config=genai_types.GenerateContentConfig(
            tools=[genai_types.Tool(google_search={})],
            temperature=0.0,
        ),
    )

    print(f"  プロンプト: 2026年の日本の最新ニュース")
    print(f"  レスポンス:")
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if part.text:
                text = part.text[:500]
                print(f"    {text}")
        # グラウンディングメタデータを表示
        if candidate.grounding_metadata:
            meta = candidate.grounding_metadata
            if meta.search_entry_point:
                print(f"    [検索クエリ使用]")
            if meta.grounding_supports:
                print(f"    [グラウンディングソース: {len(meta.grounding_supports)} 件]")


def main():
    print("=" * 60)
    print("ツール (Tools) サンプル")
    print("=" * 60)
    print(f"プロジェクト: {PROJECT_ID}")
    print(f"リージョン:   {REGION}")

    demo_function_calling()
    demo_code_execution()
    demo_google_search_grounding()

    print("\n完了!")


if __name__ == "__main__":
    main()
