"""期货数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_futures_quote(symbol: str) -> FetchResult:
    """期货实时行情。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="futures_quote",
        market="futures",
    )


def get_futures_kline(
    symbol: str,
    period: str = "daily",
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> FetchResult:
    """期货 K 线。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="futures_kline",
        market="futures",
        period=period,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


def get_futures_holdings(symbol: str) -> FetchResult:
    """期货持仓/库存。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="futures_holdings",
        market="futures",
    )
