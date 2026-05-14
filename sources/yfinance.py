"""yfinance 适配器

Yahoo Finance 非官方封装，全球覆盖，美股历史数据稳定。
限制：A 股覆盖弱，.info 接口不稳定，15-20 分钟延迟。
"""

from typing import Optional

import pandas as pd

# 懒加载
_yf = None


def _get_yfinance():
    global _yf
    if _yf is None:
        import yfinance as yf
        _yf = yf
    return _yf


class YFinanceAdapter:
    """yfinance 数据适配器"""

    name = "yfinance"
    requires_key = False

    @classmethod
    def is_available(cls) -> bool:
        try:
            _get_yfinance()
            return True
        except ImportError:
            return False

    @classmethod
    def _to_yf_ticker(cls, symbol: str, market: str = "us") -> str:
        """转换为 yfinance ticker 格式。"""
        s = str(symbol).strip().upper()
        if market == "hk":
            if s.startswith("HK"):
                s = s[2:]
            return f"{s.zfill(5)}.HK"
        if market == "a_share":
            if s.startswith(("SH", "SZ")):
                s = s[2:]
            if s.startswith("6"):
                return f"{s}.SS"
            return f"{s}.SZ"
        return s

    @classmethod
    def fetch_kline(
        cls,
        symbol: str,
        market: str = "us",
        period: str = "daily",
        limit: int = 50,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取 K 线数据。"""
        yf = _get_yfinance()
        ticker = cls._to_yf_ticker(symbol, market)

        # yfinance 的 period 参数格式: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        period_map = {
            "daily": f"{max(1, limit // 252)}y",
            "weekly": f"{max(1, limit // 52)}y",
            "monthly": f"{max(1, limit // 12)}y",
        }
        yf_period = period_map.get(period, f"{max(1, limit // 252)}y")

        # 如果提供了日期范围，用 start/end
        if start_date or end_date:
            t = yf.Ticker(ticker)
            df = t.history(start=start_date, end=end_date)
        else:
            t = yf.Ticker(ticker)
            df = t.history(period=yf_period)

        if df.empty:
            return pd.DataFrame()

        df = df.reset_index()
        return df

    @classmethod
    def fetch_quote(cls, symbol: str, market: str = "us", **kwargs) -> pd.DataFrame:
        """获取实时行情（有 15-20 分钟延迟）。"""
        yf = _get_yfinance()
        ticker = cls._to_yf_ticker(symbol, market)

        t = yf.Ticker(ticker)
        try:
            info = t.info
            if not info:
                return pd.DataFrame()
            df = pd.DataFrame([{
                "symbol": ticker,
                "name": info.get("shortName", ""),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "open": info.get("open"),
                "high": info.get("dayHigh"),
                "low": info.get("dayLow"),
                "pre_close": info.get("previousClose"),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
            }])
            return df
        except Exception:
            return pd.DataFrame()


Adapter = YFinanceAdapter
