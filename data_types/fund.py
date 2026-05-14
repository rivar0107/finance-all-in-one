"""基金数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_fund_nav(
    institution_code: str,
    page: int = 1,
    page_size: int = 50,
) -> FetchResult:
    """基金净值历史。"""
    return fetch_with_fallback(
        symbol=institution_code,
        data_type="fund_nav",
        market="a_share",
        page=page,
        page_size=page_size,
    )


def get_fund_return(
    institution_code: str,
    cal_type: str = "1Y",
) -> FetchResult:
    """基金收益率（1M/3M/6M/1Y/3Y/5Y/YTD）。"""
    return fetch_with_fallback(
        symbol=institution_code,
        data_type="fund_return",
        market="a_share",
        cal_type=cal_type,
    )
