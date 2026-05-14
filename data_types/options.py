"""期权数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_option_chain(
    underlying: str,
    expiry: Optional[str] = None,
) -> FetchResult:
    """期权链（某标的的所有到期合约）。"""
    return fetch_with_fallback(
        symbol=underlying,
        data_type="option_chain",
        market="options",
        expiry=expiry,
    )


def get_option_quote(symbol: str) -> FetchResult:
    """期权实时报价（含 Greeks）。"""
    return fetch_with_fallback(
        symbol=symbol,
        data_type="option_quote",
        market="options",
    )


def get_option_expiry(underlying: str) -> FetchResult:
    """期权到期日列表。"""
    return fetch_with_fallback(
        symbol=underlying,
        data_type="option_expiry",
        market="options",
    )
