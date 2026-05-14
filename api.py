"""纯函数 API 聚合 - 供其他 Skill 直接 import 调用。"""

from core.fetcher import batch_fetch_with_fallback
from data_types.stock import (
    get_stock_quote,
    get_stock_kline,
    get_stock_minute_kline,
    get_stock_depth,
    get_stock_ticks,
    get_stock_big_order,
    get_stock_intraday,
    get_stock_financial,
    get_stock_holders,
    get_stock_pledge,
    get_share_change,
    get_performance_express,
    get_performance_forecast,
    get_cb_base,
    get_cb_list,
    get_margin_trading,
    get_ipo_list,
    screen_stocks_wencai,
)
from data_types.etf import (
    get_etf_quote,
    get_etf_kline,
    get_etf_components,
    get_etf_pcf,
)
from data_types.index import (
    get_index_quote,
    get_index_kline,
    get_index_weight,
)
from data_types.fund import (
    get_fund_nav,
    get_fund_return,
)
from data_types.hk import (
    get_hk_quote,
    get_hk_kline,
    get_hk_valuation,
)
from data_types.futures import (
    get_futures_quote,
    get_futures_kline,
    get_futures_holdings,
)
from data_types.options import (
    get_option_chain,
    get_option_quote,
    get_option_expiry,
)
from data_types.macro import (
    get_china_gdp,
    get_china_cpi,
    get_china_ppi,
    get_china_pmi,
    get_china_lpr,
    get_china_money_supply,
    get_us_economic,
)
from data_types.news import (
    search_news,
    get_announcements,
    get_reports,
    get_fast_news,
)
from data_types.xueqiu_portfolio import (
    get_portfolio_nav,
    get_portfolio_rebalancing,
    get_northbound_flow,
)

__all__ = [
    "batch_fetch_with_fallback",

    # stock
    "get_stock_quote",
    "get_stock_kline",
    "get_stock_minute_kline",
    "get_stock_depth",
    "get_stock_ticks",
    "get_stock_big_order",
    "get_stock_intraday",
    "get_stock_financial",
    "get_stock_holders",
    "get_stock_pledge",
    "get_share_change",
    "get_performance_express",
    "get_performance_forecast",
    "get_cb_base",
    "get_cb_list",
    "get_margin_trading",
    "get_ipo_list",
    "screen_stocks_wencai",
    # etf
    "get_etf_quote",
    "get_etf_kline",
    "get_etf_components",
    "get_etf_pcf",
    # index
    "get_index_quote",
    "get_index_kline",
    "get_index_weight",
    # fund
    "get_fund_nav",
    "get_fund_return",
    # hk
    "get_hk_quote",
    "get_hk_kline",
    "get_hk_valuation",
    # futures
    "get_futures_quote",
    "get_futures_kline",
    "get_futures_holdings",
    # options
    "get_option_chain",
    "get_option_quote",
    "get_option_expiry",
    # macro
    "get_china_gdp",
    "get_china_cpi",
    "get_china_ppi",
    "get_china_pmi",
    "get_china_lpr",
    "get_china_money_supply",
    "get_us_economic",
    # news
    "search_news",
    "get_announcements",
    "get_reports",
    "get_fast_news",
    # xueqiu
    "get_portfolio_nav",
    "get_portfolio_rebalancing",
    "get_northbound_flow",
]
