"""资讯数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def search_news(
    query: str,
    limit: int = 10,
    year: Optional[int] = None,
) -> FetchResult:
    """语义搜索新闻。"""
    return fetch_with_fallback(
        symbol=query,
        data_type="news_search",
        market="news",
        limit=limit,
        year=year,
    )


def get_announcements(
    mode: str = "all",
    stock_code: Optional[str] = None,
    start_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> FetchResult:
    """公告列表（全市场或个股）。"""
    return fetch_with_fallback(
        symbol=stock_code or "all",
        data_type="announcements",
        market="news",
        mode=mode,
        start_date=start_date,
        page=page,
        page_size=page_size,
    )


def get_reports(
    mode: str = "all",
    stock_code: Optional[str] = None,
    start_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> FetchResult:
    """研报列表。"""
    return fetch_with_fallback(
        symbol=stock_code or "all",
        data_type="reports",
        market="news",
        mode=mode,
        start_date=start_date,
        page=page,
        page_size=page_size,
    )


def get_fast_news(stock_code: Optional[str] = None) -> FetchResult:
    """实时快讯。"""
    return fetch_with_fallback(
        symbol=stock_code or "all",
        data_type="fast_news",
        market="news",
    )
