"""FTShare 适配器

非凸金融数据服务，HTTP GET 请求。
覆盖：A股行情/K线/价格、财务报表、宏观、新闻、公告、大宗交易、融资融券、IPO

请求头：
- 行情类接口（/app/api/v2/*）需要 X-Client-Name: ft-web
- 数据类接口（/data/api/v1/*）一般不需要鉴权头
"""

import os
from typing import Optional, Union

import pandas as pd
import requests

from config import REQUEST_TIMEOUT


class FTShareAdapter:
    """FTShare 数据适配器"""

    name = "ftshare"
    requires_key = False

    BASE_URL = os.environ.get("FTSHARE_BASE_URL", "https://market.ft.tech")
    CLIENT_NAME = "ft-web"

    @classmethod
    def is_available(cls) -> bool:
        return True

    # ─── 代码格式转换 ───
    @classmethod
    def _to_ft_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为 FTShare 代码格式：带市场后缀。"""
        s = str(symbol).strip().upper()
        if "." in s:
            # 已有后缀，标准化
            if s.endswith(".SH"):
                return s.replace(".SH", ".XSHG")
            if s.endswith(".SZ"):
                return s.replace(".SZ", ".XSHE")
            return s
        if s.startswith("SH"):
            return f"{s[2:]}.XSHG"
        if s.startswith("SZ"):
            return f"{s[2:]}.XSHE"
        if s.startswith("BJ"):
            return f"{s[2:]}.BJ"

        s = s.zfill(6)
        if market == "a_share":
            if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
                return f"{s}.XSHG"
            return f"{s}.XSHE"
        if market == "hk":
            return f"{s.lstrip('0')}.HK"
        if market == "us":
            return s
        return s

    # ─── HTTP 请求 ───
    @classmethod
    def _request(cls, endpoint: str, params: dict = None, need_client_header: bool = False) -> dict:
        url = f"{cls.BASE_URL}{endpoint}"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        if need_client_header:
            headers["X-Client-Name"] = cls.CLIENT_NAME
        last_error = None
        for _ in range(2):
            try:
                resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.ChunkedEncodingError as e:
                last_error = e
                continue
        raise last_error

    @classmethod
    def _items_to_dataframe(cls, data: Union[dict, list]) -> pd.DataFrame:
        """将 FTShare 响应转换为 DataFrame，保留空结果的结构信息。"""
        if isinstance(data, list):
            return pd.DataFrame(data)
        items = data.get("items", data.get("data", []))
        if isinstance(items, list) and items:
            return pd.DataFrame(items)
        if isinstance(items, list):
            return pd.DataFrame([{
                "total_items": data.get("total_items", 0),
                "total_pages": data.get("total_pages", 0),
            }]).iloc[0:0]
        return pd.DataFrame(data)

    # ─── 行情类（需 X-Client-Name）───
    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取实时行情（通过 prices 接口）。"""
        try:
            code = cls._to_ft_code(symbol, market)
            data = cls._request(f"/app/api/v2/stocks/{code}/prices", need_client_header=True)
            return pd.DataFrame([data]) if isinstance(data, dict) else pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        market: str = "a_share",
        period: str = "daily",
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取 K 线数据。"""
        try:
            code = cls._to_ft_code(symbol, market)
            period_map = {"daily": "DAY1", "weekly": "WEEK1", "monthly": "MONTH1", "yearly": "YEAR1"}
            span = period_map.get(period, "DAY1")
            params = {"span": span}
            if limit:
                params["limit"] = limit
            data = cls._request(f"/app/api/v2/stocks/{code}/ohlcs", params, need_client_header=True)
            ohlcs = data.get("ohlcs", []) if isinstance(data, dict) else []
            return pd.DataFrame(ohlcs)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_stock_list(cls, **kwargs) -> pd.DataFrame:
        """获取 A 股股票列表。"""
        try:
            data = cls._request("/data/api/v1/market/data/stock-list")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 财务类 ───
    @classmethod
    def fetch_financial(cls, symbol: str, report_type: str = "income", **kwargs) -> pd.DataFrame:
        """获取财务数据（利润表/资产负债表/现金流量表）。"""
        try:
            code = cls._to_ft_code(symbol, "a_share")
            type_map = {
                "income": "income",
                "balance": "balance",
                "balance_sheet": "balance",
                "cash_flow": "cashflow",
                "cashflow": "cashflow",
            }
            ft_type = type_map.get(report_type, "income")
            params = {"mode": "single", "stock_code": code}
            data = cls._request(f"/data/api/v1/market/data/finance/{ft_type}", params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 宏观类 ───
    @classmethod
    def fetch_macro(cls, indicator: str = "gdp", **kwargs) -> pd.DataFrame:
        """获取宏观经济数据。"""
        try:
            indicator_map = {
                "gdp": "china-gdp",
                "cpi": "china-cpi",
                "ppi": "china-ppi",
                "pmi": "china-pmi",
                "lpr": "china-lpr",
                "money_supply": "china-money-supply",
                "credit": "china-credit-loans",
                "trade": "china-customs-trade",
                "fiscal": "china-fiscal-revenue",
                "tax": "china-tax-revenue",
                "retail": "china-retail-sales",
                "fai": "china-fixed-asset-investment",
                "industrial": "china-industrial-added-value",
                "forex": "china-forex-gold",
                "reserve": "china-reserve-ratio",
                "us_economic": "us-economic-by-type",
            }
            ft_indicator = indicator_map.get(indicator, indicator)
            data = cls._request(f"/data/api/v1/market/data/economic/{ft_indicator}")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 新闻/公告 ───
    @classmethod
    def fetch_news(cls, query: str = "", limit: int = 10, **kwargs) -> pd.DataFrame:
        """语义搜索新闻。"""
        try:
            params = {"query": query, "limit": limit}
            data = cls._request("/data/api/v1/market/data/semantic-search-news", params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_announcements(cls, symbol: str = None, **kwargs) -> pd.DataFrame:
        """获取公告列表。"""
        try:
            params = {}
            if symbol:
                params["stock_code"] = cls._to_ft_code(symbol, "a_share")
            data = cls._request("/data/api/v1/market/data/announcements/stock-announcements", params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 特色数据 ───
    @classmethod
    def fetch_block_trades(cls, **kwargs) -> pd.DataFrame:
        """获取大宗交易数据。"""
        try:
            data = cls._request("/data/api/v1/market/data/block-trades")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_margin(cls, **kwargs) -> pd.DataFrame:
        """获取融资融券数据。"""
        try:
            data = cls._request("/data/api/v1/market/data/margin-trading-details")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_ipo(cls, **kwargs) -> pd.DataFrame:
        """获取 IPO 数据。"""
        try:
            data = cls._request("/data/api/v1/market/data/stock-ipos")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 股东数据 ───
    @classmethod
    def fetch_stock_holders(
        cls, symbol: str, market: str = "a_share", holder_type: str = "ten", **kwargs
    ) -> pd.DataFrame:
        """获取股东数据（十大股东 / 十大流通股东 / 股东户数）。

        Args:
            holder_type: "ten" | "ften" | "nums"
        """
        try:
            code = cls._to_ft_code(symbol, market)
            endpoint_map = {
                "ten": "/data/api/v1/market/data/holder/stock-holder-ten",
                "ften": "/data/api/v1/market/data/holder/stock-holder-ften",
                "nums": "/data/api/v1/market/data/holder/stock-holder-nums",
            }
            endpoint = endpoint_map.get(holder_type, endpoint_map["ten"])
            params = {"stock_code": code}
            data = cls._request(endpoint, params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 股权质押 ───
    @classmethod
    def fetch_pledge(
        cls, symbol: str = None, market: str = "a_share", **kwargs
    ) -> pd.DataFrame:
        """获取股权质押数据。

        无 symbol 时返回全市场质押概况；有 symbol 时返回个股质押明细。
        """
        try:
            if symbol and symbol != "all":
                code = cls._to_ft_code(symbol, market)
                params = {"stock_code": code}
                data = cls._request(
                    "/data/api/v1/market/data/pledge/pledge-detail", params
                )
            else:
                data = cls._request("/data/api/v1/market/data/pledge/pledge-summary")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 股本变动 ───
    @classmethod
    def fetch_share_change(
        cls,
        symbol: str,
        market: str = "a_share",
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ) -> pd.DataFrame:
        """获取股本变动数据。"""
        try:
            code = cls._to_ft_code(symbol, market)
            params = {"stock_code": code, "page": page, "page_size": page_size}
            data = cls._request("/data/api/v1/market/data/holder/stock-share-chg", params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 业绩快报 ───
    @classmethod
    def fetch_performance(
        cls,
        symbol: str = None,
        market: str = "a_share",
        mode: str = "single",
        year: int = None,
        report_type: str = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取业绩快报数据。

        mode="single" 时需要 symbol；mode="all" 时需要 year 和 report_type。
        report_type: q1 | q2 | q3 | annual
        """
        try:
            params = {"mode": mode}
            if mode == "single" and symbol:
                params["stock_code"] = cls._to_ft_code(symbol, market)
            if year:
                params["year"] = year
            if report_type:
                params["report_type"] = report_type
            data = cls._request(
                "/data/api/v1/market/data/finance/stock-performance-express", params
            )
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 业绩预告 ───
    @classmethod
    def fetch_performance_forecast(
        cls,
        symbol: str = None,
        market: str = "a_share",
        mode: str = "single",
        year: int = None,
        report_type: str = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取业绩预告数据。

        mode="single" 时需要 symbol；mode="all" 时需要 year 和 report_type。
        """
        try:
            params = {"mode": mode}
            if mode == "single" and symbol:
                params["stock_code"] = cls._to_ft_code(symbol, market)
            if year:
                params["year"] = year
            if report_type:
                params["report_type"] = report_type
            data = cls._request(
                "/data/api/v1/market/data/finance/stock-performance-forecast", params
            )
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 可转债 ───
    @classmethod
    def fetch_cb_base(
        cls, symbol: str, market: str = "a_share", **kwargs
    ) -> pd.DataFrame:
        """获取可转债基础数据。"""
        try:
            # 可转债代码直接传，不需要市场转换
            params = {"symbol_code": symbol}
            data = cls._request("/data/api/v1/market/data/cb/cb-base-data", params)
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_cb_list(cls, **kwargs) -> pd.DataFrame:
        """获取可转债列表。"""
        try:
            data = cls._request("/data/api/v1/market/data/cb/cb-lists")
            return cls._items_to_dataframe(data)
        except Exception:
            return pd.DataFrame()

    # ─── 通用 fallback ───
    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        if data_type == "stock_financial":
            return cls.fetch_financial(**kwargs)
        if data_type in ("china_macro", "us_macro"):
            return cls.fetch_macro(**kwargs)
        if data_type == "news_search":
            return cls.fetch_news(**kwargs)
        if data_type == "announcements":
            return cls.fetch_announcements(**kwargs)
        if data_type == "block_trades":
            return cls.fetch_block_trades(**kwargs)
        if data_type == "margin_trading":
            return cls.fetch_margin(**kwargs)
        if data_type == "ipo_list":
            return cls.fetch_ipo(**kwargs)
        if data_type == "stock_holders":
            return cls.fetch_stock_holders(**kwargs)
        if data_type == "stock_pledge":
            return cls.fetch_pledge(**kwargs)
        if data_type == "share_change":
            return cls.fetch_share_change(**kwargs)
        if data_type == "performance_express":
            return cls.fetch_performance(**kwargs)
        if data_type == "performance_forecast":
            return cls.fetch_performance_forecast(**kwargs)
        if data_type == "cb_base":
            return cls.fetch_cb_base(**kwargs)
        if data_type == "cb_list":
            return cls.fetch_cb_list(**kwargs)
        return pd.DataFrame()


Adapter = FTShareAdapter
