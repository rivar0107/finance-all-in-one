"""ETF 数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_etf_quote(symbol: str) -> FetchResult:
    """ETF 详情与估值。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="etf_quote",
        market="a_share",
    )


def get_etf_kline(
    symbol: str,
    period: str = "daily",
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> FetchResult:
    """ETF K 线。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="etf_kline",
        market="a_share",
        period=period,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


def get_etf_components(symbol: str) -> FetchResult:
    """ETF 成份股。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="etf_components",
        market="a_share",
    )


def get_etf_pcf(symbol: str, date: Optional[str] = None) -> FetchResult:
    """ETF PCF（申购赎回清单）。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="etf_pcf",
        market="a_share",
        start_date=date,
    )
