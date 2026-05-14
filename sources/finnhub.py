"""Finnhub 适配器

需配置 FINNHUB_API_KEY（finnhub.io 注册免费获取）。
覆盖：美股新闻、公司基本面、实时行情
"""

import os
from datetime import date, timedelta
from typing import Optional

import pandas as pd

# 懒加载
_finnhub = None
_client = None


def _get_finnhub():
    global _finnhub, _client
    if _finnhub is None:
        import finnhub
        _finnhub = finnhub
        api_key = os.environ.get("FINNHUB_API_KEY", "")
        if api_key:
            _client = finnhub.Client(api_key=api_key)
    return _finnhub, _client


class FinnhubAdapter:
    """Finnhub 数据适配器"""

    name = "finnhub"
    requires_key = True

    @classmethod
    def is_available(cls) -> bool:
        try:
            _, client = _get_finnhub()
            return client is not None
        except ImportError:
            return False

    @classmethod
    def fetch_quote(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取实时行情。"""
        _, client = _get_finnhub()
        if client is None:
            return pd.DataFrame()
        try:
            data = client.quote(symbol.upper())
            # 返回字段: c(current), d(change), dp(change percent), h(high), l(low), o(open), pc(previous close), t(timestamp)
            df = pd.DataFrame([data])
            df["symbol"] = symbol.upper()
            return df
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_news(
        cls,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """获取公司新闻。"""
        _, client = _get_finnhub()
        if client is None:
            return pd.DataFrame()

        if end_date is None:
            end_date = date.today().isoformat()
        if start_date is None:
            start_date = (date.today() - timedelta(days=7)).isoformat()

        try:
            data = client.company_news(
                symbol.upper(),
                _from=start_date,
                to=end_date,
            )
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_fundamentals(cls, symbol: str, **kwargs) -> pd.DataFrame:
        """获取公司基本面指标（metrics）。"""
        _, client = _get_finnhub()
        if client is None:
            return pd.DataFrame()
        try:
            data = client.company_basic_financials(symbol.upper(), "all")
            metrics = data.get("series", {}).get("annual", {})
            if not metrics:
                return pd.DataFrame()
            # 将 dict of lists 转为 DataFrame
            rows = []
            # metrics 格式: {metric_name: [{period: ..., v: ...}, ...]}
            for metric_name, values in metrics.items():
                for item in values:
                    rows.append({
                        "metric": metric_name,
                        "period": item.get("period"),
                        "value": item.get("v"),
                    })
            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch_macro(cls, indicator: str = "gdp", **kwargs) -> pd.DataFrame:
        """获取美国经济指标。"""
        _, client = _get_finnhub()
        if client is None:
            return pd.DataFrame()
        try:
            # 支持的指标: gdp, cpi, unemployment_rate, retail_sales, etc.
            data = client.economic_code(indicator)
            return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    @classmethod
    def fetch(cls, data_type: str, **kwargs) -> pd.DataFrame:
        if data_type in ("stock_quote", "us_quote"):
            return cls.fetch_quote(**kwargs)
        if data_type in ("us_news", "news_search"):
            return cls.fetch_news(**kwargs)
        if data_type == "us_fundamentals":
            return cls.fetch_fundamentals(**kwargs)
        if data_type in ("us_macro", "us_economic"):
            return cls.fetch_macro(**kwargs)
        return pd.DataFrame()


Adapter = FinnhubAdapter
