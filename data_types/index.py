"""指数数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_index_quote(symbol: str) -> FetchResult:
    """指数详情。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="index_quote",
        market="a_share",
    )


def get_index_kline(
    symbol: str,
    period: str = "daily",
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> FetchResult:
    """指数 K 线。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="index_kline",
        market="a_share",
        period=period,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


def get_index_weight(
    index_code: str,
    mode: str = "list",
    page: int = 1,
    page_size: int = 20,
) -> FetchResult:
    """指数权重（汇总/明细/下载）。"""
    return fetch_with_fallback(
        symbol=index_code,
        data_type="index_weight",
        market="a_share",
        mode=mode,
        page=page,
        page_size=page_size,
    )
