"""Finance All-in-One - 免费金融数据统一获取层。"""

from api import (
    get_stock_quote,
    get_stock_kline,
    get_hk_quote,
    get_hk_kline,
    get_futures_quote,
    get_futures_kline,
    get_option_chain,
    get_index_quote,
    get_index_kline,
    get_etf_quote,
    get_etf_kline,
    get_fund_nav,
    get_china_gdp,
    get_china_cpi,
    search_news,
    get_northbound_flow,
)
from core import FetchResult, fetch_with_fallback

__version__ = "4.0.0"

__all__ = [
    "__version__",
    "FetchResult",
    "fetch_with_fallback",
    "get_stock_quote",
    "get_stock_kline",
    "get_hk_quote",
    "get_hk_kline",
    "get_futures_quote",
    "get_futures_kline",
    "get_option_chain",
    "get_index_quote",
    "get_index_kline",
    "get_etf_quote",
    "get_etf_kline",
    "get_fund_nav",
    "get_china_gdp",
    "get_china_cpi",
    "search_news",
    "get_northbound_flow",
]
