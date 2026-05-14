"""Tushare Pro 适配器

需配置 TUSHARE_TOKEN（tushare.pro 注册免费获取）。
覆盖：A 股日线、每日指标（PE/PB/市值）、财务报表、龙虎榜、融资融券、股票列表
"""

import os
from typing import Optional

import pandas as pd

# 懒加载
_ts = None
_pro = None


def _get_ts():
    global _ts, _pro
    if _ts is None:
        import tushare
        _ts = tushare
        token = os.environ.get("TUSHARE_TOKEN", "")
        if token:
            _pro = tushare.pro_api(token)
    return _ts, _pro


class TushareAdapter:
    """Tushare Pro 数据适配器"""

    name = "tushare"
    requires_key = True

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_ts()
            return _pro is not None
        except ImportError:
            return False

    @classmethod
    def _to_ts_code(cls, symbol: str) -> str:
        """转换为 tushare 代码格式：xxxxxx.SH / xxxxxx.SZ。"""
        s = str(symbol).strip().upper()
        if "." in s:
            return s
        if s.startswith("SH"):
            return f"{s[2:]}.SH"
        if s.startswith("SZ"):
            return f"{s[2:]}.SZ"
        s = s.zfill(6)
        if s.startswith(("6", "68", "88", "51", "50", "56", "58", "11", "12")):
            return f"{s}.SH"
        return f"{s}.SZ"

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取每日指标（PE/PB/市值/换手率等），最接近实时行情。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        code = cls._to_ts_code(symbol)
        try:
            df = pro.daily_basic(ts_code=code, limit=1)
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        period: str = "daily",
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取历史 K 线（日线）。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        code = cls._to_ts_code(symbol)

        # tushare 周期：D/W/M
        period_map = {"daily": "D", "weekly": "W", "monthly": "M"}
        freq = period_map.get(period, "D")

        if end_date is None:
            import datetime
            end_date = datetime.date.today().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")
        if start_date is None:
            import datetime
            days = limit * 2 if freq == "D" else limit * 14
            start_date = (datetime.date.today() - datetime.timedelta(days=days)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        try:
            df = pro.daily(
                ts_code=code,
                start_date=start_date,
                end_date=end_date,
            )
            if df is None or df.empty:
                return pd.DataFrame()
            # tushare 默认返回按日期倒序，转为正序
            df = df.sort_values("trade_date", ascending=True).reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_financial(cls, symbol: str, report_type: str = "income", **kwargs) -> pd.DataFrame:
        """获取财务报表。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        code = cls._to_ts_code(symbol)

        type_map = {
            "income": pro.income,
            "balance": pro.balancesheet,
            "cash_flow": pro.cashflow,
        }
        query_fn = type_map.get(report_type)
        if query_fn is None:
            return pd.DataFrame()

        try:
            df = query_fn(ts_code=code, limit=20)
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_dragon_tiger(cls, trade_date: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """获取龙虎榜数据。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        try:
            if trade_date is None:
                import datetime
                trade_date = datetime.date.today().strftime("%Y%m%d")
            else:
                trade_date = trade_date.replace("-", "")
            df = pro.top_list(trade_date=trade_date)
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_margin(cls, trade_date: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """获取融资融券数据。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        try:
            if trade_date is None:
                import datetime
                trade_date = datetime.date.today().strftime("%Y%m%d")
            else:
                trade_date = trade_date.replace("-", "")
            df = pro.margin(trade_date=trade_date)
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_stock_basic(cls, **kwargs) -> pd.DataFrame:
        """获取 A 股基础信息列表。"""
        _, pro = _get_ts()
        if pro is None:
            return pd.DataFrame()
        try:
            df = pro.stock_basic(exchange="", list_status="L")
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        if data_type == "stock_financial":
            return cls.fetch_financial(**kwargs)
        if data_type == "dragon_tiger":
            return cls.fetch_dragon_tiger(**kwargs)
        if data_type == "margin_trading":
            return cls.fetch_margin(**kwargs)
        if data_type == "stock_basic":
            return cls.fetch_stock_basic(**kwargs)
        return pd.DataFrame()


Adapter = TushareAdapter
