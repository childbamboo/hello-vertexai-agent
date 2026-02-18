"""Marketaux API ツール。

センチメント付き金融ニュースを取得する。
無料枠: 100 req/day
"""

import requests

from ..config.settings import MARKETAUX_API_KEY, MARKETAUX_BASE_URL


def get_financial_news_with_sentiment(
    symbols: str, limit: int = 10
) -> dict:
    """銘柄関連ニュースをセンチメント付きで取得する。

    Marketaux はニュース記事ごとにセンチメントスコアとエンティティタグを
    自動付与する。80+ グローバル市場、5,000+ ソースをカバー。

    Args:
        symbols: カンマ区切りのティッカーシンボル (例: "AAPL,GOOGL,MSFT")
        limit: 取得件数 (最大50、無料枠)

    Returns:
        センチメントスコア付きのニュース記事リスト
    """
    resp = requests.get(
        f"{MARKETAUX_BASE_URL}/news/all",
        params={
            "symbols": symbols.upper(),
            "filter_entities": "true",
            "language": "en",
            "limit": min(limit, 50),
            "api_token": MARKETAUX_API_KEY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    articles = []
    for article in data.get("data", []):
        # エンティティからセンチメントスコアを抽出
        entities = article.get("entities", [])
        sentiment_scores = [
            e.get("sentiment_score") for e in entities if e.get("sentiment_score") is not None
        ]
        avg_sentiment = (
            round(sum(sentiment_scores) / len(sentiment_scores), 4)
            if sentiment_scores
            else None
        )

        articles.append({
            "title": article.get("title"),
            "description": article.get("description", "")[:300],
            "source": article.get("source"),
            "published_at": article.get("published_at"),
            "url": article.get("url"),
            "sentiment_score": avg_sentiment,
            "entities": [
                {
                    "symbol": e.get("symbol"),
                    "name": e.get("name"),
                    "sentiment_score": e.get("sentiment_score"),
                }
                for e in entities[:5]
            ],
        })

    return {
        "symbols": symbols.upper(),
        "count": len(articles),
        "articles": articles,
    }
