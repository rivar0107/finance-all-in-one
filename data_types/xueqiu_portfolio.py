"""雪球组合数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_portfolio_nav(
    cube_symbol: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> FetchResult:
    """雪球组合净值历史。"""
    return fetch_with_fallback(
        symbol=cube_symbol,
        data_type="portfolio_nav",
        market="xueqiu",
        start_date=since,
        end_date=until,
    )


def get_portfolio_rebalancing(
    cube_symbol: str,
    count: int = 20,
    page: int = 1,
) -> FetchResult:
    """组合调仓记录。"""
    return fetch_with_fallback(
        symbol=cube_symbol,
        data_type="portfolio_rebalancing",
        market="xueqiu",
        count=count,
        page=page,
    )


def get_northbound_flow() -> FetchResult:
    """北向资金。"""
    return fetch_with_fallback(
        symbol="all",
        data_type="northbound_flow",
        market="xueqiu",
    )
