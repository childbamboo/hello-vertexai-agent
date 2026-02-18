"""FRED (Federal Reserve Economic Data) API ツール。

米国の主要経済指標を取得する。
無料枠: 完全無料 (120 req/min)
"""

import requests

from ..config.settings import FRED_API_KEY

FRED_BASE_URL = "https://api.stlouisfed.org/fred"

# 主要な経済指標のマスタ定義
INDICATOR_SERIES = {
    "gdp": {"series_id": "GDP", "name": "米国 GDP (10億ドル)", "frequency": "quarterly"},
    "gdp_growth": {"series_id": "A191RL1Q225SBEA", "name": "GDP 成長率 (%)", "frequency": "quarterly"},
    "unemployment_rate": {"series_id": "UNRATE", "name": "失業率 (%)", "frequency": "monthly"},
    "cpi": {"series_id": "CPIAUCSL", "name": "消費者物価指数 (CPI)", "frequency": "monthly"},
    "cpi_yoy": {"series_id": "CPIAUCSL", "name": "CPI 前年比", "frequency": "monthly"},
    "fed_funds_rate": {"series_id": "FEDFUNDS", "name": "FF 金利 (%)", "frequency": "monthly"},
    "treasury_10y": {"series_id": "DGS10", "name": "10年国債利回り (%)", "frequency": "daily"},
    "treasury_2y": {"series_id": "DGS2", "name": "2年国債利回り (%)", "frequency": "daily"},
    "sp500": {"series_id": "SP500", "name": "S&P 500 指数", "frequency": "daily"},
    "vix": {"series_id": "VIXCLS", "name": "VIX 恐怖指数", "frequency": "daily"},
    "initial_claims": {"series_id": "ICSA", "name": "新規失業保険申請件数", "frequency": "weekly"},
    "consumer_sentiment": {"series_id": "UMCSENT", "name": "ミシガン大消費者信頼感指数", "frequency": "monthly"},
}


def _fred_get_latest(series_id: str, limit: int = 1) -> dict:
    """FRED API から指定シリーズの最新データを取得する。"""
    resp = requests.get(
        f"{FRED_BASE_URL}/series/observations",
        params={
            "series_id": series_id,
            "api_key": FRED_API_KEY,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_economic_indicators() -> dict:
    """米国の主要経済指標の最新値を一括取得する。

    GDP成長率、失業率、CPI、FF金利、10年国債利回り、VIX 等を返す。

    Returns:
        主要経済指標の最新値と日付を含む辞書
    """
    key_indicators = [
        "gdp_growth",
        "unemployment_rate",
        "cpi",
        "fed_funds_rate",
        "treasury_10y",
        "vix",
        "consumer_sentiment",
    ]

    results = {}
    for key in key_indicators:
        info = INDICATOR_SERIES[key]
        try:
            data = _fred_get_latest(info["series_id"])
            observations = data.get("observations", [])
            if observations:
                latest = observations[0]
                value = latest.get("value", ".")
                results[key] = {
                    "name": info["name"],
                    "value": float(value) if value != "." else None,
                    "date": latest.get("date"),
                    "frequency": info["frequency"],
                }
            else:
                results[key] = {
                    "name": info["name"],
                    "value": None,
                    "date": None,
                    "frequency": info["frequency"],
                }
        except Exception as e:
            results[key] = {
                "name": info["name"],
                "value": None,
                "date": None,
                "error": str(e),
            }

    return {"indicators": results}


def get_economic_series(
    series_id: str, observation_count: int = 12
) -> dict:
    """FRED の任意のデータ系列を取得する。

    800,000+ のデータ系列から指定した系列の直近データを返す。

    Args:
        series_id: FRED シリーズ ID (例: "GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS")
        observation_count: 取得するデータポイント数 (デフォルト: 12)

    Returns:
        指定シリーズの直近データポイントのリスト
    """
    data = _fred_get_latest(series_id, limit=observation_count)
    observations = data.get("observations", [])

    return {
        "series_id": series_id,
        "count": len(observations),
        "observations": [
            {
                "date": obs.get("date"),
                "value": float(obs["value"]) if obs.get("value", ".") != "." else None,
            }
            for obs in observations
        ],
    }
