"""Twelve Data 适配器

需配置 TWELVE_DATA_API_KEY（twelvedata.com 注册免费获取）。
覆盖：多市场实时行情、历史 K 线（支持分钟/日/周/月）
"""

import os
from typing import Optional

import pandas as pd

# 懒加载
_td = None
_client = None


def _get_td():
    global _td, _client
    if _td is None:
        import twelvedata
        _td = twelvedata
        api_key = os.environ.get("TWELVE_DATA_API_KEY", "")
        if api_key:
            _client = twelvedata.TDClient(apikey=api_key)
    return _td, _client


class TwelveDataAdapter:
    """Twelve Data 数据适配器"""

    name = "twelve_data"
    requires_key = True

    @classmethod
    def is_available(cls) -> bool:
        try:
            _, client = _get_td()
            return client is not None
        except ImportError:
            return False

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        _, client = _get_td()
        if client is None:
            return pd.DataFrame()
        try:
            resp = client.quote(symbol=symbol.upper()).as_json()
            df = pd.DataFrame([resp]) if isinstance(resp, dict) else pd.DataFrame()
            return df
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
        """获取历史 K 线。"""
        _, client = _get_td()
        if client is None:
            return pd.DataFrame()

        interval_map = {
            "daily": "1day",
            "weekly": "1week",
            "monthly": "1month",
            "1m": "1min",
            "5m": "5min",
            "15m": "15min",
            "30m": "30min",
            "60m": "1h",
        }
        interval = interval_map.get(period, "1day")

        try:
            ts = client.time_series(
                symbol=symbol.upper(),
                interval=interval,
                outputsize=limit,
                start_date=start_date,
                end_date=end_date,
            )
            df = ts.as_pandas()
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        return pd.DataFrame()


Adapter = TwelveDataAdapter
