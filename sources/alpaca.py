"""Alpaca 适配器

需配置 ALPACA_API_KEY + ALPACA_SECRET_KEY。
覆盖：美股实时行情、历史 K 线（Bar）
"""

import os
from typing import Optional

import pandas as pd

# 懒加载
_alpaca = None


def _get_alpaca():
    global _alpaca
    if _alpaca is None:
        import alpaca_trade_api
        _alpaca = alpaca_trade_api
    return _alpaca


class AlpacaAdapter:
    """Alpaca 数据适配器"""

    name = "alpaca"
    requires_key = True

    @classmethod
    def _get_client(cls):
        """创建 REST client（从环境变量读取 Key）。"""
        alpaca = _get_alpaca()
        api_key = os.environ.get("ALPACA_API_KEY", "")
        api_secret = os.environ.get("ALPACA_SECRET_KEY", "")
        if not api_key or not api_secret:
            return None
        return alpaca.REST(
            api_key,
            api_secret,
            base_url="https://paper-api.alpaca.markets",
            raw_data=True,
        )

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_alpaca()
            return bool(
                os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY")
            )
        except ImportError:
            return False

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取美股实时行情（Latest Quote）。"""
        client = cls._get_client()
        if client is None:
            return pd.DataFrame()
        try:
            quote = client.get_latest_quote(symbol)
            # raw_data=True 时返回 dict
            if isinstance(quote, dict):
                df = pd.DataFrame([quote])
            else:
                df = pd.DataFrame([dict(quote)])
            df["symbol"] = symbol.upper()
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
        """获取历史 Bar 数据。"""
        client = cls._get_client()
        if client is None:
            return pd.DataFrame()

        timeframe_map = {
            "daily": "1Day",
            "weekly": "1Week",
            "monthly": "1Month",
            "1m": "1Min",
            "5m": "5Min",
            "15m": "15Min",
            "60m": "1Hour",
        }
        timeframe = timeframe_map.get(period, "1Day")

        try:
            if start_date and end_date:
                bars = client.get_bars(
                    symbol,
                    timeframe,
                    start=start_date,
                    end=end_date,
                    adjustment="all",
                )
            else:
                bars = client.get_bars(
                    symbol,
                    timeframe,
                    limit=limit,
                    adjustment="all",
                )
            df = bars.df if hasattr(bars, "df") else pd.DataFrame(bars)
            if not df.empty and "symbol" not in df.columns:
                df["symbol"] = symbol.upper()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if "kline" in data_type:
            return cls.fetch_kline(**kwargs)
        if "quote" in data_type:
            return cls.fetch_quote(**kwargs)
        return pd.DataFrame()


Adapter = AlpacaAdapter
