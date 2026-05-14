"""A股股票数据接口"""

from typing import Optional

from core.fetcher import fetch_with_fallback
from core.result import FetchResult


def get_stock_quote(symbol: str) -> FetchResult:
    """个股实时行情。

    路由：腾讯 -> 新浪 -> FTShare -> efinance -> AKShare
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_quote",
        market="a_share",
    )


def get_stock_kline(
    symbol: str,
    period: str = "daily",
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> FetchResult:
    """个股 K 线。

    路由：FTShare -> 腾讯 -> 网易CSV -> 百度(复权) -> AKShare -> efinance
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_kline",
        market="a_share",
        period=period,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
    )


def get_stock_minute_kline(symbol: str, interval: str = "5m", count: int = 78) -> FetchResult:
    """个股分钟 K 线。

    路由：同花顺(thsdk) 独占。需要安装 thsdk。
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_minute_kline",
        market="a_share",
        period=interval,
        limit=count,
    )


def get_stock_intraday(symbol: str) -> FetchResult:
    """个股日内分时。

    路由：东方财富 -> 同花顺
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_intraday",
        market="a_share",
    )


def get_stock_depth(symbol: str) -> FetchResult:
    """五档盘口深度。

    路由：同花顺(thsdk) -> mootdx
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_depth",
        market="a_share",
    )


def get_stock_ticks(symbol: str, date: Optional[str] = None) -> FetchResult:
    """逐笔成交(Tick)。

    路由：mootdx(TDX) 独占。需要安装 mootdx。
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_ticks",
        market="a_share",
        start_date=date,
    )


def get_stock_big_order(symbol: str) -> FetchResult:
    """大单流向。

    路由：同花顺(thsdk) 独占。
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_big_order",
        market="a_share",
    )


def get_stock_call_auction(market: str = "USHA") -> FetchResult:
    """集合竞价异动。

    路由：同花顺(thsdk) 独占。
    """
    return fetch_with_fallback(
        symbol=market,
        data_type="call_auction",
        market="a_share",
    )


def get_stock_financial(
    symbol: str,
    report_type: str = "income",
    year: Optional[int] = None,
    quarter: Optional[int] = None,
) -> FetchResult:
    """财务数据（income/balance/cashflow）。

    路由：FTShare -> 网易 -> AKShare
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_financial",
        market="a_share",
        report_type=report_type,
        year=year,
        quarter=quarter,
    )


def get_stock_holders(symbol: str, holder_type: str = "ten") -> FetchResult:
    """股东数据（ten/ften/nums）。

    路由：FTShare
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="stock_holders",
        market="a_share",
        holder_type=holder_type,
    )


def get_stock_pledge(symbol: Optional[str] = None) -> FetchResult:
    """股权质押（个股或全市场）。

    路由：FTShare
    """
    return fetch_with_fallback(
        symbol=symbol or "all",
        data_type="stock_pledge",
        market="a_share",
    )


def get_margin_trading(
    page: int = 1, page_size: int = 20, get_all: bool = False
) -> FetchResult:
    """融资融券。

    路由：FTShare -> AKShare
    """
    return fetch_with_fallback(
        symbol="all",
        data_type="margin_trading",
        market="a_share",
        page=page,
        page_size=page_size,
        get_all=get_all,
    )


def get_ipo_list(
    page: int = 1, page_size: int = 20, get_all: bool = False
) -> FetchResult:
    """IPO 列表。

    路由：FTShare -> AKShare -> 同花顺
    """
    return fetch_with_fallback(
        symbol="all",
        data_type="ipo_list",
        market="a_share",
        page=page,
        page_size=page_size,
        get_all=get_all,
    )


def get_share_change(symbol: str, page: int = 1, page_size: int = 20) -> FetchResult:
    """股本变动数据。

    路由：FTShare 独占。
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="share_change",
        market="a_share",
        page=page,
        page_size=page_size,
    )


def get_performance_express(
    symbol: str = None,
    mode: str = "single",
    year: int = None,
    report_type: str = None,
) -> FetchResult:
    """业绩快报数据。

    路由：FTShare 独占。
    mode="single" 时需要 symbol；mode="all" 时需要 year 和 report_type。
    """
    kwargs = {"mode": mode}
    if year:
        kwargs["year"] = year
    if report_type:
        kwargs["report_type"] = report_type
    return fetch_with_fallback(
        symbol=symbol or "all",
        data_type="performance_express",
        market="a_share",
        **kwargs,
    )


def get_performance_forecast(
    symbol: str = None,
    mode: str = "single",
    year: int = None,
    report_type: str = None,
) -> FetchResult:
    """业绩预告数据。

    路由：FTShare 独占。
    mode="single" 时需要 symbol；mode="all" 时需要 year 和 report_type。
    """
    kwargs = {"mode": mode}
    if year:
        kwargs["year"] = year
    if report_type:
        kwargs["report_type"] = report_type
    return fetch_with_fallback(
        symbol=symbol or "all",
        data_type="performance_forecast",
        market="a_share",
        **kwargs,
    )


def get_cb_base(symbol: str) -> FetchResult:
    """可转债基础数据。

    路由：FTShare 独占。
    """
    return fetch_with_fallback(
        symbol=symbol,
        data_type="cb_base",
        market="a_share",
    )


def get_cb_list() -> FetchResult:
    """可转债列表。

    路由：FTShare 独占。
    """
    return fetch_with_fallback(
        symbol="all",
        data_type="cb_list",
        market="a_share",
    )


def screen_stocks_wencai(condition: str) -> FetchResult:
    """问财 NLP 选股。

    路由：同花顺(thsdk) 独占。
    示例条件："连续3日主力净流入，换手率大于5%，非ST"
    """
    return fetch_with_fallback(
        symbol=condition,
        data_type="wencai_screen",
        market="a_share",
    )
