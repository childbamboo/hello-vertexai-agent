"""Finnhub API ツール。

株価、企業情報、マーケットニュース、ソーシャルセンチメントを取得する。
無料枠: 60 req/min
"""

from datetime import datetime, timedelta

import requests

from ..config.settings import FINNHUB_API_KEY, FINNHUB_BASE_URL


def _finnhub_get(endpoint: str, params: dict | None = None) -> dict:
    """Finnhub API への GET リクエストを実行する。"""
    params = params or {}
    params["token"] = FINNHUB_API_KEY
    resp = requests.get(f"{FINNHUB_BASE_URL}{endpoint}", params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_stock_quote(symbol: str) -> dict:
    """リアルタイム株価を取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL", "GOOGL", "MSFT")

    Returns:
        現在の株価情報 (価格, 変動率, 高値, 安値, 出来高等)
    """
    data = _finnhub_get("/quote", {"symbol": symbol.upper()})
    return {
        "symbol": symbol.upper(),
        "current_price": data.get("c"),
        "change": data.get("d"),
        "percent_change": data.get("dp"),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "previous_close": data.get("pc"),
        "timestamp": data.get("t"),
    }


def get_company_profile(symbol: str) -> dict:
    """企業のプロフィール情報を取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL")

    Returns:
        企業名, 業種, 時価総額, IPO日等の企業情報
    """
    data = _finnhub_get("/stock/profile2", {"symbol": symbol.upper()})
    return {
        "symbol": symbol.upper(),
        "name": data.get("name"),
        "industry": data.get("finnhubIndustry"),
        "market_cap": data.get("marketCapitalization"),
        "ipo_date": data.get("ipo"),
        "logo": data.get("logo"),
        "country": data.get("country"),
        "exchange": data.get("exchange"),
        "web_url": data.get("weburl"),
    }


def get_basic_financials(symbol: str) -> dict:
    """企業の主要財務指標を取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL")

    Returns:
        PER, PBR, 配当利回り, ROE, 52週高値/安値 等の財務指標
    """
    data = _finnhub_get("/stock/metric", {"symbol": symbol.upper(), "metric": "all"})
    metric = data.get("metric", {})
    return {
        "symbol": symbol.upper(),
        "pe_ratio": metric.get("peBasicExclExtraTTM"),
        "pb_ratio": metric.get("pbAnnual"),
        "dividend_yield": metric.get("dividendYieldIndicatedAnnual"),
        "roe": metric.get("roeTTM"),
        "roa": metric.get("roaTTM"),
        "eps_ttm": metric.get("epsBasicExclExtraItemsTTM"),
        "revenue_growth_ttm": metric.get("revenueGrowthTTMYoy"),
        "week_52_high": metric.get("52WeekHigh"),
        "week_52_low": metric.get("52WeekLow"),
        "beta": metric.get("beta"),
    }


def get_market_news(category: str = "general", limit: int = 10) -> dict:
    """マーケットニュースを取得する。

    Args:
        category: ニュースカテゴリ ("general", "forex", "crypto", "merger")
        limit: 取得件数 (最大50)

    Returns:
        最新のマーケットニュース記事のリスト
    """
    data = _finnhub_get("/news", {"category": category})
    articles = data[:limit] if isinstance(data, list) else []
    return {
        "category": category,
        "count": len(articles),
        "articles": [
            {
                "headline": a.get("headline"),
                "summary": a.get("summary", "")[:300],
                "source": a.get("source"),
                "url": a.get("url"),
                "datetime": a.get("datetime"),
                "related": a.get("related"),
            }
            for a in articles
        ],
    }


def get_company_news(symbol: str, days: int = 7, limit: int = 10) -> dict:
    """特定企業に関するニュースを取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL")
        days: 過去何日分のニュースを取得するか (デフォルト: 7)
        limit: 取得件数 (最大50)

    Returns:
        対象企業に関するニュース記事のリスト
    """
    today = datetime.now()
    from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    data = _finnhub_get(
        "/company-news",
        {"symbol": symbol.upper(), "from": from_date, "to": to_date},
    )
    articles = data[:limit] if isinstance(data, list) else []
    return {
        "symbol": symbol.upper(),
        "period": f"{from_date} ~ {to_date}",
        "count": len(articles),
        "articles": [
            {
                "headline": a.get("headline"),
                "summary": a.get("summary", "")[:300],
                "source": a.get("source"),
                "url": a.get("url"),
                "datetime": a.get("datetime"),
            }
            for a in articles
        ],
    }


def get_social_sentiment(symbol: str) -> dict:
    """ソーシャルメディア上のセンチメントデータを取得する。

    Args:
        symbol: ティッカーシンボル (例: "AAPL")

    Returns:
        Reddit/Twitter でのメンション数、ポジティブ/ネガティブスコア
    """
    data = _finnhub_get("/stock/social-sentiment", {"symbol": symbol.upper()})
    reddit_data = data.get("reddit", [])
    twitter_data = data.get("twitter", [])

    def summarize(entries: list) -> dict:
        if not entries:
            return {"mentions": 0, "positive_score": 0, "negative_score": 0}
        total_mentions = sum(e.get("mention", 0) for e in entries)
        avg_positive = (
            sum(e.get("positiveScore", 0) for e in entries) / len(entries)
            if entries
            else 0
        )
        avg_negative = (
            sum(e.get("negativeScore", 0) for e in entries) / len(entries)
            if entries
            else 0
        )
        return {
            "mentions": total_mentions,
            "positive_score": round(avg_positive, 4),
            "negative_score": round(avg_negative, 4),
        }

    return {
        "symbol": symbol.upper(),
        "reddit": summarize(reddit_data),
        "twitter": summarize(twitter_data),
    }
