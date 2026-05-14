"""港股数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_hk_quote(hk_code: str) -> FetchResult:
    """港股行情。"""
    return fetch_with_fallback(
        symbol=hk_code,
        data_type="stock_quote",
        market="hk",
    )


def get_hk_kline(
    hk_code: str,
    interval: str = "day",
    since_date: Optional[str] = None,
    until_date: Optional[str] = None,
    limit: int = 20,
) -> FetchResult:
    """港股 K 线。"""
    return fetch_with_fallback(
        symbol=hk_code,
        data_type="stock_kline",
        market="hk",
        period=interval,
        limit=limit,
        start_date=since_date,
        end_date=until_date,
    )


def get_hk_valuation(hk_code: str) -> FetchResult:
    """港股市盈率/估值分析。"""
    return fetch_with_fallback(
        symbol=hk_code,
        data_type="hk_valuation",
        market="hk",
    )
