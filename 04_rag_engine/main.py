"""
RAG Engine サンプル
====================
Vertex AI RAG Engine を使ったデモ:
  1. RAG コーパスの作成
  2. インラインテキストのインポート
  3. コンテキスト検索 (Retrieval Query)
  4. Gemini + RAG によるグラウンデッド生成

実行方法:
    export PROJECT_ID="your-project-id"
    export REGION="us-central1"
    python 04_rag_engine/main.py
"""

import os
import sys
import tempfile

import vertexai
from vertexai import rag
from vertexai.generative_models import GenerativeModel, Tool

PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
# RAG Engine は us-central1, us-east1, us-east4 で新規プロジェクト制限あり。
# 別リージョンを RAG_REGION で指定可能 (例: europe-west4, asia-southeast1)
RAG_REGION = os.environ.get("RAG_REGION", REGION)

if not PROJECT_ID:
    sys.exit("環境変数 PROJECT_ID を設定してください")

vertexai.init(project=PROJECT_ID, location=RAG_REGION)

# デモ用のサンプルドキュメント
SAMPLE_DOCUMENTS = {
    "company_policy.txt": """\
株式会社サンプル 社内規定 (抜粋)

第1条 (勤務時間)
標準勤務時間は 9:00〜18:00 とする。フレックスタイム制を適用し、
コアタイムは 10:00〜15:00 とする。

第2条 (リモートワーク)
週3日までリモートワークを認める。リモートワーク時も
コアタイムにはオンラインであることを必須とする。

第3条 (有給休暇)
入社6ヶ月経過後、年間10日の有給休暇を付与する。
勤続年数に応じて最大20日まで増加する。

第4条 (経費精算)
業務に必要な経費は、領収書を添付の上、月末までに精算システムから申請すること。
1件あたり5万円以上の場合は、事前に上長の承認を得ること。
""",
    "product_faq.txt": """\
製品FAQ - CloudWidget Pro

Q: CloudWidget Pro の価格プランは?
A: 3つのプランがあります。
   - スターター: 月額 1,000円/ユーザー (5ユーザーまで)
   - ビジネス: 月額 2,500円/ユーザー (50ユーザーまで)
   - エンタープライズ: 要問い合わせ (無制限)

Q: 無料トライアルはありますか?
A: はい、14日間の無料トライアルを提供しています。
   クレジットカードの登録は不要です。

Q: データのエクスポートは可能ですか?
A: はい、CSV、JSON、Excel 形式でエクスポート可能です。
   API 経由での一括エクスポートにも対応しています。

Q: SLA はどのくらいですか?
A: ビジネスプラン以上で 99.9% の稼働率を保証しています。
""",
}


def create_corpus() -> rag.RagCorpus:
    """RAG コーパスを作成する。"""
    print("\n--- 1. RAG コーパスを作成 ---")

    embedding_model_config = rag.RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model="publishers/google/models/text-embedding-005"
        )
    )

    rag_corpus = rag.create_corpus(
        display_name="hello-vertexai-demo-corpus",
        description="デモ用のサンプルコーパス",
        backend_config=rag.RagVectorDbConfig(
            rag_embedding_model_config=embedding_model_config,
        ),
    )
    print(f"  コーパス作成: {rag_corpus.name}")
    return rag_corpus


def import_documents(corpus_name: str):
    """サンプルドキュメントをコーパスにインポートする。"""
    print("\n--- 2. ドキュメントをインポート ---")

    # サンプルドキュメントを一時ファイルに書き出してアップロード
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for filename, content in SAMPLE_DOCUMENTS.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            paths.append(filepath)
            print(f"  準備: {filename}")

        # ローカルファイルをインポート
        # 注意: ローカルファイルのインポートには upload_file を使用
        for filepath in paths:
            rag_file = rag.upload_file(
                corpus_name=corpus_name,
                path=filepath,
                display_name=os.path.basename(filepath),
            )
            print(f"  インポート完了: {rag_file.name}")


def list_corpus_files(corpus_name: str):
    """コーパス内のファイル一覧を表示する。"""
    print("\n--- コーパス内ファイル一覧 ---")
    files = rag.list_files(corpus_name=corpus_name)
    for f in files:
        print(f"  - {f.display_name} ({f.name})")


def retrieval_query(corpus_name: str):
    """コーパスから関連コンテキストを検索する。"""
    print("\n--- 3. コンテキスト検索 (Retrieval Query) ---")

    queries = [
        "リモートワークのルールは?",
        "CloudWidget Pro の料金プランを教えて",
        "有給休暇は何日もらえる?",
    ]

    for query in queries:
        print(f"\n  クエリ: {query}")
        response = rag.retrieval_query(
            rag_resources=[
                rag.RagResource(rag_corpus=corpus_name),
            ],
            text=query,
            rag_retrieval_config=rag.RagRetrievalConfig(
                top_k=3,
                filter=rag.Filter(vector_distance_threshold=0.5),
            ),
        )

        if response.contexts and response.contexts.contexts:
            for i, ctx in enumerate(response.contexts.contexts):
                snippet = ctx.text[:150].replace("\n", " ")
                # SDK バージョンにより score or distance フィールドが異なる
                score = getattr(ctx, "score", None) or getattr(ctx, "distance", None)
                if score is not None:
                    print(f"    [{i+1}] (スコア: {score:.3f}) {snippet}...")
                else:
                    print(f"    [{i+1}] {snippet}...")
        else:
            print("    (関連コンテキストなし)")


def generate_with_rag(corpus_name: str):
    """Gemini + RAG でグラウンデッド生成を行う。"""
    print("\n--- 4. Gemini + RAG によるグラウンデッド生成 ---")

    rag_retrieval_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(rag_corpus=corpus_name),
                ],
                rag_retrieval_config=rag.RagRetrievalConfig(
                    top_k=3,
                    filter=rag.Filter(vector_distance_threshold=0.5),
                ),
            ),
        )
    )

    model = GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[rag_retrieval_tool],
    )

    queries = [
        "経費精算のルールを教えてください",
        "CloudWidget Pro の無料トライアルについて教えてください",
    ]

    for query in queries:
        print(f"\n  質問: {query}")
        response = model.generate_content(query)
        print(f"  回答: {response.text[:300]}")


def cleanup(corpus_name: str):
    """コーパスを削除する。"""
    print(f"\n--- クリーンアップ: コーパス削除 ---")
    rag.delete_corpus(name=corpus_name)
    print(f"  削除完了: {corpus_name}")


def main():
    print("=" * 60)
    print("RAG Engine サンプル")
    print("=" * 60)
    print(f"プロジェクト: {PROJECT_ID}")
    print(f"RAG リージョン: {RAG_REGION}")

    # 1. コーパス作成
    rag_corpus = create_corpus()

    try:
        # 2. ドキュメントインポート
        import_documents(rag_corpus.name)

        # ファイル一覧
        list_corpus_files(rag_corpus.name)

        # 3. コンテキスト検索
        retrieval_query(rag_corpus.name)

        # 4. Gemini + RAG
        generate_with_rag(rag_corpus.name)

    finally:
        # クリーンアップ
        cleanup(rag_corpus.name)

    print("\n完了!")


if __name__ == "__main__":
    main()
