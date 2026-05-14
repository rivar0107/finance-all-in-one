"""同花顺适配器 (thsdk)

游客模式，无需任何账户配置。
覆盖：A股/港股/美股/外汇/期货/债券/ETF
独特能力：分钟K线、五档盘口、大单流向、竞价异动、3秒Tick、问财NLP、实时资讯
"""

from typing import Optional

import pandas as pd

# 懒加载
_ths = None


def _get_thsdk():
    global _ths
    if _ths is None:
        from thsdk import THS
        _ths = THS
    return _ths


class THSAdapter:
    """同花顺数据适配器"""

    name = "ths"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_thsdk()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_ths_code(cls, symbol: str, market: str = "a_share") -> str:
        """转换为同花顺 THSCODE 格式。"""
        s = str(symbol).strip()
        # 如果已经是 THSCODE，直接返回
        if s.upper().startswith(("USHA", "USZA", "USHI", "USZI", "USTM", "UHKG", "UNQQ", "UCFS", "URFI", "UFXB")):
            return s.upper()

        s = s.zfill(6)
        if market == "a_share":
            if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
                return f"USHA{s}"
            return f"USZA{s}"
        if market == "hk":
            return f"UHKG{s.lstrip('0')}"
        if market == "us":
            return f"UNQQ{s.upper()}"
        if market == "futures":
            return f"UCFS{s.upper()}"
        return s

    @classmethod
    def _resolve_market_prefix(cls, ths_code: str) -> str:
        """从 THSCODE 推断市场。"""
        prefix = ths_code[:4]
        if prefix in ("USHA", "USZA", "USTM"):
            return "a_share"
        if prefix == "UHKG":
            return "hk"
        if prefix == "UNQQ":
            return "us"
        if prefix == "UCFS":
            return "futures"
        return "a_share"

    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        with THS() as ths:
            if market == "a_share":
                resp = ths.market_data_cn(code, "基础数据")
            elif market == "hk":
                resp = ths.market_data_hk(code, "基础数据")
            elif market == "us":
                resp = ths.market_data_us(code, "基础数据")
            elif market == "futures":
                resp = ths.market_data_future(code, "基础数据")
            else:
                resp = ths.market_data_cn(code, "基础数据")
            return resp.df if hasattr(resp, "df") else pd.DataFrame(resp.data if hasattr(resp, "data") else [])

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
        """获取 K 线数据（支持分钟 K 线）。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        # 周期映射
        period_map = {
            "daily": "day", "weekly": "week", "monthly": "month",
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "60m": "60m",
        }
        ths_period = period_map.get(period, "day")

        with THS() as ths:
            if start_date and end_date:
                from datetime import datetime
                from zoneinfo import ZoneInfo
                tz = ZoneInfo("Asia/Shanghai")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=tz)
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=tz)
                resp = ths.klines(code, interval=ths_period, start_time=start_dt, end_time=end_dt)
            else:
                resp = ths.klines(code, interval=ths_period, count=limit)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_intraday(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取日内分时数据。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        with THS() as ths:
            resp = ths.intraday_data(code)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_depth(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取五档盘口深度。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        with THS() as ths:
            resp = ths.depth(code)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_ticks(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取 3 秒 Tick 数据。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        with THS() as ths:
            resp = ths.tick_level1(code)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_big_order(cls, symbol: str, market: str = "a_share", **kwargs) -> pd.DataFrame:
        """获取大单流向数据。"""
        THS = _get_thsdk()
        code = cls._to_ths_code(symbol, market)

        with THS() as ths:
            resp = ths.big_order_flow(code)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_call_auction(cls, market: str = "USHA", **kwargs) -> pd.DataFrame:
        """获取集合竞价异动数据。"""
        THS = _get_thsdk()
        # market 参数直接是 USHA/USZA
        if not market.upper().startswith(("USHA", "USZA")):
            market = "USHA"

        with THS() as ths:
            resp = ths.call_auction_anomaly(market.upper())
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_wencai(cls, condition: str, **kwargs) -> pd.DataFrame:
        """问财 NLP 选股。"""
        THS = _get_thsdk()

        with THS() as ths:
            resp = ths.wencai_nlp(condition)
            return resp.df if hasattr(resp, "df") else pd.DataFrame()

    @classmethod
    def fetch_sector_flow(cls, **kwargs) -> pd.DataFrame:
        """获取板块/行业行情。"""
        THS = _get_thsdk()

        with THS() as ths:
            # 默认获取同花顺行业列表的第一个板块行情
            resp = ths.ths_industry()
            industries = resp.data if hasattr(resp, "data") else []
            if not industries:
                return pd.DataFrame()
            first = industries[0]
            link_code = first.get("代码", first.get("THSCODE", ""))
            resp2 = ths.market_data_block(link_code, "基础数据")
            return resp2.df if hasattr(resp2, "df") else pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        """通用 fallback 方法。"""
        if data_type == "stock_quote":
            return cls.fetch_quote(**kwargs)
        if data_type == "stock_kline":
            return cls.fetch_kline(**kwargs)
        if data_type == "stock_intraday":
            return cls.fetch_intraday(**kwargs)
        if data_type == "stock_depth":
            return cls.fetch_depth(**kwargs)
        if data_type == "stock_ticks":
            return cls.fetch_ticks(**kwargs)
        if data_type == "stock_big_order":
            return cls.fetch_big_order(**kwargs)
        if data_type == "call_auction":
            return cls.fetch_call_auction(**kwargs)
        if data_type == "wencai_screen":
            return cls.fetch_wencai(**kwargs)
        if data_type == "sector_fund_flow":
            return cls.fetch_sector_flow(**kwargs)
        return pd.DataFrame()


Adapter = THSAdapter
