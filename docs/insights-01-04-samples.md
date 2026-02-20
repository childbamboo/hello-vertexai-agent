# Vertex AI サンプル (01-04) 検証インサイト

01_agent_garden / 02_agent_engine / 03_tools / 04_rag_engine の動作検証を通じて得られた知見をまとめる。

---

## 1. SDK の互換性と API 変更 (全般)

### 問題

google-cloud-aiplatform / google-adk / google-genai の最新版で、ドキュメントや過去のサンプルコードがそのまま動かないケースが多い。

### 主な変更点

| パッケージ | 変更内容 |
|---|---|
| google-adk | `google.adk.tools.google_api_registry` → `google.adk.tools` にインポートパス変更 |
| google-adk | `session_service.create_session()` が async に変更 |
| google-adk | Vertex AI 接続に環境変数 `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` が必要 |
| google-genai | `Tool.from_code_execution()` 廃止 → `genai_types.Tool(code_execution={})` |
| google-genai | `google_search_retrieval` 廃止 → `genai_types.Tool(google_search={})` |
| vertexai.rag | `VertexRagStore(similarity_top_k=...)` 廃止 → `RagRetrievalConfig(top_k=..., filter=...)` に移行 |
| vertexai.rag | `ctx.distance` → `ctx.score` にフィールド名変更 (バージョンにより異なる) |

### 教訓

- SDK のバージョンを `pip show` で確認してからサンプルを書く
- 公式ドキュメントよりも SDK ソースコードの型定義を信頼する方が早い
- エラーメッセージが具体的なので、素直に従えば大体解決する

---

## 2. Function Calling vs Agent Tools (03_tools / 01_agent_garden)

### Function Calling (低レベル API)

```
アプリ → Gemini: 「こういう関数があります」+ ユーザーの質問
Gemini → アプリ: 「search_orders(customer_id='C-001') を呼んで」
アプリ: 実際に関数を実行して結果取得
アプリ → Gemini: 「結果はこうでした」
Gemini → アプリ: 自然言語の回答
```

- **JSON Schema で関数の仕様だけ定義**する (実装コードは渡さない)
- Gemini は関数を実行しない。**呼び出し指示を返すだけ**
- 実行ループはアプリケーション側が制御する

### Agent Tools (高レベル ADK)

```python
agent = Agent(tools=[get_weather, calculate])
```

- **Python 関数の実体を渡す**と、ADK が自動で Function Calling → 実行 → 結果返却のループを回す
- 開発者はループの実装不要
- ADK の InMemoryRunner や Agent Engine がこのループを管理する

### 使い分け

- **Function Calling**: 実行タイミングや結果のフォーマットを細かく制御したい場合
- **Agent Tools**: プロトタイピングや標準的なツール連携で十分な場合

---

## 3. Code Execution (03_tools)

- Gemini が **Python コードを動的に生成し、Google のサーバー側サンドボックスで実行**する
- ローカル環境に一切影響なし
- レスポンスに `executable_code` (生成コード) と `code_execution_result` (実行結果) が含まれる
- 計算、データ加工、分析タスクに有効
- Function Calling との違い: Function Calling は事前定義した関数を呼ぶ指示、Code Execution は Gemini が自由にコードを書いて実行する

---

## 4. Google Search Grounding (03_tools)

### 機能

- Gemini の回答を **リアルタイムの Google 検索結果で裏付け** (グラウンディング) する
- `genai_types.Tool(google_search={})` で有効化
- グラウンディングメタデータに検索ソース情報が付与される

### タイムアウト問題

Google Search Grounding はリアルタイム検索を経由するため、`google.genai.Client` のデフォルトタイムアウトでは不足する場合がある。

```python
client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=REGION,
    http_options=genai_types.HttpOptions(timeout=120_000),  # 120秒に延長
)
```

### 制約

- 日本語検索もバックエンドは Google 検索なので精度は高い
- ただしリアルタイム性には遅延がある (数秒〜数十秒)
- 検索クエリの制御はできない (Gemini が自動生成する)

---

## 5. Agent Engine デプロイ (02_agent_engine)

### cloudpickle シリアライズの罠

Agent Engine はエージェントを `cloudpickle` でシリアライズしてクラウドにデプロイする。外部モジュール (`agent.py`) を import しているとクラウド側で `ModuleNotFoundError` になる。

**対策**: エージェント定義はデプロイ関数内にインラインで記述する。

```python
def _create_agent():
    from google.adk.agents import Agent
    # ツール関数もここで定義
    def get_weather(city: str) -> dict: ...
    return Agent(name="demo", tools=[get_weather])
```

### requirements の明示

デプロイ設定で依存パッケージを明示する必要がある。特に `cloudpickle` と `pydantic` は暗黙的に使われるが、requirements に含めないとクラウド側で失敗する。

### API レスポンスの型が不安定

- セッション作成: `dict` が返る場合と `object` が返る場合がある → `isinstance` で判別
- ストリーミング応答: 同様に `dict` / `object` の両方をハンドリングする必要あり
- `AgentEngine.name` → `AgentEngine.api_resource.name` に変更されている

---

## 6. RAG Engine (04_rag_engine)

### リージョン制限

`us-central1`, `us-east1`, `us-east4` は新規プロジェクトでブロックされている (GCP 側の容量制限)。`europe-west4` や `asia-southeast1` を使う。`.env` で `RAG_REGION` を `REGION` とは独立して設定する設計にした。

### チャンキングの仕組み

RAG Engine はインポート時にドキュメントを自動チャンク分割 → ベクトル化 (embedding) する。

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `chunk_size` | 1024 トークン | チャンクの最大トークン数 |
| `chunk_overlap` | 200 トークン | 隣接チャンク間の重複 |

### チャンクサイズのチューニング

| サイズ | 適したドキュメント |
|---|---|
| 128〜256 | FAQ、条文、定義集 (独立性の高い短い項目) |
| 512〜1024 | 汎用的なドキュメント (最もよく使われる) |
| 1024〜2048 | 技術文書、論文 (文脈の繋がりが重要) |

- **小さすぎる**: 文脈が失われる。「コアタイムにはオンライン必須」だけだと何の話か不明
- **大きすぎる**: embedding が「全般的な内容」になり、ピンポイント検索の精度が落ちる
- **推奨**: 512 から始めて検索精度を見ながら調整。オーバーラップはチャンクサイズの 10〜20%

### カスタムチャンキング

自動分割の代わりに、アプリ側で意味的な単位で分割してからインポートする方法が最も精度が出る。

- 規約: 「第N条」で分割
- Markdown: `##` 見出しで分割
- FAQ: 「Q:」で分割

```python
import re
sections = re.split(r'(?=第\d+条)', text)
```

RAG Engine には PDF 向けの `use_advanced_pdf_parsing` オプションもあるが、テキストには使えないため、テキストドキュメントでは自前分割が実用的。

### 検索結果の表示

`retrieval_query` の結果は `ctx.text` にチャンク全文が入る。表示時にスニペットを切り出す場合は、先頭 N 文字ではなくクエリキーワード周辺を抜き出す方が有用。ただし本質的にはチャンクサイズの調整で対応すべき。

---

## 7. 環境構築メモ

- `.env` は bash で自動読み込みされない → `set -a && source .env && set +a` で読み込む
- ADC (Application Default Credentials) は期限切れする → `gcloud auth application-default login` で再認証
- `setup.sh` で Vertex AI / Cloud Storage / API Registry 等の API を一括有効化
- Agent Engine のデプロイ済みリソースは従量課金 → 検証後は必ず削除する
